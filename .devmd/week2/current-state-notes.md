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
Day 11 / Phase 2 Slice 03 and Slice 04 are complete locally.
Day 12 / Phase 2 Slice 05 is complete locally.

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

- Public Day 10 approve/audit-log/report smoke succeeded on Render.
- Frontend approval now sends the selected final text to `selected_revision`, not the `"marketing"` / `"conservative"` selector value.
- Render has `GEMINI_API_KEY` and `GEMINI_MODEL`.

Day 11 implementation completed:

- Gemini JSON parser handles raw JSON, fenced JSON, and explanation-wrapped JSON.
- Rewrite prompt now resolves context from content, latest risk result, and regulation evidence repositories.
- Supabase configured regulation docs path now queries `regulation_docs` and filters by product type and risk category overlap.
- Regulation evidence fallback remains deterministic.

Verification:

- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker `typecheck`: passed.
- Frontend Docker `lint`: passed.

Remaining:

- Redeploy Render/Vercel before public testing the updated frontend approval fix and Gemini rewrite context.
- Public-smoke `/rewrite` with Gemini enabled on Render.
- Report `evidence` and `changes` are still empty until rewrite/evidence persistence or regeneration is implemented.

## Day 11 Follow-up Verification

Status: IN_PROGRESS

Completed:

- Frontend approval sends actual selected revision text, falling back to the original input text if rewrite text is unavailable.
- Gemini failure paths log useful Render diagnostics without printing API keys.
- `.env.example` files use placeholders and do not contain project-specific Supabase keys.
- Gemini rewrite context includes original text, risk spans, risk categories, reviewer notes, and regulation evidence.
- Gemini JSON parser handles raw, fenced, and explanation-wrapped JSON.
- Regulation evidence lookup uses Supabase table filtering before fallback.
- Backend tests passed.
- Frontend Docker `npm ci`, `typecheck`, `lint`, and `build` passed from a clean temporary copy.

Public verification:

- Render `/rewrite` smoke: NOT_RUN after latest local changes.
- Vercel UI approval/report smoke: NOT_RUN after latest local changes.
- Supabase `approval_logs.selected_revision` actual text check from UI path: NOT_RUN after latest local changes.

Local verification:

- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker command used:

```bash
docker run --rm -v /tmp/dacon-day11-frontend-clean:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"
```

- Frontend `typecheck`: passed.
- Frontend `lint`: passed.
- Frontend `build`: passed.

Known limitations:

- Report `evidence` and `changes` are still empty until evidence/rewrite persistence or regeneration is added.
- Supabase regulation retrieval uses table filtering, not pgvector RPC, because seeded docs do not yet include embeddings.
- Gemini live behavior should be checked in Render logs because fallback also returns HTTP 200.

## Day 12 Frontend Mockup Polish

Status: COMPLETE locally

Completed:

- Input step now includes a readiness/context strip under the analysis note.
- Redline step now includes compact risk metrics for detected expressions and risk categories.
- Evidence step now surfaces selected risk context and guideline snippets in evidence cards.
- Rewrite step now shows a selected final revision preview before approval.
- Approval step now includes a review stamp, evidence count, report/audit summary, and clearer action feedback.
- App shell displays success/action messages separately from error notices.
- Desktop and mobile screenshots were captured through Playwright Docker.

Verification:

- Render `/v1/health`: HTTP 200.
- Render `/v1/compliance/analyze`: HTTP 200 with `risk_level=HIGH`.
- Render `/v1/compliance/rewrite`: HTTP 200 with conservative/marketing rewrites and changes.
- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker `npm ci && npm run typecheck && npm run lint && npm run build`: passed.
- Playwright Docker 5-step UI smoke against Render backend: passed.

Artifacts:

- `.devmd/memory/ui-smoke-day12-2026-05-20`

Remaining:

- Public Vercel UI smoke after redeploy.
- Supabase UI-path `approval_logs.selected_revision` actual text check after redeploy.

## Gemini Rewrite Live Smoke

Status: VERIFIED locally with root `.env`

- Added `.devmd/tools/rewrite_live_smoke.py`.
- The smoke script loads the selected env file before importing the FastAPI app.
- It runs `analyze -> rewrite` with a non-standard investment ad example:
  - includes `반드시`
  - includes `연 12% 수익`
  - includes `안전하게`
  - includes `원금 보장`
- It fails if the rewrite response exactly matches the deterministic fallback rewrite.
- Command executed from `apps/backend`:

```bash
timeout 90 bash -lc 'PYTHONPATH=. .venv/bin/python ../../.devmd/tools/rewrite_live_smoke.py --env ../../.env'
```

- Result:
  - Gemini model: `gemini-2.5-flash-lite`
  - `risk_level=HIGH`
  - `fallback_like=False`
  - Conservative and marketing rewrite outputs differed from the deterministic fallback.
