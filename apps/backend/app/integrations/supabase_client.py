from dataclasses import dataclass

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
        return bool(self.config.url and self.config.service_role_key)


def get_supabase_client() -> SupabaseClient:
    return SupabaseClient()
