import os

import httpx
import pytest

from app.integrations.llm.openai_compatible import OpenAICompatibleLlmProvider


def test_local_llm_generate_json_smoke() -> None:
    base_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:18080/v1").rstrip("/")
    api_key = os.environ.get("OPENAI_API_KEY", "local-not-required")
    model = os.environ.get("OPENAI_MODEL", "gemma-4-local")

    try:
        health = httpx.get(f"{base_url}/health", timeout=2)
    except httpx.HTTPError as exc:
        pytest.skip(f"local LLM endpoint is unreachable: {exc}")
    if health.status_code >= 500:
        pytest.skip(f"local LLM endpoint is unhealthy: {health.status_code}")

    provider = OpenAICompatibleLlmProvider(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=30,
        max_tokens=128,
    )
    result = provider.generate_json('{"task":"reply with JSON", "schema":{"ok":true}}')

    assert result is not None
    assert isinstance(result.payload, dict)
