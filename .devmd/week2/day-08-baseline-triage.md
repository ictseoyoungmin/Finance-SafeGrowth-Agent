# Day 8 — Baseline Triage

## Goal

Phase 2 작업 전 현재 repository 상태를 재확인하고, 구현된 것과 문서상 gap을 분리한다.

참조 문서:

- `.devmd/phase2/00-review-baseline/README.md`
- `.devmd/phase2/README.md`
- `.devmd/week1/README.md`

## 확인 범위

Backend:

- `apps/backend/app/api/v1/compliance.py`
- `apps/backend/app/services/analyze_service.py`
- `apps/backend/app/services/evidence_service.py`
- `apps/backend/app/services/rewrite_service.py`
- `apps/backend/app/repositories/*.py`
- `apps/backend/app/integrations/*.py`
- `apps/backend/tests/`

Frontend:

- `apps/frontend/src/features/compliance/api.ts`
- `apps/frontend/src/features/compliance/store.ts`
- `apps/frontend/src/features/compliance/types.ts`
- `apps/frontend/src/features/compliance/steps/*.tsx`
- `apps/frontend/src/styles.css`

Infra/docs:

- `infra/supabase/schema.sql`
- `infra/supabase/seed_regulation_docs.sql`
- `docker-compose.yml`
- `.github/workflows/*.yml`
- `docs/demo/`
- `docs/deployment/`

## Tasks

- [x] 현재 endpoint 목록과 request/response shape를 확인한다.
- [x] Supabase configured detection이 placeholder 값을 real secret으로 보는지 확인한다.
- [x] repository layer가 실제 DB 저장을 하는지 확인한다.
- [x] fallback store가 API sequence 전체에서 context를 유지하는지 확인한다.
- [x] approval/report 관련 endpoint 존재 여부를 확인한다.
- [x] frontend 5-step flow가 backend API와 어디까지 연결되어 있는지 확인한다.
- [x] test 명령을 실행하고 실패 목록을 정리한다.

## Output

필요하면 아래 파일을 생성한다.

```text
.devmd/week2/current-state-notes.md
```

기록 항목:

- 구현 완료
- 미구현
- 테스트 실패
- P0 blocker
- 다음 day에 넘길 결정 사항

## Done When

- [x] P0 작업에 들어가기 전 blocker가 명확하다.
- [x] Day 9에서 수정해야 할 파일 목록이 확정되어 있다.
- [x] 기존 user 변경사항이나 dirty worktree가 있으면 기록되어 있다.

## Completion Log

- Status: COMPLETE
- Output note: `.devmd/week2/current-state-notes.md`
- Key findings:
  - `content_id` fake `content-{uuid}` format and no-op persistence were the Day 9 blockers.
  - approval/audit-log/report APIs are still missing and are Day 10 scope.
  - Week 1 frontend/deployment flow is complete.
