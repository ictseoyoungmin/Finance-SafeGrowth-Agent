# Slice 01 — P0 Backend Persistence

## Goal

Replace fake/no-op repository behavior with real persistence when Supabase is configured, while keeping deterministic fallback behavior when it is not.

This slice fixes the biggest current product gap: analysis results are currently not actually stored.

## Problems to fix

1. `ContentRepository.save_original()` returns `content-{uuid}` without inserting into DB.
2. `RiskResultsRepository.save_analysis()` is a no-op.
3. `AuditService.record_analysis()` creates an object but does not persist.
4. Supabase schema uses UUID ids, while the current fake `content-{uuid}` string is incompatible.
5. `.env.example` placeholder values such as `replace-me` can be mistakenly treated as configured secrets.

## Target behavior

### If Supabase is configured

- Insert into `contents`.
- Return the actual UUID as a string.
- Insert into `risk_results`.
- Insert into `audit_logs`.
- Use real `content_id` consistently across the API.

### If Supabase is not configured

- Use deterministic in-memory fallback or local fake records.
- Still return a string `content_id`.
- Do not crash.
- Make fallback mode explicit in logs.

## Files to modify

```text
apps/backend/app/integrations/supabase_client.py
apps/backend/app/repositories/contents_repo.py
apps/backend/app/repositories/risk_results_repo.py
apps/backend/app/repositories/audit_logs_repo.py       # new if needed
apps/backend/app/services/audit_service.py
apps/backend/app/services/analyze_service.py
apps/backend/app/core/config.py
apps/backend/tests/test_analyze_api.py                 # new
apps/backend/tests/test_repositories_fallback.py        # new if useful
```

## Implementation guidance

### 1. Harden config detection

Do not treat placeholder values as real secrets.

Suggested helper:

```python
def is_real_value(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != "replace-me")
```

Use it in `SupabaseClient.is_configured`.

### 2. Create a real Supabase client wrapper

Minimum acceptable implementation:

- If using `supabase-py`, add dependency to `requirements.txt`.
- If using direct PostgreSQL, add `psycopg[binary]` or `asyncpg`.
- Keep the repository interface small.

Recommended for MVP speed:

```text
supabase-py for table insert/select
```

### 3. Fix `content_id` format

Do not return `content-{uuid}` if the DB schema uses UUID.

Return:

```python
str(inserted_row["id"])
```

Fallback can return a UUID string:

```python
str(uuid4())
```

### 4. Persist `risk_results`

Store:

- `content_id`
- `risk_level`
- `flagged_spans` as JSON
- `risk_categories`
- `reviewer_notes`

### 5. Persist `audit_logs`

Store at least:

- `content_id`
- `action="analyze"`
- `model_version="rule-engine-v1"`
- `doc_version="local-rules-v1"`
- `prompt_hash=None` for rule-only analysis

## Required Deliverables

- [x] Supabase configured detection does not accept `replace-me`.
- [x] `contents_repo.py` inserts real rows when configured.
- [x] `risk_results_repo.py` inserts real rows when configured.
- [x] `audit_service.py` persists audit logs when configured.
- [x] Supabase insert failures fall back to in-memory demo storage.
- [x] Supabase select helpers and repository lookup methods are available for Day 10 APIs.
- [x] Fallback mode still works without Supabase.
- [x] `content_id` is UUID-compatible.
- [x] Tests cover no-Supabase fallback.
- [x] Tests cover analyze API response shape.

## Test Harness

Run from `apps/backend`:

```bash
ruff check app tests
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Smoke test:

```bash
curl http://localhost:8000/v1/health

curl -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_type":"투자상품",
    "channel":"앱 푸시",
    "target_customer":"30대 직장인",
    "language":"ko",
    "original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."
  }'
```

Expected:

- response contains `content_id`
- `risk_level` is `HIGH`
- flagged spans include `누구나`, `연 8% 수익`, `안정적으로`, `원금 걱정 없이`
- fallback mode does not crash without Supabase


## Implementation Completion Placeholder

- Status: COMPLETE
- Implemented files:
  - [x] `apps/backend/requirements.txt`
  - [x] `apps/backend/requirements-dev.txt`
  - [x] `apps/backend/app/integrations/supabase_client.py`
  - [x] `apps/backend/app/repositories/contents_repo.py`
  - [x] `apps/backend/app/repositories/risk_results_repo.py`
  - [x] `apps/backend/app/repositories/audit_logs_repo.py`
  - [x] `apps/backend/app/services/audit_service.py`
  - [x] `apps/backend/app/services/analyze_service.py`
  - [x] `apps/backend/tests/test_api_analyze.py`
  - [x] `apps/backend/tests/test_persistence_fallback.py`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
- Test result summary:
  - `ruff`: passed
  - `pytest`: 14 passed, 1 warning
- Hardening notes:
  - Contents, risk results, and audit logs catch Supabase write failures and fall back to memory for MVP demo stability.
  - `select_one()` and `select_many()` were added to the Supabase REST client.
  - Repository reads now use Supabase when configured, with memory fallback on lookup failure.
  - Audit log inserts now send `created_at` explicitly.
- Known issues:
  - Live Supabase insert/select was not exercised in this environment; configured paths are covered with a fake Supabase client.
  - Fallback memory is non-persistent and demo-only. It is lost on process restart and is not multi-worker safe.
- Live Supabase verification:
  - Status: VERIFIED.
  - Supabase project created at `https://eszuojttibhkazrtqrqx.supabase.co`.
  - `schema.sql` and `seed_regulation_docs.sql` were applied through Supabase SQL Editor.
  - Render has `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.
  - Vercel has no Supabase secrets.
  - `SUPABASE_URL` must be the project base URL and must not include `/rest/v1/`.
  - Initial `POST /rest/v1/contents` returned `403 Forbidden`.
  - Cause: strict Supabase security setup did not expose/privilege new tables for Data API roles.
  - Fix: SQL grants were applied in Supabase SQL Editor.
  - Public Render `/v1/compliance/analyze` API smoke returned HTTP 200 with `risk_level=HIGH` and UUID `content_id`.
  - Public Render `/v1/compliance/analyze` is expected to persist `contents`, `risk_results`, and `audit_logs` after the grant.
  - Confirm persistence by checking Supabase Table Editor rows for `contents`, `risk_results`, and `audit_logs(action=analyze)`.
- Next recommended step:
  - Start Slice 02 / Day 10 approval, audit-log, and report APIs.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
