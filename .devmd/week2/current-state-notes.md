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

Not yet implemented:

- `POST /v1/compliance/approve`
- `GET /v1/compliance/audit-log`
- `GET /v1/compliance/report`

These are Day 10 / Phase 2 Slice 02 scope.

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

## Next Step

Proceed to Day 10:

- `.devmd/week2/day-10-approval-report-api.md`
- `.devmd/phase2/02-p0-approval-audit-report/README.md`
