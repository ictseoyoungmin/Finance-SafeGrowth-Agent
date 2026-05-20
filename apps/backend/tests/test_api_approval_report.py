from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.approval_logs_repo import FALLBACK_APPROVAL_LOGS
from app.repositories.audit_logs_repo import FALLBACK_AUDIT_LOGS
from app.repositories.contents_repo import FALLBACK_CONTENTS
from app.repositories.risk_results_repo import FALLBACK_RISK_RESULTS


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


def test_approve_audit_log_and_report_flow() -> None:
    FALLBACK_CONTENTS.clear()
    FALLBACK_RISK_RESULTS.clear()
    FALLBACK_AUDIT_LOGS.clear()
    FALLBACK_APPROVAL_LOGS.clear()
    client = TestClient(app)

    analyze_response = client.post("/v1/compliance/analyze", json=DEMO_PAYLOAD)
    content_id = analyze_response.json()["content_id"]

    approval_response = client.post(
        "/v1/compliance/approve",
        json={
            "content_id": content_id,
            "reviewer": "김준법 수석",
            "decision": "CONDITIONALLY_APPROVED",
            "comment": "Demo approval",
            "selected_revision": "marketing",
        },
    )
    audit_response = client.get(f"/v1/compliance/audit-log?content_id={content_id}")
    report_response = client.get(f"/v1/compliance/report?content_id={content_id}")

    assert approval_response.status_code == 200
    approval_body = approval_response.json()
    assert UUID(approval_body["approval_id"])
    assert approval_body["content_id"] == content_id
    assert approval_body["status"] == "APPROVED"
    assert approval_body["decision"] == "CONDITIONALLY_APPROVED"
    assert approval_body["reviewer"] == "김준법 수석"

    assert audit_response.status_code == 200
    audit_body = audit_response.json()
    assert audit_body["content_id"] == content_id
    assert [entry["action"] for entry in audit_body["entries"]] == ["analyze", "approve"]

    assert report_response.status_code == 200
    report_body = report_response.json()
    assert report_body["content_id"] == content_id
    assert report_body["risk_level"] == "HIGH"
    assert report_body["approval"]["decision"] == "CONDITIONALLY_APPROVED"
    assert report_body["audit_log"][0]["action"] == "analyze"


def test_approve_validates_decision() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/compliance/approve",
        json={
            "content_id": "11111111-1111-4111-8111-111111111111",
            "reviewer": "김준법 수석",
            "decision": "MAYBE",
        },
    )

    assert response.status_code == 422
