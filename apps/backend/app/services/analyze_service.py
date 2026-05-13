from app.repositories.contents_repo import ContentRepository, get_content_repository
from app.repositories.risk_results_repo import (
    RiskResultsRepository,
    get_risk_results_repository,
)
from app.rules.rule_engine import RuleEngine
from app.schemas.compliance import AnalyzeRequest, AnalyzeResponse, FlaggedSpan, RiskLevel
from app.services.audit_service import AuditService, get_audit_service


SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
}


class AnalyzeService:
    def __init__(
        self,
        rule_engine: RuleEngine,
        content_repository: ContentRepository,
        risk_results_repository: RiskResultsRepository,
        audit_service: AuditService,
    ) -> None:
        self._rule_engine = rule_engine
        self._content_repository = content_repository
        self._risk_results_repository = risk_results_repository
        self._audit_service = audit_service

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        content_id = self._content_repository.save_original(request)
        flagged_spans = self._rule_engine.scan(request.original_text)
        risk_level = self._risk_level(flagged_spans)
        risk_categories = self._risk_categories(flagged_spans)

        self._risk_results_repository.save_analysis(
            content_id=content_id,
            risk_level=risk_level,
            flagged_spans=flagged_spans,
        )
        self._audit_service.record_analysis(content_id)

        return AnalyzeResponse(
            content_id=content_id,
            risk_level=risk_level,
            flagged_spans=flagged_spans,
            risk_categories=risk_categories,
            reviewer_notes=self._reviewer_notes(request, flagged_spans),
        )

    def _risk_level(self, flagged_spans: list[FlaggedSpan]) -> RiskLevel:
        if not flagged_spans:
            return RiskLevel.LOW

        return max(flagged_spans, key=lambda hit: SEVERITY_ORDER[hit.severity]).severity

    def _risk_categories(self, flagged_spans: list[FlaggedSpan]) -> list[str]:
        categories: list[str] = []
        for hit in flagged_spans:
            if hit.risk_category not in categories:
                categories.append(hit.risk_category)
        return categories

    def _reviewer_notes(
        self,
        request: AnalyzeRequest,
        flagged_spans: list[FlaggedSpan],
    ) -> str:
        if not flagged_spans:
            return "현재 규칙 기반 검토에서 명확한 고위험 표현은 발견되지 않았습니다."

        categories = ", ".join(self._risk_categories(flagged_spans))
        return (
            f"{request.product_type} {request.channel} 문구에서 {categories} 관련 표현이 "
            "탐지되었습니다. 배포 전 표현 완화와 필수 유의사항 고지가 필요합니다."
        )


def get_analyze_service() -> AnalyzeService:
    return AnalyzeService(
        rule_engine=RuleEngine(),
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        audit_service=get_audit_service(),
    )
