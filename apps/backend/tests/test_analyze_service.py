from app.integrations.llm import LlmJsonResult
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import AnalyzeRequest, RiskLevel
from app.services.analyze_service import AnalyzeService


class ScriptedJsonLlmProvider:
    model = "fake-llm"
    is_configured = True

    def generate_json(self, prompt: str) -> LlmJsonResult:
        return LlmJsonResult(
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
            model_version="fake-llm",
        )


class FakeContentRepository:
    def __init__(self) -> None:
        self.calls = 0

    def save_original(self, request: AnalyzeRequest) -> str:
        self.calls += 1
        return f"content-{self.calls}"


class FakeRiskResultsRepository:
    def __init__(self) -> None:
        self.saved: dict | None = None
        self.calls: list[dict] = []

    def save_analysis(self, **kwargs) -> None:
        self.saved = kwargs
        self.calls.append(kwargs)


class FakeAuditService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []
        self.content_id: str | None = None
        self.rule_categories: list[str] = []

    def record_analysis(self, content_id: str, rule_categories: list[str] | None = None) -> None:
        self.content_id = content_id
        self.rule_categories = rule_categories or []
        self.calls.append((content_id, self.rule_categories))


def test_analyze_merges_llm_detected_spans_with_rule_spans() -> None:
    risk_repository = FakeRiskResultsRepository()
    service = AnalyzeService(
        rule_engine=RuleEngine(),
        llm_provider=ScriptedJsonLlmProvider(),  # type: ignore[arg-type]
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
    assert spans["무려 50% 및 증가"].source == "llm"
    assert "" not in spans
    assert risk_repository.saved is not None
    assert any(span.source == "llm" for span in risk_repository.saved["flagged_spans"])


# --- disclosure post-processing -------------------------------------------------


class NullLlmProvider:
    """LLM provider that returns no spans — isolates rule/post-processing."""

    model = "fake-null"
    is_configured = True

    def generate_json(self, prompt: str) -> LlmJsonResult:
        return LlmJsonResult(payload={"flagged_spans": []}, model_version=self.model)


def _build_service(llm_provider: object = NullLlmProvider()) -> AnalyzeService:
    return AnalyzeService(
        rule_engine=RuleEngine(),
        llm_provider=llm_provider,  # type: ignore[arg-type]
        content_repository=FakeContentRepository(),  # type: ignore[arg-type]
        risk_results_repository=FakeRiskResultsRepository(),  # type: ignore[arg-type]
        audit_service=FakeAuditService(),  # type: ignore[arg-type]
    )


def _request(text: str) -> AnalyzeRequest:
    return AnalyzeRequest(
        product_type="예금상품",
        channel="앱 푸시",
        target_customer="30대 직장인",
        language="ko",
        original_text=text,
    )


def test_post_processing_downgrades_when_disclosure_in_same_sentence() -> None:
    text = "연 5.0% 이자를 안정적으로 받아보세요. 투자 위험을 충분히 인지하고 시작하세요."
    response = _build_service().analyze(_request(text))
    yield_span = next(s for s in response.flagged_spans if s.risk_category == "확정 수익 오인")
    assert yield_span.severity == RiskLevel.HIGH or yield_span.severity == RiskLevel.MEDIUM
    # 인접 문장에 disclosure → 강등
    assert yield_span.severity == RiskLevel.MEDIUM
    assert "인접 고지 문구" in yield_span.reason


def test_post_processing_downgrades_across_adjacent_sentences() -> None:
    text = (
        "프리미엄 정기예금으로 최대 연 5.0% 이자를 기대할 수 있습니다. "
        "원금 손실 가능성을 유의하며 시작하세요."
    )
    response = _build_service().analyze(_request(text))
    yield_spans = [s for s in response.flagged_spans if s.risk_category == "확정 수익 오인"]
    assert yield_spans, "yield-related hit expected"
    # 직후 문장의 disclosure 로 강등 (±1 sentence window)
    assert yield_spans[0].severity == RiskLevel.MEDIUM


def test_disclosure_self_span_is_stripped() -> None:
    class DisclosureLlmProvider:
        model = "fake-llm"
        is_configured = True

        def generate_json(self, prompt: str) -> LlmJsonResult:
            return LlmJsonResult(
                payload={
                    "flagged_spans": [
                        {
                            "span_text": "원금 손실 가능성을 유의하며",
                            "risk_category": "확정 수익 오인",
                            "severity": "HIGH",
                            "reason": "LLM false positive on disclosure",
                            "confidence": 0.8,
                        }
                    ]
                },
                model_version="fake-llm",
            )

    text = "원금 손실 가능성을 유의하며 자산관리를 시작하세요."
    response = _build_service(DisclosureLlmProvider()).analyze(_request(text))
    # disclosure-only span은 제거되어야 함
    assert all(
        "원금 손실 가능성을 유의하며" != span.span_text for span in response.flagged_spans
    )


def test_negated_phrase_is_not_treated_as_disclosure() -> None:
    text = "연 5.0% 이자, 원금 손실 없이 안전하게 시작하세요."
    response = _build_service().analyze(_request(text))
    yield_span = next(s for s in response.flagged_spans if s.risk_category == "확정 수익 오인")
    # "원금 손실 없이" 는 disclosure 가 아님 → 강등되지 않아야 함
    assert yield_span.severity == RiskLevel.HIGH


def test_negated_disclosure_keyword_inside_span_is_not_stripped() -> None:
    # R-A-2: "원금 손실 가능성이 전혀 없습니다" 는 LLM이 disclaimer 로 잘못 분류해
    # span 으로 보내도, 부정구 ("전혀 없") 가 있으므로 stripping 되지 않아야 한다.
    class LlmReturningNegatedDisclaimer:
        model = "fake-llm"
        is_configured = True

        def generate_json(self, prompt: str) -> LlmJsonResult:
            return LlmJsonResult(
                payload={
                    "flagged_spans": [
                        {
                            "span_text": "원금 손실 가능성이 전혀 없습니다",
                            "risk_category": "원금 보장 오인",
                            "severity": "HIGH",
                            "reason": "원금 손실 가능성을 부인하는 표현",
                            "confidence": 0.95,
                        }
                    ]
                },
                model_version="fake-llm",
            )

    text = "지금 가입하면 원금 손실 가능성이 전혀 없습니다."
    response = _build_service(LlmReturningNegatedDisclaimer()).analyze(_request(text))

    assert any(
        s.span_text == "원금 손실 가능성이 전혀 없습니다" for s in response.flagged_spans
    ), "negated risk claim 이 disclosure 로 오인되어 strip 되면 안 됨"


# --- R-A-1: cache 와 content_id 분리 -------------------------------------------


class CountingLlmProvider:
    model = "fake-llm"
    is_configured = True

    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, prompt: str) -> LlmJsonResult:
        self.calls += 1
        return LlmJsonResult(payload={"flagged_spans": []}, model_version=self.model)


def test_repeated_input_mints_new_content_id_and_reuses_risk_body() -> None:
    """같은 입력을 두 번 보내도 content_id 는 매번 새로 생성되고
    risk_results / audit 도 매번 기록된다. LLM 은 cache hit 으로 1회만 호출."""
    content_repo = FakeContentRepository()
    risk_repo = FakeRiskResultsRepository()
    audit = FakeAuditService()
    llm = CountingLlmProvider()
    service = AnalyzeService(
        rule_engine=RuleEngine(),
        llm_provider=llm,  # type: ignore[arg-type]
        content_repository=content_repo,  # type: ignore[arg-type]
        risk_results_repository=risk_repo,  # type: ignore[arg-type]
        audit_service=audit,  # type: ignore[arg-type]
    )

    request = _request("프리미엄 정기예금으로 누구나 안정적인 수익을 받으세요.")

    first = service.analyze(request)
    second = service.analyze(request)

    assert first.content_id != second.content_id, "every submission must get its own content_id"
    assert content_repo.calls == 2
    assert len(risk_repo.calls) == 2
    assert len(audit.calls) == 2
    assert llm.calls == 1, "second call should be served from cache (no extra LLM hit)"
    # cache 가 같은 risk body 를 재사용 → 둘의 risk_level / spans 동일
    assert first.risk_level == second.risk_level
    assert [s.span_text for s in first.flagged_spans] == [s.span_text for s in second.flagged_spans]


def test_force_refresh_bypasses_cache() -> None:
    content_repo = FakeContentRepository()
    risk_repo = FakeRiskResultsRepository()
    audit = FakeAuditService()
    llm = CountingLlmProvider()
    service = AnalyzeService(
        rule_engine=RuleEngine(),
        llm_provider=llm,  # type: ignore[arg-type]
        content_repository=content_repo,  # type: ignore[arg-type]
        risk_results_repository=risk_repo,  # type: ignore[arg-type]
        audit_service=audit,  # type: ignore[arg-type]
    )

    request = _request("누구나 가입 가능한 안정적인 상품.")
    service.analyze(request)
    service.analyze(request, force_refresh=True)

    assert llm.calls == 2, "force_refresh must re-invoke LLM"
    assert content_repo.calls == 2
