from app.agent.runner import AgentRunner
from app.schemas.agent import AgentRunRequest

from tests._agent_fakes import (
    InMemoryAgentRunsRepository,
    ScriptedGeminiClient,
    build_stub_registry,
    in_memory_trace_recorder,
)


CONTENT_ID = "22222222-2222-4222-8222-222222222222"


def test_fallback_runs_full_chain_pauses_then_resumes_done() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    gemini = ScriptedGeminiClient(responses=[], configured=False)
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=in_memory_trace_recorder(),
    )

    paused = runner.run(
        AgentRunRequest(
            content_id=CONTENT_ID,
            text="누구나 연 8% 수익을 안정적으로 받는 상품",
            product_type="투자상품",
            mode="review",
        )
    )

    assert paused.status == "awaiting_human"
    assert paused.model == "fallback-deterministic-agent"
    tool_calls = [step.tool_name for step in paused.steps if step.step_type == "tool_call"]
    assert tool_calls == [
        "scan_rules",
        "search_regulation",
        "draft_rewrite",
        "request_human_review",
    ]

    resumed = runner.resume(paused.id, {"decision": "approve", "selected_revision": "마케팅안"})

    assert resumed.status == "done"
    assert resumed.final_decision == "approve"
    finalize_calls = [
        step for step in resumed.steps if step.step_type == "tool_call" and step.tool_name == "finalize_report"
    ]
    assert len(finalize_calls) == 1
    assert finalize_calls[0].payload["args"]["decision"] == "approve"
    assert finalize_calls[0].payload["args"]["selected_revision"] == "마케팅안"


def test_fallback_skips_draft_rewrite_when_no_content_id_given() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    gemini = ScriptedGeminiClient(responses=[], configured=False)
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=in_memory_trace_recorder(),
    )

    paused = runner.run(
        AgentRunRequest(
            text="누구나 안정적으로 받는 상품",
            product_type="투자상품",
            mode="review",
        )
    )

    tool_calls = [step.tool_name for step in paused.steps if step.step_type == "tool_call"]
    assert "draft_rewrite" not in tool_calls
    assert tool_calls[0] == "scan_rules"
    assert tool_calls[-1] == "request_human_review"
