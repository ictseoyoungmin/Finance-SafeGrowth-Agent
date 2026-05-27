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


# --- 확장된 카테고리 -----------------------------------------------------------


def _categories(text: str) -> set[str]:
    return {hit.risk_category for hit in RuleEngine().scan(text)}


def test_guarantee_pattern() -> None:
    assert "보증/장담 표현" in _categories("100% 보장된 수익을 약속드립니다.")


def test_scarcity_pattern() -> None:
    assert "한정 마케팅" in _categories("오늘만 진행되는 선착순 특별 이벤트!")


def test_fee_omission_pattern() -> None:
    assert "수수료 누락" in _categories("이번 상품은 수수료 무료로 가입하실 수 있습니다.")


def test_comparison_pattern() -> None:
    assert "비교 광고" in _categories("타사 대비 가장 높은 우대금리를 제공합니다.")


def test_award_pattern() -> None:
    assert "수상/검증 과장" in _categories("3년 연속 1위 수상 상품입니다.")


def test_urgency_pattern() -> None:
    assert "시급성/감정 호소" in _categories("이번 기회 놓치지 마세요!")


def test_rate_omission_pattern() -> None:
    assert "금리 기간 미명시" in _categories("고금리 혜택을 누려보세요.")


def test_security_pattern() -> None:
    assert "보안 오인" in _categories("절대 안전한 시스템으로 자산을 지킵니다.")


def test_word_바라dsi_no_longer_false_positive() -> None:
    # "반드시 확인" 같은 disclaimer 톤에서 더 이상 잡히지 않아야 함.
    assert "과장 표현" not in _categories("가입 전 상품설명서를 반드시 확인하시기 바랍니다.")
