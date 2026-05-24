from app.ingestion.extractors.html import extract_html_text
from app.integrations.supabase_client import SupabaseClient, SupabaseConfig
from app.ingestion.normalizer import normalize_regulation_text
from app.repositories.regulation_sources_repo import FALLBACK_REGULATION_SOURCES
from app.repositories.regulation_sources_repo import RegulationSourcesRepository
from app.repositories.regulation_versions_repo import (
    FALLBACK_REGULATION_CHUNKS,
    FALLBACK_REGULATION_VERSIONS,
    RegulationVersionsRepository,
)
from app.services.regulation_ingestion_service import RegulationIngestionService


SOURCE_ID = "11111111-1111-4111-8111-111111111111"


class TinyEmbeddingProvider:
    dimensions = 2

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def setup_function() -> None:
    FALLBACK_REGULATION_VERSIONS.clear()
    FALLBACK_REGULATION_CHUNKS.clear()


def _service() -> RegulationIngestionService:
    supabase = SupabaseClient(SupabaseConfig(None, None, None))
    return RegulationIngestionService(
        sources_repository=RegulationSourcesRepository(supabase),
        versions_repository=RegulationVersionsRepository(supabase),
        embedding_provider=TinyEmbeddingProvider(),
    )


def test_html_extractor_and_normalizer_make_chunks_and_categories() -> None:
    text = extract_html_text(
        "<html><body><h1>Guide</h1><script>x()</script><p>수익률 확정 표현 금지. 원금 손실 고지.</p></body></html>".encode()
    )
    normalized = normalize_regulation_text(text, product_type="투자상품")

    assert "script" not in normalized.text.lower()
    assert normalized.product_type == "투자상품"
    assert "확정 수익 오인" in normalized.risk_categories
    assert "원금 보장 오인" in normalized.risk_categories
    assert normalized.chunks


def test_ingest_payload_is_idempotent_for_same_hash() -> None:
    result = _service().ingest_payload(
        source_id=SOURCE_ID,
        title="금융상품 광고 심사 가이드",
        version_label="2026-05",
        raw_bytes="수익률 확정 표현 금지. 원금 손실 가능성 고지.".encode(),
        content_type="text/plain",
    )
    second = _service().ingest_payload(
        source_id=SOURCE_ID,
        title="금융상품 광고 심사 가이드",
        version_label="2026-05",
        raw_bytes="수익률 확정 표현 금지. 원금 손실 가능성 고지.".encode(),
        content_type="text/plain",
    )

    assert result.status == "created"
    assert second.status == "unchanged"
    assert second.version_id == result.version_id
    assert len(FALLBACK_REGULATION_VERSIONS) == 1
    assert len(FALLBACK_REGULATION_CHUNKS) == result.chunk_count
    assert FALLBACK_REGULATION_CHUNKS[0]["embedding"] == [1.0, 0.0]


def test_ingest_payload_supersedes_previous_version() -> None:
    first = _service().ingest_payload(
        source_id=SOURCE_ID,
        title="가이드",
        version_label="v1",
        raw_bytes=b"old text",
    )
    second = _service().ingest_payload(
        source_id=SOURCE_ID,
        title="가이드",
        version_label="v2",
        raw_bytes=b"new text with \xec\x88\x98\xec\x9d\xb5\xeb\xa5\xa0",
    )

    assert second.status == "updated"
    assert FALLBACK_REGULATION_VERSIONS[first.version_id]["superseded_by"] == second.version_id


def test_ingest_payload_rejects_unknown_source() -> None:
    assert SOURCE_ID in FALLBACK_REGULATION_SOURCES
    try:
        _service().ingest_payload(
            source_id="missing",
            title="missing",
            version_label=None,
            raw_bytes=b"text",
        )
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("expected ValueError")
