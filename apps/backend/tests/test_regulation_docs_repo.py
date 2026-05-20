from app.integrations.supabase_client import SupabaseClient, SupabaseConfig
from app.repositories.regulation_docs_repo import RegulationDocsRepository


class FakeSupabaseClient:
    is_configured = True

    def select_many(
        self,
        table: str,
        filters: dict,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        assert table == "regulation_docs"
        assert filters == {}
        assert order == "id.asc"
        return [
            {
                "id": "doc-invest-001",
                "title": "투자상품 광고 가이드",
                "version": "live-v1",
                "product_type": "투자상품",
                "risk_categories": ["확정 수익 오인"],
                "snippet": "수익률을 확정적으로 표현하지 않습니다.",
                "guideline_snippet": "수익률 확정 표현 금지",
            },
            {
                "id": "doc-card-001",
                "title": "카드 광고 가이드",
                "version": "live-v1",
                "product_type": "카드",
                "risk_categories": ["혜택 조건 누락"],
                "snippet": "카드 혜택 조건을 표시합니다.",
                "guideline_snippet": "조건 표시",
            },
        ][:limit]


class EmptySupabaseClient:
    is_configured = True

    def select_many(
        self,
        table: str,
        filters: dict,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        return []


def test_regulation_docs_repository_filters_supabase_rows() -> None:
    repository = RegulationDocsRepository(FakeSupabaseClient())  # type: ignore[arg-type]

    docs = repository.search(["확정 수익 오인"], "투자상품")

    assert [doc.evidence_id for doc in docs] == ["doc-invest-001"]
    assert docs[0].guideline_snippet == "수익률 확정 표현 금지"


def test_regulation_docs_repository_falls_back_when_supabase_has_no_rows() -> None:
    repository = RegulationDocsRepository(EmptySupabaseClient())  # type: ignore[arg-type]

    docs = repository.search(["원금 보장 오인"], "투자상품")

    assert {doc.evidence_id for doc in docs} >= {"doc-demo-002"}


def test_regulation_docs_repository_fallback_without_supabase() -> None:
    repository = RegulationDocsRepository(SupabaseClient(SupabaseConfig(None, None, None)))

    docs = repository.search(["확정 수익 오인"], "투자상품")

    assert docs[0].evidence_id == "doc-demo-001"
