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
            try:
                self._supabase_client.insert("risk_results", payload)
                return
            except Exception:
                logger.exception("Supabase risk result insert failed; falling back to memory store.")

        self._save_fallback(content_id, payload)

    def get_latest_by_content_id(self, content_id: str) -> dict[str, Any] | None:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_one(
                    "risk_results",
                    {"content_id": content_id},
                    order="created_at.desc",
                )
            except Exception:
                logger.exception("Supabase risk result lookup failed; falling back to memory store.")

        records = FALLBACK_RISK_RESULTS.get(content_id, [])
        if not records:
            return None
        return records[-1]

    def _save_fallback(self, content_id: str, payload: dict[str, Any]) -> None:
        FALLBACK_RISK_RESULTS.setdefault(content_id, []).append(payload)
        logger.info("Supabase not configured; stored risk result in fallback memory.")


def get_risk_results_repository() -> RiskResultsRepository:
    return RiskResultsRepository(get_supabase_client())
