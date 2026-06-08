from app.rag.retriever import RegulationRetriever, get_regulation_retriever
from app.schemas.evidence import EvidenceItem, EvidenceRequest, EvidenceResponse


class EvidenceService:
    def __init__(self, retriever: RegulationRetriever) -> None:
        self._retriever = retriever

    def retrieve(self, request: EvidenceRequest) -> EvidenceResponse:
        docs = self._retriever.retrieve(
            risk_categories=request.risk_categories,
            product_type=request.product_type,
            query=self._build_query(request),
        )

        return EvidenceResponse(
            content_id=request.content_id,
            evidence_list=[
                EvidenceItem(
                    evidence_id=doc.evidence_id,
                    title=doc.title,
                    version=doc.version,
                    snippet=doc.snippet,
                    similarity=doc.similarity,
                    version_id=doc.version_id,
                    effective_date=str(doc.effective_date) if doc.effective_date else None,
                    risk_categories=list(doc.risk_categories),
                )
                for doc in docs
            ],
            guideline_snippets=[doc.guideline_snippet for doc in docs],
        )


    def _build_query(self, request: EvidenceRequest) -> str | None:
        """Compose a vector-search query from product, categories, copy, spans.

        Returns None when no meaningful context is supplied so the retriever
        falls back to its category-only lookup path.
        """
        parts: list[str] = []
        if request.product_type:
            parts.append(request.product_type)
        if request.risk_categories:
            parts.append(" ".join(request.risk_categories))
        if request.original_text:
            parts.append(request.original_text)
        if request.flagged_spans:
            parts.append(" ".join(request.flagged_spans))
        query = "\n".join(p for p in parts if p).strip()
        # The retriever already routes empty queries to the category-only
        # path; only return a query when there's actual textual context to
        # search against (more than just product_type + categories alone).
        if not request.original_text and not request.flagged_spans:
            return None
        return query or None


def get_evidence_service() -> EvidenceService:
    return EvidenceService(get_regulation_retriever())
