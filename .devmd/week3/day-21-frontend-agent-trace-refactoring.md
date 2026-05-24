# Day 21 — Frontend Agent Trace UI Refactoring

## Goal

현재 Agent/legacy 승인 화면에서 심사자가 느끼는 불편을 줄인다. 특히 상단 바, 글자 크기, 레이아웃 배치, 버튼 클릭 후 로딩/비동기 상태, agent tool 사용 추적, 승인 결과 표현을 정리해서 "Agent가 무엇을 했고 사람이 무엇을 확정했는지" 한눈에 확인되도록 리팩터링한다.

핵심 문제:

- 승인 후 성공 메시지가 상단 notice에만 조용히 표시되어, 사용자가 스크롤을 직접 올려야 결과를 확인한다.
- `CONDITIONALLY_APPROVED` 같은 내부 enum이 심의 결과, trace 상세, action message에 그대로 노출된다.
- 최종 승인 화면의 CTA는 클릭 후 저장 중/저장 완료/실패 상태가 충분히 분명하지 않다.
- 오른쪽 rail에 검토 흐름, Agent 판단 흐름, 상세 정보가 모두 쌓여 있어 정보 우선순위가 약하다.
- 상단 바와 본문 카드의 글자 크기/밀도 차이가 커서 실제 심의 업무 화면보다 데모용 대시보드처럼 보인다.
- agent tool 사용 추적이 "진행 단계"와 "도구 호출/결과"를 분명히 구분하지 못한다.

## UX Principles

- 사람의 최종 행동은 화면 안에서 즉시 피드백한다. 승인/반려/수정 요청 버튼을 누르면 버튼 근처, 결과 배너, trace rail이 동시에 갱신되어야 한다.
- 사용자에게 보이는 문구는 업무 언어를 사용한다. 내부 enum, API field name, trace raw key는 상세 JSON을 펼쳤을 때만 보이게 한다.
- 비동기 요청은 최소 3단계로 드러낸다: `요청 중` → `완료` 또는 `실패` → `다음 행동`.
- Agent trace는 timeline이 아니라 감사 가능한 실행 기록이다. `관찰`, `도구 호출`, `도구 결과`, `판단`, `사람 확인`을 시각적으로 구분한다.
- 오른쪽 rail은 보조 정보다. 최종 판단과 버튼 피드백은 중앙 승인 패키지 안에서 먼저 확인 가능해야 한다.

## Decision Label Contract

프론트엔드는 내부 enum을 화면에 직접 출력하지 않는다.

```ts
const APPROVAL_DECISION_LABELS = {
  APPROVED: "승인",
  CONDITIONALLY_APPROVED: "조건부 승인",
  REJECTED: "반려",
  REVISION_REQUESTED: "수정 요청",
} as const;
```

적용 위치:

- 승인 배너: `심의 결과: 조건부 승인`
- 승인 완료 message: `조건부 승인으로 저장되었습니다.`
- trace rail 상세: `심의 결과가 조건부 승인으로 기록되었습니다.`
- 상세 정보 카드: `결정 조건부 승인`
- report/approval summary: 업무 문구 우선, raw enum은 개발자용 JSON 또는 audit payload에서만 노출

## Layout Refactoring

### Topbar

- 높이를 줄이고 정보 밀도를 정리한다.
- 현재 화면 제목, run 상태, fallback/API 상태를 한 줄에 배치한다.
- `Admin`, `API https://...`, `Fallback` chip은 우선순위를 낮춰 오른쪽 compact status group으로 묶는다.
- 성공/실패 notice는 topbar 아래 full-width로 계속 둘 수 있지만, 최종 승인 같은 주요 행동의 유일한 피드백이 되면 안 된다.

권장 구조:

```text
| 승인 패키지                         저장 완료 · 조건부 승인 | Admin | Fallback |
```

### Main Approval Panel

- 승인 결과 배너를 버튼 액션의 피드백 중심으로 사용한다.
- 버튼 클릭 전: `심의 결과: 조건부 승인 권고`
- 저장 중: `조건부 승인 저장 중...`
- 저장 완료: `심의 결과: 조건부 승인` + `방금 김준법 수석 이름으로 저장되었습니다.`
- 실패: `저장 실패` + 재시도 버튼

### Right Rail

오른쪽 rail은 3개 영역으로 축소하거나 접을 수 있게 한다.

- `검토 흐름`: 5-step 진행 상태만 표시
- `Agent 실행 기록`: tool call/tool result 중심 trace
- `상세 정보`: 선택된 step 또는 tool event 상세

`판단 상세`은 별도 카드로 계속 쌓기보다 `Agent 실행 기록`에서 선택한 항목의 detail panel로 합친다.

### Typography

- topbar h1: 22-24px
- section h2: 18-20px
- card title: 15-16px
- body: 14-15px
- metadata/chip: 12-13px
- 버튼: 13-14px, 높이 36-40px

긴 enum, URL, content id는 줄바꿈 가능한 chip 또는 monospace detail로 분리한다. 버튼 내부 텍스트는 줄바꿈 없이 유지한다.

## Button And Async States

승인/반려/수정 요청/리포트 확인 버튼은 독립 pending 상태를 가진다.

```ts
type PendingAction =
  | "approve"
  | "reject"
  | "request_revision"
  | "load_report"
  | undefined;
```

버튼 동작:

- 클릭한 버튼만 spinner/`저장 중` label을 표시한다.
- 다른 destructive/decision 버튼은 pending 동안 disabled 처리한다.
- 완료 후 버튼 row 위에 inline result bar를 표시한다.
- 완료 후 화면을 자동으로 승인 결과 배너 위치로 스크롤하거나, sticky action feedback을 사용한다.
- 상단 notice는 보조 기록으로 유지한다.

예시:

```text
[조건부 승인 저장 중...] [반려 disabled] [수정 요청 disabled] [리포트 확인]

조건부 승인으로 저장되었습니다. 리포트 패키지를 확인할 수 있습니다.
[리포트 확인]
```

## Agent Tool Trace

Agent trace는 사람이 "이 결론이 어떻게 나왔는지" 검증하는 영역이다.

이벤트 타입 표현:

- `thought`: 판단 준비, 회색/보라 계열, 짧은 요약만
- `tool_call`: 도구 호출, 파란색, tool name 강조
- `tool_result`: 도구 결과, 초록색 또는 neutral, count/status 강조
- `human_prompt`: 사람 확인 요청, amber
- `final`: 최종 결과, green
- `error`: 실패, red

도구별 친화 요약:

- `scan_rules`: `HIGH · 탐지 표현 3건`
- `search_regulations`: `근거 문서 3건 연결`
- `draft_rewrite`: `수정 포인트 3건 생성`
- `approval_report`: `조건부 승인 리포트 생성`

trace item 클릭 시:

- 기본 view: 업무 요약, 입력/출력 핵심 수치, 다음 행동
- "Raw JSON" toggle: payload 원문
- tool failure인 경우: 재시도 가능 여부, fallback 사용 여부

## Files

```text
apps/frontend/src/features/compliance/approvalDecisionLabels.ts      (NEW)
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx         (MOD)
apps/frontend/src/features/compliance/store.ts                       (MOD)
apps/frontend/src/features/compliance/components/ComplianceTraceRail.tsx (MOD)
apps/frontend/src/features/agent/components/TraceTimeline.tsx        (MOD)
apps/frontend/src/features/agent/components/StepDetailPanel.tsx      (MOD)
apps/frontend/src/components/layout/AppShell.tsx                     (MOD)
apps/frontend/src/styles.css                                         (MOD)
apps/frontend/tests/agent.spec.ts                                    (MOD)
.devmd/tools/agent-ui-smoke.mjs                                      (MOD)
```

## Tasks

### P0 — Enum Localization

- [x] `approvalDecisionLabels.ts` 추가.
- [x] `ApprovalStep`의 `state.approval?.decision` 직접 출력 제거.
- [x] `ComplianceTraceRail`의 approval detail, meta, judgment 문구에 label helper 적용.
- [x] `store.submitApproval`의 `actionMessage`를 `조건부 승인으로 저장되었습니다.` 형태로 변경.
- [x] report 관련 표시에서도 사용자 화면에는 한국어 label만 노출.

### P0 — Approval Feedback

- [x] `pendingAction` 상태를 추가해 클릭한 버튼의 요청 상태를 분리.
- [x] 승인 버튼 클릭 시 버튼 label을 `저장 중...`으로 변경.
- [x] 승인 완료 후 중앙 `decision-banner`에 완료 상태를 표시.
- [x] 버튼 row 위 또는 아래에 inline success/error result bar 추가.
- [x] 저장 완료 후 자동 스크롤이 필요하면 `decision-banner`로 `scrollIntoView({ block: "center" })`.
- [x] 실패 시 `승인 저장에 실패했습니다. 다시 시도해주세요.`와 재시도 가능 CTA 표시.

### P1 — Topbar And Notice

- [x] topbar h1, status chip, API chip 크기 조정.
- [x] success notice는 1줄 compact로 유지하되 주요 업무 결과의 유일한 피드백이 되지 않게 한다.
- [x] API URL이 긴 경우 max-width와 ellipsis 적용.
- [x] fallback badge는 API chip 옆에 붙이고 과도한 주황색 강조를 줄인다.

### P1 — Layout Density

- [x] 승인 패키지의 hero 영역 높이를 줄이고 reviewer/stamp를 compact 배치.
- [x] `package-grid` 카드의 title/body font hierarchy 정리.
- [ ] 오른쪽 rail card 간격과 height를 줄이고, 선택 상세는 하나의 detail 영역으로 통합 검토.
- [ ] 모바일/좁은 화면에서 rail이 본문 아래로 내려갈 때 승인 CTA가 먼저 보이도록 순서 조정.

### P1 — Agent Tool Trace

- [x] trace event type별 icon/color/token 정의.
- [ ] tool call/result pair가 같은 tool run으로 연결되어 보이도록 `tool_call_id` 또는 index 기반 grouping 적용.
- [x] `StepDetailPanel`에 도구별 summary renderer 추가.
- [x] raw payload는 접힌 상태가 기본.
- [ ] fallback/polling 상태를 trace header에 표시: `실시간 연결`, `polling fallback`, `연결 끊김`.

### P2 — Accessibility And Microcopy

- [x] 승인/반려/수정 요청 버튼에 `aria-busy`, `aria-disabled` 적용.
- [x] 저장 완료/실패 result bar에 `role="status"` 또는 `role="alert"` 적용.
- [x] trace item button에 선택 상태 `aria-pressed` 또는 `aria-current` 적용.
- [x] "승인" 버튼은 실제로 조건부 승인을 저장한다면 label을 `조건부 승인`으로 바꿀지 검토.

## Acceptance Criteria

- 승인 버튼 클릭 직후 버튼 또는 inline result area에서 요청 중임을 볼 수 있다.
- 승인 완료 후 스크롤을 올리지 않아도 중앙 승인 패키지 안에서 저장 완료를 확인할 수 있다.
- 사용자 화면에 `CONDITIONALLY_APPROVED`가 보이지 않는다.
- trace rail에는 agent tool 호출과 결과가 구분되어 보인다.
- tool 결과 상세는 업무 요약을 먼저 보여주고 raw JSON은 접어서 볼 수 있다.
- topbar의 긴 API URL이 레이아웃을 밀어내지 않는다.
- Playwright smoke가 승인 완료 문구 `조건부 승인으로 저장되었습니다.`를 검증한다.

## Test Plan

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
npm run test -- --project=chromium
```

Playwright 추가 검증:

- 승인 패키지 진입 후 `CONDITIONALLY_APPROVED` 텍스트가 화면에 없는지 확인.
- `조건부 승인` 버튼 클릭 후 `저장 중` 상태 확인.
- 저장 완료 후 viewport 안에 `조건부 승인으로 저장되었습니다.`가 보이는지 확인.
- trace panel에서 `도구 호출`, `도구 결과`, `사람 확인 요청` 항목이 구분되는지 확인.
- fallback mode에서도 동일 문구와 layout이 유지되는지 확인.

## Risks / Notes

- backend API enum은 유지한다. 변경 범위는 프론트엔드 표시 계층으로 제한한다.
- audit/report raw payload까지 한국어로 바꾸면 데이터 계약이 흔들릴 수 있으므로, 사람이 보는 summary와 raw payload를 분리한다.
- 승인 버튼 label을 `승인`으로 유지하면 실제 저장값인 `조건부 승인`과 차이가 생긴다. 데모 명확성을 우선하면 버튼 label도 `조건부 승인`으로 바꾸는 편이 낫다.
- 자동 스크롤은 사용자가 하단 문안을 읽는 중일 때 방해가 될 수 있다. 가능하면 inline/sticky feedback으로 먼저 해결하고, 스크롤은 저장 완료 배너가 viewport 밖일 때만 수행한다.

## Done When

- Day 21 agent trace UI와 legacy 승인 패키지 모두에서 내부 enum 노출이 사라진다.
- 승인 저장 결과가 버튼 주변과 결과 배너에서 즉시 확인된다.
- agent tool 사용 내역이 호출/결과/사람 판단으로 분리되어 심사자가 추적 가능하다.
- 상단 바와 오른쪽 rail이 화면을 압박하지 않고, 최종 승인 업무가 중앙에 또렷하게 남는다.
- lint/typecheck/build 및 agent UI smoke가 통과한다.

## Completion Log

- Status: PARTIAL DONE (2026-05-24)
- Completed:
  - 사용자 화면의 `CONDITIONALLY_APPROVED` 노출을 `조건부 승인`으로 치환.
  - legacy 승인 패키지에 pending action, 중앙 decision banner 완료 상태, inline success/error feedback 추가.
  - 조건부 승인 버튼 label과 저장 중 label을 업무 문구로 변경.
  - Agent trace timeline에 `도구 호출`, `도구 결과`, `사람 확인 요청` 타입 라벨 추가.
  - Agent step detail에 `scan_rules`, regulation search, rewrite tool 친화 요약 추가.
  - topbar/API/fallback chip과 승인 패키지 typography/density 조정.
  - Playwright config와 enum 노출 회귀 테스트 추가.
- Verification:
  - Docker Node temp workspace: `npm run typecheck` passed.
  - Docker Node temp workspace: `npm run lint` passed.
  - Docker Node temp workspace: `npm run build` passed.
  - Local backend + Playwright Docker: `npm run test:e2e -- --project=chromium` passed, 2 tests.
- Remaining:
  - tool call/result grouping by `tool_call_id` or paired index.
  - trace stream status chip: `실시간 연결`, `polling fallback`, `연결 끊김`.
  - right rail detail consolidation and mobile ordering pass.
