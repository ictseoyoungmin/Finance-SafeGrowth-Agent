from pydantic import BaseModel, Field


class EvidenceRequest(BaseModel):
    content_id: str = Field(..., min_length=1)
    risk_categories: list[str] = Field(default_factory=list)
    product_type: str = Field(..., min_length=1)


class EvidenceItem(BaseModel):
    evidence_id: str
    title: str
    version: str
    snippet: str
    similarity: float = Field(..., ge=0, le=1)
    version_id: str | None = None
    effective_date: str | None = None
    risk_categories: list[str] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    content_id: str
    evidence_list: list[EvidenceItem]
    guideline_snippets: list[str]
