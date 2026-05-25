from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.schemas.regulation import RegulationVersion


FALLBACK_REGULATION_VERSIONS: dict[str, dict[str, Any]] = {}
FALLBACK_REGULATION_CHUNKS: list[dict[str, Any]] = []
_NEXT_CHUNK_ID = 1


class RegulationVersionsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def find_by_hash(self, source_id: str, content_hash: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one(
                "regulation_versions",
                {"source_id": source_id, "content_hash": content_hash},
            )
            return RegulationVersion.model_validate(row) if row else None
        for row in FALLBACK_REGULATION_VERSIONS.values():
            if row["source_id"] == source_id and row["content_hash"] == content_hash:
                return RegulationVersion.model_validate(row)
        return None

    def latest_for_source(self, source_id: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one(
                "regulation_versions",
                {"source_id": source_id},
                order="ingested_at.desc",
            )
            return RegulationVersion.model_validate(row) if row else None

        rows = [
            row
            for row in FALLBACK_REGULATION_VERSIONS.values()
            if row["source_id"] == source_id and row.get("superseded_by") is None
        ]
        rows.sort(key=lambda row: str(row.get("ingested_at") or ""), reverse=True)
        return RegulationVersion.model_validate(rows[0]) if rows else None

    def get(self, version_id: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one("regulation_versions", {"id": version_id})
            return RegulationVersion.model_validate(row) if row else None
        row = FALLBACK_REGULATION_VERSIONS.get(version_id)
        return RegulationVersion.model_validate(row) if row else None

    def list_by_source(self, source_id: str, limit: int = 20) -> list[RegulationVersion]:
        if self._supabase_client.is_configured:
            rows = self._supabase_client.select_many(
                "regulation_versions",
                {"source_id": source_id},
                order="ingested_at.desc",
                limit=limit,
            )
            return [RegulationVersion.model_validate(row) for row in rows]

        rows = [row for row in FALLBACK_REGULATION_VERSIONS.values() if row["source_id"] == source_id]
        rows.sort(key=lambda row: str(row.get("ingested_at") or ""), reverse=True)
        return [RegulationVersion.model_validate(row) for row in rows[:limit]]

    def insert(
        self,
        *,
        source_id: str,
        title: str,
        version_label: str | None,
        effective_date: date | None,
        content_hash: str,
        raw_text: str,
        chunks: list[dict[str, Any]],
    ) -> RegulationVersion:
        payload = {
            "source_id": source_id,
            "title": title,
            "version_label": version_label,
            "effective_date": effective_date.isoformat() if effective_date else None,
            "content_hash": content_hash,
            "raw_text": raw_text,
            "chunk_count": len(chunks),
        }
        if self._supabase_client.is_configured:
            row = self._supabase_client.insert("regulation_versions", payload)
            version_id = str(row["id"])
            for chunk in chunks:
                self._supabase_client.insert("regulation_chunks", {**chunk, "version_id": version_id})
            return RegulationVersion.model_validate(row)

        global _NEXT_CHUNK_ID
        version_id = str(uuid4())
        row = {
            "id": version_id,
            **payload,
            "superseded_by": None,
            "ingested_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        FALLBACK_REGULATION_VERSIONS[version_id] = row
        for chunk in chunks:
            FALLBACK_REGULATION_CHUNKS.append(
                {
                    "id": _NEXT_CHUNK_ID,
                    "version_id": version_id,
                    **chunk,
                }
            )
            _NEXT_CHUNK_ID += 1
        return RegulationVersion.model_validate(row)

    def mark_superseded(self, version_id: str, superseded_by: str) -> None:
        if self._supabase_client.is_configured:
            self._supabase_client.patch(
                "regulation_versions",
                {"id": version_id},
                {"superseded_by": superseded_by},
            )
            return
        if version_id in FALLBACK_REGULATION_VERSIONS:
            FALLBACK_REGULATION_VERSIONS[version_id]["superseded_by"] = superseded_by


def get_regulation_versions_repository() -> RegulationVersionsRepository:
    return RegulationVersionsRepository(get_supabase_client())
