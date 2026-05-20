from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


DEMO_PAYLOAD = {
    "product_type": "투자상품",
    "channel": "앱 푸시",
    "target_customer": "30대 직장인",
    "language": "ko",
    "original_text": (
        "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! "
        "원금 걱정 없이 시작하세요."
    ),
}


def test_analyze_returns_high_risk_for_demo_sentence() -> None:
    client = TestClient(app)

    response = client.post("/v1/compliance/analyze", json=DEMO_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert UUID(body["content_id"])
    assert body["risk_level"] == "HIGH"
    assert len(body["flagged_spans"]) >= 3
    assert "확정 수익 오인" in body["risk_categories"]
    assert body["reviewer_notes"]


def test_analyze_returns_expected_demo_spans() -> None:
    client = TestClient(app)

    response = client.post("/v1/compliance/analyze", json=DEMO_PAYLOAD)

    body = response.json()
    span_texts = {span["span_text"] for span in body["flagged_spans"]}
    assert {"누구나", "연 8% 수익", "안정적으로", "원금 걱정 없이"} <= span_texts

    for span in body["flagged_spans"]:
        assert isinstance(span["start"], int)
        assert isinstance(span["end"], int)
        assert span["risk_category"]
        assert span["severity"] in {"MEDIUM", "HIGH"}
        assert span["reason"]
        assert 0 <= span["confidence"] <= 1
