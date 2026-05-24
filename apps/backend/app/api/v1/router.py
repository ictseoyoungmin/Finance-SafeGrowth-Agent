from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.admin import router as admin_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(compliance_router, prefix="/compliance")
router.include_router(agent_router, prefix="/agent")
router.include_router(admin_router, prefix="/admin")
