import hashlib
import json
import re
from typing import Any

from app.integrations.llm import LlmAttempt, LlmProvider, get_llm_provider
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.regulation_docs_repo import RegulationDocsRepository, get_regulation_docs_repository
from app.repositories.risk_results_repo import RiskResultsRepository, get_risk_results_repository
from app.rules.disclosure import apply_to_spans as apply_disclosure_post_processing
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import RiskLevel
from app.schemas.rewrite import (
    ResidualSpan,
    RevisionValidation,
    RewriteAttempt,
    RewriteChange,
    RewriteRequest,
    RewriteResponse,
)
from app.services._response_cache import ResponseCache


_SEVERITY_ORDER = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}

_REWRITE_CACHE: ResponseCache[RewriteResponse] = ResponseCache()


def _llm_attempts_to_schema(attempts: list[LlmAttempt]) -> list[RewriteAttempt]:
    return [
        RewriteAttempt(
            model=item.model,
            status=item.status,
            error_code=item.error_code,
            detail=item.detail,
        )
        for item in attempts
    ]


FALLBACK_REWRITE = RewriteResponse(
    content_id="fallback",
    revised_text_conservative=(
        "본 상품은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, "
        "가입 전 상품설명서와 유의사항을 반드시 확인하시기 바랍니다."
    ),
    revised_text_marketing=(
        "시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. "
        "가입 전 상품설명서와 유의사항을 확인해 주세요."
    ),
    changes=[
        RewriteChange(
            original="연 5.0% 이자를 안정적으로",
            replacement="시장 상황에 따라 수익은 변동될 수 있으며",
            reason="확정 수익 및 안정성 오인 표현 완화",
        ),
        RewriteChange(
            original="원금 걱정 없이",
            replacement="원금 손실 가능성이 있습니다",
            reason="원금 보장 오인 표현을 필수 고지로 대체",
        ),
    ],
)


class RewriteService:
    def __init__(
        self,
        llm_provider: LlmProvider,
        content_repository: ContentRepository,
        risk_results_repository: RiskResultsRepository,
        regulation_docs_repository: RegulationDocsRepository,
        rule_engine: RuleEngine | None = None,
        cache: ResponseCache[RewriteResponse] | None = None,
    ) -> None:
        self._llm = llm_provider
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._regulation_docs_repository = regulation_docs_repository
        self._rule_engine = rule_engine or RuleEngine()
        self._cache = cache if cache is not None else _REWRITE_CACHE

    def rewrite(self, request: RewriteRequest, *, force_refresh: bool = False) -> RewriteResponse:
        context = self._resolve_context(request.content_id)
        prompt = self._build_prompt(request, context)
        cache_key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        result = self._llm.generate_json(prompt)
        if result and result.payload:
            parsed = self._parse_response(request.content_id, result.payload, context)
            if parsed:
                response = parsed.model_copy(
                    update={
                        "model_version": result.model_version,
                        "attempts": _llm_attempts_to_schema(result.attempts),
                    }
                )
                validated = self._attach_validation(response)
                self._cache.set(cache_key, validated)
                return validated

        response = self._build_fallback_response(
            request.content_id,
            context,
            attempts=_llm_attempts_to_schema(result.attempts) if result else [],
        )
        validated = self._attach_validation(response)
        self._cache.set(cache_key, validated)
        return validated

    def _attach_validation(self, response: RewriteResponse) -> RewriteResponse:
        return response.model_copy(
            update={
                "validation_conservative": self._validate_revision(response.revised_text_conservative),
                "validation_marketing": self._validate_revision(response.revised_text_marketing),
            }
        )

    def _validate_revision(self, text: str) -> RevisionValidation:
        if not text or not text.strip():
            return RevisionValidation(risk_level=RiskLevel.LOW.value)

        raw_spans = self._rule_engine.scan(text)
        processed = apply_disclosure_post_processing(text, raw_spans)

        counts = {RiskLevel.HIGH: 0, RiskLevel.MEDIUM: 0, RiskLevel.LOW: 0}
        residual: list[ResidualSpan] = []
        for span in processed:
            counts[span.severity] = counts.get(span.severity, 0) + 1
            residual.append(
                ResidualSpan(
                    span_text=span.span_text,
                    risk_category=span.risk_category,
                    severity=span.severity.value,
                )
            )

        if processed:
            risk_level = max(processed, key=lambda s: _SEVERITY_ORDER[s.severity]).severity
        else:
            risk_level = RiskLevel.LOW

        return RevisionValidation(
            risk_level=risk_level.value,
            residual_high=counts[RiskLevel.HIGH],
            residual_medium=counts[RiskLevel.MEDIUM],
            residual_low=counts[RiskLevel.LOW],
            residual_spans=residual,
        )

    def prompt_hash(self, request: RewriteRequest) -> str:
        context = self._resolve_context(request.content_id)
        return hashlib.sha256(self._build_prompt(request, context).encode("utf-8")).hexdigest()

    def _build_prompt(self, request: RewriteRequest, context: dict[str, Any]) -> str:
        return json.dumps(
            {
                "task": "financial_ad_compliance_rewrite",
                "content_id": request.content_id,
                "mode": request.mode,
                "instruction": "Return only raw JSON. Do not use markdown. Do not include explanation outside JSON.",
                "change_rules": [
                    "Every changes[].original must be a non-empty exact substring from source.original_text.",
                    "Prefer originals from risk_context.flagged_spans.",
                    "Do not invent original text that is absent from source.original_text.",
                    "If the whole sentence is rewritten, use the most relevant exact risky substring as original.",
                ],
                "source": {
                    "product_type": context["content"].get("product_type"),
                    "channel": context["content"].get("channel"),
                    "target_customer": context["content"].get("target_customer"),
                    "language": context["content"].get("language"),
                    "original_text": context["content"].get("original_text"),
                },
                "risk_context": {
                    "risk_level": context["risk_result"].get("risk_level"),
                    "risk_categories": context["risk_result"].get("risk_categories", []),
                    "flagged_spans": context["risk_result"].get("flagged_spans", []),
                    "reviewer_notes": context["risk_result"].get("reviewer_notes"),
                },
                "evidence": [
                    {
                        "evidence_id": doc.evidence_id,
                        "title": doc.title,
                        "version": doc.version,
                        "snippet": doc.snippet,
                        "guideline_snippet": doc.guideline_snippet,
                    }
                    for doc in context["evidence"]
                ],
                "response_schema": {
                    "revised_text_conservative": "string",
                    "revised_text_marketing": "string",
                    "changes": [
                        {
                            "original": "string",
                            "replacement": "string",
                            "reason": "string",
                        }
                    ],
                },
            },
            ensure_ascii=False,
        )

    def _resolve_context(self, content_id: str) -> dict[str, Any]:
        content = self._content_repository.get(content_id) or self._fallback_content(content_id)
        risk_result = self._risk_results_repository.get_latest_by_content_id(content_id) or self._fallback_risk_result()
        evidence = self._regulation_docs_repository.search(
            risk_categories=list(risk_result.get("risk_categories") or []),
            product_type=str(content.get("product_type") or "투자상품"),
        )
        return {
            "content": content,
            "risk_result": risk_result,
            "evidence": evidence,
        }

    def _fallback_content(self, content_id: str) -> dict[str, str]:
        return {
            "id": content_id,
            "product_type": "투자상품",
            "channel": "앱 푸시",
            "target_customer": "30대 직장인",
            "language": "ko",
            "original_text": (
                "[JB Bank] 신규 고객 특별 혜택! 누구나 가입 가능한 프리미엄 정기예금으로 "
                "연 5.0% 이자를 안정적으로 받아보세요. 원금 걱정 없이 시작하는 든든한 "
                "자산관리, 지금 신청하세요."
            ),
        }

    def _fallback_risk_result(self) -> dict[str, Any]:
        return {
            "risk_level": "HIGH",
            "risk_categories": ["과장 표현", "확정 수익 오인", "안정성 오인", "원금 보장 오인"],
            "flagged_spans": [
                {"span_text": "누구나", "risk_category": "과장 표현", "severity": "HIGH"},
                {"span_text": "연 5.0% 이자", "risk_category": "확정 수익 오인", "severity": "HIGH"},
                {"span_text": "안정적으로", "risk_category": "안정성 오인", "severity": "MEDIUM"},
                {"span_text": "원금 걱정 없이", "risk_category": "원금 보장 오인", "severity": "HIGH"},
            ],
            "reviewer_notes": "수익률, 안정성, 원금 관련 표현 완화가 필요합니다.",
        }

    def _parse_response(
        self,
        content_id: str,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> RewriteResponse | None:
        try:
            normalized = {
                **payload,
                "changes": self._sanitize_llm_changes(payload, context),
                "source": "llm",
            }
            return RewriteResponse(content_id=content_id, **normalized)
        except ValueError:
            return None

    def _sanitize_llm_changes(self, payload: dict[str, Any], context: dict[str, Any]) -> list[dict[str, str]]:
        original_text = str(context["content"].get("original_text") or "")
        raw_changes = payload.get("changes")
        if not isinstance(raw_changes, list):
            raw_changes = []

        changes: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            original = str(item.get("original") or "").strip()
            replacement = str(item.get("replacement") or "").strip()
            reason = str(item.get("reason") or "").strip()
            if not original:
                original = self._best_original_for_replacement(replacement, context)
            if not original or original in seen:
                continue
            if original != "전체 문안" and original not in original_text:
                recovered = self._best_original_for_replacement(replacement, context)
                if not recovered or recovered in seen:
                    continue
                original = recovered
            changes.append(
                {
                    "original": original,
                    "replacement": replacement or "오인 가능성을 낮춘 표현",
                    "reason": reason or "LLM 수정안의 변경 근거입니다.",
                }
            )
            seen.add(original)

        if changes:
            return changes

        return [
            {
                "original": change["original"],
                "replacement": change["marketing"],
                "reason": change["reason"],
            }
            for change in self._fallback_changes(original_text, list(context["risk_result"].get("flagged_spans") or []))
        ] or [
            {
                "original": "전체 문안",
                "replacement": "수정안 본문",
                "reason": "LLM이 전체 문장 기준 수정안을 반환했습니다.",
            }
        ]

    def _best_original_for_replacement(self, replacement: str, context: dict[str, Any]) -> str:
        flagged_spans = list(context["risk_result"].get("flagged_spans") or [])
        for span in flagged_spans:
            span_text = str(self._span_value(span, "span_text") or "").strip()
            if span_text:
                return span_text
        return "전체 문안" if replacement else ""

    def _build_fallback_response(
        self,
        content_id: str,
        context: dict[str, Any],
        attempts: list[RewriteAttempt] | None = None,
    ) -> RewriteResponse:
        attempts = attempts or []
        original_text = str(context["content"].get("original_text") or self._fallback_content(content_id)["original_text"])
        flagged_spans = list(context["risk_result"].get("flagged_spans") or [])
        changes = self._fallback_changes(original_text, flagged_spans)

        if not changes:
            return FALLBACK_REWRITE.model_copy(
                update={
                    "content_id": content_id,
                    "revised_text_conservative": self._append_disclosure(original_text, strict=True),
                    "revised_text_marketing": self._append_disclosure(original_text, strict=False),
                    "changes": [
                        RewriteChange(
                            original="전체 문안",
                            replacement="손실 가능성과 상품설명서 확인 문구 추가",
                            reason="감지된 span이 없을 때도 투자상품 필수 고지를 보강합니다.",
                        )
                    ],
                    "source": "fallback",
                    "model_version": None,
                    "attempts": attempts,
                }
            )

        return RewriteResponse(
            content_id=content_id,
            revised_text_conservative=self._compose_fallback_text(context, strict=True),
            revised_text_marketing=self._compose_fallback_text(context, strict=False),
            changes=[
                RewriteChange(original=change["original"], replacement=change["marketing"], reason=change["reason"])
                for change in changes
            ],
            source="fallback",
            model_version=None,
            attempts=attempts,
        )

    def _fallback_changes(self, original_text: str, flagged_spans: list[Any]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        seen: set[tuple[str, int, int]] = set()

        for span in flagged_spans:
            span_text = str(self._span_value(span, "span_text") or "")
            start = self._span_int(span, "start")
            end = self._span_int(span, "end")
            risk_category = str(self._span_value(span, "risk_category") or "")
            if not span_text:
                continue
            if start < 0 or end <= start or original_text[start:end] != span_text:
                start = original_text.find(span_text)
                end = start + len(span_text) if start >= 0 else -1
            if start < 0 or end <= start:
                continue

            key = (span_text, start, end)
            if key in seen:
                continue
            seen.add(key)

            conservative, marketing, reason = self._replacement_for(span_text, risk_category)
            changes.append(
                {
                    "original": span_text,
                    "start": start,
                    "end": end,
                    "conservative": conservative,
                    "marketing": marketing,
                    "reason": reason,
                }
            )

        return sorted(changes, key=lambda change: (change["start"], change["end"]))

    def _compose_fallback_text(self, context: dict[str, Any], strict: bool) -> str:
        content = context["content"]
        original_text = str(content.get("original_text") or "")
        product_type = str(content.get("product_type") or "상품")
        product_label = self._product_label(original_text, product_type)
        target_customer = str(content.get("target_customer") or "").strip()

        if strict:
            return (
                f"{product_label}은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, "
                "원금 손실 가능성이 있습니다. 가입 전 상품설명서와 투자 유의사항을 반드시 확인하시기 바랍니다."
            )

        if target_customer.endswith("고객"):
            audience = f"{target_customer}을 위한 "
        else:
            audience = f"{target_customer} 고객을 위한 " if target_customer else ""
        return (
            f"{audience}{product_label}입니다. 시장 상황에 따라 수익은 변동될 수 있고 원금 손실 가능성이 있으므로, "
            "가입 전 상품설명서와 유의사항을 확인해 주세요."
        )

    def _product_label(self, original_text: str, product_type: str) -> str:
        match = re.search(r"(?:[A-Za-z0-9가-힣]+\s*)?투자상품", original_text)
        if match:
            return match.group(0).strip()
        return product_type

    def _replacement_for(self, span_text: str, risk_category: str) -> tuple[str, str, str]:
        if "확정 수익" in risk_category:
            return (
                "수익은 시장 상황에 따라 변동될 수 있으며",
                "목표 수익은 시장 상황에 따라 달라질 수 있으며",
                "확정 수익처럼 보이는 표현을 변동 가능성 안내로 전환",
            )
        if "원금" in risk_category:
            return (
                "원금 손실 가능성이 있으며",
                "원금 손실 가능성을 확인하고",
                "원금 보장 오인 표현을 손실 가능성 고지로 대체",
            )
        if "안정" in risk_category:
            return (
                "위험과 변동 가능성을 확인한 뒤",
                "투자 위험을 확인한 뒤",
                "안정성 오인 표현을 투자 위험 확인 문구로 완화",
            )
        if "과장" in risk_category:
            return (
                "조건을 충족한 고객은",
                "조건을 확인한 고객은",
                "보편적 수혜처럼 보이는 표현을 조건 확인 문구로 완화",
            )
        return (
            "관련 조건과 유의사항을 확인한 뒤",
            f"{span_text}(조건 및 유의사항 확인 필요)",
            "오인 가능성이 있는 표현에 확인 조건 추가",
        )

    def _append_disclosure(self, text: str, strict: bool) -> str:
        disclosure = (
            "가입 전 상품설명서와 투자 유의사항을 반드시 확인하시기 바랍니다."
            if strict
            else "가입 전 상품설명서와 유의사항을 확인해 주세요."
        )
        if "상품설명서" in text or "유의사항" in text:
            return text
        return f"{text} {disclosure}"

    def _span_value(self, span: Any, key: str) -> Any:
        if isinstance(span, dict):
            return span.get(key)
        return getattr(span, key, None)

    def _span_int(self, span: Any, key: str) -> int:
        value = self._span_value(span, key)
        return value if isinstance(value, int) else -1


def get_rewrite_service() -> RewriteService:
    return RewriteService(
        llm_provider=get_llm_provider(),
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        regulation_docs_repository=get_regulation_docs_repository(),
    )
