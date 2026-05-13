from fastapi.testclient import TestClient

from app.main import app


def test_evidence_returns_fallback_docs_without_supabase() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/compliance/evidence",
        json={
            "content_id": "demo-content",
            "risk_categories": ["확정 수익 오인", "원금 보장 오인"],
            "product_type": "투자상품",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content_id"] == "demo-content"
    assert len(body["evidence_list"]) >= 1
    assert body["guideline_snippets"]
