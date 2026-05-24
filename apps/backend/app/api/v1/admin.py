from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from app.core.config import settings
from app.integrations.supabase_client import is_real_value
from app.repositories.regulation_sources_repo import (
    RegulationSourcesRepository,
    get_regulation_sources_repository,
)
from app.repositories.regulation_versions_repo import (
    RegulationVersionsRepository,
    get_regulation_versions_repository,
)
from app.schemas.regulation import IngestResult, RegulationSource, RegulationVersion
from app.services.regulation_ingestion_service import (
    RegulationIngestionService,
    get_regulation_ingestion_service,
)


router = APIRouter(tags=["admin"])


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if not is_real_value(settings.admin_api_token) or x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=403, detail="Admin token is required.")


@router.get("/regulations/sources", response_model=list[RegulationSource])
def list_regulation_sources(
    _: None = Depends(require_admin_token),
    repository: RegulationSourcesRepository = Depends(get_regulation_sources_repository),
) -> list[RegulationSource]:
    return repository.list_all()


@router.get("/regulations/sources/{source_id}/versions", response_model=list[RegulationVersion])
def list_regulation_versions(
    source_id: str,
    _: None = Depends(require_admin_token),
    repository: RegulationVersionsRepository = Depends(get_regulation_versions_repository),
) -> list[RegulationVersion]:
    return repository.list_by_source(source_id)


@router.post("/regulations/ingest", response_model=IngestResult)
async def ingest_regulation(
    source_id: str = Form(...),
    title: str = Form(...),
    version_label: str | None = Form(default=None),
    file: UploadFile = File(...),
    _: None = Depends(require_admin_token),
    service: RegulationIngestionService = Depends(get_regulation_ingestion_service),
) -> IngestResult:
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        return service.ingest_payload(
            source_id=source_id,
            title=title,
            version_label=version_label,
            raw_bytes=raw_bytes,
            content_type=file.content_type,
            filename=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
