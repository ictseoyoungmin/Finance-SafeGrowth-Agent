from app.agent.state import init_state
from app.agent.tools.request_human_review import RequestHumanReviewTool
from app.schemas.agent import AgentRunRequest
from app.schemas.tools import RequestHumanReviewArgs


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def test_request_human_review_sets_state_to_awaiting_human() -> None:
    tool = RequestHumanReviewTool()
    state = _state()

    result = tool.run(
        RequestHumanReviewArgs(
            question="이 수정안으로 승인할까요?",
            options=["approve", "reject", "revise"],
            proposed_action={"decision": "approve", "selected_revision": "marketing"},
        ),
        state,
    )

    assert state.status == "awaiting_human"
    assert state.pending_human is not None
    assert state.pending_human.question == "이 수정안으로 승인할까요?"
    assert result.awaiting_human is True
    assert result.options == ["approve", "reject", "revise"]
    assert result.proposed_action == {"decision": "approve", "selected_revision": "marketing"}


def test_request_human_review_accepts_minimal_payload() -> None:
    tool = RequestHumanReviewTool()
    state = _state()

    result = tool.run(
        RequestHumanReviewArgs(question="추가 정보가 필요합니다."),
        state,
    )

    assert result.question == "추가 정보가 필요합니다."
    assert result.options is None
    assert result.proposed_action is None
    assert state.status == "awaiting_human"
