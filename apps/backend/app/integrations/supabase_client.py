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

        url = f"{self.config.url.rstrip('/')}/rest/v1/{table}"
        headers = {
            "apikey": self.config.service_role_key or "",
            "Authorization": f"Bearer {self.config.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise RuntimeError(f"Supabase insert into {table} returned no rows.")
        return rows[0]


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
