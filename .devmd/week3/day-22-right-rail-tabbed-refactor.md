# Day 22 — Right Rail Tabbed Refactor (Option A)

## 배경

`LegacyWizard` (`apps/frontend/src/App.tsx`) 의 우측 `ComplianceTraceRail` 은 현재 4개의 카드를 2×2 그리드로 띄운다.

| 위치 | 카드 | 내용 |
| --- | --- | --- |
| 좌상 | 검토 흐름 | 5-step 워크플로우 진행 상태 (콘텐츠 입력 → 승인 패키지) |
| 우상 | Agent 판단 흐름 | Agent 5-step 추론 (문맥 구성 → 사람 판단 요청) |
| 좌하 | 상세 정보 | 검토 흐름에서 선택된 step 의 메타 |
| 우하 | 판단 상세 | 판단 흐름에서 선택된 step 의 관찰/판단/다음 행동 |

두 쌍이 시각적으로 거울처럼 마주 보고 있어 **"같은 정보가 중복"** 으로 보인다. 실제로는 의미가 다르지만 (시스템 파이프라인 vs Agent 추론), UI 가 그 차이를 전달하지 못한다.

대화에서 사용자는 **Option A — 탭 전환** 으로 가기로 결정.

## 목표

- 우측 패널을 4 카드 → **2 카드 (각각 탭 2개)** 로 축소
- 두 흐름의 의미 차이를 탭 라벨로 명확히 전달
- 기존 데이터/로직 (`buildTraceItems`, `buildJudgmentItems`) 은 그대로 두고 **표현만 재배치**
- 기능 손실 없음: 모든 step 클릭/선택 동작 유지

## Non-goals

- Agent 5-step 을 검토 5-step 하위 sub-step 으로 묶는 **계층화** (이건 더 큰 IA 변경이라 별도 작업)
- `AgentRunPage` (`/`) 쪽 UI 는 손대지 않음 — 이번 작업은 `/legacy/wizard` 에 한정
- 새로운 디자인 토큰/컴포넌트 라이브러리 도입 없음

## 새 화면 구성

```
┌────────────────────────────────────────────┐
│  [ 검토 흐름 ]  [ Agent 판단 ]      🟦 진행 중│   <- Flow card (tabs)
│ ─────────────────────────────────────────  │
│  ① 콘텐츠 입력         (검토 흐름 활성 시)   │
│  ② 리스크 분석                              │
│  ③ 근거 매칭                                │
│  ④ 수정안 생성                              │
│  ⑤ 승인 패키지                              │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  [ 단계 상세 ]  [ 판단 상세 ]       🟦 진행 중│   <- Detail card (tabs)
│ ─────────────────────────────────────────  │
│  콘텐츠 입력                                 │
│  투자상품 · 앱 푸시 · 30대 직장인            │
│  ┌─문자수 59─┐  ┌─언어 KO─┐                 │
│  └──────────┘  └─────────┘                  │
└────────────────────────────────────────────┘
```

- 두 카드 모두 **세로로 stacked** (1-column).
  - 현재의 2-column 2×2 그리드는 카드가 좁아 가독성이 떨어졌고, 탭으로 통합하면 카드 수가 줄어 세로 stacked 가 자연스럽다.
  - 모바일 breakpoint (`@media max-width: 820px/1080px`) 는 이미 1-column 으로 떨어지므로 추가 작업 거의 없음.

### 탭 동작

- 두 카드의 탭 상태는 **독립적**으로 관리 (Flow 탭 ↔ Detail 탭 자동 동기화 안 함).
  - 이유: 사용자가 "검토 흐름을 보면서 Agent 판단 상세"를 보고 싶은 케이스를 막지 않기 위해.
  - 단, **첫 진입 시 기본값**은 양쪽 모두 좌측 탭 (검토 흐름 / 단계 상세) 로 동기화.
- 탭 클릭은 표시 내용만 바꿈. 기존 `selectedId`, `selectedJudgmentId` state 는 그대로 유지.

### Header 의 상태 pill

- Flow 카드: 현재 활성 탭에 맞춰 pill 갱신
  - 검토 흐름 탭 → `currentItem.status` 기반
  - Agent 판단 탭 → `currentJudgment.status` 기반
- Detail 카드: 동일하게 활성 탭의 selected 항목 status 기반 (단계 상세 탭은 별도 pill 없이도 OK — 현재 디자인 따라감)

## 구현 계획

### 1. `ComplianceTraceRail.tsx` 리팩토링

- 기존 4 `<section className="trace-rail-card">` 블록을 **두 개의 `<TabCard>`** 로 묶는다.
- 새 로컬 컴포넌트 (같은 파일에 인라인) 도입:
  ```tsx
  type TabKey = string;
  interface TabSpec {
    key: TabKey;
    label: string;
    badge?: ReactNode;     // 오른쪽 status pill 같은 것
    content: ReactNode;
  }
  function TabCard({ tabs, activeKey, onChange, className }: { ... }) { ... }
  ```
- `useState<TabKey>` 를 두 개 추가:
  - `flowTab`: `"workflow" | "judgment"` (default `"workflow"`)
  - `detailTab`: `"step" | "judgment"` (default `"step"`)
- 기존 `selectedId` / `selectedJudgmentId` 로직은 손대지 않음.
- 클릭 핸들러 동작은 그대로 (검토 흐름 step 클릭 시 `goTo`, 판단 step 클릭 시 selection 만 변경).

### 2. CSS 추가 (`apps/frontend/src/styles.css`)

기존 클래스 (`.legacy-trace-item`, `.agent-judgment-item`, `.judgment-detail-list`, `.trace-detail-copy`, `.trace-meta-grid`) 는 **그대로 재사용**. 새로 추가할 것:

```css
.trace-rail-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0;
}

.trace-rail-tab {
  padding: 8px 14px;
  border: 0;
  background: transparent;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 800;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.trace-rail-tab.is-active {
  color: var(--blue);
  border-bottom-color: var(--blue);
}

.trace-rail-tab:hover:not(.is-active) {
  color: #0f172a;
}

/* Rail layout: 2-column → 1-column stacked */
.compliance-trace-rail {
  grid-template-columns: minmax(0, 1fr);
}
```

- 그리드를 1-column 으로 바꾸면 1080px / 820px 미디어쿼리도 자동으로 호환.
- `.agent-judgment-card` 의 배경 그라데이션은 **탭 안에 들어가도 유지**할지 결정: 일관성을 위해 제거하고 동일한 카드 스타일로 통일.

### 3. 동작 검증

- `npm run build` 가 통과해야 함 (TypeScript)
- `/#/legacy/wizard` 로 진입해 다음 확인:
  - 두 카드만 보이고 각 카드 헤더에 탭 2개
  - Flow 탭 전환 시 검토 흐름 ↔ Agent 판단 리스트 토글
  - Detail 탭 전환 시 단계 상세 ↔ 판단 상세 토글
  - 검토 흐름의 step 을 클릭하면 화면이 해당 step 으로 이동
  - 판단 step 클릭은 Detail 카드의 판단 상세 내용만 갱신 (페이지 이동 X)

## 영향 범위

- 변경: `apps/frontend/src/features/compliance/components/ComplianceTraceRail.tsx`, `apps/frontend/src/styles.css`
- 영향 없음: 백엔드, `AgentRunPage`, store, types
- 테스트: 기존 Playwright 테스트 (`apps/frontend/tests/agent.spec.ts`) 는 `/` (AgentRunPage) 만 대상이라 영향 없음

## 롤백

`ComplianceTraceRail.tsx` 와 `styles.css` 의 해당 hunk 만 revert 하면 즉시 원복 가능. 새 컴포넌트/타입을 외부에 export 하지 않음.
