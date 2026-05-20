from uuid import UUID

from app.integrations.supabase_client import SupabaseClient, SupabaseConfig, is_real_value
from app.repositories.audit_logs_repo import FALLBACK_AUDIT_LOGS, AuditLogsRepository
from app.repositories.contents_repo import FALLBACK_CONTENTS, ContentRepository
from app.repositories.risk_results_repo import FALLBACK_RISK_RESULTS, RiskResultsRepository
from app.schemas.compliance import AnalyzeRequest, FlaggedSpan, RiskLevel
from app.services.audit_service import AuditService


class FakeSupabaseClient:
    is_configured = True

    def __init__(self) -> None:
        self.inserts: list[tuple[str, dict]] = []

    def insert(self, table: str, payload: dict) -> dict:
        self.inserts.append((table, payload))
        if table == "contents":
            return {"id": "22222222-2222-4222-8222-222222222222", **payload}
        return {"id": "33333333-3333-4333-8333-333333333333", **payload}


def test_placeholder_supabase_values_are_not_configured() -> None:
    client = SupabaseClient(
        SupabaseConfig(
            url="https://replace-me.supabase.co",
            anon_key="replace-me",
            service_role_key="replace-me",
        )
    )

    assert client.is_configured is False
    assert is_real_value("replace-me") is False
    assert is_real_value("") is False
    assert is_real_value("https://real-project.supabase.co") is True


def test_content_repository_fallback_returns_uuid_and_stores_content() -> None:
    FALLBACK_CONTENTS.clear()
    repository = ContentRepository(SupabaseClient(SupabaseConfig(None, None, None)))
    request = AnalyzeRequest(
        product_type="투자상품",
        channel="앱 푸시",
        target_customer="30대 직장인",
        language="ko",
        original_text="테스트 문구",
    )

    content_id = repository.save_original(request)

    assert UUID(content_id)
    assert FALLBACK_CONTENTS[content_id]["original_text"] == "테스트 문구"
    assert repository.get(content_id) == FALLBACK_CONTENTS[content_id]


def test_risk_results_and_audit_fallback_store_records() -> None:
    FALLBACK_RISK_RESULTS.clear()
    FALLBACK_AUDIT_LOGS.clear()
    supabase_client = SupabaseClient(SupabaseConfig(None, None, None))
    risk_repository = RiskResultsRepository(supabase_client)
    audit_repository = AuditLogsRepository(supabase_client)
    audit_service = AuditService(audit_repository)
    content_id = "11111111-1111-4111-8111-111111111111"
    flagged_spans = [
        FlaggedSpan(
            span_text="연 8% 수익",
            start=0,
            end=7,
            risk_category="확정 수익 오인",
            severity=RiskLevel.HIGH,
            reason="확정 수익처럼 해석될 수 있습니다.",
            confidence=0.95,
        )
    ]

    risk_repository.save_analysis(
        content_id=content_id,
        risk_level=RiskLevel.HIGH,
        flagged_spans=flagged_spans,
        risk_categories=["확정 수익 오인"],
        reviewer_notes="수익률 표현 완화 필요",
    )
    audit_service.record_analysis(content_id)

    latest = risk_repository.get_latest_by_content_id(content_id)
    assert latest is not None
    assert latest["risk_level"] == "HIGH"
    assert latest["flagged_spans"][0]["span_text"] == "연 8% 수익"
    assert latest["risk_categories"] == ["확정 수익 오인"]
    assert latest["reviewer_notes"] == "수익률 표현 완화 필요"

    audit_entries = audit_repository.list_by_content_id(content_id)
    assert len(audit_entries) == 1
    assert audit_entries[0]["action"] == "analyze"
    assert audit_entries[0]["model_version"] == "rule-engine-v1"
    assert audit_entries[0]["doc_version"] == "local-rules-v1"


def test_configured_repositories_insert_into_supabase_tables() -> None:
    fake_client = FakeSupabaseClient()
    content_repository = ContentRepository(fake_client)  # type: ignore[arg-type]
    risk_repository = RiskResultsRepository(fake_client)  # type: ignore[arg-type]
    audit_repository = AuditLogsRepository(fake_client)  # type: ignore[arg-type]
    audit_service = AuditService(audit_repository)
    request = AnalyzeRequest(
        product_type="투자상품",
        channel="앱 푸시",
        target_customer="30대 직장인",
        language="ko",
        original_text="지금 가입하면 누구나 연 8% 수익을 받을 수 있습니다.",
    )
    flagged_spans = [
        FlaggedSpan(
            span_text="누구나",
            start=6,
            end=9,
            risk_category="과장 표현",
            severity=RiskLevel.HIGH,
            reason="보편적 수혜처럼 해석될 수 있습니다.",
            confidence=0.92,
        )
    ]

    content_id = content_repository.save_original(request)
    risk_repository.save_analysis(
        content_id=content_id,
        risk_level=RiskLevel.HIGH,
        flagged_spans=flagged_spans,
        risk_categories=["과장 표현"],
        reviewer_notes="표현 완화 필요",
    )
    audit_service.record_analysis(content_id)

    assert content_id == "22222222-2222-4222-8222-222222222222"
    inserted_tables = [table for table, _payload in fake_client.inserts]
    assert inserted_tables == ["contents", "risk_results", "audit_logs"]
    assert fake_client.inserts[1][1]["flagged_spans"][0]["span_text"] == "누구나"
    assert fake_client.inserts[2][1]["action"] == "analyze"
