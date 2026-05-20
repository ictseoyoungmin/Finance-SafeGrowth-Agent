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
    ) -> None:
        payload = {
            "content_id": content_id,
            "action": action,
            "model_version": model_version,
            "doc_version": doc_version,
            "prompt_hash": prompt_hash,
        }

        if self._supabase_client.is_configured:
            self._supabase_client.insert("audit_logs", payload)
            return

        fallback_payload = {**payload, "created_at": created_at.isoformat()}
        FALLBACK_AUDIT_LOGS.setdefault(content_id, []).append(fallback_payload)
        logger.info("Supabase not configured; stored audit log in fallback memory.")

    def list_by_content_id(self, content_id: str) -> list[dict[str, Any]]:
        return list(FALLBACK_AUDIT_LOGS.get(content_id, []))


def get_audit_logs_repository() -> AuditLogsRepository:
    return AuditLogsRepository(get_supabase_client())
