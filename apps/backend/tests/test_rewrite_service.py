import json

from app.integrations.gemini_client import GeminiResult
from app.repositories.regulation_docs_repo import RegulationDoc
from app.schemas.rewrite import RewriteRequest
from app.services.rewrite_service import RewriteService


class FakeGeminiClient:
    def __init__(self, payload: dict | None) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def generate_json(self, prompt: str) -> GeminiResult | None:
        self.prompts.append(prompt)
        if self.payload is None:
            return None
        return GeminiResult(payload=self.payload, model_version="fake-gemini")


class FakeContentRepository:
    def get(self, content_id: str) -> dict:
        return {
            "id": content_id,
            "product_type": "투자상품",
            "channel": "앱 푸시",
            "target_customer": "30대 직장인",
            "language": "ko",
            "original_text": "누구나 연 8% 수익을 안정적으로 받을 수 있습니다.",
        }


class FakeRiskResultsRepository:
    def get_latest_by_content_id(self, content_id: str) -> dict:
        return {
            "content_id": content_id,
            "risk_level": "HIGH",
            "risk_categories": ["확정 수익 오인", "안정성 오인"],
            "flagged_spans": [
                {
                    "span_text": "연 8% 수익",
                    "risk_category": "확정 수익 오인",
                    "severity": "HIGH",
                }
            ],
            "reviewer_notes": "수익률과 안정성 표현 완화 필요",
        }


class FakeRegulationDocsRepository:
    def search(self, risk_categories: list[str], product_type: str, limit: int = 5) -> list[RegulationDoc]:
        return [
            RegulationDoc(
                evidence_id="doc-test",
                title="투자상품 광고 가이드",
                version="test-v1",
                product_type=product_type,
                risk_categories=tuple(risk_categories),
                snippet="수익률은 확정적으로 표현하지 않습니다.",
                guideline_snippet="손실 가능성 고지 필요",
                similarity=0.9,
            )
        ]


def test_rewrite_prompt_includes_content_risk_and_evidence_context() -> None:
    gemini = FakeGeminiClient(
        {
            "revised_text_conservative": "수익 또는 손실이 발생할 수 있습니다.",
            "revised_text_marketing": "수익은 변동될 수 있으며 원금 손실 가능성이 있습니다.",
            "changes": [
                {
                    "original": "연 8% 수익",
                    "replacement": "수익은 변동될 수 있으며",
                    "reason": "확정 수익 오인 완화",
                }
            ],
        }
    )
    service = RewriteService(
        gemini_client=gemini,  # type: ignore[arg-type]
        content_repository=FakeContentRepository(),  # type: ignore[arg-type]
        risk_results_repository=FakeRiskResultsRepository(),  # type: ignore[arg-type]
        regulation_docs_repository=FakeRegulationDocsRepository(),  # type: ignore[arg-type]
    )

    response = service.rewrite(RewriteRequest(content_id="content-1", mode="marketing_balanced"))
    prompt = json.loads(gemini.prompts[0])

    assert response.revised_text_marketing == "수익은 변동될 수 있으며 원금 손실 가능성이 있습니다."
    assert prompt["source"]["original_text"] == "누구나 연 8% 수익을 안정적으로 받을 수 있습니다."
    assert prompt["risk_context"]["flagged_spans"][0]["span_text"] == "연 8% 수익"
    assert prompt["evidence"][0]["guideline_snippet"] == "손실 가능성 고지 필요"
    assert "Return only raw JSON" in prompt["instruction"]


def test_rewrite_returns_deterministic_fallback_when_gemini_unavailable() -> None:
    service = RewriteService(
        gemini_client=FakeGeminiClient(None),  # type: ignore[arg-type]
        content_repository=FakeContentRepository(),  # type: ignore[arg-type]
        risk_results_repository=FakeRiskResultsRepository(),  # type: ignore[arg-type]
        regulation_docs_repository=FakeRegulationDocsRepository(),  # type: ignore[arg-type]
    )

    response = service.rewrite(RewriteRequest(content_id="content-1", mode="marketing_balanced"))

    assert response.content_id == "content-1"
    assert response.revised_text_conservative
    assert response.revised_text_marketing
    assert response.changes
