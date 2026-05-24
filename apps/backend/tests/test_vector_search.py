from app.rag.vector_search import cosine_search
from app.repositories.regulation_versions_repo import FALLBACK_REGULATION_CHUNKS


class FakeSupabaseClient:
    is_configured = False


class FakeRpcSupabaseClient:
    is_configured = True

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def rpc(self, function_name: str, payload: dict) -> list[dict]:
        self.calls.append((function_name, payload))
        return [
            {
                "id": 1,
                "version_id": "version-1",
                "chunk_text": "원금 손실 가능성 고지",
                "risk_categories": ["원금 보장 오인"],
                "product_type": "투자상품",
                "similarity": 0.91,
            }
        ]


def setup_function() -> None:
    FALLBACK_REGULATION_CHUNKS.clear()


def test_cosine_search_orders_fallback_chunks_by_similarity() -> None:
    FALLBACK_REGULATION_CHUNKS.extend(
        [
            {
                "id": 1,
                "version_id": "version-1",
                "chunk_text": "close",
                "risk_categories": ["원금 보장 오인"],
                "product_type": "투자상품",
                "embedding": [1.0, 0.0],
            },
            {
                "id": 2,
                "version_id": "version-2",
                "chunk_text": "far",
                "risk_categories": ["원금 보장 오인"],
                "product_type": "투자상품",
                "embedding": [0.0, 1.0],
            },
        ]
    )

    hits = cosine_search(
        FakeSupabaseClient(),  # type: ignore[arg-type]
        [1.0, 0.0],
        top_k=2,
        product_type="투자상품",
        risk_categories=["원금 보장 오인"],
    )

    assert [hit.id for hit in hits] == ["1", "2"]
    assert hits[0].similarity > hits[1].similarity


def test_cosine_search_calls_supabase_rpc_when_configured() -> None:
    client = FakeRpcSupabaseClient()

    hits = cosine_search(
        client,  # type: ignore[arg-type]
        [0.1, 0.2],
        top_k=3,
        product_type="투자상품",
        risk_categories=["원금 보장 오인"],
    )

    assert client.calls[0][0] == "match_regulation_chunks"
    assert client.calls[0][1]["match_count"] == 3
    assert hits[0].version_id == "version-1"
