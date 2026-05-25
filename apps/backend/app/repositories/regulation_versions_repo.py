from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from app.integrations.supabase_client import SupabaseClient, get_supabase_client
from app.schemas.regulation import RegulationVersion


FALLBACK_REGULATION_VERSIONS: dict[str, dict[str, Any]] = {}
FALLBACK_REGULATION_CHUNKS: list[dict[str, Any]] = []
_NEXT_CHUNK_ID = 1


_DEMO_RAW_TEXTS: dict[str, str] = {
    "ver-demo-001": (
        "제3조(허위·과장 광고 금지)\n"
        "금융상품 광고를 함에 있어서는 다음 각 호에 해당하는 표현을 사용해서는 안 된다.\n"
        "1. 수익률을 확정적으로 안내하는 표현\n"
        "2. 원금 손실 가능성이 없는 것으로 오인할 수 있는 표현\n"
        "3. 보편적 혜택, 전 고객 적용 등 무조건적 보장으로 해석될 수 있는 표현\n\n"
        "제4조(필수 고지 사항)\n"
        "투자성 상품 광고에는 손실 가능성, 예금자보호 비대상 여부, 운용 책임 등을 함께 안내하여야 한다.\n\n"
        "제5조(심사 절차)\n"
        "준법감시팀의 사전 검토를 거치지 않은 광고 문구는 외부에 게시하거나 발송할 수 없다.\n"
    ),
    "ver-demo-002": (
        "제2조(원금 보장 오인 표현)\n"
        "원금 손실 가능성이 있는 금융상품에 대하여는 \"원금 보장\", \"안전하게\", \"걱정 없이\" 등 손실 가능성을 부인하는 표현을 사용하여서는 안 된다.\n\n"
        "제3조(권유 시 설명 의무)\n"
        "고객에게 상품을 권유하는 경우 손실 발생 가능성, 환매 제한, 수수료 체계를 사전에 충분히 설명하여야 한다.\n\n"
        "제4조(피해구제)\n"
        "위반 광고로 인한 소비자 피해 발생 시 회사는 즉시 광고를 중지하고 피해 구제 절차를 안내하여야 한다.\n"
    ),
    "ver-demo-003": (
        "제1장 총칙\n"
        "본 규정은 회사 내부의 모든 대외 마케팅 커뮤니케이션이 법령·가이드라인을 준수하도록 사전 검토 절차를 규정함을 목적으로 한다.\n\n"
        "제2장 사전 검토\n"
        "1. 모든 광고 문안은 배포 전 준법감시팀의 검토를 거쳐야 한다.\n"
        "2. 보편적 혜택, 확정적 결과, 심의 누락으로 오인될 수 있는 표현은 사전 점검 대상이다.\n"
        "3. 사후 발견 시 즉시 광고를 중단하고 시정 조치를 이행한다.\n"
    ),
}


def _seed_demo_versions() -> None:
    """Populate fallback regulation versions for demo / DB instance modal."""
    demo_versions = [
        {
            "id": "ver-demo-001",
            "source_id": "src-internal-guidelines",
            "title": "금융상품 광고 심사 가이드라인",
            "version_label": "demo-v1",
            "effective_date": "2026-01-15",
            "content_hash": "sha256:demo-001-1f4b9c2e7d8a06f5c3b2e1a8d9f6c4e2a7b5d3f1",
            "raw_text": _DEMO_RAW_TEXTS["ver-demo-001"],
            "chunk_count": 8,
            "superseded_by": None,
            "ingested_at": "2026-01-15T09:00:00+00:00",
        },
        {
            "id": "ver-demo-002",
            "source_id": "src-consumer-protection",
            "title": "금융소비자 보호 가이드라인",
            "version_label": "demo-v1",
            "effective_date": "2025-11-01",
            "content_hash": "sha256:demo-002-9b8a72d4e6f0c1d2b3a4e5d6c7f8901a2b3c4d5e",
            "raw_text": _DEMO_RAW_TEXTS["ver-demo-002"],
            "chunk_count": 6,
            "superseded_by": None,
            "ingested_at": "2025-11-01T09:00:00+00:00",
        },
        {
            "id": "ver-demo-003",
            "source_id": "src-internal-control",
            "title": "내부 통제 규정",
            "version_label": "demo-v1",
            "effective_date": "2025-08-20",
            "content_hash": "sha256:demo-003-3e5d7c8b1a92f4e6c5b8a7d9e0f2c4b6a8d0e2f4",
            "raw_text": _DEMO_RAW_TEXTS["ver-demo-003"],
            "chunk_count": 5,
            "superseded_by": None,
            "ingested_at": "2025-08-20T09:00:00+00:00",
        },
    ]
    for version in demo_versions:
        FALLBACK_REGULATION_VERSIONS.setdefault(version["id"], version)


_seed_demo_versions()


class RegulationVersionsRepository:
    def __init__(self, supabase_client: SupabaseClient) -> None:
        self._supabase_client = supabase_client

    def find_by_hash(self, source_id: str, content_hash: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one(
                "regulation_versions",
                {"source_id": source_id, "content_hash": content_hash},
            )
            return RegulationVersion.model_validate(row) if row else None
        for row in FALLBACK_REGULATION_VERSIONS.values():
            if row["source_id"] == source_id and row["content_hash"] == content_hash:
                return RegulationVersion.model_validate(row)
        return None

    def latest_for_source(self, source_id: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one(
                "regulation_versions",
                {"source_id": source_id},
                order="ingested_at.desc",
            )
            return RegulationVersion.model_validate(row) if row else None

        rows = [
            row
            for row in FALLBACK_REGULATION_VERSIONS.values()
            if row["source_id"] == source_id and row.get("superseded_by") is None
        ]
        rows.sort(key=lambda row: str(row.get("ingested_at") or ""), reverse=True)
        return RegulationVersion.model_validate(rows[0]) if rows else None

    def get(self, version_id: str) -> RegulationVersion | None:
        if self._supabase_client.is_configured:
            row = self._supabase_client.select_one("regulation_versions", {"id": version_id})
            return RegulationVersion.model_validate(row) if row else None
        row = FALLBACK_REGULATION_VERSIONS.get(version_id)
        return RegulationVersion.model_validate(row) if row else None

    def list_by_source(self, source_id: str, limit: int = 20) -> list[RegulationVersion]:
        if self._supabase_client.is_configured:
            rows = self._supabase_client.select_many(
                "regulation_versions",
                {"source_id": source_id},
                order="ingested_at.desc",
                limit=limit,
            )
            return [RegulationVersion.model_validate(row) for row in rows]

        rows = [row for row in FALLBACK_REGULATION_VERSIONS.values() if row["source_id"] == source_id]
        rows.sort(key=lambda row: str(row.get("ingested_at") or ""), reverse=True)
        return [RegulationVersion.model_validate(row) for row in rows[:limit]]

    def insert(
        self,
        *,
        source_id: str,
        title: str,
        version_label: str | None,
        effective_date: date | None,
        content_hash: str,
        raw_text: str,
        chunks: list[dict[str, Any]],
    ) -> RegulationVersion:
        payload = {
            "source_id": source_id,
            "title": title,
            "version_label": version_label,
            "effective_date": effective_date.isoformat() if effective_date else None,
            "content_hash": content_hash,
            "raw_text": raw_text,
            "chunk_count": len(chunks),
        }
        if self._supabase_client.is_configured:
            row = self._supabase_client.insert("regulation_versions", payload)
            version_id = str(row["id"])
            for chunk in chunks:
                self._supabase_client.insert("regulation_chunks", {**chunk, "version_id": version_id})
            return RegulationVersion.model_validate(row)

        global _NEXT_CHUNK_ID
        version_id = str(uuid4())
        row = {
            "id": version_id,
            **payload,
            "superseded_by": None,
            "ingested_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        FALLBACK_REGULATION_VERSIONS[version_id] = row
        for chunk in chunks:
            FALLBACK_REGULATION_CHUNKS.append(
                {
                    "id": _NEXT_CHUNK_ID,
                    "version_id": version_id,
                    **chunk,
                }
            )
            _NEXT_CHUNK_ID += 1
        return RegulationVersion.model_validate(row)

    def mark_superseded(self, version_id: str, superseded_by: str) -> None:
        if self._supabase_client.is_configured:
            self._supabase_client.patch(
                "regulation_versions",
                {"id": version_id},
                {"superseded_by": superseded_by},
            )
            return
        if version_id in FALLBACK_REGULATION_VERSIONS:
            FALLBACK_REGULATION_VERSIONS[version_id]["superseded_by"] = superseded_by


def get_regulation_versions_repository() -> RegulationVersionsRepository:
    return RegulationVersionsRepository(get_supabase_client())
