from app.repositories.approval_logs_repo import ApprovalLogsRepository, get_approval_logs_repository
from app.repositories.audit_logs_repo import get_audit_logs_repository
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.services.audit_service import AuditService


class ApprovalService:
    def __init__(
        self,
        approval_logs_repository: ApprovalLogsRepository,
        audit_service: AuditService,
    ) -> None:
        self._approval_logs_repository = approval_logs_repository
        self._audit_service = audit_service

    def approve(self, request: ApprovalRequest) -> ApprovalResponse:
        approval_id = self._approval_logs_repository.save(
            content_id=request.content_id,
            reviewer=request.reviewer,
            decision=request.decision.value,
            comment=request.comment,
            selected_revision=request.selected_revision,
        )
        self._audit_service.record_action(
            content_id=request.content_id,
            action="approve",
            model_version="human-review-v1",
            doc_version="local-rules-v1",
        )
        return ApprovalResponse(
            approval_id=approval_id,
            content_id=request.content_id,
            status=self._status_for_decision(request.decision.value),
            decision=request.decision,
            reviewer=request.reviewer,
        )

    def _status_for_decision(self, decision: str) -> str:
        if decision == "CONDITIONALLY_APPROVED":
            return "APPROVED"
        return decision


def get_approval_service() -> ApprovalService:
    return ApprovalService(
        approval_logs_repository=get_approval_logs_repository(),
        audit_service=AuditService(get_audit_logs_repository()),
    )
