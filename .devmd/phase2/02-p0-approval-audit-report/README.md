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

- [ ] Approval schema added.
- [ ] Approval service added.
- [ ] Approval repository added.
- [ ] `POST /approve` persists or fallback-stores approval.
- [ ] `GET /audit-log` returns entries.
- [ ] `GET /report` returns structured report JSON.
- [ ] Frontend ApprovalStep calls the backend approve API.
- [ ] Fallback behavior remains available.
- [ ] API tests added.

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
  -d "{\"content_id\":\"$CONTENT_ID\",\"reviewer\":\"김준법 수석\",\"decision\":\"CONDITIONALLY_APPROVED\",\"comment\":\"Demo approval\",\"selected_revision\":\"marketing\"}"

curl "http://localhost:8000/v1/compliance/audit-log?content_id=$CONTENT_ID"
curl "http://localhost:8000/v1/compliance/report?content_id=$CONTENT_ID"
```


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
