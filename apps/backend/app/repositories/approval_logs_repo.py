from typing import Any
from uuid import uuid4

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client


FALLBACK_APPROVAL_LOGS: dict[str, list[dict[str, Any]]] = {}
logger = get_logger(__name__)


class ApprovalLogsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def save(
        self,
        content_id: str,
        reviewer: str,
        decision: str,
        comment: str | None,
        selected_revision: str | None,
    ) -> str:
        payload = {
            "content_id": content_id,
            "reviewer": reviewer,
            "decision": decision,
            "comment": comment,
            "selected_revision": selected_revision,
        }

        if self._supabase_client.is_configured:
            try:
                row = self._supabase_client.insert("approval_logs", payload)
                return str(row["id"])
            except Exception:
                logger.exception("Supabase approval log insert failed; falling back to memory store.")

        return self._save_fallback(payload)

    def list_by_content_id(self, content_id: str) -> list[dict[str, Any]]:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_many(
                    "approval_logs",
                    {"content_id": content_id},
                    order="created_at.asc",
                )
            except Exception:
                logger.exception("Supabase approval log lookup failed; falling back to memory store.")

        return list(FALLBACK_APPROVAL_LOGS.get(content_id, []))

    def get_latest_by_content_id(self, content_id: str) -> dict[str, Any] | None:
        records = self.list_by_content_id(content_id)
        return records[-1] if records else None

    def delete_by_content_id(self, content_id: str) -> None:
        if self._supabase_client.is_configured:
            try:
                self._supabase_client.delete("approval_logs", {"content_id": content_id})
            except Exception:
                logger.exception("Supabase approval_logs delete failed; falling back to memory store.")
        FALLBACK_APPROVAL_LOGS.pop(content_id, None)

    def delete_all(self) -> None:
        """Fallback-memory cleanup only — Supabase rows are preserved.

        ``approval_logs.content_id`` uses ON DELETE SET NULL, so the audit
        trail survives even when its parent content is removed. We intentionally
        do not bulk-delete Supabase rows from this helper.
        """
        FALLBACK_APPROVAL_LOGS.clear()

    def _save_fallback(self, payload: dict[str, Any]) -> str:
        approval_id = str(uuid4())
        fallback_payload = {"id": approval_id, **payload}
        FALLBACK_APPROVAL_LOGS.setdefault(payload["content_id"], []).append(fallback_payload)
        logger.info("Supabase not configured; stored approval log in fallback memory.")
        return approval_id


def get_approval_logs_repository() -> ApprovalLogsRepository:
    return ApprovalLogsRepository(get_supabase_client())
