from app.agent.limits import AgentLimits
from app.agent.runner import AgentRunner
from app.schemas.agent import AgentRunRequest

from tests._agent_fakes import (
    InMemoryAgentRunsRepository,
    ScriptedGeminiClient,
    build_stub_registry,
    fn_call,
    in_memory_trace_recorder,
)


CONTENT_ID = "22222222-2222-4222-8222-222222222222"


def test_max_iterations_exceeded_marks_run_failed() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    # Endless loop: every iteration the model picks scan_rules again.
    infinite_scan = [fn_call("scan_rules", {"text": "loop"}) for _ in range(10)]
    gemini = ScriptedGeminiClient(infinite_scan)
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=in_memory_trace_recorder(),
        limits=AgentLimits(max_iterations=2, deadline_seconds=60),
    )

    detail = runner.run(AgentRunRequest(content_id=CONTENT_ID, text="loop", mode="review"))

    assert detail.status == "failed"
    assert detail.final_summary is not None
    assert "max_iterations_exceeded" in detail.final_summary
    tool_calls = [step.tool_name for step in detail.steps if step.step_type == "tool_call"]
    # Exactly max_iterations tool calls were executed before failure.
    assert tool_calls == ["scan_rules", "scan_rules"]


def test_deadline_exceeded_marks_run_failed() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    gemini = ScriptedGeminiClient([fn_call("scan_rules", {"text": "x"})])
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=in_memory_trace_recorder(),
        limits=AgentLimits(max_iterations=8, deadline_seconds=0),
    )

    detail = runner.run(AgentRunRequest(content_id=CONTENT_ID, text="x", mode="review"))

    assert detail.status == "failed"
    assert detail.final_summary is not None
    assert "deadline_exceeded" in detail.final_summary
