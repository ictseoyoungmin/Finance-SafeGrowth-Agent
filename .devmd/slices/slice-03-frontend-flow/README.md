# Slice 3 — Frontend Flow

이 slice README는 agent가 해당 구현 단위를 독립적으로 수행할 수 있도록 통합 지시문, 구현 범위, 테스트 하네스, 완료 placeholder를 포함한다.


## Objective

mockup 기준 5단계 wizard UI와 backend API 연동을 구현한다.

## Mapped Days

Day 6

## Prerequisites

Slice 1 analyze API와 Slice 2 evidence/rewrite API가 동작하거나 mock response가 준비되어 있어야 한다.

## Integrated Instructions

1. 좌측 step sidebar는 항상 현재 단계를 표시한다.
2. 입력 화면의 primary CTA는 `준법검토 시작`.
3. Redline은 `start/end` 기준 렌더링을 우선한다.
4. API 실패 시 mock/fallback으로 다음 단계 시연이 가능해야 한다.
5. frontend는 Gemini/Supabase secret을 직접 다루지 않는다.

## Required Deliverables

- [x] AppShell / Sidebar / Header
- [x] Compliance state machine
- [x] API client
- [x] InputStep
- [x] RedlineStep
- [x] EvidenceStep
- [x] RewriteStep
- [x] ApprovalStep
- [x] Redline renderer
- [x] mock/fallback data
- [x] build success

## Test Harness

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual check:

1. 표준 문구 입력.
2. Redline 표시 확인.
3. 근거 패널 표시 확인.
4. 수정안 비교 확인.
5. 승인 패키지 확인.

## Done Criteria

- [ ] 표준 문구로 5단계 진행 가능.
- [ ] backend down 상태에서도 mock fallback 표시.
- [x] build 성공.
- [x] 화면별 CTA와 상태 전이가 명확함.

## Implementation Completion Placeholder

- Status: IN_PROGRESS
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `apps/frontend/src/App.tsx`
  - `apps/frontend/src/styles.css`
  - `apps/frontend/src/components/layout/AppShell.tsx`
  - `apps/frontend/src/components/redline/RiskMark.tsx`
  - `apps/frontend/src/components/redline/renderRedline.tsx`
  - `apps/frontend/src/features/compliance/types.ts`
  - `apps/frontend/src/features/compliance/api.ts`
  - `apps/frontend/src/features/compliance/store.ts`
  - `apps/frontend/src/features/compliance/steps/InputStep.tsx`
  - `apps/frontend/src/features/compliance/steps/RedlineStep.tsx`
  - `apps/frontend/src/features/compliance/steps/EvidenceStep.tsx`
  - `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
  - `apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
- Test commands executed:
  - `cd apps/frontend && npm run lint`
  - `cd apps/frontend && npm run typecheck`
  - `cd apps/frontend && npm run build`
  - `cd apps/frontend && npm run dev`
  - `curl http://172.18.208.1:5174`
  - `curl http://192.168.0.5:5174`
- Test result:
  - Frontend lint passed.
  - Frontend typecheck passed.
  - Frontend build passed.
  - Vite dev server started and served `index.html` from the advertised network URLs.
- Known issues:
  - Manual browser click-through across all 5 screens was not executed in this environment, so the slice is not marked COMPLETE.
  - A previous Windows-side Vite process may still be serving on port 5173. Future `npm run dev` may select another available port.
- Fallback behavior:
  - API client falls back to deterministic analyze/evidence/rewrite demo data if backend requests fail.
  - Frontend does not read or expose Gemini or Supabase service-role secrets.
- Next recommended task:
  - Manually validate the 5-screen flow in a browser, then mark Slice 3 COMPLETE if the flow passes.
