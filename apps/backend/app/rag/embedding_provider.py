import hashlib
from typing import Protocol

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.supabase_client import is_real_value


logger = get_logger(__name__)
DEFAULT_EMBEDDING_DIMENSIONS = 3072


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class DeterministicHashEmbeddingProvider:
    dimensions = DEFAULT_EMBEDDING_DIMENSIONS

    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embedding(text, self.dimensions) for text in texts]


class GeminiEmbeddingProvider:
    dimensions = DEFAULT_EMBEDDING_DIMENSIONS

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_embedding_model
        self._client = client or httpx.Client()

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not is_real_value(self._api_key):
            raise RuntimeError("Gemini embedding API key is not configured.")
        if not texts:
            return []

        model_name = f"models/{self._model}"
        response = self._client.post(
            f"https://generativelanguage.googleapis.com/v1beta/{model_name}:batchEmbedContents",
            params={"key": self._api_key},
            json={
                "requests": [
                    {
                        "model": model_name,
                        "content": {"parts": [{"text": text}]},
                    }
                    for text in texts
                ]
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        embeddings = payload.get("embeddings") or []
        values: list[list[float]] = []
        for embedding in embeddings:
            raw_values = embedding.get("values") if isinstance(embedding, dict) else None
            if not isinstance(raw_values, list):
                raise RuntimeError("Gemini embedding response did not contain values.")
            values.append([float(value) for value in raw_values])
        if len(values) != len(texts):
            raise RuntimeError("Gemini embedding response count did not match request count.")
        return values


def get_embedding_provider() -> EmbeddingProvider:
    if is_real_value(settings.gemini_api_key):
        return GeminiEmbeddingProvider()
    if settings.app_env == "production":
        logger.warning("Using deterministic hash embeddings in production because Gemini is not configured.")
    return DeterministicHashEmbeddingProvider()


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        for index in range(0, len(digest), 4):
            integer = int.from_bytes(digest[index : index + 4], "big", signed=False)
            values.append((integer / 2**32) * 2 - 1)
            if len(values) == dimensions:
                break
        counter += 1
    norm = sum(value * value for value in values) ** 0.5 or 1.0
    return [value / norm for value in values]
