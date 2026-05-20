from typing import Any

from app.repositories.approval_logs_repo import ApprovalLogsRepository, get_approval_logs_repository
from app.repositories.audit_logs_repo import AuditLogsRepository, get_audit_logs_repository
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.risk_results_repo import RiskResultsRepository, get_risk_results_repository
from app.schemas.report import ReportResponse


class ReportService:
    def __init__(
        self,
        content_repository: ContentRepository,
        risk_results_repository: RiskResultsRepository,
        approval_logs_repository: ApprovalLogsRepository,
        audit_logs_repository: AuditLogsRepository,
    ) -> None:
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._approval_logs_repository = approval_logs_repository
        self._audit_logs_repository = audit_logs_repository

    def build(self, content_id: str) -> ReportResponse:
        content = self._content_repository.get(content_id) or {}
        risk_result = self._risk_results_repository.get_latest_by_content_id(content_id) or {}
        approval = self._approval_logs_repository.get_latest_by_content_id(content_id)
        audit_log = self._audit_logs_repository.list_by_content_id(content_id)
        risk_level = risk_result.get("risk_level")
        final_text = self._final_text(content, approval)

        return ReportResponse(
            content_id=content_id,
            summary=self._summary(risk_level, approval),
            risk_level=risk_level,
            final_text=final_text,
            evidence=[],
            changes=[],
            approval=approval,
            audit_log=audit_log,
        )

    def _final_text(self, content: dict[str, Any], approval: dict[str, Any] | None) -> str:
        if approval and approval.get("selected_revision"):
            return str(approval["selected_revision"])
        return str(content.get("original_text") or "")

    def _summary(self, risk_level: str | None, approval: dict[str, Any] | None) -> str:
        if approval:
            return f"Approval package generated with decision {approval.get('decision')}."
        if risk_level:
            return f"Approval package generated with latest risk level {risk_level}."
        return "Approval package generated without stored analysis details."


def get_report_service() -> ReportService:
    return ReportService(
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        approval_logs_repository=get_approval_logs_repository(),
        audit_logs_repository=get_audit_logs_repository(),
    )
