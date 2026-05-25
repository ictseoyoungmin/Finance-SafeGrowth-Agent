from app.rag.retriever import RegulationRetriever, get_regulation_retriever
from app.schemas.evidence import EvidenceItem, EvidenceRequest, EvidenceResponse


class EvidenceService:
    def __init__(self, retriever: RegulationRetriever) -> None:
        self._retriever = retriever

    def retrieve(self, request: EvidenceRequest) -> EvidenceResponse:
        docs = self._retriever.retrieve(
            risk_categories=request.risk_categories,
            product_type=request.product_type,
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


def get_evidence_service() -> EvidenceService:
    return EvidenceService(get_regulation_retriever())
