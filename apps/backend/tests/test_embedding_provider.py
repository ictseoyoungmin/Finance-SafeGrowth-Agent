from typing import Any

from app.rag.embedding_provider import DeterministicHashEmbeddingProvider, GeminiEmbeddingProvider


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeHttpxClient:
    def __init__(self) -> None:
        self.posts: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        count = len(kwargs["json"]["requests"])
        return FakeResponse(
            {
                "embeddings": [
                    {"values": [float(index), float(index + 1), float(index + 2)]}
                    for index in range(count)
                ]
            }
        )


def test_deterministic_hash_embedding_is_stable_and_normalized() -> None:
    provider = DeterministicHashEmbeddingProvider(dimensions=16)

    first = provider.embed("수익률 확정 표현")
    second = provider.embed("수익률 확정 표현")
    other = provider.embed("원금 손실 고지")

    assert first == second
    assert first != other
    assert len(first) == 16
    assert abs(sum(value * value for value in first) - 1.0) < 0.000001


def test_gemini_embedding_provider_uses_batch_embed_endpoint() -> None:
    client = FakeHttpxClient()
    provider = GeminiEmbeddingProvider(
        api_key="real-key",
        model="gemini-embedding-001",
        client=client,  # type: ignore[arg-type]
    )

    embeddings = provider.embed_batch(["a", "b"])

    assert embeddings == [[0.0, 1.0, 2.0], [1.0, 2.0, 3.0]]
    assert client.posts[0]["url"].endswith("/models/gemini-embedding-001:batchEmbedContents")
    assert client.posts[0]["params"] == {"key": "real-key"}
    assert client.posts[0]["json"]["requests"][0]["content"]["parts"][0]["text"] == "a"
