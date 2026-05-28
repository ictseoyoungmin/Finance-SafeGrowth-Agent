from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client


FALLBACK_AUDIT_LOGS: dict[str, list[dict[str, Any]]] = {}
logger = get_logger(__name__)


class AuditLogsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def save(
        self,
        content_id: str,
        action: str,
        model_version: str,
        doc_version: str,
        prompt_hash: str | None,
        created_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "content_id": content_id,
            "action": action,
            "model_version": model_version,
            "doc_version": doc_version,
            "prompt_hash": prompt_hash,
            "created_at": created_at.isoformat(),
        }
        if metadata:
            # Supabase: requires a jsonb `metadata` column (see migration
            # 0002_audit_metadata.sql). If absent, insert fails and we fall
            # back to memory below — no data loss in demo mode.
            payload["metadata"] = metadata

        if self._supabase_client.is_configured:
            try:
                self._supabase_client.insert("audit_logs", payload)
                return
            except Exception:
                logger.exception("Supabase audit log insert failed; falling back to memory store.")

        self._save_fallback(content_id, payload)

    def list_by_content_id(self, content_id: str) -> list[dict[str, Any]]:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_many(
                    "audit_logs",
                    {"content_id": content_id},
                    order="created_at.asc",
                )
            except Exception:
                logger.exception("Supabase audit log lookup failed; falling back to memory store.")

        return list(FALLBACK_AUDIT_LOGS.get(content_id, []))

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_many(
                    "audit_logs",
                    filters={},
                    order="created_at.desc",
                    limit=limit,
                )
            except Exception:
                logger.exception("Supabase audit_logs list_recent failed; falling back to memory store.")

        records: list[dict[str, Any]] = []
        for entries in FALLBACK_AUDIT_LOGS.values():
            records.extend(entries)
        records.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
        return records[:limit]

    def delete_by_content_id(self, content_id: str) -> None:
        if self._supabase_client.is_configured:
            try:
                self._supabase_client.delete("audit_logs", {"content_id": content_id})
            except Exception:
                logger.exception("Supabase audit_logs delete failed; falling back to memory store.")
        FALLBACK_AUDIT_LOGS.pop(content_id, None)

    def delete_all(self) -> None:
        if self._supabase_client.is_configured:
            for content_id in list(FALLBACK_AUDIT_LOGS.keys()):
                try:
                    self._supabase_client.delete("audit_logs", {"content_id": content_id})
                except Exception:
                    logger.exception("Supabase audit_logs bulk delete partial failure.")
        FALLBACK_AUDIT_LOGS.clear()

    def _save_fallback(self, content_id: str, payload: dict[str, Any]) -> None:
        FALLBACK_AUDIT_LOGS.setdefault(content_id, []).append(payload)
        logger.info("Supabase not configured; stored audit log in fallback memory.")


def get_audit_logs_repository() -> AuditLogsRepository:
    return AuditLogsRepository(get_supabase_client())
