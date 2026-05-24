from uuid import UUID

import pytest

from app.agent.state import init_state
from app.agent.tools.base import ToolError
from app.agent.tools.fetch_content import FetchContentTool
from app.schemas.agent import AgentRunRequest
from app.schemas.tools import FetchContentArgs


class StubContentRepository:
    def __init__(self, store: dict[str, dict[str, str]] | None = None) -> None:
        self.store = store or {}
        self.calls: list[str] = []

    def get(self, content_id: str) -> dict[str, str] | None:
        self.calls.append(content_id)
        return self.store.get(content_id)


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def test_fetch_content_returns_record() -> None:
    repo = StubContentRepository(
        {
            "22222222-2222-4222-8222-222222222222": {
                "id": "22222222-2222-4222-8222-222222222222",
                "original_text": "원문 텍스트",
                "product_type": "투자상품",
                "channel": "앱 푸시",
                "target_customer": "30대 직장인",
                "language": "ko",
            }
        }
    )
    tool = FetchContentTool(repository=repo)
    state = _state()

    result = tool.run(
        FetchContentArgs(content_id="22222222-2222-4222-8222-222222222222"),
        state,
    )

    assert result.original_text == "원문 텍스트"
    assert result.product_type == "투자상품"
    assert result.channel == "앱 푸시"
    assert result.language == "ko"
    assert state.content_id == UUID("22222222-2222-4222-8222-222222222222")
    assert repo.calls == ["22222222-2222-4222-8222-222222222222"]


def test_fetch_content_raises_when_missing() -> None:
    tool = FetchContentTool(repository=StubContentRepository())

    with pytest.raises(ToolError) as exc_info:
        tool.run(FetchContentArgs(content_id="missing-id"), _state())

    assert exc_info.value.code == "content_not_found"


def test_fetch_content_handles_non_uuid_id_without_breaking_state() -> None:
    repo = StubContentRepository(
        {"abc": {"id": "abc", "original_text": "raw"}}
    )
    tool = FetchContentTool(repository=repo)
    state = _state()

    result = tool.run(FetchContentArgs(content_id="abc"), state)

    assert result.original_text == "raw"
    assert state.content_id is None
