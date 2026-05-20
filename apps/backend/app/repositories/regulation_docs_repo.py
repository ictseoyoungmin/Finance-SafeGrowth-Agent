from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client


@dataclass(frozen=True)
class RegulationDoc:
    evidence_id: str
    title: str
    version: str
    product_type: str
    risk_categories: tuple[str, ...]
    snippet: str
    guideline_snippet: str
    similarity: float


FALLBACK_REGULATION_DOCS = [
    RegulationDoc(
        evidence_id="doc-demo-001",
        title="금융상품 광고 심사 가이드라인",
        version="demo-v1",
        product_type="투자상품",
        risk_categories=("확정 수익 오인", "안정성 오인"),
        snippet="투자성 상품 광고에서는 수익률을 확정적으로 표현하지 않아야 하며 손실 가능성을 함께 안내해야 합니다.",
        guideline_snippet="수익률 확정 표현 금지",
        similarity=0.87,
    ),
    RegulationDoc(
        evidence_id="doc-demo-002",
        title="금융소비자 보호 가이드라인",
        version="demo-v1",
        product_type="투자상품",
        risk_categories=("원금 보장 오인",),
        snippet="원금 손실 가능성이 있는 상품은 원금 보장 또는 원금 걱정이 없다는 취지로 안내하지 않아야 합니다.",
        guideline_snippet="원금 손실 가능성 고지 필요",
        similarity=0.84,
    ),
    RegulationDoc(
        evidence_id="doc-demo-003",
        title="내부 통제 규정",
        version="demo-v1",
        product_type="공통",
        risk_categories=("과장 표현",),
        snippet="마케팅 커뮤니케이션은 보편적 혜택, 확정적 결과, 심의 누락으로 오인되는 표현을 사전 점검해야 합니다.",
        guideline_snippet="마케팅 문구 배포 전 준법 심의 필요",
        similarity=0.79,
    ),
]
logger = get_logger(__name__)


class RegulationDocsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def search(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int = 5,
    ) -> list[RegulationDoc]:
        if self._supabase_client.is_configured:
            try:
                docs = self._supabase_search(risk_categories, product_type, limit)
                if docs:
                    return docs
            except Exception:
                logger.exception("Supabase regulation docs lookup failed; falling back to demo docs.")

        return self._fallback_search(risk_categories, product_type, limit)

    def _supabase_search(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int,
    ) -> list[RegulationDoc]:
        rows = self._supabase_client.select_many(
            "regulation_docs",
            filters={},
            order="id.asc",
            limit=100,
        )
        requested = set(risk_categories)
        docs = [
            self._row_to_doc(row, requested)
            for row in rows
            if row.get("product_type") in {product_type, "공통"}
            and (not requested or requested.intersection(row.get("risk_categories") or []))
        ]
        return sorted(docs, key=lambda doc: (-doc.similarity, doc.evidence_id))[:limit]

    def _fallback_search(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int,
    ) -> list[RegulationDoc]:
        requested = set(risk_categories)
        docs = [
            doc
            for doc in FALLBACK_REGULATION_DOCS
            if doc.product_type in {product_type, "공통"}
            and (not requested or requested.intersection(doc.risk_categories))
        ]
        if not docs:
            docs = FALLBACK_REGULATION_DOCS
        return sorted(docs, key=lambda doc: doc.similarity, reverse=True)[:limit]

    def _row_to_doc(self, row: dict[str, Any], requested: set[str]) -> RegulationDoc:
        row_categories = tuple(row.get("risk_categories") or ())
        overlap_count = len(requested.intersection(row_categories)) if requested else 1
        similarity = min(0.99, 0.72 + (0.05 * overlap_count))
        return RegulationDoc(
            evidence_id=str(row.get("id")),
            title=str(row.get("title") or ""),
            version=str(row.get("version") or ""),
            product_type=str(row.get("product_type") or "공통"),
            risk_categories=row_categories,
            snippet=str(row.get("snippet") or ""),
            guideline_snippet=str(row.get("guideline_snippet") or ""),
            similarity=similarity,
        )


def get_regulation_docs_repository() -> RegulationDocsRepository:
    return RegulationDocsRepository(get_supabase_client())
