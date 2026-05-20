# Day 12 — Frontend Mockup Polish

## Goal

`.devmd/mockup`의 5개 화면을 기준으로 frontend 5-step workflow를 demo-ready 수준으로 다듬는다.

참조 문서:

- `.devmd/phase2/05-p1-frontend-mockup-polish/README.md`
- `.devmd/mockup/`

## Mockup Mapping

```text
1_콘텐츠입력.png        -> InputStep
2_검토문장.png          -> RedlineStep
3_근거패널.png          -> EvidenceStep
4_수정안비교.png        -> RewriteStep
5_최종승인요약.png      -> ApprovalStep
```

## Files

```text
apps/frontend/src/components/layout/AppShell.tsx
apps/frontend/src/features/compliance/steps/InputStep.tsx
apps/frontend/src/features/compliance/steps/RedlineStep.tsx
apps/frontend/src/features/compliance/steps/EvidenceStep.tsx
apps/frontend/src/features/compliance/steps/RewriteStep.tsx
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/styles.css
```

## Tasks

- [x] InputStep에 product/channel/target/language/text/character count/CTA를 정리한다.
- [x] RedlineStep에 risk summary, confidence, categories, AI reviewer note를 보강한다.
- [x] EvidenceStep에 selected risk context, evidence card, doc version, snippet, relevance를 정리한다.
- [x] RewriteStep에 original vs revised, conservative/marketing variants, changes, selected final text를 연결한다.
- [x] ApprovalStep에 decision panel, evidence summary, final text, approve/reject/request revision/report action을 배치한다.
- [x] loading/error/fallback 상태가 화면 흐름을 막지 않게 한다.
- [x] mobile/desktop에서 text overflow와 버튼 깨짐을 확인한다.

## Design Constraints

- Mockup 이미지는 reference로만 사용하고 app에 직접 삽입하지 않는다.
- Operational tool 성격에 맞게 dense but readable한 UI를 유지한다.
- 과한 landing/hero 구성 대신 5-step workflow를 첫 화면 경험으로 유지한다.
- 버튼, 탭, 토글, selector, 카드 크기는 responsive constraint를 둔다.

## Test

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual flow:

- standard demo sentence로 5단계를 모두 이동한다.
- backend online/offline 양쪽을 확인한다.
- redline highlight, evidence card, rewrite comparison, approval action이 보이는지 확인한다.

## Done When

- 5개 step이 mockup 구조에 더 가까워졌다.
- approval API 연결 상태와 fallback 상태가 모두 자연스럽다.
- frontend build가 통과한다.

## Completion Log

- Status: COMPLETE
- Implemented files:
  - [x] `apps/frontend/src/App.tsx`
  - [x] `apps/frontend/src/components/layout/AppShell.tsx`
  - [x] `apps/frontend/src/features/compliance/steps/InputStep.tsx`
  - [x] `apps/frontend/src/features/compliance/steps/RedlineStep.tsx`
  - [x] `apps/frontend/src/features/compliance/steps/EvidenceStep.tsx`
  - [x] `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
  - [x] `apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
  - [x] `apps/frontend/src/styles.css`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
  - [x] `docker run --rm -v /tmp/dacon-day12-frontend-clean:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"`
  - [x] Playwright Docker local UI smoke against Render backend
- Test result summary:
  - `ruff`: passed
  - `pytest`: 25 passed, 1 warning
  - frontend `typecheck`: passed
  - frontend `lint`: passed
  - frontend `build`: passed
  - UI smoke: passed
- Smoke artifacts:
  - `.devmd/memory/ui-smoke-day12-2026-05-20`
- Known issues:
  - Public Vercel UI smoke after redeploy is still required.
  - Report `evidence` and `changes` remain backend-empty until report enrichment is implemented.
