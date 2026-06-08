"""Tests for EvidenceService.

R-B-2: EvidenceService must compose a vector-search query from the optional
original_text / flagged_spans context. If those are absent, the retriever
should keep using its category-only lookup path.
"""

from app.repositories.regulation_docs_repo import RegulationDoc
from app.rag.retriever import RegulationRetriever
from app.schemas.evidence import EvidenceRequest
from app.services.evidence_service import EvidenceService


class RecordingRetriever(RegulationRetriever):
    """Captures retrieve() kwargs without touching the underlying repository."""

    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    def retrieve(self, **kwargs) -> list[RegulationDoc]:
        self.last_kwargs = kwargs
        return []


def _request(**overrides) -> EvidenceRequest:
    payload = {
        "content_id": "c-1",
        "risk_categories": ["확정 수익 오인"],
        "product_type": "투자상품",
    }
    payload.update(overrides)
    return EvidenceRequest(**payload)


def test_evidence_with_text_context_routes_query_to_vector_search() -> None:
    retriever = RecordingRetriever()
    service = EvidenceService(retriever)

    service.retrieve(
        _request(
            original_text="연 5.0% 수익을 안정적으로 받아보세요.",
            flagged_spans=["연 5.0% 수익", "안정적으로"],
        )
    )

    assert retriever.last_kwargs is not None
    query = retriever.last_kwargs.get("query")
    assert query, "query should be composed from original_text + flagged_spans"
    assert "연 5.0% 수익" in query
    assert "안정적으로" in query
    assert "투자상품" in query


def test_evidence_without_text_context_keeps_category_only_path() -> None:
    retriever = RecordingRetriever()
    service = EvidenceService(retriever)

    service.retrieve(_request())

    assert retriever.last_kwargs is not None
    # No original_text and no flagged_spans → retriever stays on the
    # category-only path (query is None).
    assert retriever.last_kwargs.get("query") is None
