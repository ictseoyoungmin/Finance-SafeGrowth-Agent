from fastapi.testclient import TestClient
import pytest

from app.agent.runner import AgentRunner, get_agent_runner
from app.main import app
from app.repositories.agent_runs_repo import FALLBACK_AGENT_RUNS
from app.repositories.agent_steps_repo import FALLBACK_AGENT_STEPS
from app.repositories.approval_logs_repo import FALLBACK_APPROVAL_LOGS
from app.repositories.audit_logs_repo import FALLBACK_AUDIT_LOGS
from app.repositories.contents_repo import FALLBACK_CONTENTS
from app.repositories.risk_results_repo import FALLBACK_RISK_RESULTS
from tests._agent_fakes import ScriptedLlmProvider


@pytest.fixture(autouse=True)
def fallback_agent_runner_override():
    app.dependency_overrides[get_agent_runner] = lambda: AgentRunner(
        llm_provider=ScriptedLlmProvider(configured=False)
    )
    yield
    app.dependency_overrides.pop(get_agent_runner, None)


def _reset_fallback_stores() -> None:
    for store in (
        FALLBACK_AGENT_RUNS,
        FALLBACK_AGENT_STEPS,
        FALLBACK_APPROVAL_LOGS,
        FALLBACK_AUDIT_LOGS,
        FALLBACK_CONTENTS,
        FALLBACK_RISK_RESULTS,
    ):
        store.clear()


def _analyze_first(client: TestClient) -> str:
    response = client.post(
        "/v1/compliance/analyze",
        json={
            "product_type": "투자상품",
            "channel": "앱 푸시",
            "target_customer": "30대 직장인",
            "language": "ko",
            "original_text": "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["content_id"]


def test_post_agent_run_returns_awaiting_human_in_fallback_mode() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)

    response = client.post(
        "/v1/agent/run",
        json={
            "content_id": content_id,
            "text": "누구나 연 8% 수익을 안정적으로 받는 상품 검토 요청",
            "product_type": "투자상품",
            "mode": "review",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "awaiting_human"
    assert body["model"] == "fallback-deterministic-agent"
    assert body["pending_human"] is not None
    assert body["pending_human"]["options"] == ["approve", "reject", "revise"]

    tool_calls = [step["tool_name"] for step in body["steps"] if step["step_type"] == "tool_call"]
    assert tool_calls[0] == "scan_rules"
    assert "search_regulation" in tool_calls
    assert "draft_rewrite" in tool_calls
    assert tool_calls[-1] == "request_human_review"


def test_get_agent_run_returns_persisted_detail() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)

    started = client.post(
        "/v1/agent/run",
        json={"content_id": content_id, "text": "검토 요청", "mode": "review"},
    ).json()
    run_id = started["id"]

    fetched = client.get(f"/v1/agent/runs/{run_id}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["id"] == run_id
    assert body["status"] == "awaiting_human"
    assert len(body["steps"]) >= len(started["steps"])


def test_respond_completes_run_with_decision() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)

    started = client.post(
        "/v1/agent/run",
        json={"content_id": content_id, "text": "검토 요청", "mode": "review"},
    ).json()
    run_id = started["id"]

    resumed = client.post(
        f"/v1/agent/runs/{run_id}/respond",
        json={"response": {"decision": "approve", "selected_revision": "마케팅안"}},
    )
    assert resumed.status_code == 200, resumed.text
    body = resumed.json()
    assert body["status"] == "done"
    assert body["final_decision"] == "approve"
    assert body["final_report"] is not None
    assert body["final_report"]["final_text"]


def test_respond_returns_409_when_run_not_paused() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)
    started = client.post(
        "/v1/agent/run",
        json={"content_id": content_id, "text": "검토", "mode": "review"},
    ).json()
    run_id = started["id"]
    # First respond completes the run.
    client.post(
        f"/v1/agent/runs/{run_id}/respond",
        json={"response": "approve"},
    )

    second = client.post(
        f"/v1/agent/runs/{run_id}/respond",
        json={"response": "approve"},
    )
    assert second.status_code == 409


def test_get_returns_404_for_unknown_run() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    response = client.get("/v1/agent/runs/11111111-1111-4111-8111-111111111111")
    assert response.status_code == 404


def test_cancel_marks_run_cancelled() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)
    started = client.post(
        "/v1/agent/run",
        json={"content_id": content_id, "text": "검토", "mode": "review"},
    ).json()
    run_id = started["id"]

    cancelled = client.post(f"/v1/agent/runs/{run_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_stream_endpoint_yields_step_events_and_status() -> None:
    _reset_fallback_stores()
    client = TestClient(app)
    content_id = _analyze_first(client)
    started = client.post(
        "/v1/agent/run",
        json={"content_id": content_id, "text": "검토", "mode": "review"},
    ).json()
    run_id = started["id"]

    with client.stream("GET", f"/v1/agent/runs/{run_id}/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = response.read().decode("utf-8")

    assert "event: step" in body
    assert "event: status" in body
    assert "awaiting_human" in body
