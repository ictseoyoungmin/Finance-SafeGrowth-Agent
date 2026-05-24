from app.agent.state import init_state
from app.agent.tools.search_regulation import SearchRegulationTool
from app.repositories.regulation_docs_repo import RegulationDoc
from app.schemas.agent import AgentRunRequest
from app.schemas.tools import SearchRegulationArgs


class RecordingRetriever:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def retrieve(self, **kwargs):
        self.calls.append(kwargs)
        return [
            RegulationDoc(
                evidence_id="reg-chunk-1",
                title="가이드",
                version="v1",
                version_id="version-1",
                version_label="v1",
                product_type="투자상품",
                risk_categories=("원금 보장 오인",),
                snippet="원금 손실 가능성 고지",
                guideline_snippet="원금 손실 가능성 고지",
                similarity=0.8,
            )
        ]


def test_search_regulation_tool_passes_query_to_retriever() -> None:
    retriever = RecordingRetriever()
    tool = SearchRegulationTool(retriever=retriever)  # type: ignore[arg-type]

    result = tool.run(
        SearchRegulationArgs(
            query="원금 보장 표현",
            risk_categories=["원금 보장 오인"],
            product_type="투자상품",
        ),
        init_state(AgentRunRequest(text="demo")),
    )

    assert retriever.calls[0]["query"] == "원금 보장 표현"
    assert result.evidence[0].version_id == "version-1"
