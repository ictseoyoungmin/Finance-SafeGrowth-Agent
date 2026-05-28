from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.repositories.audit_logs_repo import AuditLogsRepository, get_audit_logs_repository


@dataclass(frozen=True)
class AuditRecord:
    content_id: str
    action: str
    model_version: str
    doc_version: str
    prompt_hash: str | None
    created_at: datetime
    rule_categories: list[str] = field(default_factory=list)


class AuditService:
    def __init__(self, audit_logs_repository: AuditLogsRepository) -> None:
        self._audit_logs_repository = audit_logs_repository

    def record_analysis(
        self,
        content_id: str,
        rule_categories: list[str] | None = None,
    ) -> AuditRecord:
        return self.record_action(
            content_id=content_id,
            action="analyze",
            model_version="rule-engine-v1",
            doc_version="local-rules-v1",
            prompt_hash=None,
            rule_categories=rule_categories,
        )

    def record_action(
        self,
        content_id: str,
        action: str,
        model_version: str,
        doc_version: str,
        prompt_hash: str | None = None,
        rule_categories: list[str] | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            content_id=content_id,
            action=action,
            model_version=model_version,
            doc_version=doc_version,
            prompt_hash=prompt_hash,
            created_at=datetime.now(timezone.utc),
            rule_categories=list(rule_categories or []),
        )
        metadata = {"rule_categories": record.rule_categories} if record.rule_categories else None
        self._audit_logs_repository.save(
            content_id=record.content_id,
            action=record.action,
            model_version=record.model_version,
            doc_version=record.doc_version,
            prompt_hash=record.prompt_hash,
            created_at=record.created_at,
            metadata=metadata,
        )
        return record

    def list_by_content_id(self, content_id: str) -> list[dict[str, Any]]:
        return self._audit_logs_repository.list_by_content_id(content_id)


def get_audit_service() -> AuditService:
    return AuditService(get_audit_logs_repository())
