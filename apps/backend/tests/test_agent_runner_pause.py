from app.agent.runner import AgentRunner
from app.schemas.agent import AgentRunRequest

from tests._agent_fakes import (
    InMemoryAgentRunsRepository,
    ScriptedLlmProvider,
    build_stub_registry,
    fn_call,
    in_memory_trace_recorder,
)


CONTENT_ID = "22222222-2222-4222-8222-222222222222"


def test_pause_on_request_human_review_then_resume_with_approve() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    llm = ScriptedLlmProvider(
        [
            fn_call("scan_rules", {"text": "demo"}),
            fn_call(
                "request_human_review",
                {
                    "question": "이 수정안으로 승인할까요?",
                    "options": ["approve", "reject"],
                    "proposed_action": {"decision": "approve"},
                },
            ),
            # After resume, the model decides to finalize.
            fn_call(
                "finalize_report",
                {
                    "content_id": CONTENT_ID,
                    "decision": "approve",
                    "selected_revision": "마케팅안 최종 텍스트",
                    "summary": "approved after human review",
                },
            ),
        ]
    )
    recorder = in_memory_trace_recorder()
    runner = AgentRunner(
        registry=registry,
        llm_provider=llm,
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=recorder,
    )

    paused = runner.run(
        AgentRunRequest(content_id=CONTENT_ID, text="누구나 연 8% 수익", mode="review")
    )

    assert paused.status == "awaiting_human"
    assert paused.pending_human is not None
    assert paused.pending_human.options == ["approve", "reject"]
    persisted_paused = runs_repo.get(paused.id)
    assert persisted_paused["status"] == "awaiting_human"

    resumed = runner.resume(paused.id, "approve")

    assert resumed.status == "done"
    assert resumed.final_decision == "approve"
    tool_calls = [step.tool_name for step in resumed.steps if step.step_type == "tool_call"]
    assert tool_calls == ["scan_rules", "request_human_review", "finalize_report"]
    response_steps = [step for step in resumed.steps if step.step_type == "human_response"]
    assert len(response_steps) == 1
    assert response_steps[0].payload["response"] == "approve"
