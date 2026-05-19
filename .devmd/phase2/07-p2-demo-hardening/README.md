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

- [ ] Demo script added.
- [ ] Deployment checklist added.
- [ ] Smoke test instructions added.
- [ ] Demo freeze checklist completed.
- [ ] Known issues documented.
- [ ] Optional regulation-impact placeholder added if time allows.

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

- Status: NOT_STARTED / IN_PROGRESS / COMPLETE / BLOCKED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Test result summary:
  - TBD
- Known issues:
  - TBD
- Next recommended step:
  - TBD

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
