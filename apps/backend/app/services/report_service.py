from typing import Any

from app.repositories.approval_logs_repo import ApprovalLogsRepository, get_approval_logs_repository
from app.repositories.audit_logs_repo import AuditLogsRepository, get_audit_logs_repository
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.risk_results_repo import RiskResultsRepository, get_risk_results_repository
from app.schemas.history import RecentContentItem, RecentContentsResponse
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

    def list_recent(self, limit: int = 20) -> RecentContentsResponse:
        records = self._content_repository.list_recent(limit=limit)
        items: list[RecentContentItem] = []
        for record in records:
            content_id = str(record.get("id"))
            risk_result = self._risk_results_repository.get_latest_by_content_id(content_id) or {}
            approval = self._approval_logs_repository.get_latest_by_content_id(content_id) or {}
            original_text = str(record.get("original_text") or "")
            items.append(
                RecentContentItem(
                    id=content_id,
                    created_at=_optional_str(record.get("created_at")),
                    product_type=str(record.get("product_type") or ""),
                    channel=str(record.get("channel") or ""),
                    target_customer=str(record.get("target_customer") or ""),
                    language=str(record.get("language") or "ko"),
                    original_text_preview=_truncate(original_text, 80),
                    risk_level=_optional_str(risk_result.get("risk_level")),
                    decision=_optional_str(approval.get("decision")),
                    reviewer=_optional_str(approval.get("reviewer")),
                )
            )
        return RecentContentsResponse(items=items)

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


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def get_report_service() -> ReportService:
    return ReportService(
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        approval_logs_repository=get_approval_logs_repository(),
        audit_logs_repository=get_audit_logs_repository(),
    )
