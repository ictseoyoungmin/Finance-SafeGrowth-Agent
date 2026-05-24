"""Shared fakes for Day 17 agent runner tests.

Not collected by pytest because the filename does not match `test_*.py`.
"""

from typing import Any
from uuid import UUID

from app.agent.state import AgentState
from app.agent.tools.registry import ToolRegistry
from app.agent.tools.request_human_review import RequestHumanReviewTool
from app.agent.trace import InMemoryTraceRecorder
from app.integrations.gemini_client import GeminiFunctionCall, GeminiToolResponse
from app.schemas.agent import AgentFinal
from app.schemas.compliance import FlaggedSpan, RiskLevel
from app.schemas.report import ReportResponse
from app.schemas.tools import (
    DraftRewriteArgs,
    DraftRewriteResult,
    FetchContentArgs,
    FetchContentResult,
    FinalizeReportArgs,
    FinalizeReportResult,
    ScanRulesArgs,
    ScanRulesResult,
    SearchRegulationArgs,
    SearchRegulationHit,
    SearchRegulationResult,
)


# ---------------------------------------------------------------------------
# Gemini fake
# ---------------------------------------------------------------------------


class ScriptedGeminiClient:
    """Returns scripted GeminiToolResponse objects in order."""

    def __init__(
        self,
        responses: list[GeminiToolResponse | None] | None = None,
        *,
        configured: bool = True,
        model: str = "fake-gemini-1.5-flash",
    ) -> None:
        self._responses: list[GeminiToolResponse | None] = list(responses or [])
        self._configured = configured
        self._model = model
        self.calls: list[dict[str, Any]] = []

    @property
    def is_configured(self) -> bool:
        return self._configured

    @property
    def model(self) -> str:
        return self._model

    def generate_with_tools(self, **kwargs: Any) -> GeminiToolResponse | None:
        self.calls.append(kwargs)
        if not self._responses:
            return None
        return self._responses.pop(0)

    def generate_json(self, prompt: str):  # pragma: no cover - unused here
        return None


def fn_call(name: str, args: dict[str, Any], *, in_tokens: int = 0, out_tokens: int = 0) -> GeminiToolResponse:
    return GeminiToolResponse(
        function_call=GeminiFunctionCall(name=name, args=args),
        text=None,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        model_version="fake-gemini-1.5-flash",
    )


def text_response(text: str, *, in_tokens: int = 0, out_tokens: int = 0) -> GeminiToolResponse:
    return GeminiToolResponse(
        function_call=None,
        text=text,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        model_version="fake-gemini-1.5-flash",
    )


# ---------------------------------------------------------------------------
# Runs repository fake (per-test isolation, unlike FALLBACK_AGENT_RUNS global)
# ---------------------------------------------------------------------------


class InMemoryAgentRunsRepository:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def insert(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload)
        self.store[str(row["id"])] = row
        return row

    def update(self, run_id, patch: dict[str, Any]) -> dict[str, Any] | None:
        key = str(run_id)
        if key not in self.store:
            return None
        self.store[key].update(patch)
        return self.store[key]

    def get(self, run_id) -> dict[str, Any] | None:
        return self.store.get(str(run_id))


# ---------------------------------------------------------------------------
# Stub tools that do not touch repositories
# ---------------------------------------------------------------------------


class StubFetchContentTool:
    name = "fetch_content"
    description = "Stub fetch_content."
    args_model = FetchContentArgs
    result_model = FetchContentResult

    def __init__(self, store: dict[str, dict[str, str]] | None = None) -> None:
        self.store = store or {}

    def run(self, args: FetchContentArgs, state: AgentState) -> FetchContentResult:
        record = self.store.get(args.content_id, {})
        try:
            state.content_id = UUID(args.content_id)
        except ValueError:
            state.content_id = None
        return FetchContentResult(
            content_id=args.content_id,
            original_text=str(record.get("original_text") or "stub original text"),
            product_type=record.get("product_type") or "투자상품",
            channel=record.get("channel") or "앱 푸시",
            target_customer=record.get("target_customer") or "30대 직장인",
            language=record.get("language") or "ko",
        )


class StubScanRulesTool:
    name = "scan_rules"
    description = "Stub scan_rules."
    args_model = ScanRulesArgs
    result_model = ScanRulesResult

    def __init__(
        self,
        *,
        risk_level: RiskLevel = RiskLevel.HIGH,
        risk_categories: list[str] | None = None,
        spans: list[FlaggedSpan] | None = None,
    ) -> None:
        self.risk_level = risk_level
        self.risk_categories = risk_categories or ["과장 표현", "확정 수익 오인"]
        self.spans = spans or [
            FlaggedSpan(
                span_text="누구나",
                start=0,
                end=3,
                risk_category="과장 표현",
                severity=RiskLevel.HIGH,
                reason="stub",
                confidence=0.9,
            )
        ]

    def run(self, args: ScanRulesArgs, state: AgentState) -> ScanRulesResult:
        return ScanRulesResult(
            risk_level=self.risk_level,
            risk_categories=list(self.risk_categories),
            flagged_spans=list(self.spans),
        )


class StubSearchRegulationTool:
    name = "search_regulation"
    description = "Stub search_regulation."
    args_model = SearchRegulationArgs
    result_model = SearchRegulationResult

    def __init__(self, evidence: list[SearchRegulationHit] | None = None) -> None:
        self.evidence = evidence or [
            SearchRegulationHit(
                evidence_id="doc-demo-001",
                title="가이드라인",
                version="demo-v1",
                snippet="snippet",
                guideline_snippet="g",
                similarity=0.85,
            )
        ]

    def run(self, args: SearchRegulationArgs, state: AgentState) -> SearchRegulationResult:
        return SearchRegulationResult(evidence=list(self.evidence))


class StubDraftRewriteTool:
    name = "draft_rewrite"
    description = "Stub draft_rewrite."
    args_model = DraftRewriteArgs
    result_model = DraftRewriteResult

    def __init__(self) -> None:
        self.calls: list[DraftRewriteArgs] = []

    def run(self, args: DraftRewriteArgs, state: AgentState) -> DraftRewriteResult:
        self.calls.append(args)
        return DraftRewriteResult(
            content_id=args.content_id,
            revised_text_conservative="보수안",
            revised_text_marketing="마케팅안",
            changes=[],
            source="gemini",
        )


class StubFinalizeReportTool:
    name = "finalize_report"
    description = "Stub finalize_report."
    args_model = FinalizeReportArgs
    result_model = FinalizeReportResult

    def __init__(self, runs_repository: InMemoryAgentRunsRepository | None = None) -> None:
        self.runs_repository = runs_repository
        self.calls: list[FinalizeReportArgs] = []

    def run(self, args: FinalizeReportArgs, state: AgentState) -> FinalizeReportResult:
        self.calls.append(args)
        report = ReportResponse(
            content_id=args.content_id,
            summary=args.summary or "stub",
            risk_level="HIGH",
            final_text=args.selected_revision or "최종 텍스트",
            evidence=[],
            changes=[],
            approval=None,
            audit_log=[],
        )
        state.final = AgentFinal(
            decision=args.decision,
            selected_revision=args.selected_revision,
            summary=args.summary or "stub",
            report=report,
        )
        state.status = "done"
        if self.runs_repository is not None:
            self.runs_repository.update(
                state.run_id,
                {
                    "status": "done",
                    "final_decision": args.decision,
                    "final_summary": args.summary or "stub",
                    "final_report": report.model_dump(mode="json"),
                },
            )
        return FinalizeReportResult(
            content_id=args.content_id,
            decision=args.decision,
            summary=args.summary or "stub",
            report=report,
        )


def build_stub_registry(
    runs_repository: InMemoryAgentRunsRepository | None = None,
    *,
    fetch_store: dict[str, dict[str, str]] | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(StubFetchContentTool(store=fetch_store))
    registry.register(StubScanRulesTool())
    registry.register(StubSearchRegulationTool())
    registry.register(StubDraftRewriteTool())
    registry.register(RequestHumanReviewTool())  # pure, safe to use real
    registry.register(StubFinalizeReportTool(runs_repository=runs_repository))
    return registry


def in_memory_trace_recorder() -> InMemoryTraceRecorder:
    return InMemoryTraceRecorder()


__all__ = [
    "InMemoryAgentRunsRepository",
    "ScriptedGeminiClient",
    "StubDraftRewriteTool",
    "StubFetchContentTool",
    "StubFinalizeReportTool",
    "StubScanRulesTool",
    "StubSearchRegulationTool",
    "build_stub_registry",
    "fn_call",
    "in_memory_trace_recorder",
    "text_response",
]
