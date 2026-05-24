from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


RegulationSourceType = Literal["admin_upload", "rss", "manual_seed"]
IngestStatus = Literal["created", "unchanged", "updated"]


class RegulationSource(BaseModel):
    id: str
    name: str
    source_type: RegulationSourceType
    url: str | None = None
    product_type: str | None = None
    default_risk_categories: list[str] = Field(default_factory=list)
    last_polled_at: datetime | None = None
    active: bool = True


class RegulationVersion(BaseModel):
    id: str
    source_id: str
    title: str
    version_label: str | None = None
    effective_date: date | None = None
    content_hash: str
    raw_text: str | None = None
    chunk_count: int = 0
    superseded_by: str | None = None
    ingested_at: datetime | None = None


class RegulationChunk(BaseModel):
    id: int | None = None
    version_id: str
    chunk_index: int
    chunk_text: str
    risk_categories: list[str] = Field(default_factory=list)
    product_type: str | None = None


class IngestResult(BaseModel):
    status: IngestStatus
    source_id: str
    version_id: str
    title: str
    version_label: str | None = None
    content_hash: str
    chunk_count: int
