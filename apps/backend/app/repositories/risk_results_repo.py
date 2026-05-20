from typing import Any

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.schemas.compliance import FlaggedSpan, RiskLevel


FALLBACK_RISK_RESULTS: dict[str, list[dict[str, Any]]] = {}
logger = get_logger(__name__)


class RiskResultsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def save_analysis(
        self,
        content_id: str,
        risk_level: RiskLevel,
        flagged_spans: list[FlaggedSpan],
        risk_categories: list[str],
        reviewer_notes: str,
    ) -> None:
        payload = {
            "content_id": content_id,
            "risk_level": risk_level.value,
            "flagged_spans": [span.model_dump(mode="json") for span in flagged_spans],
            "risk_categories": risk_categories,
            "reviewer_notes": reviewer_notes,
        }

        if self._supabase_client.is_configured:
            self._supabase_client.insert("risk_results", payload)
            return

        FALLBACK_RISK_RESULTS.setdefault(content_id, []).append(payload)
        logger.info("Supabase not configured; stored risk result in fallback memory.")

    def get_latest_by_content_id(self, content_id: str) -> dict[str, Any] | None:
        records = FALLBACK_RISK_RESULTS.get(content_id, [])
        if not records:
            return None
        return records[-1]


def get_risk_results_repository() -> RiskResultsRepository:
    return RiskResultsRepository(get_supabase_client())
