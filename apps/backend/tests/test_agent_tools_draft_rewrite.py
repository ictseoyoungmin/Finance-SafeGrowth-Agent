import pytest

from app.agent.state import init_state
from app.agent.tools.base import ToolError
from app.agent.tools.draft_rewrite import DraftRewriteTool
from app.schemas.agent import AgentRunRequest
from app.schemas.rewrite import RewriteChange, RewriteRequest, RewriteResponse
from app.schemas.tools import DraftRewriteArgs


class StubRewriteService:
    def __init__(self, response: RewriteResponse) -> None:
        self.response = response
        self.calls: list[RewriteRequest] = []

    def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        self.calls.append(request)
        return self.response


class ExplodingRewriteService:
    def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        raise RuntimeError("llm boom")


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def test_draft_rewrite_returns_rewrite_response_from_service() -> None:
    response = RewriteResponse(
        content_id="22222222-2222-4222-8222-222222222222",
        revised_text_conservative="보수안",
        revised_text_marketing="마케팅안",
        changes=[
            RewriteChange(
                original="연 8% 수익",
                replacement="시장 상황에 따라 수익은 변동될 수 있으며",
                reason="확정 수익 오인 표현 완화",
            )
        ],
        source="llm",
    )
    service = StubRewriteService(response)
    tool = DraftRewriteTool(rewrite_service=service)

    result = tool.run(
        DraftRewriteArgs(
            content_id="22222222-2222-4222-8222-222222222222",
            mode="marketing_balanced",
        ),
        _state(),
    )

    assert result.revised_text_conservative == "보수안"
    assert result.revised_text_marketing == "마케팅안"
    assert result.source == "llm"
    assert len(result.changes) == 1
    assert service.calls[0].mode == "marketing_balanced"
    assert service.calls[0].content_id == "22222222-2222-4222-8222-222222222222"


def test_draft_rewrite_wraps_service_exception_as_tool_error() -> None:
    tool = DraftRewriteTool(rewrite_service=ExplodingRewriteService())

    with pytest.raises(ToolError) as exc_info:
        tool.run(
            DraftRewriteArgs(content_id="abc"),
            _state(),
        )

    assert exc_info.value.code == "rewrite_failed"
    assert exc_info.value.retryable is True
    assert exc_info.value.details["type"] == "RuntimeError"
