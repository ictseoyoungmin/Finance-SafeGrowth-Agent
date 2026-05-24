from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client


FALLBACK_AGENT_STEPS: dict[str, list[dict[str, Any]]] = {}
logger = get_logger(__name__)


class AgentStepsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def append(
        self,
        run_id: str | UUID,
        step_index: int,
        step_type: str,
        payload: dict[str, Any],
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        key = str(run_id)
        row = {
            "run_id": key,
            "step_index": step_index,
            "step_type": step_type,
            "tool_name": tool_name,
            "payload": payload,
            "created_at": _utc_now_iso(),
        }

        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.insert("agent_steps", row)
            except Exception:
                logger.exception("Supabase agent_steps insert failed; falling back to memory store.")

        FALLBACK_AGENT_STEPS.setdefault(key, []).append(row)
        return row

    def list_for_run(self, run_id: str | UUID) -> list[dict[str, Any]]:
        key = str(run_id)

        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_many(
                    "agent_steps",
                    filters={"run_id": key},
                    order="step_index.asc",
                )
            except Exception:
                logger.exception("Supabase agent_steps lookup failed; falling back to memory store.")

        return list(FALLBACK_AGENT_STEPS.get(key, []))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_agent_steps_repository() -> AgentStepsRepository:
    return AgentStepsRepository(get_supabase_client())
