from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditRecord:
    content_id: str
    action: str
    model_version: str
    doc_version: str
    created_at: datetime


class AuditService:
    def record_analysis(self, content_id: str) -> AuditRecord:
        return AuditRecord(
            content_id=content_id,
            action="analyze",
            model_version="rule-engine-v1",
            doc_version="local-rules-v1",
            created_at=datetime.now(timezone.utc),
        )


def get_audit_service() -> AuditService:
    return AuditService()
