from datetime import datetime, timezone

from app.agent.state import AgentState
from app.agent.tools.base import ToolError
from app.repositories.agent_runs_repo import (
    AgentRunsRepository,
    get_agent_runs_repository,
)
from app.schemas.agent import AgentDecision, AgentFinal
from app.schemas.approval import ApprovalDecision, ApprovalRequest
from app.schemas.tools import FinalizeReportArgs, FinalizeReportResult
from app.services.approval_service import ApprovalService, get_approval_service
from app.services.report_service import ReportService, get_report_service


_DECISION_TO_APPROVAL = {
    "approve": ApprovalDecision.APPROVED,
    "reject": ApprovalDecision.REJECTED,
    "revise": ApprovalDecision.REVISION_REQUESTED,
}


class FinalizeReportTool:
    name = "finalize_report"
    description = (
        "Conclude the agent run. Records the reviewer decision (approve|reject|revise|none), "
        "stores the selected_revision, builds the final report payload, and updates the "
        "agent_run row with the result. Call this exactly once, at the end of the run, "
        "after any draft_rewrite and human review steps. When decision is 'none' the "
        "report is still produced but no approval row is created."
    )
    args_model = FinalizeReportArgs
    result_model = FinalizeReportResult

    def __init__(
        self,
        approval_service: ApprovalService | None = None,
        report_service: ReportService | None = None,
        agent_runs_repository: AgentRunsRepository | None = None,
    ) -> None:
        self._approval_service = approval_service or get_approval_service()
        self._report_service = report_service or get_report_service()
        self._agent_runs_repository = agent_runs_repository or get_agent_runs_repository()

    def run(self, args: FinalizeReportArgs, state: AgentState) -> FinalizeReportResult:
        if args.decision != "none":
            try:
                self._approval_service.approve(
                    ApprovalRequest(
                        content_id=args.content_id,
                        reviewer=args.reviewer,
                        decision=_DECISION_TO_APPROVAL[args.decision],
                        comment=args.comment,
                        selected_revision=args.selected_revision,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise ToolError(
                    "approval_failed",
                    str(exc) or "Approval recording failed.",
                    retryable=True,
                    details={"type": exc.__class__.__name__},
                ) from exc

        try:
            report = self._report_service.build(args.content_id)
        except Exception as exc:  # noqa: BLE001
            raise ToolError(
                "report_build_failed",
                str(exc) or "Report build failed.",
                retryable=True,
                details={"type": exc.__class__.__name__},
            ) from exc

        summary = args.summary or _default_summary(args.decision, report.risk_level)

        state.final = AgentFinal(
            decision=args.decision,
            selected_revision=args.selected_revision,
            summary=summary,
            report=report,
        )
        state.status = "done"

        self._agent_runs_repository.update(
            state.run_id,
            {
                "status": "done",
                "final_decision": args.decision,
                "final_summary": summary,
                "final_report": report.model_dump(mode="json"),
                "ended_at": _utc_now_iso(),
                "token_input": state.token_input,
                "token_output": state.token_output,
            },
        )

        return FinalizeReportResult(
            content_id=args.content_id,
            decision=args.decision,
            summary=summary,
            report=report,
        )


def _default_summary(decision: AgentDecision, risk_level: str | None) -> str:
    risk_label = risk_level or "unknown"
    if decision == "approve":
        return f"Approved after review (risk_level={risk_label})."
    if decision == "reject":
        return f"Rejected by reviewer (risk_level={risk_label})."
    if decision == "revise":
        return f"Revision requested (risk_level={risk_label})."
    return f"Run finalized without explicit decision (risk_level={risk_label})."


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
