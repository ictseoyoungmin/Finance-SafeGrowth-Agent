# Slice 07 — P2 Demo Hardening

## Goal

Freeze the demo path and make the project robust for public evaluation.

This slice should happen after P0 and P1 work.

## Scope

- demo script
- smoke tests
- fallback strategy
- regulation-impact placeholder
- report polish
- deployment checklist
- known issue tracking

## Files to modify

```text
README.md
docs/demo-script.md
docs/deployment-checklist.md
docs/smoke-test.md
apps/backend/app/api/v1/compliance.py
apps/backend/app/schemas/regulation_impact.py          # optional
apps/backend/app/services/regulation_impact_service.py # optional
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
```

## Standard demo sentence

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

Expected risky expressions:

```text
누구나
연 8% 수익
안정적으로
원금 걱정 없이
```

## Demo freeze checklist

- [ ] Vercel frontend URL opens.
- [ ] Render backend `/v1/health` returns OK.
- [ ] Supabase seed data exists.
- [ ] Gemini API key is configured or fallback mode is intentionally enabled.
- [ ] Standard demo sentence completes all 5 screens.
- [ ] Analyze returns HIGH risk.
- [ ] Evidence returns relevant snippets.
- [ ] Rewrite returns conservative and marketing-balanced variants.
- [ ] Approval saves or fallback-saves decision.
- [ ] Report payload is available.
- [ ] Backend cold-start mitigation documented.

## Optional Regulation Impact API

Add placeholder:

```text
POST /v1/compliance/regulation-impact
```

Request:

```json
{
  "doc_id": "doc-demo-001",
  "new_version": "demo-v2",
  "summary": "New rule affecting fixed-return expressions."
}
```

Response:

```json
{
  "affected_contents": [],
  "message": "No persisted contents found in fallback mode."
}
```

This can remain a demo placeholder if time is limited.

## Required Deliverables

- [x] Demo script added.
- [ ] Deployment checklist added.
- [ ] Smoke test instructions added.
- [ ] Demo freeze checklist completed.
- [x] Known issues documented.
- [ ] Optional regulation-impact placeholder added if time allows.

## Demo Detail Hardening Pass

Status: IN_PROGRESS locally

Completed in the first implementation pass:

- Fixed the rewrite demo-risk where Gemini-unavailable responses could show only fixed standard-demo correction text.
- Backend deterministic rewrite fallback now uses the submitted original text and detected risky spans.
- Rewrite responses now include `source: "gemini" | "fallback"`.
- Frontend rewrite UI now displays `Gemini 검수 결과` or `Deterministic fallback`.
- RuleEngine now catches broader non-demo financial ad risk phrases and deduplicates overlapping highlights.
- Demo docs now explain rewrite source badges and input-aware fallback behavior.

Verification:

- Backend `ruff`: passed.
- Backend `pytest`: `28 passed, 1 warning`.
- Frontend Playwright Docker `npm ci && npm run typecheck && npm run lint && npm run build`: passed.

Remaining before marking full Slice 07 complete:

- Public Vercel/Render smoke after redeploy.
- Deployment checklist and smoke-test docs.
- Optional regulation-impact placeholder, if still desired.

## Test Harness

Run full local checks:

```bash
cd apps/backend
ruff check app tests
pytest

cd ../frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

Run smoke test after deployment:

```bash
curl https://<render-backend-url>/v1/health
```

Then manually run the 5-step UI flow from the Vercel URL.


## Implementation Completion Placeholder

- Status: IN_PROGRESS
- Implemented files:
  - [x] `apps/backend/app/schemas/rewrite.py`
  - [x] `apps/backend/app/services/rewrite_service.py`
  - [x] `apps/backend/app/rules/rule_engine.py`
  - [x] `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
  - [x] `apps/frontend/src/features/compliance/store.ts`
  - [x] `docs/demo/README.md`
  - [x] `docs/demo/demo-script.md`
  - [x] `docs/demo/fallback-plan.md`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 90 .venv/bin/pytest -q`
  - [x] `docker run --rm -v /tmp/dacon-day14-frontend-full:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"`
- Test result summary:
  - Backend and frontend checks passed locally.
- Known issues:
  - Public redeploy/smoke remains pending.
  - npm audit warnings remain in frontend dependency tree.
- Next recommended step:
  - Redeploy and run public 5-step smoke, then finish deployment checklist and handover docs.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
