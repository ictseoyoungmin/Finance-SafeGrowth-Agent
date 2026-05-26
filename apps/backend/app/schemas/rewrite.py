from typing import Literal

from pydantic import BaseModel, Field


class RewriteRequest(BaseModel):
    content_id: str = Field(..., min_length=1)
    mode: str = "marketing_balanced"


class RewriteChange(BaseModel):
    original: str
    replacement: str
    reason: str


class RewriteAttempt(BaseModel):
    model: str
    status: str
    error_code: int | None = None
    detail: str | None = None


class RewriteResponse(BaseModel):
    content_id: str
    revised_text_conservative: str
    revised_text_marketing: str
    changes: list[RewriteChange]
    source: Literal["llm", "gemini", "fallback"] = "fallback"
    model_version: str | None = None
    attempts: list[RewriteAttempt] = Field(default_factory=list)
