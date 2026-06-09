from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.auth import require_admin_role
from app.repositories.audit_logs_repo import (
    AuditLogsRepository,
    get_audit_logs_repository,
)
from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.regulation_versions_repo import (
    RegulationVersionsRepository,
    get_regulation_versions_repository,
)
from app.repositories.risk_results_repo import (
    RiskResultsRepository,
    get_risk_results_repository,
)
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.audit import AuditLogResponse, RecentAuditEntry, RecentAuditResponse
from app.schemas.compliance import AnalyzeRequest, AnalyzeResponse
from app.schemas.evidence import EvidenceRequest, EvidenceResponse
from app.schemas.history import RecentContentsResponse
from app.schemas.regulation import RegulationVersion
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
    refresh: bool = Query(False, description="Bypass cached analyze response."),
    service: AnalyzeService = Depends(get_analyze_service),
) -> AnalyzeResponse:
    return service.analyze(request, force_refresh=refresh)


@router.post("/evidence", response_model=EvidenceResponse)
def retrieve_compliance_evidence(
    request: EvidenceRequest,
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    return service.retrieve(request)


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_compliance_content(
    request: RewriteRequest,
    refresh: bool = Query(False, description="Bypass cached rewrite response."),
    service: RewriteService = Depends(get_rewrite_service),
) -> RewriteResponse:
    return service.rewrite(request, force_refresh=refresh)


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


@router.get("/contents/recent", response_model=RecentContentsResponse)
def list_recent_contents(
    limit: int = Query(20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
) -> RecentContentsResponse:
    return service.list_recent(limit=limit)


@router.get("/regulation-versions/{version_id}", response_model=RegulationVersion)
def get_regulation_version(
    version_id: str,
    repository: RegulationVersionsRepository = Depends(get_regulation_versions_repository),
) -> RegulationVersion:
    version = repository.get(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="regulation version not found")
    return version


@router.delete("/contents/{content_id}", status_code=204)
def delete_content(
    content_id: str,
    contents: ContentRepository = Depends(get_content_repository),
    risks: RiskResultsRepository = Depends(get_risk_results_repository),
    _: object = Depends(require_admin_role),
) -> Response:
    # Supabase: deleting the content cascades into risk_results (FK ON DELETE
    # CASCADE). approval_logs / audit_logs intentionally retain the audit trail
    # with content_id set to NULL, so they are *not* touched here.
    # Fallback memory has no FK — prune the risk_results dict explicitly.
    existed = contents.delete(content_id)
    risks.delete_by_content_id(content_id)
    if not existed:
        raise HTTPException(status_code=404, detail="content not found")
    return Response(status_code=204)


@router.delete("/contents", status_code=204)
def delete_all_contents(
    contents: ContentRepository = Depends(get_content_repository),
    risks: RiskResultsRepository = Depends(get_risk_results_repository),
    _: object = Depends(require_admin_role),
) -> Response:
    # Same policy as the single-content delete: contents bulk delete cascades
    # into risk_results on Supabase; approval_logs / audit_logs are preserved.
    # The risks.delete_all() call is for fallback-memory parity.
    contents.delete_all()
    risks.delete_all()
    return Response(status_code=204)


@router.get("/audit-log/recent", response_model=RecentAuditResponse)
def list_recent_audit_events(
    limit: int = Query(10, ge=1, le=100),
    repository: AuditLogsRepository = Depends(get_audit_logs_repository),
) -> RecentAuditResponse:
    rows = repository.list_recent(limit=limit)
    entries = [
        RecentAuditEntry(
            content_id=str(row.get("content_id") or ""),
            action=str(row.get("action") or ""),
            model_version=str(row.get("model_version")) if row.get("model_version") else None,
            created_at=str(row.get("created_at")) if row.get("created_at") else None,
        )
        for row in rows
    ]
    return RecentAuditResponse(entries=entries)
