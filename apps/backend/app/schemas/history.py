from pydantic import BaseModel


class RecentContentItem(BaseModel):
    id: str
    created_at: str | None = None
    product_type: str
    channel: str
    target_customer: str
    language: str
    original_text_preview: str
    risk_level: str | None = None
    decision: str | None = None
    reviewer: str | None = None


class RecentContentsResponse(BaseModel):
    items: list[RecentContentItem]
