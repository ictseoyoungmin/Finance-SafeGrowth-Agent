from app.agent.state import init_state
from app.agent.tools.scan_rules import ScanRulesTool
from app.schemas.agent import AgentRunRequest
from app.schemas.compliance import RiskLevel
from app.schemas.tools import ScanRulesArgs


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def test_scan_rules_returns_high_risk_for_standard_demo() -> None:
    tool = ScanRulesTool()
    text = "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."

    result = tool.run(ScanRulesArgs(text=text), _state())

    assert result.risk_level == RiskLevel.HIGH
    categories = set(result.risk_categories)
    assert {"과장 표현", "확정 수익 오인", "안정성 오인", "원금 보장 오인"} <= categories
    span_texts = {span.span_text for span in result.flagged_spans}
    assert "누구나" in span_texts
    assert "원금 걱정 없이" in span_texts


def test_scan_rules_returns_low_for_clean_text() -> None:
    tool = ScanRulesTool()
    text = "본 상품은 시장 상황에 따라 손실이 발생할 수 있으며, 가입 전 상품설명서를 확인해 주세요."

    result = tool.run(ScanRulesArgs(text=text), _state())

    assert result.risk_level == RiskLevel.LOW
    assert result.flagged_spans == []
    assert result.risk_categories == []


def test_scan_rules_dedupes_categories_in_order() -> None:
    tool = ScanRulesTool()
    text = "누구나 누구나 받을 수 있는 상품"

    result = tool.run(ScanRulesArgs(text=text), _state())

    assert result.risk_categories == ["과장 표현"]
