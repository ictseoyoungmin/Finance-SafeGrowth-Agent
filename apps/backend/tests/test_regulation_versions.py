from app.integrations.supabase_client import SupabaseClient, SupabaseConfig
from app.repositories.regulation_versions_repo import (
    FALLBACK_REGULATION_CHUNKS,
    FALLBACK_REGULATION_VERSIONS,
    RegulationVersionsRepository,
)


def setup_function() -> None:
    FALLBACK_REGULATION_VERSIONS.clear()
    FALLBACK_REGULATION_CHUNKS.clear()


def test_versions_repository_latest_and_hash_lookup() -> None:
    repository = RegulationVersionsRepository(SupabaseClient(SupabaseConfig(None, None, None)))
    version = repository.insert(
        source_id="source-1",
        title="가이드",
        version_label="v1",
        effective_date=None,
        content_hash="abc",
        raw_text="본문",
        chunks=[
            {
                "chunk_index": 0,
                "chunk_text": "본문",
                "risk_categories": ["과장 표현"],
                "product_type": "공통",
            }
        ],
    )

    assert repository.find_by_hash("source-1", "abc") == version
    assert repository.latest_for_source("source-1") == version
    assert FALLBACK_REGULATION_CHUNKS[0]["version_id"] == version.id


def test_versions_repository_marks_superseded() -> None:
    repository = RegulationVersionsRepository(SupabaseClient(SupabaseConfig(None, None, None)))
    first = repository.insert(
        source_id="source-1",
        title="가이드",
        version_label="v1",
        effective_date=None,
        content_hash="abc",
        raw_text="old",
        chunks=[],
    )
    second = repository.insert(
        source_id="source-1",
        title="가이드",
        version_label="v2",
        effective_date=None,
        content_hash="def",
        raw_text="new",
        chunks=[],
    )

    repository.mark_superseded(first.id, second.id)

    assert FALLBACK_REGULATION_VERSIONS[first.id]["superseded_by"] == second.id
