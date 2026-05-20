from typing import Any

from pydantic import BaseModel


class ReportResponse(BaseModel):
    content_id: str
    summary: str
    risk_level: str | None = None
    final_text: str
    evidence: list[dict[str, Any]]
    changes: list[dict[str, Any]]
    approval: dict[str, Any] | None
    audit_log: list[dict[str, Any]]
