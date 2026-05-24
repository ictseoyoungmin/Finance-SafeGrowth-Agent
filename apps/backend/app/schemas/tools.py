from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agent import AgentDecision
from app.schemas.compliance import FlaggedSpan, RiskLevel
from app.schemas.report import ReportResponse
from app.schemas.rewrite import RewriteChange


# ----- fetch_content -----


class FetchContentArgs(BaseModel):
    content_id: str = Field(..., min_length=1)


class FetchContentResult(BaseModel):
    content_id: str
    original_text: str
    product_type: str | None = None
    channel: str | None = None
    target_customer: str | None = None
    language: str = "ko"


# ----- scan_rules -----


class ScanRulesArgs(BaseModel):
    text: str = Field(..., min_length=1)


class ScanRulesResult(BaseModel):
    risk_level: RiskLevel
    risk_categories: list[str] = Field(default_factory=list)
    flagged_spans: list[FlaggedSpan] = Field(default_factory=list)


# ----- search_regulation -----


class SearchRegulationArgs(BaseModel):
    query: str | None = None
    risk_categories: list[str] = Field(default_factory=list)
    product_type: str = "공통"
    limit: int = Field(default=5, ge=1, le=20)


class SearchRegulationHit(BaseModel):
    evidence_id: str
    title: str
    version: str
    version_id: str | None = None
    version_label: str | None = None
    effective_date: str | None = None
    snippet: str
    guideline_snippet: str
    similarity: float = Field(..., ge=0, le=1)


class SearchRegulationResult(BaseModel):
    evidence: list[SearchRegulationHit] = Field(default_factory=list)


# ----- draft_rewrite -----


class DraftRewriteArgs(BaseModel):
    content_id: str = Field(..., min_length=1)
    mode: str = "marketing_balanced"


class DraftRewriteResult(BaseModel):
    content_id: str
    revised_text_conservative: str
    revised_text_marketing: str
    changes: list[RewriteChange] = Field(default_factory=list)
    source: str = "fallback"


# ----- request_human_review -----


class RequestHumanReviewArgs(BaseModel):
    question: str = Field(..., min_length=1)
    options: list[str] | None = None
    proposed_action: dict[str, Any] | None = None


class RequestHumanReviewResult(BaseModel):
    awaiting_human: bool = True
    question: str
    options: list[str] | None = None
    proposed_action: dict[str, Any] | None = None


# ----- finalize_report -----


class FinalizeReportArgs(BaseModel):
    content_id: str = Field(..., min_length=1)
    decision: AgentDecision = "none"
    selected_revision: str | None = None
    reviewer: str = "AI Agent"
    summary: str = ""
    comment: str | None = None


class FinalizeReportResult(BaseModel):
    content_id: str
    decision: AgentDecision
    summary: str
    report: ReportResponse | None = None
