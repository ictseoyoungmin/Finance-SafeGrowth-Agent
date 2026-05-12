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

- [ ] AppShell / Sidebar / Header
- [ ] Compliance state machine
- [ ] API client
- [ ] InputStep
- [ ] RedlineStep
- [ ] EvidenceStep
- [ ] RewriteStep
- [ ] ApprovalStep
- [ ] Redline renderer
- [ ] mock/fallback data
- [ ] build success

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
- [ ] build 성공.
- [ ] 화면별 CTA와 상태 전이가 명확함.

## Implementation Completion Placeholder

- Status: [ ] Not Started / [ ] In Progress / [ ] Completed
- Branch:
- Commit / PR:
- Implemented files:
  - 
- Test commands executed:
  - 
- Test result:
  - 
- Known issues:
  - 
- Fallback behavior:
  - 
- Next recommended task:
  -
