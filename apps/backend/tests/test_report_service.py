"""Tests for ReportService.

R-B-1a: ReportService now reconstructs evidence and changes when building the
approval package, instead of returning empty lists.
"""

from app.rag.retriever import RegulationRetriever
from app.repositories.regulation_docs_repo import RegulationDoc
from app.services.report_service import ReportService


class StubContentRepository:
    def __init__(self, payload: dict | None) -> None:
        self.payload = payload

    def get(self, content_id: str) -> dict | None:
        return self.payload


class StubRiskResultsRepository:
    def __init__(self, payload: dict | None) -> None:
        self.payload = payload

    def get_latest_by_content_id(self, content_id: str) -> dict | None:
        return self.payload


class StubApprovalLogsRepository:
    def __init__(self, payload: dict | None) -> None:
        self.payload = payload

    def get_latest_by_content_id(self, content_id: str) -> dict | None:
        return self.payload


class StubAuditLogsRepository:
    def list_by_content_id(self, content_id: str) -> list[dict]:
        return []


class StubRetriever(RegulationRetriever):
    """Returns one canned doc so we can verify evidence is reconstructed."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def retrieve(self, **kwargs) -> list[RegulationDoc]:
        self.calls.append(kwargs)
        return [
            RegulationDoc(
                evidence_id="doc-1",
                title="투자성 상품 광고 심사 가이드라인",
                version="v1",
                product_type="투자상품",
                risk_categories=("확정 수익 오인",),
                snippet="투자성 상품 광고는 수익률을 확정적으로 표현해서는 안 됩니다.",
                guideline_snippet="수익률 확정 표현 금지",
                similarity=0.9,
                version_id="ver-1",
            )
        ]


def _build(
    *,
    content: dict | None,
    risk: dict | None,
    approval: dict | None = None,
) -> tuple[ReportService, StubRetriever]:
    retriever = StubRetriever()
    service = ReportService(
        content_repository=StubContentRepository(content),  # type: ignore[arg-type]
        risk_results_repository=StubRiskResultsRepository(risk),  # type: ignore[arg-type]
        approval_logs_repository=StubApprovalLogsRepository(approval),  # type: ignore[arg-type]
        audit_logs_repository=StubAuditLogsRepository(),  # type: ignore[arg-type]
        retriever=retriever,
    )
    return service, retriever


def test_report_includes_reconstructed_evidence_from_retriever() -> None:
    content = {
        "id": "c-1",
        "product_type": "투자상품",
        "original_text": "연 5.0% 수익을 안정적으로 받아보세요.",
    }
    risk = {
        "risk_level": "HIGH",
        "risk_categories": ["확정 수익 오인"],
        "flagged_spans": [],
    }
    service, retriever = _build(content=content, risk=risk)

    report = service.build("c-1")

    assert len(report.evidence) == 1
    assert report.evidence[0]["title"].startswith("투자성 상품")
    # retriever was called with the content's original_text as the vector query
    assert retriever.calls and retriever.calls[0].get("query") == content["original_text"]


def test_report_reconstructs_changes_from_resolved_spans() -> None:
    """spans flagged in original_text but not present in the approved revision
    should show up as resolved changes in the report."""
    content = {
        "id": "c-1",
        "product_type": "투자상품",
        "original_text": "연 5.0% 수익을 안정적으로 받아보세요. 누구나 가입 가능.",
    }
    risk = {
        "risk_level": "HIGH",
        "risk_categories": ["확정 수익 오인", "과장 표현"],
        "flagged_spans": [
            {"span_text": "연 5.0% 수익", "risk_category": "확정 수익 오인", "severity": "HIGH"},
            {"span_text": "누구나", "risk_category": "과장 표현", "severity": "HIGH"},
            {"span_text": "안정적으로", "risk_category": "안정성 오인", "severity": "MEDIUM"},
        ],
    }
    approval = {
        "decision": "approved",
        "selected_revision": (
            "수익률은 시장 상황에 따라 변동될 수 있으며 자산은 안정적으로 운용됩니다. "
            "가입 자격은 상품설명서를 확인하세요."
        ),
    }
    service, _ = _build(content=content, risk=risk, approval=approval)

    report = service.build("c-1")

    resolved_originals = {change["original"] for change in report.changes}
    # spans removed in the approved revision are surfaced
    assert "연 5.0% 수익" in resolved_originals
    assert "누구나" in resolved_originals
    # span still present in revision is NOT flagged as a change
    assert "안정적으로" not in resolved_originals


def test_report_empty_changes_when_no_approval_revision() -> None:
    """Without an approval revision, final_text == original_text → no diff."""
    content = {"id": "c-1", "product_type": "투자상품", "original_text": "원금 걱정 없이"}
    risk = {
        "risk_level": "HIGH",
        "risk_categories": ["원금 보장 오인"],
        "flagged_spans": [{"span_text": "원금 걱정 없이", "risk_category": "원금 보장 오인"}],
    }
    service, _ = _build(content=content, risk=risk, approval=None)

    report = service.build("c-1")

    assert report.changes == []
