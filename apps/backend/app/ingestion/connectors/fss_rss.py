import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.repositories.regulation_sources_repo import RegulationSourcesRepository
from app.services.regulation_ingestion_service import RegulationIngestionService


class FssRssConnector:
    def __init__(
        self,
        *,
        sources_repository: RegulationSourcesRepository,
        ingestion_service: RegulationIngestionService,
        fetch_full_text: bool = False,
    ) -> None:
        self._sources_repository = sources_repository
        self._ingestion_service = ingestion_service
        self._fetch_full_text = fetch_full_text

    def poll(self, source: Any) -> list[dict[str, str]]:
        if not source.url:
            return []
        response = httpx.get(source.url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items: list[dict[str, str]] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title:
                continue
            items.append({"title": title, "link": link})
            if self._fetch_full_text and link:
                detail = httpx.get(link, timeout=10)
                detail.raise_for_status()
                self._ingestion_service.ingest_payload(
                    source_id=source.id,
                    title=title,
                    version_label=None,
                    raw_bytes=detail.content,
                    content_type=detail.headers.get("content-type"),
                    filename=link,
                )
        self._sources_repository.mark_polled(source.id)
        return items
