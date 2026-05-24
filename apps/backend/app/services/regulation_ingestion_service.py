import hashlib
from datetime import date

from app.ingestion.extractors.html import extract_html_text
from app.ingestion.extractors.pdf import extract_pdf_text
from app.ingestion.normalizer import normalize_regulation_text
from app.repositories.regulation_sources_repo import (
    RegulationSourcesRepository,
    get_regulation_sources_repository,
)
from app.repositories.regulation_versions_repo import (
    RegulationVersionsRepository,
    get_regulation_versions_repository,
)
from app.schemas.regulation import IngestResult


class RegulationIngestionService:
    def __init__(
        self,
        sources_repository: RegulationSourcesRepository,
        versions_repository: RegulationVersionsRepository,
    ) -> None:
        self._sources_repository = sources_repository
        self._versions_repository = versions_repository

    def ingest_payload(
        self,
        *,
        source_id: str,
        title: str,
        version_label: str | None,
        raw_bytes: bytes,
        content_type: str | None = None,
        filename: str | None = None,
        effective_date: date | None = None,
    ) -> IngestResult:
        source = self._sources_repository.get(source_id)
        if source is None:
            raise ValueError(f"Regulation source {source_id} not found.")

        raw_text = self._extract_text(raw_bytes, content_type, filename)
        normalized = normalize_regulation_text(
            raw_text,
            product_type=source.product_type,
            default_risk_categories=source.default_risk_categories,
        )
        content_hash = hashlib.sha256(normalized.text.encode("utf-8")).hexdigest()

        existing = self._versions_repository.find_by_hash(source_id, content_hash)
        if existing is not None:
            return IngestResult(
                status="unchanged",
                source_id=source_id,
                version_id=existing.id,
                title=existing.title,
                version_label=existing.version_label,
                content_hash=existing.content_hash,
                chunk_count=existing.chunk_count,
            )

        latest = self._versions_repository.latest_for_source(source_id)
        chunks = [
            {
                "chunk_index": index,
                "chunk_text": chunk,
                "risk_categories": normalized.risk_categories,
                "product_type": normalized.product_type,
            }
            for index, chunk in enumerate(normalized.chunks)
        ]
        version = self._versions_repository.insert(
            source_id=source_id,
            title=title,
            version_label=version_label,
            effective_date=effective_date,
            content_hash=content_hash,
            raw_text=normalized.text,
            chunks=chunks,
        )
        if latest is not None:
            self._versions_repository.mark_superseded(latest.id, version.id)

        return IngestResult(
            status="updated" if latest else "created",
            source_id=source_id,
            version_id=version.id,
            title=version.title,
            version_label=version.version_label,
            content_hash=version.content_hash,
            chunk_count=version.chunk_count,
        )

    def _extract_text(
        self,
        raw_bytes: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> str:
        lowered_type = (content_type or "").lower()
        lowered_name = (filename or "").lower()
        if "pdf" in lowered_type or lowered_name.endswith(".pdf"):
            return extract_pdf_text(raw_bytes)
        if "html" in lowered_type or lowered_name.endswith((".html", ".htm")):
            return extract_html_text(raw_bytes)
        return raw_bytes.decode("utf-8", errors="ignore")


def get_regulation_ingestion_service() -> RegulationIngestionService:
    return RegulationIngestionService(
        sources_repository=get_regulation_sources_repository(),
        versions_repository=get_regulation_versions_repository(),
    )
