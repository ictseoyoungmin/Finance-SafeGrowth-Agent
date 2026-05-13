from fastapi.testclient import TestClient

from app.main import app


def test_rewrite_returns_fallback_without_gemini() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/compliance/rewrite",
        json={"content_id": "demo-content", "mode": "marketing_balanced"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content_id"] == "demo-content"
    assert body["revised_text_conservative"]
    assert body["revised_text_marketing"]
    assert len(body["changes"]) >= 1
