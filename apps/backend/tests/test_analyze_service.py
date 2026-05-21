from app.integrations.gemini_client import GeminiResult
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import AnalyzeRequest
from app.services.analyze_service import AnalyzeService


class FakeGeminiClient:
    def generate_json(self, prompt: str) -> GeminiResult:
        return GeminiResult(
            payload={
                "flagged_spans": [
                    {
                        "span_text": "무려 50% 및 증가",
                        "risk_category": "과장 표현",
                        "severity": "HIGH",
                        "reason": "정확하지 않은 수치 표현이 소비자 오인을 유발할 수 있습니다.",
                        "confidence": 0.88,
                    },
                    {
                        "span_text": "",
                        "risk_category": "과장 표현",
                        "severity": "HIGH",
                        "reason": "빈 span은 무시되어야 합니다.",
                        "confidence": 0.9,
                    },
                ]
            },
            model_version="fake-gemini",
        )


class FakeContentRepository:
    def save_original(self, request: AnalyzeRequest) -> str:
        return "content-1"


class FakeRiskResultsRepository:
    def __init__(self) -> None:
        self.saved: dict | None = None

    def save_analysis(self, **kwargs) -> None:
        self.saved = kwargs


class FakeAuditService:
    def record_analysis(self, content_id: str) -> None:
        self.content_id = content_id


def test_analyze_merges_gemini_detected_spans_with_rule_spans() -> None:
    risk_repository = FakeRiskResultsRepository()
    service = AnalyzeService(
        rule_engine=RuleEngine(),
        gemini_client=FakeGeminiClient(),  # type: ignore[arg-type]
        content_repository=FakeContentRepository(),  # type: ignore[arg-type]
        risk_results_repository=risk_repository,  # type: ignore[arg-type]
        audit_service=FakeAuditService(),  # type: ignore[arg-type]
    )

    response = service.analyze(
        AnalyzeRequest(
            product_type="대출상품",
            channel="앱 푸시",
            target_customer="30대 직장인",
            language="ko",
            original_text="지금 가입하면 누구나 연 금리 23%. 2년 안에 못 갚으면 무려 50% 및 증가!",
        )
    )

    spans = {span.span_text: span for span in response.flagged_spans}

    assert "누구나" in spans
    assert spans["누구나"].source == "rule"
    assert "무려 50% 및 증가" in spans
    assert spans["무려 50% 및 증가"].source == "gemini"
    assert "" not in spans
    assert risk_repository.saved is not None
    assert any(span.source == "gemini" for span in risk_repository.saved["flagged_spans"])
