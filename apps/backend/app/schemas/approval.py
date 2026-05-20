from enum import Enum

from pydantic import BaseModel, Field


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    CONDITIONALLY_APPROVED = "CONDITIONALLY_APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"


class ApprovalRequest(BaseModel):
    content_id: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    decision: ApprovalDecision
    comment: str | None = None
    selected_revision: str | None = None


class ApprovalResponse(BaseModel):
    approval_id: str
    content_id: str
    status: str
    decision: ApprovalDecision
    reviewer: str
