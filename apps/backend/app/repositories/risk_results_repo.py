from app.schemas.compliance import FlaggedSpan, RiskLevel


class RiskResultsRepository:
    def save_analysis(
        self,
        content_id: str,
        risk_level: RiskLevel,
        flagged_spans: list[FlaggedSpan],
    ) -> None:
        _ = (content_id, risk_level, flagged_spans)


def get_risk_results_repository() -> RiskResultsRepository:
    return RiskResultsRepository()
