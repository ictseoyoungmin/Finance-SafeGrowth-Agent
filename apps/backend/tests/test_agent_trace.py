from typing import Any
from uuid import uuid4

import pytest

from app.agent.state import init_state, time_exceeded
from app.agent.trace import InMemoryTraceRecorder, SupabaseTraceRecorder
from app.integrations.supabase_client import SupabaseClient, SupabaseConfig
from app.repositories.agent_runs_repo import (
    FALLBACK_AGENT_RUNS,
    AgentRunsRepository,
)
from app.repositories.agent_steps_repo import (
    FALLBACK_AGENT_STEPS,
    AgentStepsRepository,
)
from app.schemas.agent import AgentRunRequest


class FakeSupabaseClient:
    is_configured = True

    def __init__(self) -> None:
        self.inserts: list[tuple[str, dict[str, Any]]] = []
        self.patches: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        self.select_many_calls: list[tuple[str, dict[str, Any], str | None, int | None]] = []

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.inserts.append((table, payload))
        if table == "agent_runs":
            return {"id": payload.get("id") or "11111111-1111-4111-8111-111111111111", **payload}
        if table == "agent_steps":
            return {"id": len(self.inserts), **payload}
        return {"id": "noop", **payload}

    def patch(
        self,
        table: str,
        filters: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        self.patches.append((table, filters, payload))
        return {"id": filters.get("id"), **payload}

    def select_one(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None = None,
    ) -> dict[str, Any] | None:
        return None

    def select_many(
        self,
        table: str,
        filters: dict[str, Any],
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.select_many_calls.append((table, filters, order, limit))
        return []


def test_init_state_creates_running_state_with_deadline() -> None:
    request = AgentRunRequest(text="누구나 안정적으로 받을 수 있는 상품")
    state = init_state(request, max_iterations=4, deadline_seconds=30)

    assert state.status == "running"
    assert state.iteration == 0
    assert state.max_iterations == 4
    assert state.next_step_index == 0
    assert state.claim_step_index() == 0
    assert state.claim_step_index() == 1
    assert state.deadline > state.started_at
    assert state.user_message == "누구나 안정적으로 받을 수 있는 상품"
    assert state.mode == "review"
    assert not time_exceeded(state)


def test_in_memory_recorder_records_full_trace() -> None:
    recorder = InMemoryTraceRecorder()
    run_id = uuid4()

    recorder.record_thought(run_id, 0, "starting")
    recorder.record_tool_call(run_id, 1, "scan_rules", {"text": "demo"})
    recorder.record_tool_result(run_id, 2, "scan_rules", {"risk_level": "HIGH"})
    recorder.record_human_prompt(run_id, 3, {"question": "approve?"})
    recorder.record_human_response(run_id, 4, {"response": "approve"})
    recorder.record_final(run_id, 5, {"decision": "approve", "summary": "ok"})

    steps = recorder.list_steps(run_id)
    assert [step.step_type for step in steps] == [
        "thought",
        "tool_call",
        "tool_result",
        "human_prompt",
        "human_response",
        "final",
    ]
    assert steps[1].tool_name == "scan_rules"
    assert steps[1].payload["args"] == {"text": "demo"}
    assert steps[2].payload["result"]["risk_level"] == "HIGH"
    assert steps[5].payload["decision"] == "approve"


def test_in_memory_recorder_requires_monotonic_step_index() -> None:
    recorder = InMemoryTraceRecorder()
    run_id = uuid4()

    recorder.record_thought(run_id, 0, "a")
    recorder.record_thought(run_id, 1, "b")
    with pytest.raises(ValueError):
        recorder.record_thought(run_id, 1, "duplicate")
    with pytest.raises(ValueError):
        recorder.record_thought(run_id, 0, "stale")


def test_supabase_trace_recorder_inserts_into_agent_steps() -> None:
    fake_client = FakeSupabaseClient()
    repository = AgentStepsRepository(fake_client)  # type: ignore[arg-type]
    recorder = SupabaseTraceRecorder(repository)
    run_id = uuid4()

    recorder.record_tool_call(run_id, 0, "scan_rules", {"text": "demo"})
    recorder.record_tool_result(run_id, 1, "scan_rules", {"risk_level": "HIGH"})

    inserted_tables = [table for table, _payload in fake_client.inserts]
    assert inserted_tables == ["agent_steps", "agent_steps"]
    first_payload = fake_client.inserts[0][1]
    assert first_payload["run_id"] == str(run_id)
    assert first_payload["step_index"] == 0
    assert first_payload["step_type"] == "tool_call"
    assert first_payload["tool_name"] == "scan_rules"
    assert first_payload["payload"] == {"args": {"text": "demo"}}


def test_agent_runs_repository_fallback_when_supabase_missing() -> None:
    FALLBACK_AGENT_RUNS.clear()
    repository = AgentRunsRepository(SupabaseClient(SupabaseConfig(None, None, None)))

    inserted = repository.insert(
        {"content_id": None, "user_message": "테스트", "initiator": "user"}
    )

    assert inserted["status"] == "running"
    assert inserted["id"] in FALLBACK_AGENT_RUNS
    assert repository.get(inserted["id"]) == inserted

    updated = repository.update(inserted["id"], {"status": "done", "final_decision": "approve"})
    assert updated is not None
    assert updated["status"] == "done"
    assert updated["final_decision"] == "approve"


def test_agent_steps_repository_fallback_when_supabase_missing() -> None:
    FALLBACK_AGENT_STEPS.clear()
    repository = AgentStepsRepository(SupabaseClient(SupabaseConfig(None, None, None)))
    run_id = uuid4()

    repository.append(
        run_id=run_id,
        step_index=0,
        step_type="thought",
        payload={"text": "starting"},
    )
    repository.append(
        run_id=run_id,
        step_index=1,
        step_type="tool_call",
        tool_name="scan_rules",
        payload={"args": {"text": "demo"}},
    )

    rows = repository.list_for_run(run_id)
    assert [row["step_index"] for row in rows] == [0, 1]
    assert rows[1]["tool_name"] == "scan_rules"


def test_agent_runs_repository_update_calls_supabase_patch() -> None:
    fake_client = FakeSupabaseClient()
    repository = AgentRunsRepository(fake_client)  # type: ignore[arg-type]

    inserted = repository.insert({"id": "22222222-2222-4222-8222-222222222222"})
    repository.update(inserted["id"], {"status": "done"})

    assert fake_client.patches == [
        (
            "agent_runs",
            {"id": "22222222-2222-4222-8222-222222222222"},
            {"status": "done"},
        )
    ]
