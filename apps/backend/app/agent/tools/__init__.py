from app.agent.tools.draft_rewrite import DraftRewriteTool
from app.agent.tools.fetch_content import FetchContentTool
from app.agent.tools.finalize_report import FinalizeReportTool
from app.agent.tools.registry import ToolRegistry
from app.agent.tools.request_human_review import RequestHumanReviewTool
from app.agent.tools.scan_rules import ScanRulesTool
from app.agent.tools.search_regulation import SearchRegulationTool


def get_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FetchContentTool())
    registry.register(ScanRulesTool())
    registry.register(SearchRegulationTool())
    registry.register(DraftRewriteTool())
    registry.register(RequestHumanReviewTool())
    registry.register(FinalizeReportTool())
    return registry


__all__ = [
    "DraftRewriteTool",
    "FetchContentTool",
    "FinalizeReportTool",
    "RequestHumanReviewTool",
    "ScanRulesTool",
    "SearchRegulationTool",
    "ToolRegistry",
    "get_default_registry",
]
