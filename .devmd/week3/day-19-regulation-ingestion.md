# Day 19 — Regulation Ingestion and Change Tracking

## Goal

`FALLBACK_REGULATION_DOCS` 3건짜리 더미 RAG를 **실제 규제 문서가 들어오는 ingestion 파이프라인**으로 교체한다. "AI 규제 Agent가 최신 금융규제와 내부 기준을 자동으로 추적합니다"라는 대회 명세 명제를 충족시키는 P1 작업이다.

Day 19에서 "자동 크롤링까지 모두 구현"하지 않는다. 현실적 우선순위:

1. **Admin-upload-first**: 운영자가 PDF/HTML/MD를 업로드하면 hash 기반 변경 감지·버전 관리·RAG index 갱신이 자동으로 동작한다.
2. **외부 RSS connector 1종 시범**: 금감원 보도자료 또는 금융위 RSS 중 정책상 안전한 1개를 fetch → 변경 감지까지 동작. 본문 ingestion은 placeholder 가능.
3. 스케줄러는 Render Cron 또는 CLI `python -m app.jobs.regulation_refresh` 1종으로 시작.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §8
- 기존 `apps/backend/app/repositories/regulation_docs_repo.py`
- `infra/supabase/schema.sql` (기존 `regulation_docs` 테이블)

## Files

```text
infra/supabase/migrations/2026-05-26_regulation_tracking.sql  (NEW)
apps/backend/app/schemas/regulation.py                        (NEW or MOD)
apps/backend/app/repositories/regulation_sources_repo.py      (NEW)
apps/backend/app/repositories/regulation_versions_repo.py     (NEW)
apps/backend/app/services/regulation_ingestion_service.py     (NEW)
apps/backend/app/ingestion/__init__.py                        (NEW)
apps/backend/app/ingestion/connectors/__init__.py             (NEW)
apps/backend/app/ingestion/connectors/admin_upload.py         (NEW)
apps/backend/app/ingestion/connectors/fss_rss.py              (NEW, placeholder ok)
apps/backend/app/ingestion/extractors/pdf.py                  (NEW)
apps/backend/app/ingestion/extractors/html.py                 (NEW)
apps/backend/app/ingestion/normalizer.py                      (NEW)
apps/backend/app/jobs/regulation_refresh.py                   (NEW, CLI)
apps/backend/app/api/v1/admin.py                              (NEW)
apps/backend/tests/test_regulation_ingestion.py               (NEW)
apps/backend/tests/test_regulation_versions.py                (NEW)
apps/backend/tests/test_admin_upload_endpoint.py              (NEW)
infra/supabase/seed_regulation_sources.sql                    (NEW)
```

수정:

```text
apps/backend/app/repositories/regulation_docs_repo.py  (MOD: read from new tables)
apps/backend/app/agent/tools/search_regulation.py      (MOD: cite version id)
```

## Schema additions

```sql
create table regulation_sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source_type text not null check (source_type in ('admin_upload','rss','manual_seed')),
  url text,
  product_type text,
  default_risk_categories text[] default '{}',
  last_polled_at timestamptz,
  active boolean not null default true,
  created_at timestamptz default now()
);

create table regulation_versions (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references regulation_sources(id) on delete cascade,
  title text not null,
  version_label text,                  -- e.g. "2026-05", "v3"
  effective_date date,
  content_hash text not null,
  raw_text text,                       -- normalized plain text
  chunk_count int default 0,
  superseded_by uuid references regulation_versions(id),
  ingested_at timestamptz default now(),
  unique (source_id, content_hash)
);

create table regulation_chunks (
  id bigserial primary key,
  version_id uuid not null references regulation_versions(id) on delete cascade,
  chunk_index int not null,
  chunk_text text not null,
  risk_categories text[] default '{}',
  product_type text,
  embedding vector(768),               -- Day 20에서 채움. 이날은 NULL 허용.
  created_at timestamptz default now()
);

create index on regulation_chunks (product_type);
create index on regulation_chunks using gin (risk_categories);
```

`regulation_docs` 테이블은 deprecated. `RegulationDocsRepository`는 새 `regulation_chunks + regulation_versions` join 결과를 `RegulationDoc` dataclass로 매핑한다 (기존 인터페이스 보존).

## Tasks

### Schema and migration

- [ ] 위 SQL을 `infra/supabase/migrations/2026-05-26_regulation_tracking.sql`에 작성. `vector` extension 활성화 확인 (Supabase는 기본 활성).
- [ ] 권한 grant 추가 (day-10 패턴 따름).
- [ ] `seed_regulation_sources.sql`: admin_upload 소스 1건, manual_seed 소스 1건(기존 demo 3건 마이그레이션). RSS 소스는 url placeholder.

### Repositories

- [ ] `regulation_sources_repo.py`: CRUD + `list_active()`. Supabase 미설정 시 fallback list.
- [ ] `regulation_versions_repo.py`: `insert(version, chunks)`, `find_by_hash(source_id, hash)`, `latest_for_source(source_id)`, `mark_superseded`.

### Ingestion pipeline

- [ ] `extractors/pdf.py`: `pypdf` 또는 `pdfminer.six` 사용. raw text 추출. 표/이미지는 무시. requirements.txt에 추가.
- [ ] `extractors/html.py`: `beautifulsoup4` 또는 표준 라이브러리만으로 텍스트 추출. requirements.txt에 추가.
- [ ] `normalizer.py`: 공백/제목/번호 정규화, chunk_text(600자) 적용, 카테고리/제품 추론(간단 키워드 매핑 + LLM은 후일).
- [ ] `regulation_ingestion_service.py`:
  - `ingest_payload(source_id, title, version_label, raw_bytes, content_type) -> IngestResult`.
  - 흐름: extract → normalize → hash 계산 → 기존 version과 hash 비교 → 신규/동일/변경 판정 → 신규/변경 시 `regulation_versions` insert + `regulation_chunks` bulk insert + 이전 version `superseded_by` 갱신.
  - 임베딩은 Day 20에서 추가. 이날은 `embedding` NULL.
- [ ] `connectors/admin_upload.py`: API에서 받은 파일을 `ingest_payload`에 위임.
- [ ] `connectors/fss_rss.py`: `httpx.get(rss_url)` → 항목별 link → HTML fetch → ingest. **저작권/이용약관 이슈로 본문 fetch를 비활성화하고, 메타데이터만 저장하는 모드도 지원** (`fetch_full_text: bool` 옵션).

### CLI job

- [ ] `app/jobs/regulation_refresh.py`: `python -m app.jobs.regulation_refresh --source <id|all>`. 활성 connector를 순회하며 `connector.poll()` 호출. 로그를 stdout에 남기고 exit code로 성공/실패 표시.
- [ ] Render Cron 등록 가이드는 `docs/deployment/`에 추가 (Day 22).

### Admin API

- [ ] `api/v1/admin.py`:
  - `POST /v1/admin/regulations/ingest` (multipart): `source_id`, `title`, `version_label`, `file`.
  - `GET /v1/admin/regulations/sources` / `GET /sources/{id}/versions`.
  - 인증: 일단 env `ADMIN_API_TOKEN` 헤더 검증 (간단). 비어 있으면 403.
- [ ] `main.py` router 등록.

### Repository switch

- [ ] `regulation_docs_repo.py`의 `_supabase_search`를 `regulation_chunks + regulation_versions` 기반 쿼리로 교체. Day 20에서 벡터 검색이 추가될 자리만 유지.
- [ ] 결과 dataclass `RegulationDoc`에 `version_id`, `effective_date` 추가.
- [ ] `search_regulation` tool 결과에 `version_id`, `version_label`을 함께 노출 → agent가 cite 가능.

### Tests

- [ ] `test_regulation_ingestion.py`: fixture PDF/HTML → extract → normalize → chunks 생성 → hash 안정성.
- [ ] `test_regulation_versions.py`: 같은 hash 재인서트 시 idempotent, 다른 hash insert 시 이전 버전 `superseded_by` 갱신.
- [ ] `test_admin_upload_endpoint.py`: 인증 헤더 없음 → 403, 유효 토큰 + 파일 → 200 + version_id 반환. fake supabase로 검증.

## Done When

- admin API로 PDF 1개를 업로드하면 `regulation_versions`와 `regulation_chunks`가 채워진다.
- 같은 파일을 다시 업로드하면 신규 row가 생기지 않는다 (hash 기반).
- 같은 source에 새 파일을 업로드하면 이전 version이 `superseded_by`로 표시된다.
- `regulation_refresh.py` CLI가 활성 source를 순회해 변경을 감지한다 (RSS는 placeholder도 허용).
- `search_regulation` tool 결과에 `version_id`가 포함되고, agent가 trace에서 이를 인용한다.
- `pytest`, `ruff` 통과.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q tests/test_regulation_*.py tests/test_admin_upload_endpoint.py

# 수동 ingestion
curl -X POST http://localhost:8000/v1/admin/regulations/ingest \
  -H "X-Admin-Token: $ADMIN_API_TOKEN" \
  -F "source_id=<seed_uuid>" \
  -F "title=금융상품 광고 심사 가이드라인" \
  -F "version_label=2026-05" \
  -F "file=@./tests/fixtures/sample-regulation.pdf"

# CLI refresh
.venv/bin/python -m app.jobs.regulation_refresh --source all
```

## Risks / Notes

- 외부 RSS 본문 fetch는 저작권/약관 위반 위험이 있으므로 기본 OFF. 본문 ingestion이 필요하면 운영자 admin upload로 우회한다. 이 점을 `docs/handover/`에 명시.
- PDF 추출 품질이 RAG 정확도를 좌우한다. table/footer 노이즈 제거는 normalizer에서 단순 휴리스틱으로 시작.
- `regulation_chunks.embedding`은 Day 19 종료 시점에 NULL 허용. Day 20 마이그레이션이 backfill을 담당.
- 기존 `seed_regulation_docs.sql` 데이터는 manual_seed 소스로 이관. legacy `regulation_docs` 테이블은 즉시 drop하지 않고 Week 4에서 drop.

## Completion Log

- Status: DONE (2026-05-24)
- Implemented files:
  - `infra/supabase/migrations/2026-05-26_regulation_tracking.sql`
  - `infra/supabase/seed_regulation_sources.sql`
  - `apps/backend/app/schemas/regulation.py`
  - `apps/backend/app/repositories/regulation_sources_repo.py`
  - `apps/backend/app/repositories/regulation_versions_repo.py`
  - `apps/backend/app/services/regulation_ingestion_service.py`
  - `apps/backend/app/ingestion/**`
  - `apps/backend/app/jobs/regulation_refresh.py`
  - `apps/backend/app/api/v1/admin.py`
  - `apps/backend/tests/test_regulation_ingestion.py`
  - `apps/backend/tests/test_regulation_versions.py`
  - `apps/backend/tests/test_admin_upload_endpoint.py`
- Test commands executed:
  - `ruff check app tests`
  - `docker run --rm --add-host=host.docker.internal:host-gateway -e OPENAI_BASE_URL=http://host.docker.internal:18080/v1 ... "ruff check app tests && pytest"`
- Test result summary: Docker backend validation passed: 104 passed, 1 warning. Local LLM integration smoke executed and passed.
- Known issues:
  - RSS connector defaults to metadata-only behavior unless `--fetch-full-text` is explicitly set, to avoid copyright/terms risk.
  - PDF extraction ignores tables/images. Day 20 embedding/backfill still owns `regulation_chunks.embedding`.
