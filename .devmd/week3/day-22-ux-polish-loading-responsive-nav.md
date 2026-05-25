# Day 22 — UX Polish: 로딩 인디케이터 · 반응형 · 좌측 nav 단순화

## 배경

[day-22-right-rail-tabbed-refactor.md](day-22-right-rail-tabbed-refactor.md) 로 우측 패널을 정리한 뒤, 같은 화면에서 발견된 3가지 결함을 한 묶음으로 폴리시한다.

| 현상 | 영향 | 원인 |
| --- | --- | --- |
| `준법검토 시작` 등 버튼을 눌렀을 때 텍스트만 "검토 중" 으로 바뀜 | 사용자가 클릭이 먹혔는지 시각적 신호가 부족 | 버튼에 스피너 없음, 화면 어디에도 진행 인디케이터 없음 |
| 좁은 가로 폭에서 textarea 의 `59 / 2,000` 카운터가 두 줄로 깨지고 우측 rail 콘텐츠와 겹쳐 보임 | 데모/발표 시 "버그처럼" 보임 | `workspace-with-rail` 그리드가 너무 큰 min-width 까지 2-column 을 유지, `.character-count` 줄바꿈 허용 |
| 좌측 사이드바: `1 ◆ Agent Run` / `2 ▤ 구버전 5-step 검토` / `1 □ 콘텐츠 입력` 등 두 모드 nav 가 공존, 유니코드 도형 아이콘 (□ ○ ▤ ⇄ ▱ ◆) 이 보임, 일부 항목이 영어 ("Redline Risk Review") | 정보 구조 혼란 + 시각적 정돈도 낮음 | `AppShell` 의 `mode === "agent"` / `mode === "legacy"` 분기 nav + 각 step 의 `icon` 필드 |

사용자가 명시한 방향:

1. 버튼 클릭 후 대기 시 **로딩 중임을 알리기**
2. **화면 비율 변동 시 글자가 삐져나가지 않게 flexible** 하게
3. 좌측 **Agent Run 항목 제거**, agent 통합된 5-step 만 유지
4. 좌측 nav 의 **특수문자 제거**, **Text만**, **한국어 통일**

## 목표 / Non-goals

### 목표
- 4개 primary 액션 ("준법검토 시작", "근거 확인", "수정안 생성", "승인/조건부 승인/반려/수정 요청") 모두에 동작 중인 시각 신호 (스피너 + 작업 영역 흐림)
- 800px ~ 1920px 가로폭에서 텍스트 잘림/오버랩 0건
- 좌측 nav: 5-step 1개 리스트, 텍스트만, 한국어
- 라우팅: `/` → 5-step (LegacyWizard) 이 기본. AgentRunPage 는 `#/agent` 로 보존만.

### Non-goals
- AgentRunPage 자체의 디자인/기능 변경 — 노출 위치만 이동
- 새 디자인 토큰/색상 추가 — 기존 변수만 활용
- 백엔드 API 변경 없음

## 변경 사항

### 1. 좌측 사이드바 단순화

`apps/frontend/src/components/layout/AppShell.tsx`

- `STEPS` 배열에서 `icon` 필드 제거 (`□ ○ ▤ ⇄ ▱`)
- `mode === "agent"` 분기 제거 — 항상 5-step nav 만 렌더
- `"Agent Run으로"` 백 링크 제거
- `STEPS` 의 라벨 한국어화:
  - `"Redline Risk Review"` → `"리스크 분석"`
  - 나머지는 이미 한국어 (콘텐츠 입력 / 근거 패널 / 수정안 비교 / 승인 패키지)
- `step-item` 의 `<i aria-hidden="true">{icon}</i>` 마크업과 관련 CSS (`.step-item i`, `.step-item.is-active i`) 제거
- `AppShellProps.mode` 는 단순화 가능 → 일단 prop 자체는 제거 (호출부 1군데뿐: `App.tsx`)
- `currentTitle` 도 `STEPS` 에서 직접 찾는 단일 경로로 단순화
- `side-card` 의 mode 분기 문구도 5-step 문구로 통일

CSS (`apps/frontend/src/styles.css`)
- `.step-item` 그리드: `38px 38px minmax(0, 1fr)` → `38px minmax(0, 1fr)` (아이콘 컬럼 삭제)
- `.step-item i`, `.step-item.is-active i` 규칙 삭제
- `.app-nav-list`, `.app-nav-item`, `.app-nav-item.legacy-home` 관련 규칙 정리 (사용처가 사라짐)
- `.brand-kicker` (그라데이션 로고 마크) 는 **유지** — 사용자가 말한 "특수 문자" 는 nav 안의 텍스트 아이콘을 의미

### 2. 라우팅 변경

`apps/frontend/src/App.tsx`
- `"/legacy/wizard"` 분기 → 기본 (`/`) 로 끌어올림
- AgentRunPage 는 `"/agent"` 라우트로 보존 (코드/기능 손실 없음). nav 에서는 노출 안 함.

`apps/frontend/tests/agent.spec.ts`
- 첫 번째 테스트 (`agent trace flow reaches final report`) 의 `await page.goto("/")` → `"/#/agent"` 로 수정
- 두 번째 테스트 (`legacy approval feedback`) 의 `"/#/legacy/wizard"` → `"/"` 로 수정

### 3. 로딩 인디케이터

#### 3a. 버튼 스피너

`apps/frontend/src/styles.css`
- `.primary-button.is-loading`, `.danger-button.is-loading` 등에 스피너 CSS 추가
  - 버튼 텍스트 좌측에 12-14px 원형 spinner (border-top 색만 다르게 회전)
  - `@keyframes spin-1`
- `disabled` 와 시각적으로 명확히 구분 (단순 회색이 아니라 "동작 중" 느낌)

각 step 컴포넌트 (`InputStep`, `RedlineStep`, `EvidenceStep`, `RewriteStep`, `ApprovalStep`):
- `className={\`primary-button ${state.isLoading ? "is-loading" : ""}\`}` 패턴 적용
- 버튼 내부: `{state.isLoading ? <span className="spinner" aria-hidden /> : null}` 와 라벨
- `ApprovalStep` 4개 버튼은 `pendingAction` 으로 어떤 버튼이 로딩 중인지 구분 (이미 store 에 `pendingAction` 있음 — 활용)
  - 예: `decision === "APPROVED"` 버튼은 `pendingAction === "approve"` 일 때만 spinner
  - 다른 버튼은 `disabled` 만

#### 3b. 작업 영역 흐림 + 상단 progress bar

- `<section className="step-panel">` 가 `state.isLoading` 일 때 `is-busy` 클래스 → `pointer-events: none; opacity: 0.6` 로 입력 잠금
- AppShell topbar 아래에 1px 짜리 indeterminate progress bar (`.global-progress`) 를 `isLoading` 시 표시
- LegacyWizard 에서 workflow.state.isLoading 을 AppShell 로 prop 전달 (이미 `usedFallback` / `errorMessage` 등 전달 중)

### 4. 반응형 보강

`apps/frontend/src/styles.css`

- `.character-count`: `white-space: nowrap;` 추가 + `display: block` 보장
- `.workspace-with-rail`:
  - 현재 `grid-template-columns: minmax(560px, 840px) minmax(430px, 520px); max-width: 1410px;`
  - 변경: 1280px 이하에서는 1-column 으로 떨어지도록 미디어쿼리 조정
  - 1080px breakpoint 의 `grid-template-columns: minmax(0, 1fr);` 는 이미 있으나 1080px 가 너무 좁음 → **1280px** 로 상향
- `.topbar`: `flex-wrap: wrap` 추가 (이미 status-stack 은 wrap 됨, h1 줄도 줄바꿈 허용)
- `.input-grid`: 720px 이하에서 1-column (이미 820px 에서 처리되지만, 입력 grid 만 별도로 720px breakpoint 보강)
- `.trace-rail-tabbar`: `flex-wrap: wrap` (탭이 많아지거나 badge 가 클 때 대비)
- 모든 grid container 에 `min-width: 0` 적용 보강 — Firefox/Chrome 의 grid item 기본 min-width 가 overflow 원인
- `.copy-field` (label.copy-field) 의 grid: 명시적으로 `grid-template-columns: minmax(0, 1fr)` 로 자녀 wrap 보장

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| `apps/frontend/src/App.tsx` | 라우트 매핑 변경 |
| `apps/frontend/src/components/layout/AppShell.tsx` | nav 단일화, mode prop 제거, isLoading prop 추가, global-progress 렌더 |
| `apps/frontend/src/features/compliance/steps/InputStep.tsx` | 버튼 spinner |
| `apps/frontend/src/features/compliance/steps/RedlineStep.tsx` | 버튼 spinner |
| `apps/frontend/src/features/compliance/steps/EvidenceStep.tsx` | 버튼 spinner |
| `apps/frontend/src/features/compliance/steps/RewriteStep.tsx` | 버튼 spinner (해당 시) |
| `apps/frontend/src/features/compliance/steps/ApprovalStep.tsx` | 4개 버튼 pendingAction 기반 spinner |
| `apps/frontend/src/styles.css` | spinner, global-progress, nav, character-count, breakpoint |
| `apps/frontend/tests/agent.spec.ts` | 라우트 변경에 맞춰 URL 수정 |

## 검증 계획

- `npm run build` 통과
- Headless Edge 로 스크린샷 캡처:
  - 기본 1400px: 좌측 nav 한글 5-step, 우측 rail 2 카드, 카운터 한 줄
  - 1100px (rail 이 panel 아래로 stack 되는 폭): 깨짐 없음
  - isLoading=true 상태에서 spinner 와 progress bar 확인 (코드의 default state 를 잠시 true 로 토글 후 원복하는 방식)
- 첫 step 의 "준법검토 시작" 버튼 클릭 시뮬레이션 → 잠깐의 isLoading 상태 캡처가 어려우면 위 방식으로 대체

## 롤백

각 파일별로 hunk 단위 revert 가능. Spinner 도 클래스 한 줄 toggle 이라 부작용 없음.
