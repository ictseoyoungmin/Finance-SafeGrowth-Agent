from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    action: str
    model_version: str
    doc_version: str
    prompt_hash: str | None = None
    created_at: str | None = None


class AuditLogResponse(BaseModel):
    content_id: str
    entries: list[AuditLogEntry]
