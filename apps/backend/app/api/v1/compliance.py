from fastapi import APIRouter, Depends, Query

from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.compliance import AnalyzeRequest, AnalyzeResponse
from app.schemas.evidence import EvidenceRequest, EvidenceResponse
from app.schemas.report import ReportResponse
from app.schemas.rewrite import RewriteRequest, RewriteResponse
from app.services.approval_service import ApprovalService, get_approval_service
from app.services.analyze_service import AnalyzeService, get_analyze_service
from app.services.audit_service import AuditService, get_audit_service
from app.services.evidence_service import EvidenceService, get_evidence_service
from app.services.report_service import ReportService, get_report_service
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


@router.post("/approve", response_model=ApprovalResponse)
def approve_compliance_content(
    request: ApprovalRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResponse:
    return service.approve(request)


@router.get("/audit-log", response_model=AuditLogResponse)
def get_audit_log(
    content_id: str = Query(..., min_length=1),
    service: AuditService = Depends(get_audit_service),
) -> AuditLogResponse:
    entries = service.list_by_content_id(content_id)
    return AuditLogResponse(content_id=content_id, entries=entries)


@router.get("/report", response_model=ReportResponse)
def get_report(
    content_id: str = Query(..., min_length=1),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    return service.build(content_id)
