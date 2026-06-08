from typing import Any

from app.rag.retriever import RegulationRetriever, get_regulation_retriever
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
        retriever: RegulationRetriever,
    ) -> None:
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._approval_logs_repository = approval_logs_repository
        self._audit_logs_repository = audit_logs_repository
        self._retriever = retriever

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
        original_text = str(content.get("original_text") or "")
        final_text = self._final_text(content, approval)

        return ReportResponse(
            content_id=content_id,
            summary=self._summary(risk_level, approval),
            risk_level=risk_level,
            final_text=final_text,
            evidence=self._reconstruct_evidence(
                risk_categories=list(risk_result.get("risk_categories") or []),
                product_type=str(content.get("product_type") or ""),
                original_text=original_text,
            ),
            changes=self._reconstruct_changes(
                original_text=original_text,
                final_text=final_text,
                flagged_spans=list(risk_result.get("flagged_spans") or []),
            ),
            approval=approval,
            audit_log=audit_log,
        )

    def _reconstruct_evidence(
        self,
        risk_categories: list[str],
        product_type: str,
        original_text: str,
    ) -> list[dict[str, Any]]:
        """Re-run the regulation retriever for the report view.

        Same retriever the evidence step uses, so the approval package shows
        the same legal references the reviewer saw earlier — without having to
        persist them separately. Empty risk_categories returns [].
        """
        if not risk_categories:
            return []
        docs = self._retriever.retrieve(
            risk_categories=risk_categories,
            product_type=product_type or "투자상품",
            query=original_text or None,
        )
        return [
            {
                "evidence_id": doc.evidence_id,
                "title": doc.title,
                "version": doc.version,
                "snippet": doc.snippet,
                "similarity": doc.similarity,
                "version_id": doc.version_id,
                "effective_date": str(doc.effective_date) if doc.effective_date else None,
                "risk_categories": list(doc.risk_categories),
            }
            for doc in docs
        ]

    def _reconstruct_changes(
        self,
        original_text: str,
        final_text: str,
        flagged_spans: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Heuristic diff: spans flagged in the original but absent from the
        final text are reported as resolved changes. Cheap stand-in until
        rewrite_results is persisted (see R-B-1b)."""
        if not original_text or not final_text or original_text == final_text:
            return []
        changes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for span in flagged_spans:
            span_text = str(span.get("span_text") or "")
            if not span_text or span_text in seen:
                continue
            if span_text in original_text and span_text not in final_text:
                seen.add(span_text)
                changes.append(
                    {
                        "original": span_text,
                        "replacement": "(수정안에서 완화/제거됨)",
                        "risk_category": span.get("risk_category"),
                        "severity": span.get("severity"),
                        "reason": span.get("reason"),
                    }
                )
        return changes

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
        retriever=get_regulation_retriever(),
    )
