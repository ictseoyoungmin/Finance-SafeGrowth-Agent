from app.agent.state import AgentState
from app.rag.retriever import RegulationRetriever, get_regulation_retriever
from app.schemas.tools import (
    SearchRegulationArgs,
    SearchRegulationHit,
    SearchRegulationResult,
)


class SearchRegulationTool:
    name = "search_regulation"
    description = (
        "Search the regulation knowledge base for evidence snippets that match the given "
        "risk_categories and product_type. Returns up to `limit` evidence items with "
        "title, version, snippet, guideline_snippet, and similarity score. Prefer calling "
        "this after scan_rules so the risk_categories list is meaningful. The optional "
        "`query` string will be used by the Day 19 vector search; for now it is logged "
        "for tracing but does not affect filtering."
    )
    args_model = SearchRegulationArgs
    result_model = SearchRegulationResult

    def __init__(self, retriever: RegulationRetriever | None = None) -> None:
        self._retriever = retriever or get_regulation_retriever()

    def run(self, args: SearchRegulationArgs, state: AgentState) -> SearchRegulationResult:
        docs = self._retriever.retrieve(
            risk_categories=list(args.risk_categories),
            product_type=args.product_type,
            limit=args.limit,
        )
        return SearchRegulationResult(
            evidence=[
                SearchRegulationHit(
                    evidence_id=doc.evidence_id,
                    title=doc.title,
                    version=doc.version,
                    snippet=doc.snippet,
                    guideline_snippet=doc.guideline_snippet,
                    similarity=max(0.0, min(float(doc.similarity), 1.0)),
                )
                for doc in docs
            ]
        )
