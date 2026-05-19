# Agent Start Instruction

You are working on the `Finance-SafeGrowth-Agent` repository.

Read these files first:

```text
.devmd/fix-plan/README.md
.devmd/fix-plan/agent-guides/global-fix-instructions.md
.devmd/fix-plan/agent-guides/api-contract-target.md
.devmd/fix-plan/agent-guides/test-harness-target.md
.devmd/fix-plan/00-review-baseline/README.md
```

Then implement fixes in this order:

```text
01-p0-backend-persistence
02-p0-approval-audit-report
03-p0-gemini-rewrite-context
04-p1-rag-quality
05-p1-frontend-mockup-polish
06-p1-test-ci-docker
07-p2-demo-hardening
```

Do not begin UI polish until P0 backend correctness is complete.

Important:

- Mockup screenshots are stored in `.devmd/mockup`.
- Use the mockups as visual reference only.
- Do not embed the mockup screenshots into the app.
- Keep fallback mode working.
- Never expose backend secrets to frontend.
- Update each slice README completion placeholder before marking it done.

Expected final result:

- Backend persists analysis, risk results, approvals, and audit logs when Supabase is configured.
- Backend still works in deterministic fallback mode when Supabase/Gemini is unavailable.
- Rewrite generation uses original text, flagged spans, and evidence context.
- Approval/report/audit APIs exist.
- Frontend calls the full workflow APIs.
- Frontend visually matches `.devmd/mockup` more closely.
- CI, Docker, and env handling are safe.
