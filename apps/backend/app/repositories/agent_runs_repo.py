from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client


FALLBACK_AGENT_RUNS: dict[str, dict[str, Any]] = {}
logger = get_logger(__name__)


class AgentRunsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def insert(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload)
        row.setdefault("id", str(uuid4()))
        row.setdefault("status", "running")
        row.setdefault("started_at", _utc_now_iso())

        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.insert("agent_runs", row)
            except Exception:
                logger.exception("Supabase agent_runs insert failed; falling back to memory store.")

        FALLBACK_AGENT_RUNS[row["id"]] = row
        logger.info("Supabase not configured; stored agent run in fallback memory.")
        return row

    def update(self, run_id: str | UUID, patch: dict[str, Any]) -> dict[str, Any] | None:
        key = str(run_id)
        if not patch:
            return self.get(key)

        if self._supabase_client.is_configured:
            try:
                updated = self._supabase_client.patch(
                    "agent_runs", filters={"id": key}, payload=patch
                )
                if updated is not None:
                    return updated
            except Exception:
                logger.exception("Supabase agent_runs update failed; falling back to memory store.")

        existing = FALLBACK_AGENT_RUNS.get(key)
        if existing is None:
            return None
        existing.update(patch)
        return existing

    def get(self, run_id: str | UUID) -> dict[str, Any] | None:
        key = str(run_id)

        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_one("agent_runs", {"id": key})
            except Exception:
                logger.exception("Supabase agent_runs lookup failed; falling back to memory store.")

        return FALLBACK_AGENT_RUNS.get(key)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_agent_runs_repository() -> AgentRunsRepository:
    return AgentRunsRepository(get_supabase_client())
