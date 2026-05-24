from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.schemas.regulation import RegulationSource


FALLBACK_REGULATION_SOURCES: dict[str, dict[str, Any]] = {
    "11111111-1111-4111-8111-111111111111": {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "운영자 업로드",
        "source_type": "admin_upload",
        "url": None,
        "product_type": "공통",
        "default_risk_categories": [],
        "last_polled_at": None,
        "active": True,
    },
    "22222222-2222-4222-8222-222222222222": {
        "id": "22222222-2222-4222-8222-222222222222",
        "name": "데모 규정 seed",
        "source_type": "manual_seed",
        "url": None,
        "product_type": "투자상품",
        "default_risk_categories": ["확정 수익 오인", "안정성 오인", "원금 보장 오인", "과장 표현"],
        "last_polled_at": None,
        "active": True,
    },
}


class RegulationSourcesRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def list_active(self) -> list[RegulationSource]:
        if self._supabase_client.is_configured:
            rows = self._supabase_client.select_many(
                "regulation_sources",
                filters={"active": "true"},
                order="created_at.asc",
                limit=100,
            )
            return [RegulationSource.model_validate(row) for row in rows]
        return [
            RegulationSource.model_validate(row)
            for row in FALLBACK_REGULATION_SOURCES.values()
            if row.get("active")
        ]

    def list_all(self) -> list[RegulationSource]:
        if self._supabase_client.is_configured:
            rows = self._supabase_client.select_many(
                "regulation_sources",
                filters={},
                order="created_at.asc",
                limit=100,
            )
            return [RegulationSource.model_validate(row) for row in rows]
        return [RegulationSource.model_validate(row) for row in FALLBACK_REGULATION_SOURCES.values()]

    def get(self, source_id: str) -> RegulationSource | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one("regulation_sources", {"id": source_id})
            return RegulationSource.model_validate(row) if row else None
        row = FALLBACK_REGULATION_SOURCES.get(source_id)
        return RegulationSource.model_validate(row) if row else None

    def create(self, payload: dict[str, Any]) -> RegulationSource:
        if self._supabase_client.is_configured:
            row = self._supabase_client.insert("regulation_sources", payload)
            return RegulationSource.model_validate(row)

        source_id = str(payload.get("id") or uuid4())
        row = {
            "id": source_id,
            "name": payload["name"],
            "source_type": payload["source_type"],
            "url": payload.get("url"),
            "product_type": payload.get("product_type"),
            "default_risk_categories": list(payload.get("default_risk_categories") or []),
            "last_polled_at": payload.get("last_polled_at"),
            "active": bool(payload.get("active", True)),
        }
        FALLBACK_REGULATION_SOURCES[source_id] = row
        return RegulationSource.model_validate(row)

    def mark_polled(self, source_id: str) -> None:
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        if self._supabase_client.is_configured:
            self._supabase_client.patch("regulation_sources", {"id": source_id}, {"last_polled_at": timestamp})
            return
        if source_id in FALLBACK_REGULATION_SOURCES:
            FALLBACK_REGULATION_SOURCES[source_id]["last_polled_at"] = timestamp


def get_regulation_sources_repository() -> RegulationSourcesRepository:
    return RegulationSourcesRepository(get_supabase_client())
