# Day 21 — Frontend Agent Trace UI

## Goal

5-step wizard("사람이 단계마다 버튼을 눌러 진행")를 **agent run trace 뷰**("agent가 알아서 판단하고 사람은 검토·승인")로 재구성한다. 이 화면이 심사위원이 직접 보게 될 "Agent형 서비스"의 얼굴이다.

기존 5-step 화면은 `/legacy/wizard` 경로로 보존 (fallback demo, 회귀 검증용).

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §10
- `.devmd/week3/day-17-agent-runner.md` (`/v1/agent/*` API)
- `.devmd/mockup/` (있다면 agent run mockup. 없으면 이 문서의 와이어프레임 참조)

## Files

```text
apps/frontend/src/features/agent/api.ts                (NEW)
apps/frontend/src/features/agent/types.ts              (NEW)
apps/frontend/src/features/agent/store.ts              (NEW)
apps/frontend/src/features/agent/AgentRunPage.tsx      (NEW)
apps/frontend/src/features/agent/components/InputForm.tsx        (NEW)
apps/frontend/src/features/agent/components/TraceTimeline.tsx    (NEW)
apps/frontend/src/features/agent/components/StepDetailPanel.tsx  (NEW)
apps/frontend/src/features/agent/components/HumanReviewPanel.tsx (NEW)
apps/frontend/src/features/agent/components/FinalReportPanel.tsx (NEW)
apps/frontend/src/features/agent/hooks/useAgentRunStream.ts      (NEW)
apps/frontend/src/App.tsx                              (MOD: routes /, /legacy/wizard)
apps/frontend/src/components/layout/AppShell.tsx       (MOD: nav 항목 추가)
apps/frontend/src/styles.css                           (MOD)
.devmd/tools/agent-ui-smoke.mjs                        (NEW: Playwright smoke)
apps/frontend/tests/agent.spec.ts                      (NEW, Playwright)
```

기존 `features/compliance/*`는 손대지 않는다. legacy로 그대로 노출.

## Tasks

### Routing

- [x] `App.tsx`를 `react-router` 또는 단순 hash 라우터 기반으로 변경.
  - `/`: AgentRunPage (기본)
  - `/legacy/wizard`: 기존 ComplianceWizard
 - `/admin/regulations`: Day 19에서 만든 admin API용 간단 페이지(선택, P2)
- [x] AppShell 사이드바에 두 항목 노출. legacy는 "구버전 5-step 검토".

### API & types

- [x] `agent/types.ts`: backend `schemas/agent.py`와 1:1 대응.
- [x] `agent/api.ts`:
  - `startAgentRun(req)`, `getAgentRun(runId)`, `respondAgentRun(runId, body)`, `cancelAgentRun(runId)`.
  - `subscribeAgentStream(runId, onEvent)`: EventSource. 실패 시 1s polling fallback (`getAgentRun`).

### State

- [x] `agent/store.ts` (Zustand 또는 기존 패턴):
  - `currentRunId`, `runDetail`, `streamStatus`, `humanPrompt`, `error`.
  - actions: `start`, `respond`, `cancel`, `reset`.

### Layout (와이어프레임)

```text
+--------------------------------------------------------------+
| Compliance AI · Agent Run                                    |
+--------------------------------------------------------------+
| [Input form ▼ collapsed once run starts]                     |
+----------------------+---------------------------------------+
| Trace timeline       | Detail panel                          |
| (left, narrow)       | (right, wide)                         |
|                      |                                       |
| ● 14:02 thought      | ▌ scan_rules                          |
| ● 14:02 scan_rules   | input  : { text: "..." }              |
| ● 14:02 result HIGH  | output : { spans: [...], risk: HIGH } |
| ● 14:03 search_reg.  |                                       |
| ● 14:03 result 3 ev. |                                       |
| ● 14:03 draft_rewrt  |                                       |
| ● 14:03 result 2안   |                                       |
| ◐ 14:03 human review |                                       |
|                      | [ HumanReviewPanel: 승인 / 거절 / 추가지시 ] |
|                      |                                       |
+----------------------+---------------------------------------+
| Run status: awaiting_human · tokens 1.4k in / 0.8k out       |
+--------------------------------------------------------------+
```

`thought` step과 `tool_call/tool_result` 페어는 다른 아이콘으로 구분. `human_prompt`는 amber, `final`은 green.

### Components

- [x] `InputForm`: 텍스트, 채널, 제품, 언어 입력. submit 시 `start({text, ...})`.
- [x] `TraceTimeline`: SSE 이벤트 누적, step 클릭 시 선택.
- [x] `StepDetailPanel`: 선택 step의 raw payload(JSON viewer)와 도구별 친화적 요약(예: scan_rules는 risk badge + span chip list).
- [x] `HumanReviewPanel`: agent의 `request_human_review` 응답. 옵션 버튼 또는 자유 텍스트 입력. submit → `respond(runId, { response })`.
- [x] `FinalReportPanel`: agent `final` step 도착 시 표시. 기존 report payload의 최종 문안, evidence 수, 결정 배지 표시.

### Streaming

- [x] `useAgentRunStream(runId)`: EventSource open + polling fallback으로 동일 run detail을 갱신.

### Legacy 보존

- [x] `/legacy/wizard`에서 기존 5-step 화면이 그대로 동작하도록 보존.
- [x] AppShell에 toggle. demo fallback 가이드(`docs/demo/fallback-plan.md`)에 legacy 경로 안내 추가(Day 21에서).

### Tests

- [x] Playwright smoke `.devmd/tools/agent-ui-smoke.mjs`:
  - input 입력 → submit → trace timeline에 step ≥ 4개 도착 → human review panel 표시 → "승인" 클릭 → final report 표시.
  - mock backend 사용 또는 실제 backend (Gemini stub) 사용.
- [x] `agent.spec.ts`: 위 시나리오를 Playwright assertion으로 분해.

## Done When

- `/` 진입 → 표준 데모 문장 입력 → agent run이 timeline에 실시간으로 그려진다.
- `request_human_review` 단계에서 승인/거절 UI가 표시되고, 응답 후 final report까지 도달한다.
- backend Gemini 미설정 환경에서도 fallback agent run trace가 동일 UI에 표시된다 (`source: fallback_agent` 배지).
- `/legacy/wizard`에서 기존 5-step 흐름이 동작한다.
- Playwright smoke 통과, lint/typecheck/build 통과.

## Test Harness

```bash
cd apps/frontend
npm ci
npm run lint
npm run typecheck
npm run build

# 로컬 backend + agent UI smoke
# (backend는 별도 터미널에서 uvicorn 실행)
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e VITE_API_BASE_URL=http://host.docker.internal:8000 \
  -e FRONTEND_URL=http://host.docker.internal:5173 \
  -v /tmp/dacon-day20-frontend:/app -w /app \
  mcr.microsoft.com/playwright:v1.60.0-noble \
  sh -c "npm ci && node .devmd/tools/agent-ui-smoke.mjs"
```

## Risks / Notes

- SSE는 브라우저에서는 별다른 폴리필 없이 동작하지만 Render Free tier에서 끊김이 잦으면 polling fallback이 실제 경로가 된다. 두 경로 모두 시각적으로 동일하게 동작해야 한다.
- JSON viewer 의존성을 새로 도입하지 말고 `pre` + 색상 코드로 충분히 구현. 번들 크기 관리.
- `request_human_review`의 options/proposed_action UI 변형(객관식 vs 자유 입력)을 한 컴포넌트로 처리. backend 응답 schema가 둘 다 허용한다는 점 주의.
- legacy wizard를 살려둠으로써 회귀 안전망이 생기지만, demo 시 "둘 다 동작하는" 모습이 심사 혼란을 낳을 수 있다. 메인 페이지가 agent run임을 분명히 보여주고 legacy는 사이드바에 작은 항목으로만.

## Completion Log

- Status: DONE (2026-05-24)
- Implemented files:
  - `apps/frontend/src/features/agent/*`
  - `apps/frontend/src/App.tsx`
  - `apps/frontend/src/components/layout/AppShell.tsx`
  - `apps/frontend/src/styles.css`
  - `apps/frontend/src/features/compliance/*` UX feedback refinements
  - `apps/frontend/package.json`
  - `apps/frontend/package-lock.json`
  - `.devmd/tools/agent-ui-smoke.mjs`
  - `apps/frontend/tests/agent.spec.ts`
  - `docs/demo/fallback-plan.md`
- Test commands executed:
  - `docker run --rm ... npm ci && npm run lint && npm run typecheck && npm run build`
  - `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
  - `docker run --rm --add-host=host.docker.internal:host-gateway ... node /tmp/app/agent-ui-smoke.mjs`
- Test result summary:
  - Frontend lint/typecheck/build passed in Docker.
  - Agent UI smoke passed: input → run trace → human approval → final report.
- Follow-up UX updates:
  - Redline risk pagination now shows multiple cards per page instead of one-card paging.
  - Evidence cards were compacted for denser scanning when many references exist.
  - Legacy 5-step wizard now includes a right-side Trace/detail rail using the available horizontal workspace.
  - The right rail now separates workflow progress from Agent judgment flow, showing observation → decision → next action.
- Known issues:
  - npm audit reports existing dependency vulnerabilities in the frontend dependency tree.
  - `/admin/regulations` remains optional P2 follow-up and was not added in this slice.
