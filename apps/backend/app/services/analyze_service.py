import hashlib
import json
from typing import Any

from app.integrations.llm import LlmProvider, get_llm_provider
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.risk_results_repo import (
    RiskResultsRepository,
    get_risk_results_repository,
)
from app.rules.disclosure import apply_to_spans as apply_disclosure_post_processing
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import AnalyzeRequest, AnalyzeResponse, FlaggedSpan, RiskLevel
from app.services._response_cache import ResponseCache
from app.services.audit_service import AuditService, get_audit_service


_ANALYZE_CACHE: ResponseCache[AnalyzeResponse] = ResponseCache()


def _analyze_cache_key(request: AnalyzeRequest) -> str:
    payload = request.model_dump_json()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
}


class AnalyzeService:
    def __init__(
        self,
        rule_engine: RuleEngine,
        llm_provider: LlmProvider,
        content_repository: ContentRepository,
        risk_results_repository: RiskResultsRepository,
        audit_service: AuditService,
        cache: ResponseCache[AnalyzeResponse] | None = None,
    ) -> None:
        self._rule_engine = rule_engine
        self._llm = llm_provider
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._audit_service = audit_service
        self._cache = cache if cache is not None else _ANALYZE_CACHE

    def analyze(self, request: AnalyzeRequest, *, force_refresh: bool = False) -> AnalyzeResponse:
        cache_key = _analyze_cache_key(request)
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        content_id = self._content_repository.save_original(request)
        flagged_spans = self._merge_spans(
            request.original_text,
            [
                *self._rule_engine.scan(request.original_text),
                *self._llm_spans(request),
            ],
        )
        flagged_spans = self._post_process_disclosures(request.original_text, flagged_spans)
        risk_level = self._risk_level(flagged_spans)
        risk_categories = self._risk_categories(flagged_spans)
        reviewer_notes = self._reviewer_notes(request, flagged_spans)

        self._risk_results_repository.save_analysis(
            content_id=content_id,
            risk_level=risk_level,
            flagged_spans=flagged_spans,
            risk_categories=risk_categories,
            reviewer_notes=reviewer_notes,
        )
        self._audit_service.record_analysis(content_id)

        response = AnalyzeResponse(
            content_id=content_id,
            risk_level=risk_level,
            flagged_spans=flagged_spans,
            risk_categories=risk_categories,
            reviewer_notes=reviewer_notes,
        )
        self._cache.set(cache_key, response)
        return response

    def _llm_spans(self, request: AnalyzeRequest) -> list[FlaggedSpan]:
        prompt = json.dumps(
            {
                "task": "financial_ad_compliance_risk_detection",
                "instruction": (
                    "Return only raw JSON. Identify risky financial advertising expressions. "
                    "Every span_text must be a non-empty exact substring of original_text. "
                    "Do not invent text. Do not return rewrite suggestions."
                ),
                "source": {
                    "product_type": request.product_type,
                    "channel": request.channel,
                    "target_customer": request.target_customer,
                    "language": request.language,
                    "original_text": request.original_text,
                },
                "risk_categories": [
                    "과장 표현",
                    "확정 수익 오인",
                    "안정성 오인",
                    "원금 보장 오인",
                    "상환 부담 오인",
                    "불명확한 비용/금리 고지",
                ],
                "response_schema": {
                    "flagged_spans": [
                        {
                            "span_text": "exact substring from original_text",
                            "risk_category": "string",
                            "severity": "LOW|MEDIUM|HIGH",
                            "reason": "string",
                            "confidence": 0.0,
                        }
                    ]
                },
            },
            ensure_ascii=False,
        )
        result = self._llm.generate_json(prompt)
        if not result:
            return []

        raw_spans = result.payload.get("flagged_spans")
        if not isinstance(raw_spans, list):
            return []

        spans: list[FlaggedSpan] = []
        for item in raw_spans:
            span = self._parse_llm_span(request.original_text, item)
            if span:
                spans.append(span)
        return spans

    def _parse_llm_span(self, original_text: str, item: Any) -> FlaggedSpan | None:
        if not isinstance(item, dict):
            return None

        span_text = str(item.get("span_text") or "").strip()
        if not span_text:
            return None

        start = item.get("start")
        end = item.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or original_text[start:end] != span_text:
            start = original_text.find(span_text)
            end = start + len(span_text) if start >= 0 else -1

        if start < 0 or end <= start:
            return None

        severity = self._parse_severity(item.get("severity"))
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)):
            confidence = 0.82

        return FlaggedSpan(
            span_text=span_text,
            start=start,
            end=end,
            risk_category=str(item.get("risk_category") or "AI 추가 탐지"),
            severity=severity,
            reason=str(item.get("reason") or "LLM이 추가 검토가 필요한 표현으로 탐지했습니다."),
            confidence=max(0, min(float(confidence), 1)),
            source="llm",
        )

    def _parse_severity(self, value: Any) -> RiskLevel:
        try:
            return RiskLevel(str(value))
        except ValueError:
            return RiskLevel.MEDIUM

    def _merge_spans(self, original_text: str, spans: list[FlaggedSpan]) -> list[FlaggedSpan]:
        valid = [
            span
            for span in spans
            if span.start >= 0
            and span.end > span.start
            and original_text[span.start : span.end] == span.span_text
        ]
        selected: list[FlaggedSpan] = []
        for span in sorted(
            valid,
            key=lambda item: (
                item.start,
                -SEVERITY_ORDER[item.severity],
                -(item.end - item.start),
                0 if item.source == "rule" else 1,
            ),
        ):
            if any(span.start < existing.end and span.end > existing.start for existing in selected):
                continue
            selected.append(span)
        return sorted(selected, key=lambda hit: (hit.start, hit.end, hit.risk_category))

    def _risk_level(self, flagged_spans: list[FlaggedSpan]) -> RiskLevel:
        if not flagged_spans:
            return RiskLevel.LOW

        return max(flagged_spans, key=lambda hit: SEVERITY_ORDER[hit.severity]).severity

    def _post_process_disclosures(
        self,
        text: str,
        spans: list[FlaggedSpan],
    ) -> list[FlaggedSpan]:
        return apply_disclosure_post_processing(text, spans)

    def _risk_categories(self, flagged_spans: list[FlaggedSpan]) -> list[str]:
        categories: list[str] = []
        for hit in flagged_spans:
            if hit.risk_category not in categories:
                categories.append(hit.risk_category)
        return categories

    def _reviewer_notes(
        self,
        request: AnalyzeRequest,
        flagged_spans: list[FlaggedSpan],
    ) -> str:
        if not flagged_spans:
            return "현재 규칙 기반 검토에서 명확한 고위험 표현은 발견되지 않았습니다."

        categories = ", ".join(self._risk_categories(flagged_spans))
        return (
            f"{request.product_type} {request.channel} 문구에서 {categories} 관련 표현이 "
            "탐지되었습니다. 배포 전 표현 완화와 필수 유의사항 고지가 필요합니다."
        )


def get_analyze_service() -> AnalyzeService:
    return AnalyzeService(
        rule_engine=RuleEngine(),
        llm_provider=get_llm_provider(),
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        audit_service=get_audit_service(),
    )
