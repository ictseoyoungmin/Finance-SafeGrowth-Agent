from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.repositories.regulation_versions_repo import (
    FALLBACK_REGULATION_CHUNKS,
    FALLBACK_REGULATION_VERSIONS,
)


SOURCE_ID = "11111111-1111-4111-8111-111111111111"


def setup_function() -> None:
    FALLBACK_REGULATION_VERSIONS.clear()
    FALLBACK_REGULATION_CHUNKS.clear()


def test_admin_upload_requires_token() -> None:
    client = TestClient(app)
    response = client.post("/v1/admin/regulations/ingest")

    assert response.status_code == 403


def test_admin_upload_ingests_file(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_api_token", "secret")
    client = TestClient(app)

    response = client.post(
        "/v1/admin/regulations/ingest",
        headers={"X-Admin-Token": "secret"},
        data={
            "source_id": SOURCE_ID,
            "title": "금융상품 광고 심사 가이드",
            "version_label": "2026-05",
        },
        files={"file": ("guide.md", b"# Guide\n\n\xec\x88\x98\xec\x9d\xb5\xeb\xa5\xa0 \xed\x99\x95\xec\xa0\x95 \xed\x91\x9c\xed\x98\x84 \xea\xb8\x88\xec\xa7\x80", "text/markdown")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "created"
    assert body["version_id"]
    assert body["chunk_count"] >= 1
    assert FALLBACK_REGULATION_CHUNKS


def test_admin_sources_and_versions(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_api_token", "secret")
    client = TestClient(app)

    sources = client.get("/v1/admin/regulations/sources", headers={"X-Admin-Token": "secret"})

    assert sources.status_code == 200
    assert any(source["id"] == SOURCE_ID for source in sources.json())
