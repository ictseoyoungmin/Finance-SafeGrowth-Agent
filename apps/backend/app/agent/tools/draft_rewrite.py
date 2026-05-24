from app.agent.state import AgentState
from app.agent.tools.base import ToolError
from app.schemas.rewrite import RewriteRequest
from app.schemas.tools import DraftRewriteArgs, DraftRewriteResult
from app.services.rewrite_service import RewriteService, get_rewrite_service


class DraftRewriteTool:
    name = "draft_rewrite"
    description = (
        "Generate a compliance-aware rewrite of the stored advertisement text. "
        "Returns both a conservative and a marketing variant plus the list of changes. "
        "Uses Gemini when configured, otherwise a deterministic rule-driven fallback. "
        "The `mode` argument is a free-form hint forwarded to the rewriter "
        "(default 'marketing_balanced'). Call this after scan_rules and search_regulation "
        "so the rewrite context is rich."
    )
    args_model = DraftRewriteArgs
    result_model = DraftRewriteResult

    def __init__(self, rewrite_service: RewriteService | None = None) -> None:
        self._rewrite_service = rewrite_service or get_rewrite_service()

    def run(self, args: DraftRewriteArgs, state: AgentState) -> DraftRewriteResult:
        try:
            response = self._rewrite_service.rewrite(
                RewriteRequest(content_id=args.content_id, mode=args.mode)
            )
        except Exception as exc:  # noqa: BLE001
            raise ToolError(
                "rewrite_failed",
                str(exc) or "Rewrite service failed.",
                retryable=True,
                details={"type": exc.__class__.__name__},
            ) from exc

        return DraftRewriteResult(
            content_id=response.content_id,
            revised_text_conservative=response.revised_text_conservative,
            revised_text_marketing=response.revised_text_marketing,
            changes=list(response.changes),
            source=response.source,
        )
