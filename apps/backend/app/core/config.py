from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_models: str = "gemini-2.5-flash,gemini-3-flash,gemini-2.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    llm_provider: str = "gemini"
    openai_base_url: str = "http://127.0.0.1:18080/v1"
    openai_api_key: str | None = "local-not-required"
    openai_model: str = "gemma-4-local"
    # Single HTTP timeout for every Gemini call. 60s keeps wizard-flow
    # requests (analyze / rewrite) responsive while still covering occasional
    # slow ingest prompts. Override via env for one-off long-running ingests.
    llm_timeout_seconds: int = 60
    llm_thinking_enabled: bool = False
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.2
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    database_url: str | None = None
    agent_max_iterations: int = 8
    agent_deadline_seconds: int = 60
    admin_api_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @cached_property
    def gemini_models_list(self) -> list[str]:
        raw = self.gemini_models or self.gemini_model or ""
        models = [m.strip() for m in raw.split(",") if m.strip()]
        return models or [self.gemini_model]


settings = Settings()
