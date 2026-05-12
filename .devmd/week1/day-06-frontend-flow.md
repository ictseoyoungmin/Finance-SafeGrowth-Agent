# Day 6 — Frontend 5-Step Flow

## 목표

mockup 기준 5단계 wizard UI를 구현하고 backend API와 연결한다.

## 매핑 Slice

- `slices/slice-03-frontend-flow/README.md`

## 작업 범위

1. Layout: sidebar, header, step container.
2. Compliance state machine.
3. API client.
4. 콘텐츠 입력 화면.
5. Redline Risk Review 화면.
6. 근거 패널 화면.
7. 수정안 비교 화면.
8. 승인 패키지 화면.
9. fallback mock data.

## Required files

```text
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/steps/InputStep.tsx
apps/frontend/src/features/compliance/steps/RedlineStep.tsx
apps/frontend/src/features/compliance/steps/EvidenceStep.tsx
apps/frontend/src/features/compliance/steps/RewriteStep.tsx
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
apps/frontend/src/components/layout/AppShell.tsx
apps/frontend/src/components/redline/RiskMark.tsx
apps/frontend/src/components/redline/renderRedline.tsx
```

## State Flow

```text
input -> redline -> evidence -> rewrite -> approval
```

재검토:

```text
approval/rewrite -> rewrite or redline
```

## Redline rendering rule

1. 우선 `start/end` 기준으로 split rendering.
2. `start/end`가 없으면 `span_text` 첫 매칭 fallback.
3. severity별 className을 분리한다.

## 테스트 / 검증

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
```

Manual:

- 표준 문구 입력.
- Redline 화면에서 위험 span 확인.
- 근거 패널 표시.
- 수정안 비교 표시.
- 승인 패키지 표시.

## 산출물

- [ ] 5-step UI
- [ ] API client
- [ ] workflow store
- [ ] Redline renderer
- [ ] fallback mock data
- [ ] build success

## 완료 기준

- [ ] 단일 샘플 문구로 5단계 진행 가능.
- [ ] backend down 상태에서도 mock fallback으로 UI 확인 가능.
- [ ] 화면별 primary CTA가 명확하다.
