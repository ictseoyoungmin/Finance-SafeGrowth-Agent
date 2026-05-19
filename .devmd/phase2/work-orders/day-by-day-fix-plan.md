# Day-by-Day Fix Plan

## Day 1 — Persistence and ID correctness

Slice: `01-p0-backend-persistence`

Tasks:

- Harden Supabase configured detection.
- Replace fake `content-{uuid}` with UUID-compatible IDs.
- Implement real/fallback content repository.
- Implement real/fallback risk result repository.
- Implement audit log persistence.
- Add analyze API tests.

Done when:

- `/analyze` works with and without Supabase.
- Tests pass.

## Day 2 — Approval, audit-log, report

Slice: `02-p0-approval-audit-report`

Tasks:

- Add approval schemas.
- Add approval repository/service.
- Add `/approve`.
- Add `/audit-log`.
- Add `/report` JSON payload.
- Update frontend ApprovalStep to call backend.

Done when:

- Full workflow reaches persisted/fallback approval.
- API tests pass.

## Day 3 — Gemini rewrite context

Slice: `03-p0-gemini-rewrite-context`

Tasks:

- Resolve content/risk/evidence context by `content_id`.
- Build context-rich rewrite prompt.
- Improve Gemini JSON parser.
- Add parser tests.

Done when:

- Rewrite works with real context or fallback context.
- Gemini failure does not break demo flow.

## Day 4 — RAG quality

Slice: `04-p1-rag-quality`

Tasks:

- Query Supabase `regulation_docs` when configured.
- Keep fallback search when DB is unavailable.
- Improve evidence filtering.
- Document seed process.

Done when:

- Evidence API returns relevant docs in both DB and fallback mode.

## Day 5 — Frontend polish against mockups

Slice: `05-p1-frontend-mockup-polish`

Tasks:

- Use `.devmd/mockup` as visual reference.
- Improve all five steps.
- Add language field.
- Add approval actions.
- Improve loading/fallback states.

Done when:

- All five screens are demo-ready and closer to mockups.

## Day 6 — CI/Docker/test cleanup

Slice: `06-p1-test-ci-docker`

Tasks:

- Update backend CI path filters.
- Use `npm ci` in frontend CI.
- Fix docker env handling.
- Add missing tests.

Done when:

- Backend and frontend checks pass locally and in CI.

## Day 7 — Demo hardening

Slice: `07-p2-demo-hardening`

Tasks:

- Add demo script.
- Add smoke test docs.
- Add deployment checklist.
- Optional regulation-impact placeholder.
- Freeze known issues.

Done when:

- Public demo path is stable and documented.
