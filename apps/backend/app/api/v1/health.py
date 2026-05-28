from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", env=settings.app_env)


@router.get("/health/cache-stats")
def cache_stats() -> dict[str, Any]:
    from app.services.analyze_service import _ANALYZE_CACHE
    from app.services.rewrite_service import _REWRITE_CACHE

    return {"analyze": _ANALYZE_CACHE.stats(), "rewrite": _REWRITE_CACHE.stats()}
