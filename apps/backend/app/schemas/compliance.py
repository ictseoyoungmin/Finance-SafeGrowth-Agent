from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnalyzeRequest(BaseModel):
    product_type: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    target_customer: str = Field(..., min_length=1)
    language: str = "ko"
    # Upper bound guards against pathological inputs (e.g. an attacker pasting
    # hundreds of KB) that would otherwise be forwarded to the LLM and blow
    # past quota / cost limits. 5000 chars covers any realistic ad copy.
    original_text: str = Field(..., min_length=1, max_length=5000)


class FlaggedSpan(BaseModel):
    span_text: str
    start: int
    end: int
    risk_category: str
    severity: RiskLevel
    reason: str
    confidence: float = Field(..., ge=0, le=1)
    source: Literal["rule", "llm", "gemini"] = "rule"


class AnalyzeResponse(BaseModel):
    content_id: str
    risk_level: RiskLevel
    flagged_spans: list[FlaggedSpan]
    risk_categories: list[str]
    reviewer_notes: str
