import hashlib
import json
from typing import Any

from app.integrations.gemini_client import GeminiClient, get_gemini_client
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.regulation_docs_repo import RegulationDocsRepository, get_regulation_docs_repository
from app.repositories.risk_results_repo import RiskResultsRepository, get_risk_results_repository
from app.schemas.rewrite import RewriteChange, RewriteRequest, RewriteResponse


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
            original="연 8% 수익을 안정적으로",
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
        gemini_client: GeminiClient,
        content_repository: ContentRepository,
        risk_results_repository: RiskResultsRepository,
        regulation_docs_repository: RegulationDocsRepository,
    ) -> None:
        self._gemini_client = gemini_client
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._regulation_docs_repository = regulation_docs_repository

    def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        prompt = self._build_prompt(request)
        result = self._gemini_client.generate_json(prompt)
        if result:
            parsed = self._parse_response(request.content_id, result.payload)
            if parsed:
                return parsed

        return FALLBACK_REWRITE.model_copy(update={"content_id": request.content_id})

    def prompt_hash(self, request: RewriteRequest) -> str:
        return hashlib.sha256(self._build_prompt(request).encode("utf-8")).hexdigest()

    def _build_prompt(self, request: RewriteRequest) -> str:
        context = self._resolve_context(request.content_id)
        return json.dumps(
            {
                "task": "financial_ad_compliance_rewrite",
                "content_id": request.content_id,
                "mode": request.mode,
                "instruction": "Return only raw JSON. Do not use markdown. Do not include explanation outside JSON.",
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
                "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! "
                "원금 걱정 없이 시작하세요."
            ),
        }

    def _fallback_risk_result(self) -> dict[str, Any]:
        return {
            "risk_level": "HIGH",
            "risk_categories": ["과장 표현", "확정 수익 오인", "안정성 오인", "원금 보장 오인"],
            "flagged_spans": [
                {"span_text": "누구나", "risk_category": "과장 표현", "severity": "HIGH"},
                {"span_text": "연 8% 수익", "risk_category": "확정 수익 오인", "severity": "HIGH"},
                {"span_text": "안정적으로", "risk_category": "안정성 오인", "severity": "MEDIUM"},
                {"span_text": "원금 걱정 없이", "risk_category": "원금 보장 오인", "severity": "HIGH"},
            ],
            "reviewer_notes": "수익률, 안정성, 원금 관련 표현 완화가 필요합니다.",
        }

    def _parse_response(self, content_id: str, payload: dict[str, Any]) -> RewriteResponse | None:
        try:
            return RewriteResponse(content_id=content_id, **payload)
        except ValueError:
            return None


def get_rewrite_service() -> RewriteService:
    return RewriteService(
        gemini_client=get_gemini_client(),
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        regulation_docs_repository=get_regulation_docs_repository(),
    )
