from dataclasses import dataclass
from typing import Any

from app.integrations.supabase_client import SupabaseClient
from app.repositories.regulation_versions_repo import FALLBACK_REGULATION_CHUNKS


@dataclass(frozen=True)
class RegulationChunkHit:
    id: str
    version_id: str
    chunk_text: str
    risk_categories: tuple[str, ...]
    product_type: str
    similarity: float


def cosine_search(
    supabase_client: SupabaseClient,
    embedding: list[float],
    *,
    top_k: int,
    product_type: str,
    risk_categories: list[str],
) -> list[RegulationChunkHit]:
    if supabase_client.is_configured:
        rows = supabase_client.rpc(
            "match_regulation_chunks",
            {
                "query_embedding": embedding,
                "match_count": top_k,
                "match_product_type": product_type,
                "match_risk_categories": risk_categories,
            },
        )
        return [_row_to_hit(row) for row in rows]

    requested = set(risk_categories)
    hits: list[RegulationChunkHit] = []
    for row in FALLBACK_REGULATION_CHUNKS:
        row_embedding = row.get("embedding")
        if not isinstance(row_embedding, list):
            continue
        if row.get("product_type") not in {product_type, "공통"}:
            continue
        row_categories = tuple(row.get("risk_categories") or ())
        if requested and not requested.intersection(row_categories):
            continue
        hits.append(
            RegulationChunkHit(
                id=str(row.get("id")),
                version_id=str(row.get("version_id")),
                chunk_text=str(row.get("chunk_text") or ""),
                risk_categories=row_categories,
                product_type=str(row.get("product_type") or "공통"),
                similarity=_cosine_similarity(embedding, [float(value) for value in row_embedding]),
            )
        )
    return sorted(hits, key=lambda hit: hit.similarity, reverse=True)[:top_k]


def _row_to_hit(row: dict[str, Any]) -> RegulationChunkHit:
    return RegulationChunkHit(
        id=str(row.get("id") or row.get("chunk_id") or ""),
        version_id=str(row.get("version_id") or ""),
        chunk_text=str(row.get("chunk_text") or ""),
        risk_categories=tuple(row.get("risk_categories") or ()),
        product_type=str(row.get("product_type") or "공통"),
        similarity=float(row.get("similarity") or 0.0),
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(-1.0, min(dot / (left_norm * right_norm), 1.0))
