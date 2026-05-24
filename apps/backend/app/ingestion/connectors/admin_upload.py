from app.services.regulation_ingestion_service import RegulationIngestionService


class AdminUploadConnector:
    def __init__(self, service: RegulationIngestionService) -> None:
        self._service = service

    def ingest(
        self,
        *,
        source_id: str,
        title: str,
        version_label: str | None,
        raw_bytes: bytes,
        content_type: str | None,
        filename: str | None,
    ):
        return self._service.ingest_payload(
            source_id=source_id,
            title=title,
            version_label=version_label,
            raw_bytes=raw_bytes,
            content_type=content_type,
            filename=filename,
        )
