from datetime import datetime
from typing import Any

from app.services.audit_service import AuditService


class FakeAuditLogsRepository:
    def __init__(self) -> None:
        self.saved: list[dict[str, Any]] = []

    def save(
        self,
        content_id: str,
        action: str,
        model_version: str,
        doc_version: str,
        prompt_hash: str | None,
        created_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.saved.append(
            {
                "content_id": content_id,
                "action": action,
                "metadata": metadata,
            }
        )


def test_record_analysis_attaches_rule_categories_metadata() -> None:
    repo = FakeAuditLogsRepository()
    service = AuditService(repo)  # type: ignore[arg-type]

    record = service.record_analysis("content-1", rule_categories=["과장 표현", "확정 수익 오인"])

    assert record.rule_categories == ["과장 표현", "확정 수익 오인"]
    assert repo.saved[0]["metadata"] == {"rule_categories": ["과장 표현", "확정 수익 오인"]}


def test_record_analysis_without_categories_omits_metadata() -> None:
    repo = FakeAuditLogsRepository()
    service = AuditService(repo)  # type: ignore[arg-type]

    service.record_analysis("content-1")

    assert repo.saved[0]["metadata"] is None
