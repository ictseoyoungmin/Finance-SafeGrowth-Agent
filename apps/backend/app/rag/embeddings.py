from app.rag.embedding_provider import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DeterministicHashEmbeddingProvider,
    EmbeddingProvider,
    GeminiEmbeddingProvider,
    get_embedding_provider,
)


def fallback_embedding(text: str, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> list[float]:
    return DeterministicHashEmbeddingProvider(dimensions=dimensions).embed(text)


__all__ = [
    "DEFAULT_EMBEDDING_DIMENSIONS",
    "DeterministicHashEmbeddingProvider",
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "fallback_embedding",
    "get_embedding_provider",
]
