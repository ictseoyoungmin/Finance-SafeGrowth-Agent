from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import RiskLevel


DEMO_TEXT = (
    "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! "
    "원금 걱정 없이 시작하세요."
)


def test_rule_engine_detects_investment_risks() -> None:
    hits = RuleEngine().scan(DEMO_TEXT)

    categories = {hit.risk_category for hit in hits}

    assert "확정 수익 오인" in categories
    assert "원금 보장 오인" in categories
    assert "과장 표현" in categories


def test_rule_engine_returns_span_offsets() -> None:
    hits = RuleEngine().scan(DEMO_TEXT)
    span_texts = {hit.span_text for hit in hits}

    assert {"누구나", "연 8% 수익", "안정적으로", "원금 걱정 없이"} <= span_texts

    for hit in hits:
        assert DEMO_TEXT[hit.start : hit.end] == hit.span_text
        assert hit.risk_category
        assert hit.reason
        assert 0 <= hit.confidence <= 1


def test_rule_engine_detects_non_demo_financial_ad_variants() -> None:
    text = "업계 최고 혜택으로 확정 수익률을 매월 지급하고, 원금 손실 없이 안전하게 운용됩니다."
    hits = RuleEngine().scan(text)
    span_texts = {hit.span_text for hit in hits}
    categories = {hit.risk_category for hit in hits}

    assert "업계 최고" in span_texts
    assert "확정 수익률" in span_texts
    assert "원금 손실 없이" in span_texts
    assert "안전하게" in span_texts
    assert {"과장 표현", "확정 수익 오인", "원금 보장 오인", "안정성 오인"} <= categories


def test_disclosure_in_same_sentence_downgrades_severity() -> None:
    text = (
        "지금 JB 투자상품에 가입하세요! "
        "연 8% 수익률을 기대할 수 있으며, 투자 위험을 충분히 인지하고 시작하세요."
    )
    hits = RuleEngine().scan(text)

    yield_hits = [h for h in hits if h.risk_category == "확정 수익 오인"]
    assert yield_hits, "yield-related hit expected"
    yield_hit = yield_hits[0]
    assert yield_hit.severity == RiskLevel.MEDIUM
    assert "한 단계 완화" in yield_hit.reason
    assert yield_hit.confidence < 0.95


def test_disclosure_in_different_sentence_does_not_downgrade() -> None:
    text = (
        "연 8% 수익률을 기대할 수 있습니다. "
        "투자 위험을 충분히 인지하고 시작하세요."
    )
    hits = RuleEngine().scan(text)
    yield_hit = next(h for h in hits if h.risk_category == "확정 수익 오인")
    # disclosure가 다른 문장에 있어 강등되지 않아야 함
    assert yield_hit.severity == RiskLevel.HIGH


def test_negated_disclosure_phrase_does_not_downgrade() -> None:
    # "원금 손실 없이"는 disclosure가 아니라 오인 표현. 강등 대상 아님.
    text = "연 8% 수익률, 원금 손실 없이 시작하세요."
    hits = RuleEngine().scan(text)
    yield_hit = next(h for h in hits if h.risk_category == "확정 수익 오인")
    assert yield_hit.severity == RiskLevel.HIGH
