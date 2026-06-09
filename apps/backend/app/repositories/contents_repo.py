from uuid import uuid4

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.schemas.compliance import AnalyzeRequest


FALLBACK_CONTENTS: dict[str, dict[str, str]] = {}
logger = get_logger(__name__)


class ContentRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def save_original(self, request: AnalyzeRequest) -> str:
        payload = {
            "product_type": request.product_type,
            "channel": request.channel,
            "target_customer": request.target_customer,
            "language": request.language,
            "original_text": request.original_text,
        }

        if self._supabase_client.is_configured:
            try:
                row = self._supabase_client.insert("contents", payload)
                return str(row["id"])
            except Exception:
                logger.exception("Supabase contents insert failed; falling back to memory store.")

        return self._save_fallback(payload)

    def get(self, content_id: str) -> dict[str, str] | None:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_one("contents", {"id": content_id})
            except Exception:
                logger.exception("Supabase contents lookup failed; falling back to memory store.")

        return FALLBACK_CONTENTS.get(content_id)

    def delete(self, content_id: str) -> bool:
        supabase_deleted = 0
        if self._supabase_client.is_configured:
            try:
                # SupabaseClient.delete returns the number of removed rows.
                supabase_deleted = self._supabase_client.delete(
                    "contents", {"id": content_id}
                )
            except Exception:
                logger.exception("Supabase contents delete failed; falling back to memory store.")

        # OR the two paths so a Supabase-mode deletion doesn't read as
        # not-found just because the row was never in the local fallback dict
        # (which was the case for every prod content_id).
        fallback_deleted = FALLBACK_CONTENTS.pop(content_id, None) is not None
        return supabase_deleted > 0 or fallback_deleted

    def delete_all(self) -> int:
        if self._supabase_client.is_configured:
            # bulk delete via PostgREST requires an explicit filter; iterate over known ids
            for content_id in list(self.list_recent(limit=1000)):
                try:
                    self._supabase_client.delete("contents", {"id": content_id.get("id")})
                except Exception:
                    logger.exception("Supabase contents bulk delete partial failure.")

        removed = len(FALLBACK_CONTENTS)
        FALLBACK_CONTENTS.clear()
        return removed

    def list_recent(self, limit: int = 20) -> list[dict[str, str]]:
        if self._supabase_client.is_configured:
            try:
                return self._supabase_client.select_many(
                    "contents",
                    filters={},
                    order="created_at.desc",
                    limit=limit,
                )
            except Exception:
                logger.exception("Supabase contents list failed; falling back to memory store.")

        records = list(FALLBACK_CONTENTS.values())
        return list(reversed(records))[:limit]

    def _save_fallback(self, payload: dict[str, str]) -> str:
        content_id = str(uuid4())
        FALLBACK_CONTENTS[content_id] = {"id": content_id, **payload}
        logger.info("Supabase not configured; stored original content in fallback memory.")
        return content_id


def get_content_repository() -> ContentRepository:
    return ContentRepository(get_supabase_client())
