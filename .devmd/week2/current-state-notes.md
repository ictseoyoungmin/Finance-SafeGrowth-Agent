# Week 2 Current State Notes

Last updated: 2026-05-20

## Baseline Summary

Week 1 is complete:

- Bootstrap, backend core, RAG/Gemini fallback, frontend flow, and deployment polish are documented as complete.
- Public deployment URLs:
  - Render: `https://finance-safegrowth-agent.onrender.com`
  - Vercel: `https://finance-safe-growth-agent.vercel.app`

## Endpoint State

Implemented:

- `GET /v1/health`
- `POST /v1/compliance/analyze`
- `POST /v1/compliance/evidence`
- `POST /v1/compliance/rewrite`
- `POST /v1/compliance/approve`
- `GET /v1/compliance/audit-log`
- `GET /v1/compliance/report`

Day 10 / Phase 2 Slice 02 is complete locally.

## Day 8 Findings

- Supabase placeholder values were previously treated as configured if both URL and service role key were non-empty.
- `ContentRepository.save_original()` returned fake `content-{uuid}` IDs.
- `RiskResultsRepository.save_analysis()` was a no-op.
- `AuditService.record_analysis()` returned an in-memory record but did not persist through a repository.
- Evidence and rewrite fallback APIs are available and pass tests.
- Frontend 5-step flow is complete and public smoke passed in Week 1.

## Day 9 Resolution

Implemented:

- Hardened Supabase configured detection with placeholder filtering.
- Added Supabase REST insert and select helpers.
- Changed fallback `content_id` to UUID-compatible strings.
- Added fallback content store.
- Added fallback risk result store.
- Added audit logs repository with fallback store.
- Added repository-level fallback when Supabase insert/select fails.
- Added Supabase-backed lookup methods for content, latest risk result, and audit logs.
- Included explicit `created_at` in audit log insert payloads.
- Wired `AuditService.record_analysis()` to persist audit logs.
- Updated analyze service to persist risk categories and reviewer notes.
- Added tests for:
  - placeholder Supabase config detection
  - fallback content UUID/store
  - fallback risk and audit persistence
  - fallback after configured Supabase failures
  - configured repository insert paths
  - configured repository select paths
  - analyze API UUID response shape

## Verification

Backend:

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q
```

Result:

- `ruff`: passed
- `pytest`: `14 passed, 1 warning`

Known environment note:

- Starting `uvicorn` in one sandboxed exec session and calling it via `curl` from another exec session failed with connection error in this environment. API behavior is covered by FastAPI `TestClient` tests.
- Fallback memory is non-persistent and demo-only. It is lost on process restart and is not shared across multiple workers.

## Live Supabase Verification

Status: VERIFIED

- Supabase project created: `https://eszuojttibhkazrtqrqx.supabase.co`.
- `infra/supabase/schema.sql` was applied through Supabase SQL Editor.
- `infra/supabase/seed_regulation_docs.sql` was applied through Supabase SQL Editor.
- SQL Editor requires pasted SQL contents, not repository file paths. Pasting `infra/supabase/schema.sql` directly fails with `syntax error at or near "infra"`.
- Render environment variables configured:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
- Vercel does not contain Supabase secrets. Vercel only keeps `VITE_API_BASE_URL=https://finance-safegrowth-agent.onrender.com`.
- `SUPABASE_URL` must be `https://eszuojttibhkazrtqrqx.supabase.co` and must not include `/rest/v1/`.
- Initial Supabase REST insert returned `403 Forbidden`.
- Cause: new tables were not exposed/privileged for Data API roles due to strict security setup.
- Fix: SQL grants were applied in Supabase SQL Editor for the relevant public tables.
- Public Render smoke on 2026-05-20:
  - `GET /v1/health`: HTTP 200.
  - `POST /v1/compliance/analyze`: HTTP 200.
  - Response `risk_level`: `HIGH`.
  - Response `content_id`: UUID-compatible, no `content-` prefix.
  - Flagged spans included `누구나`, `연 8% 수익`, `안정적으로`, `원금 걱정 없이`.
- Public Render `/v1/compliance/analyze` is expected to persist after the grant:
  - `contents`
  - `risk_results`
  - `audit_logs`
- Supabase Table Editor should be checked after each live smoke as operational confirmation:
  - `contents` has a new row.
  - `risk_results` has a new row.
  - `audit_logs` has a new row with `action = analyze`.

## Next Step

Day 10 implementation completed:

- `.devmd/week2/day-10-approval-report-api.md`
- `.devmd/phase2/02-p0-approval-audit-report/README.md`

Verification:

- Backend `ruff`: passed.
- Backend `pytest`: 16 passed, 1 warning.
- Frontend Docker `typecheck`: passed.
- Frontend Docker `lint`: passed.

Next:

- Apply the updated `infra/supabase/schema.sql` to production Supabase so `approval_logs.selected_revision` exists.
- Redeploy Render/Vercel.
- Public-smoke approve, audit-log, and report endpoints.
