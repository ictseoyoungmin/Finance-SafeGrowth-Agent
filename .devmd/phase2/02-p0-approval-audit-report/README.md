# Slice 02 — P0 Approval, Audit Log, and Report APIs

## Goal

Complete the workflow after rewrite generation by adding backend APIs and frontend integration for approval, audit-log lookup, and report payload generation.

The current approval screen is local-only. It does not call the backend.

## Problems to fix

1. `POST /v1/compliance/approve` does not exist.
2. `GET /v1/compliance/audit-log` does not exist.
3. `GET /v1/compliance/report` does not exist.
4. `ApprovalStep` shows a fixed decision and reviewer without persistence.
5. `approval_logs` table exists in SQL but is not used.

## Target APIs

### POST `/v1/compliance/approve`

Request:

```json
{
  "content_id": "uuid-string",
  "reviewer": "김준법 수석",
  "decision": "CONDITIONALLY_APPROVED",
  "comment": "Approved after required wording changes.",
  "selected_revision": "marketing"
}
```

Response:

```json
{
  "approval_id": "uuid-string-or-fallback-id",
  "content_id": "uuid-string",
  "status": "APPROVED",
  "decision": "CONDITIONALLY_APPROVED",
  "reviewer": "김준법 수석"
}
```

### GET `/v1/compliance/audit-log?content_id=...`

Response:

```json
{
  "content_id": "uuid-string",
  "entries": [
    {
      "action": "analyze",
      "model_version": "rule-engine-v1",
      "doc_version": "local-rules-v1",
      "created_at": "ISO-8601"
    }
  ]
}
```

### GET `/v1/compliance/report?content_id=...`

For this slice, return JSON. PDF generation can be P2.

Response:

```json
{
  "content_id": "uuid-string",
  "summary": "Approval package summary",
  "risk_level": "HIGH",
  "final_text": "...",
  "evidence": [],
  "changes": [],
  "approval": {}
}
```

## Files to modify

```text
apps/backend/app/api/v1/compliance.py
apps/backend/app/schemas/approval.py              # new
apps/backend/app/schemas/audit.py                 # new
apps/backend/app/schemas/report.py                # new
apps/backend/app/services/approval_service.py     # new
apps/backend/app/services/audit_service.py
apps/backend/app/services/report_service.py       # new
apps/backend/app/repositories/approval_logs_repo.py # new
apps/backend/app/repositories/audit_logs_repo.py  # if not added in Slice 01
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
```

## Frontend changes

`ApprovalStep` must include actions:

- Approve
- Reject
- Request revision
- View/download report payload
- Start new review

For MVP, approval decision can be selected from fixed values:

```text
APPROVED
CONDITIONALLY_APPROVED
REJECTED
REVISION_REQUESTED
```

## Required Deliverables

- [x] Approval schema added.
- [x] Approval service added.
- [x] Approval repository added.
- [x] `POST /approve` persists or fallback-stores approval.
- [x] `GET /audit-log` returns entries.
- [x] `GET /report` returns structured report JSON.
- [x] Frontend ApprovalStep calls the backend approve API.
- [x] Fallback behavior remains available.
- [x] API tests added.

## Test Harness

Backend:

```bash
ruff check app tests
pytest
```

Manual API sequence:

```bash
CONTENT_ID=$(curl -s -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['content_id'])")

curl -X POST http://localhost:8000/v1/compliance/approve \
  -H "Content-Type: application/json" \
  -d "{\"content_id\":\"$CONTENT_ID\",\"reviewer\":\"김준법 수석\",\"decision\":\"CONDITIONALLY_APPROVED\",\"comment\":\"Demo approval\",\"selected_revision\":\"시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. 가입 전 상품설명서와 유의사항을 확인해 주세요.\"}"

curl "http://localhost:8000/v1/compliance/audit-log?content_id=$CONTENT_ID"
curl "http://localhost:8000/v1/compliance/report?content_id=$CONTENT_ID"
```


## Implementation Completion Placeholder

- Status: COMPLETE
- Implemented files:
  - [x] `apps/backend/app/api/v1/compliance.py`
  - [x] `apps/backend/app/schemas/approval.py`
  - [x] `apps/backend/app/schemas/audit.py`
  - [x] `apps/backend/app/schemas/report.py`
  - [x] `apps/backend/app/services/approval_service.py`
  - [x] `apps/backend/app/services/audit_service.py`
  - [x] `apps/backend/app/services/report_service.py`
  - [x] `apps/backend/app/repositories/approval_logs_repo.py`
  - [x] `apps/backend/tests/test_api_approval_report.py`
  - [x] `apps/backend/tests/test_persistence_fallback.py`
  - [x] `apps/frontend/src/features/compliance/api.ts`
  - [x] `apps/frontend/src/features/compliance/store.ts`
  - [x] `apps/frontend/src/features/compliance/types.ts`
  - [x] `apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
  - [x] `infra/supabase/schema.sql`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
  - [x] `docker run --rm -v /mnt/f/NowWorking/Dacon-Fin-Agent/apps/frontend:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm run typecheck"`
  - [x] `docker run --rm -v /mnt/f/NowWorking/Dacon-Fin-Agent/apps/frontend:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm run lint"`
- Test result summary:
  - `ruff`: passed
  - `pytest`: 25 passed, 1 warning
  - frontend `typecheck`: passed
  - frontend `lint`: passed
- Live public verification:
  - Render `/v1/compliance/analyze` returned HTTP 200 with UUID `content_id`.
  - Render `/v1/compliance/approve` returned UUID `approval_id`.
  - Render `/v1/compliance/audit-log` returned `analyze` and `approve` entries.
  - Render `/v1/compliance/report` returned `risk_level=HIGH` and the actual selected revision text as `final_text`.
- Bug fix:
  - Frontend approval now sends the selected revision text, not only the `"marketing"` or `"conservative"` selector value.
- Known issues:
  - Existing Supabase projects need the `approval_logs.selected_revision` schema update applied before live approval persistence can store that field.
  - Report API returns JSON only; PDF generation remains P2.
  - Report `evidence` and `changes` are still empty until rewrite/evidence persistence or regeneration is added.
- Next recommended step:
  - Apply the updated `infra/supabase/schema.sql` to production Supabase, redeploy Render/Vercel, then public-smoke the approve, audit-log, and report sequence.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
