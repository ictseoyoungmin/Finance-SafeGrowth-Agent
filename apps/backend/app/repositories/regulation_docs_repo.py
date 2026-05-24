from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.repositories.regulation_versions_repo import (
    FALLBACK_REGULATION_CHUNKS,
    FALLBACK_REGULATION_VERSIONS,
)
from app.rag.embedding_provider import EmbeddingProvider, get_embedding_provider
from app.rag.vector_search import RegulationChunkHit, cosine_search


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
    version_id: str | None = None
    version_label: str | None = None
    effective_date: str | None = None


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
    def __init__(
        self,
        supabase_client: SupabaseClient,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._supabase_client = supabase_client
        self._embedding_provider = embedding_provider or get_embedding_provider()

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

    def vector_search(
        self,
        query_text: str,
        risk_categories: list[str],
        product_type: str,
        limit: int = 5,
    ) -> list[RegulationDoc]:
        query = query_text.strip()
        if not query:
            return self.search(risk_categories, product_type, limit)

        try:
            embedding = self._embedding_provider.embed(query)
            hits = cosine_search(
                self._supabase_client,
                embedding,
                top_k=limit,
                product_type=product_type,
                risk_categories=risk_categories,
            )
            docs = self._hits_to_docs(hits)
        except Exception:
            logger.exception("Vector regulation search failed; falling back to category search.")
            return self.search(risk_categories, product_type, limit)

        if len(docs) < limit or (docs and docs[0].similarity < 0.25):
            existing = {doc.version_id or doc.evidence_id for doc in docs}
            for doc in self.search(risk_categories, product_type, limit):
                key = doc.version_id or doc.evidence_id
                if key not in existing:
                    docs.append(doc)
                    existing.add(key)
                if len(docs) >= limit:
                    break
        return docs[:limit]

    def _supabase_search(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int,
    ) -> list[RegulationDoc]:
        rows = self._supabase_client.select_many(
            "regulation_chunks",
            filters={},
            order="id.asc",
            limit=100,
        )
        requested = set(risk_categories)
        docs: list[RegulationDoc] = []
        seen_versions: set[str] = set()
        for row in rows:
            if row.get("product_type") not in {product_type, "공통"}:
                continue
            if requested and not requested.intersection(row.get("risk_categories") or []):
                continue
            version_id = str(row.get("version_id") or "")
            if not version_id or version_id in seen_versions:
                continue
            version = self._supabase_client.select_one("regulation_versions", {"id": version_id})
            if not version or version.get("superseded_by"):
                continue
            docs.append(self._chunk_row_to_doc(row, version, requested))
            seen_versions.add(version_id)
        return sorted(docs, key=lambda doc: (-doc.similarity, doc.evidence_id))[:limit]

    def _fallback_search(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int,
    ) -> list[RegulationDoc]:
        requested = set(risk_categories)
        ingested = self._fallback_ingested_search(requested, product_type, limit)
        if ingested:
            return ingested

        docs = [
            doc
            for doc in FALLBACK_REGULATION_DOCS
            if doc.product_type in {product_type, "공통"}
            and (not requested or requested.intersection(doc.risk_categories))
        ]
        if not docs:
            docs = FALLBACK_REGULATION_DOCS
        return sorted(docs, key=lambda doc: doc.similarity, reverse=True)[:limit]

    def _fallback_ingested_search(
        self,
        requested: set[str],
        product_type: str,
        limit: int,
    ) -> list[RegulationDoc]:
        docs: list[RegulationDoc] = []
        seen_versions: set[str] = set()
        for row in FALLBACK_REGULATION_CHUNKS:
            if row.get("product_type") not in {product_type, "공통"}:
                continue
            if requested and not requested.intersection(row.get("risk_categories") or []):
                continue
            version_id = str(row.get("version_id") or "")
            if not version_id or version_id in seen_versions:
                continue
            version = FALLBACK_REGULATION_VERSIONS.get(version_id)
            if not version or version.get("superseded_by"):
                continue
            docs.append(self._chunk_row_to_doc(row, version, requested))
            seen_versions.add(version_id)
        return sorted(docs, key=lambda doc: (-doc.similarity, doc.evidence_id))[:limit]

    def _hits_to_docs(self, hits: list[RegulationChunkHit]) -> list[RegulationDoc]:
        docs: list[RegulationDoc] = []
        seen_versions: set[str] = set()
        for hit in hits:
            if hit.version_id in seen_versions:
                continue
            version = self._version_row(hit.version_id)
            if not version or version.get("superseded_by"):
                continue
            docs.append(self._hit_to_doc(hit, version))
            seen_versions.add(hit.version_id)
        return docs

    def _version_row(self, version_id: str) -> dict[str, Any] | None:
        if self._supabase_client.is_configured:
            return self._supabase_client.select_one("regulation_versions", {"id": version_id})
        return FALLBACK_REGULATION_VERSIONS.get(version_id)

    def _hit_to_doc(self, hit: RegulationChunkHit, version: dict[str, Any]) -> RegulationDoc:
        return RegulationDoc(
            evidence_id=f"reg-chunk-{hit.id}",
            title=str(version.get("title") or ""),
            version=str(version.get("version_label") or version.get("id") or ""),
            product_type=hit.product_type,
            risk_categories=hit.risk_categories,
            snippet=hit.chunk_text[:220],
            guideline_snippet=_first_sentence(hit.chunk_text),
            similarity=max(0.0, min(hit.similarity, 1.0)),
            version_id=str(version.get("id") or hit.version_id),
            version_label=version.get("version_label"),
            effective_date=version.get("effective_date"),
        )

    def _chunk_row_to_doc(
        self,
        row: dict[str, Any],
        version: dict[str, Any],
        requested: set[str],
    ) -> RegulationDoc:
        row_categories = tuple(row.get("risk_categories") or ())
        overlap_count = len(requested.intersection(row_categories)) if requested else 1
        similarity = min(0.99, 0.72 + (0.05 * overlap_count))
        chunk_text = str(row.get("chunk_text") or "")
        return RegulationDoc(
            evidence_id=f"reg-chunk-{row.get('id')}",
            title=str(version.get("title") or ""),
            version=str(version.get("version_label") or version.get("id") or ""),
            product_type=str(row.get("product_type") or "공통"),
            risk_categories=row_categories,
            snippet=chunk_text[:220],
            guideline_snippet=_first_sentence(chunk_text),
            similarity=similarity,
            version_id=str(version.get("id") or ""),
            version_label=version.get("version_label"),
            effective_date=version.get("effective_date"),
        )


def _first_sentence(text: str) -> str:
    for delimiter in (".", "。", "다.", "\n"):
        if delimiter in text:
            end = text.find(delimiter) + len(delimiter)
            return text[:end].strip()
    return text[:120].strip()


def get_regulation_docs_repository() -> RegulationDocsRepository:
    return RegulationDocsRepository(get_supabase_client())
