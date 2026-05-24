from app.agent.state import AgentState
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import FlaggedSpan, RiskLevel
from app.schemas.tools import ScanRulesArgs, ScanRulesResult


SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
}


class ScanRulesTool:
    name = "scan_rules"
    description = (
        "Run the deterministic Korean financial-ad rule scanner over a piece of text. "
        "Returns flagged spans, the unique risk categories, and the overall risk level "
        "(LOW|MEDIUM|HIGH). This tool is fast and free; call it before search_regulation "
        "or draft_rewrite. The text must be a non-empty string."
    )
    args_model = ScanRulesArgs
    result_model = ScanRulesResult

    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        self._rule_engine = rule_engine or RuleEngine()

    def run(self, args: ScanRulesArgs, state: AgentState) -> ScanRulesResult:
        flagged_spans = self._rule_engine.scan(args.text)
        return ScanRulesResult(
            risk_level=_risk_level(flagged_spans),
            risk_categories=_risk_categories(flagged_spans),
            flagged_spans=flagged_spans,
        )


def _risk_level(spans: list[FlaggedSpan]) -> RiskLevel:
    if not spans:
        return RiskLevel.LOW
    return max(spans, key=lambda hit: SEVERITY_ORDER[hit.severity]).severity


def _risk_categories(spans: list[FlaggedSpan]) -> list[str]:
    categories: list[str] = []
    for hit in spans:
        if hit.risk_category not in categories:
            categories.append(hit.risk_category)
    return categories
