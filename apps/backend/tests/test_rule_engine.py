from app.rules.rule_engine import RuleEngine


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
