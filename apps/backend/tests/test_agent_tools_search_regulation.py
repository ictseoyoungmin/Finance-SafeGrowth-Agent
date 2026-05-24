from app.agent.state import init_state
from app.agent.tools.search_regulation import SearchRegulationTool
from app.rag.retriever import RegulationRetriever
from app.repositories.regulation_docs_repo import (
    FALLBACK_REGULATION_DOCS,
    RegulationDoc,
    RegulationDocsRepository,
)
from app.schemas.agent import AgentRunRequest
from app.schemas.tools import SearchRegulationArgs


class _FakeSupabaseClient:
    is_configured = False

    def insert(self, *_args, **_kwargs):  # pragma: no cover - unused
        raise RuntimeError("unused in this test")

    def select_one(self, *_args, **_kwargs):  # pragma: no cover - unused
        return None

    def select_many(self, *_args, **_kwargs):  # pragma: no cover - unused
        return []


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def _tool() -> SearchRegulationTool:
    docs_repo = RegulationDocsRepository(_FakeSupabaseClient())  # type: ignore[arg-type]
    return SearchRegulationTool(retriever=RegulationRetriever(docs_repo))


def test_search_regulation_returns_matching_demo_docs() -> None:
    tool = _tool()

    result = tool.run(
        SearchRegulationArgs(
            risk_categories=["확정 수익 오인"],
            product_type="투자상품",
            limit=5,
        ),
        _state(),
    )

    assert len(result.evidence) >= 1
    titles = {hit.title for hit in result.evidence}
    assert "금융상품 광고 심사 가이드라인" in titles


def test_search_regulation_clamps_similarity_to_unit_interval() -> None:
    class _BadRetriever:
        def retrieve(self, **_kwargs):
            return [
                RegulationDoc(
                    evidence_id="doc-bad",
                    title="t",
                    version="v",
                    product_type="공통",
                    risk_categories=("과장 표현",),
                    snippet="s",
                    guideline_snippet="g",
                    similarity=1.7,
                )
            ]

    tool = SearchRegulationTool(retriever=_BadRetriever())  # type: ignore[arg-type]

    result = tool.run(
        SearchRegulationArgs(risk_categories=["과장 표현"], product_type="공통"),
        _state(),
    )

    assert result.evidence[0].similarity == 1.0


def test_search_regulation_falls_back_to_all_docs_when_no_category_match() -> None:
    tool = _tool()

    result = tool.run(
        SearchRegulationArgs(
            risk_categories=["존재하지않는카테고리"],
            product_type="투자상품",
            limit=5,
        ),
        _state(),
    )

    expected_titles = {doc.title for doc in FALLBACK_REGULATION_DOCS}
    actual_titles = {hit.title for hit in result.evidence}
    assert actual_titles & expected_titles
