from fastapi import APIRouter, Depends

from app.schemas.compliance import AnalyzeRequest, AnalyzeResponse
from app.schemas.evidence import EvidenceRequest, EvidenceResponse
from app.schemas.rewrite import RewriteRequest, RewriteResponse
from app.services.analyze_service import AnalyzeService, get_analyze_service
from app.services.evidence_service import EvidenceService, get_evidence_service
from app.services.rewrite_service import RewriteService, get_rewrite_service

router = APIRouter(tags=["compliance"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_compliance_content(
    request: AnalyzeRequest,
    service: AnalyzeService = Depends(get_analyze_service),
) -> AnalyzeResponse:
    return service.analyze(request)


@router.post("/evidence", response_model=EvidenceResponse)
def retrieve_compliance_evidence(
    request: EvidenceRequest,
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    return service.retrieve(request)


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_compliance_content(
    request: RewriteRequest,
    service: RewriteService = Depends(get_rewrite_service),
) -> RewriteResponse:
    return service.rewrite(request)
