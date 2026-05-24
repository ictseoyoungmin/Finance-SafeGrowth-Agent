from uuid import UUID

from app.agent.state import AgentState
from app.agent.tools.base import ToolError
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.schemas.tools import FetchContentArgs, FetchContentResult


class FetchContentTool:
    name = "fetch_content"
    description = (
        "Load the original advertisement text and its metadata for a given content_id. "
        "Call this first when the user supplies content_id but the agent has not yet "
        "received the actual text. Returns product_type, channel, target_customer, language, "
        "and original_text. Raises content_not_found if the content_id is unknown."
    )
    args_model = FetchContentArgs
    result_model = FetchContentResult

    def __init__(self, repository: ContentRepository | None = None) -> None:
        self._repository = repository or get_content_repository()

    def run(self, args: FetchContentArgs, state: AgentState) -> FetchContentResult:
        record = self._repository.get(args.content_id)
        if record is None:
            raise ToolError(
                "content_not_found",
                f"No stored content for content_id={args.content_id}.",
            )

        try:
            state.content_id = UUID(args.content_id)
        except ValueError:
            state.content_id = None

        return FetchContentResult(
            content_id=args.content_id,
            original_text=str(record.get("original_text") or ""),
            product_type=_optional_str(record.get("product_type")),
            channel=_optional_str(record.get("channel")),
            target_customer=_optional_str(record.get("target_customer")),
            language=str(record.get("language") or "ko"),
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
