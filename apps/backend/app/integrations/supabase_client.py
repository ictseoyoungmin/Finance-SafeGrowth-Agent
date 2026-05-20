from dataclasses import dataclass
from typing import Any

import httpx
from app.core.config import settings


@dataclass(frozen=True)
class SupabaseConfig:
    url: str | None
    anon_key: str | None
    service_role_key: str | None


class SupabaseClient:
    def __init__(self, config: SupabaseConfig | None = None) -> None:
        self.config = config or SupabaseConfig(
            url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            service_role_key=settings.supabase_service_role_key,
        )

    @property
    def is_configured(self) -> bool:
        return is_real_value(self.config.url) and is_real_value(self.config.service_role_key)

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("Supabase is not configured.")

        response = httpx.post(
            self._table_url(table),
            headers=self._headers(prefer="return=representation"),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise RuntimeError(f"Supabase insert into {table} returned no rows.")
        return rows[0]

    def select_one(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None = None,
    ) -> dict[str, Any] | None:
        rows = self.select_many(table, filters=filters, order=order, limit=1)
        return rows[0] if rows else None

    def select_many(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not self.is_configured:
            raise RuntimeError("Supabase is not configured.")

        params: dict[str, str] = {"select": "*"}
        params.update({key: f"eq.{value}" for key, value in filters.items()})
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)

        response = httpx.get(
            self._table_url(table),
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list):
            raise RuntimeError(f"Supabase select from {table} returned a non-list response.")
        return rows

    def _table_url(self, table: str) -> str:
        if self.config.url is None:
            raise RuntimeError("Supabase URL is not configured.")
        return f"{self.config.url.rstrip('/')}/rest/v1/{table}"

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        service_role_key = self.config.service_role_key or ""
        headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers


def is_real_value(value: str | None) -> bool:
    if value is None:
        return False

    cleaned = value.strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    placeholder_tokens = ("replace-me", "your-", "example", "placeholder")
    return not any(token in lowered for token in placeholder_tokens)


def get_supabase_client() -> SupabaseClient:
    return SupabaseClient()
