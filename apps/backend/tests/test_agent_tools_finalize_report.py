import pytest

from app.agent.state import init_state
from app.agent.tools.base import ToolError
from app.agent.tools.finalize_report import FinalizeReportTool
from app.schemas.agent import AgentRunRequest
from app.schemas.approval import ApprovalRequest, ApprovalResponse, ApprovalDecision
from app.schemas.report import ReportResponse
from app.schemas.tools import FinalizeReportArgs


class StubApprovalService:
    def __init__(self) -> None:
        self.calls: list[ApprovalRequest] = []

    def approve(self, request: ApprovalRequest) -> ApprovalResponse:
        self.calls.append(request)
        return ApprovalResponse(
            approval_id="44444444-4444-4444-8444-444444444444",
            content_id=request.content_id,
            status=request.decision.value,
            decision=request.decision,
            reviewer=request.reviewer,
        )


class StubReportService:
    def __init__(self, report: ReportResponse) -> None:
        self.report = report
        self.calls: list[str] = []

    def build(self, content_id: str) -> ReportResponse:
        self.calls.append(content_id)
        return self.report


class ExplodingReportService:
    def build(self, content_id: str) -> ReportResponse:
        raise RuntimeError("supabase down")


class StubAgentRunsRepository:
    def __init__(self) -> None:
        self.updates: list[tuple[str, dict]] = []

    def update(self, run_id, patch):
        self.updates.append((str(run_id), patch))
        return {"id": str(run_id), **patch}


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def _report(content_id: str = "abc") -> ReportResponse:
    return ReportResponse(
        content_id=content_id,
        summary="prebuilt",
        risk_level="HIGH",
        final_text="최종 텍스트",
        evidence=[],
        changes=[],
        approval=None,
        audit_log=[],
    )


def test_finalize_report_with_approve_records_approval_and_updates_run() -> None:
    approval = StubApprovalService()
    report_service = StubReportService(_report("22222222-2222-4222-8222-222222222222"))
    runs_repo = StubAgentRunsRepository()
    tool = FinalizeReportTool(
        approval_service=approval,
        report_service=report_service,
        agent_runs_repository=runs_repo,
    )
    state = _state()

    result = tool.run(
        FinalizeReportArgs(
            content_id="22222222-2222-4222-8222-222222222222",
            decision="approve",
            selected_revision="마케팅 최종안 텍스트",
            reviewer="AI Agent",
            summary="approved after review",
        ),
        state,
    )

    assert result.decision == "approve"
    assert result.summary == "approved after review"
    assert result.report is not None
    assert state.status == "done"
    assert state.final is not None
    assert state.final.decision == "approve"

    assert len(approval.calls) == 1
    recorded = approval.calls[0]
    assert recorded.decision == ApprovalDecision.APPROVED
    assert recorded.selected_revision == "마케팅 최종안 텍스트"

    assert len(runs_repo.updates) == 1
    patch = runs_repo.updates[0][1]
    assert patch["status"] == "done"
    assert patch["final_decision"] == "approve"
    assert patch["final_summary"] == "approved after review"
    assert patch["final_report"]["final_text"] == "최종 텍스트"


def test_finalize_report_with_none_decision_skips_approval() -> None:
    approval = StubApprovalService()
    report_service = StubReportService(_report())
    runs_repo = StubAgentRunsRepository()
    tool = FinalizeReportTool(
        approval_service=approval,
        report_service=report_service,
        agent_runs_repository=runs_repo,
    )

    result = tool.run(
        FinalizeReportArgs(content_id="abc", decision="none"),
        _state(),
    )

    assert result.decision == "none"
    assert approval.calls == []
    assert runs_repo.updates and runs_repo.updates[0][1]["final_decision"] == "none"


def test_finalize_report_wraps_report_build_failure() -> None:
    tool = FinalizeReportTool(
        approval_service=StubApprovalService(),
        report_service=ExplodingReportService(),
        agent_runs_repository=StubAgentRunsRepository(),
    )

    with pytest.raises(ToolError) as exc_info:
        tool.run(FinalizeReportArgs(content_id="abc", decision="none"), _state())

    assert exc_info.value.code == "report_build_failed"
    assert exc_info.value.retryable is True


def test_finalize_report_default_summary_when_blank() -> None:
    approval = StubApprovalService()
    report_service = StubReportService(_report())
    runs_repo = StubAgentRunsRepository()
    tool = FinalizeReportTool(
        approval_service=approval,
        report_service=report_service,
        agent_runs_repository=runs_repo,
    )

    result = tool.run(
        FinalizeReportArgs(content_id="abc", decision="approve"),
        _state(),
    )

    assert "Approved" in result.summary
    assert "risk_level=HIGH" in result.summary
