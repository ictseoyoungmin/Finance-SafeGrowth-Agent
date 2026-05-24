from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.report import ReportResponse


AgentRunStatus = Literal["running", "awaiting_human", "done", "failed", "cancelled"]
AgentStepType = Literal[
    "thought",
    "tool_call",
    "tool_result",
    "human_prompt",
    "human_response",
    "final",
]
AgentMode = Literal["review", "rewrite_only", "explain"]
AgentDecision = Literal["approve", "reject", "revise", "none"]


class AgentInitiator(str, Enum):
    USER = "user"
    SCHEDULED = "scheduled"


class HumanPrompt(BaseModel):
    question: str = Field(..., min_length=1)
    options: list[str] | None = None
    proposed_action: dict[str, Any] | None = None


class HumanResponse(BaseModel):
    response: str | dict[str, Any]


class AgentFinal(BaseModel):
    decision: AgentDecision = "none"
    selected_revision: str | None = None
    summary: str = ""
    report: ReportResponse | None = None


class AgentRunRequest(BaseModel):
    content_id: UUID | None = None
    text: str | None = None
    user_message: str | None = None
    mode: AgentMode = "review"
    product_type: str | None = None
    channel: str | None = None
    target_customer: str | None = None
    language: str = "ko"
    initiator: AgentInitiator = AgentInitiator.USER


class AgentStep(BaseModel):
    run_id: UUID
    step_index: int = Field(..., ge=0)
    step_type: AgentStepType
    tool_name: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AgentRunSummary(BaseModel):
    id: UUID
    status: AgentRunStatus
    started_at: datetime
    ended_at: datetime | None = None
    content_id: UUID | None = None
    initiator: AgentInitiator | None = None
    user_message: str | None = None
    final_decision: AgentDecision | None = None
    final_summary: str | None = None
    token_input: int | None = None
    token_output: int | None = None
    model: str | None = None


class AgentRunDetail(AgentRunSummary):
    steps: list[AgentStep] = Field(default_factory=list)
    pending_human: HumanPrompt | None = None
    final_report: ReportResponse | None = None


class AgentRunResult(BaseModel):
    run: AgentRunDetail
