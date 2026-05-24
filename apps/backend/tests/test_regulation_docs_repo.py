from app.integrations.supabase_client import SupabaseClient, SupabaseConfig
from app.repositories.regulation_docs_repo import RegulationDocsRepository


class FakeSupabaseClient:
    is_configured = True
    versions = {
        "version-1": {
            "id": "version-1",
            "title": "투자상품 광고 가이드",
            "version_label": "live-v1",
            "effective_date": "2026-05-01",
            "superseded_by": None,
        },
        "version-2": {
            "id": "version-2",
            "title": "카드 광고 가이드",
            "version_label": "live-v1",
            "effective_date": None,
            "superseded_by": None,
        },
    }

    def select_many(
        self,
        table: str,
        filters: dict,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        assert table == "regulation_chunks"
        assert filters == {}
        assert order == "id.asc"
        return [
            {
                "id": 1,
                "version_id": "version-1",
                "product_type": "투자상품",
                "risk_categories": ["확정 수익 오인"],
                "chunk_text": "수익률을 확정적으로 표현하지 않습니다. 손실 가능성을 함께 고지합니다.",
            },
            {
                "id": 2,
                "version_id": "version-2",
                "product_type": "카드",
                "risk_categories": ["혜택 조건 누락"],
                "chunk_text": "카드 혜택 조건을 표시합니다.",
            },
        ][:limit]

    def select_one(self, table: str, filters: dict, order: str | None = None) -> dict | None:
        assert table == "regulation_versions"
        return self.versions.get(filters["id"])


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

    assert [doc.evidence_id for doc in docs] == ["reg-chunk-1"]
    assert docs[0].version_id == "version-1"
    assert docs[0].version_label == "live-v1"
    assert "수익률" in docs[0].guideline_snippet


def test_regulation_docs_repository_falls_back_when_supabase_has_no_rows() -> None:
    repository = RegulationDocsRepository(EmptySupabaseClient())  # type: ignore[arg-type]

    docs = repository.search(["원금 보장 오인"], "투자상품")

    assert {doc.evidence_id for doc in docs} >= {"doc-demo-002"}


def test_regulation_docs_repository_fallback_without_supabase() -> None:
    repository = RegulationDocsRepository(SupabaseClient(SupabaseConfig(None, None, None)))

    docs = repository.search(["확정 수익 오인"], "투자상품")

    assert docs[0].evidence_id == "doc-demo-001"
