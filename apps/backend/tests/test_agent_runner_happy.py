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


def test_happy_path_executes_full_tool_chain_and_ends_done() -> None:
    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    gemini = ScriptedGeminiClient(
        [
            fn_call("scan_rules", {"text": "demo"}, in_tokens=120, out_tokens=20),
            fn_call(
                "search_regulation",
                {
                    "risk_categories": ["과장 표현", "확정 수익 오인"],
                    "product_type": "투자상품",
                    "limit": 5,
                },
                in_tokens=80,
                out_tokens=15,
            ),
            fn_call(
                "draft_rewrite",
                {"content_id": CONTENT_ID, "mode": "marketing_balanced"},
                in_tokens=140,
                out_tokens=30,
            ),
            fn_call(
                "finalize_report",
                {
                    "content_id": CONTENT_ID,
                    "decision": "approve",
                    "selected_revision": "마케팅안 최종 텍스트",
                    "reviewer": "AI Agent",
                    "summary": "approved after review",
                },
                in_tokens=60,
                out_tokens=10,
            ),
        ]
    )
    recorder = in_memory_trace_recorder()
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=recorder,
        limits=AgentLimits(max_iterations=8, deadline_seconds=60),
    )

    detail = runner.run(
        AgentRunRequest(
            content_id=CONTENT_ID,
            text="누구나 연 8% 수익 안정적으로",
            mode="review",
        )
    )

    assert detail.status == "done"
    assert detail.final_decision == "approve"
    assert detail.final_report is not None
    assert detail.token_input == 120 + 80 + 140 + 60
    assert detail.token_output == 20 + 15 + 30 + 10

    step_types = [step.step_type for step in detail.steps]
    # 2 initial thoughts + 4*(call+result) + 1 final = 11
    assert step_types.count("thought") >= 2
    assert step_types.count("tool_call") == 4
    assert step_types.count("tool_result") == 4
    assert step_types.count("final") == 1

    tool_calls = [step.tool_name for step in detail.steps if step.step_type == "tool_call"]
    assert tool_calls == [
        "scan_rules",
        "search_regulation",
        "draft_rewrite",
        "finalize_report",
    ]

    persisted = runs_repo.get(detail.id)
    assert persisted is not None
    assert persisted["status"] == "done"
    assert persisted["final_decision"] == "approve"
    assert persisted["model"] == "fake-gemini-1.5-flash"


def test_happy_path_no_tool_call_forces_finalize_with_none_decision() -> None:
    from tests._agent_fakes import text_response

    runs_repo = InMemoryAgentRunsRepository()
    registry = build_stub_registry(runs_repository=runs_repo)
    gemini = ScriptedGeminiClient([text_response("플레인 텍스트 응답")])
    runner = AgentRunner(
        registry=registry,
        gemini_client=gemini,  # type: ignore[arg-type]
        runs_repository=runs_repo,  # type: ignore[arg-type]
        trace_recorder=in_memory_trace_recorder(),
    )

    detail = runner.run(
        AgentRunRequest(content_id=CONTENT_ID, text="안내문", mode="review")
    )

    assert detail.status == "done"
    assert detail.final_decision == "none"
    finalize_calls = [
        step for step in detail.steps if step.step_type == "tool_call" and step.tool_name == "finalize_report"
    ]
    assert len(finalize_calls) == 1
