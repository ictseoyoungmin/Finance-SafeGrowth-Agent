# Day 10 — Approval, Audit Log, and Report API

## Goal

5단계 workflow의 마지막을 backend API로 완성한다. Approval screen의 local-only 동작을 approve/audit-log/report API와 연결한다.

참조 문서:

- `.devmd/phase2/02-p0-approval-audit-report/README.md`

## Target APIs

```text
POST /v1/compliance/approve
GET  /v1/compliance/audit-log?content_id=...
GET  /v1/compliance/report?content_id=...
```

## Files

Backend:

```text
apps/backend/app/api/v1/compliance.py
apps/backend/app/schemas/approval.py
apps/backend/app/schemas/audit.py
apps/backend/app/schemas/report.py
apps/backend/app/services/approval_service.py
apps/backend/app/services/audit_service.py
apps/backend/app/services/report_service.py
apps/backend/app/repositories/approval_logs_repo.py
apps/backend/app/repositories/audit_logs_repo.py
apps/backend/tests/
```

Frontend:

```text
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
```

## Tasks

- [x] approval request/response schema를 추가한다.
- [x] approval repository/service를 추가한다.
- [x] `POST /approve`가 Supabase 또는 fallback에 decision을 저장한다.
- [x] `GET /audit-log`가 content별 action entries를 반환한다.
- [x] `GET /report`가 JSON approval package를 반환한다.
- [x] frontend ApprovalStep에 approve/reject/request revision/report action을 연결한다.
- [x] backend offline/fallback 상황에서 UI가 깨지지 않게 한다.
- [x] API tests를 추가한다.

## Test

```bash
cd apps/backend
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

## Done When

- Approval decision이 backend에 저장 또는 fallback 저장된다.
- report JSON이 final text, risk, evidence, changes, approval 정보를 포함한다.
- frontend final step이 backend API를 호출한다.
- 관련 tests가 통과한다.

## Completion Log

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
  - `pytest`: 16 passed, 1 warning
  - frontend `typecheck`: passed
  - frontend `lint`: passed
- Known issues:
  - Existing Supabase projects need the `approval_logs.selected_revision` schema update applied before live approval persistence can store that field.
  - Report API returns JSON only; PDF generation remains out of scope for this slice.
