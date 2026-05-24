# Day 22 — Evaluation, Demo Freeze, Handover

## Goal

Day 15~21에서 만든 Agent 구현을 **심사위원이 보고 평가할 수 있는 형태**로 마무리한다. 코드 추가는 최소화하고, 시연 시나리오·평가 근거·문서·known issues에 시간을 쓴다.

이 날의 산출물 3가지:

1. **Evaluation scenarios**: 표준 risky/clean/edge 입력 셋에 대한 agent 행동 기록과 비교.
2. **Judging criteria fit document**: 대회 평가 항목(예상) vs 본 구현이 어떻게 대응하는지 매핑.
3. **Demo freeze + handover**: 안정 경로, 시연 스크립트, 다음 개발자 시작점.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md`
- `.devmd/week3/day-17-agent-runner.md`
- `.devmd/week3/day-21-frontend-agent-trace.md`
- `.devmd/week2/day-14-demo-freeze-handover.md` (Week 2 freeze 형식 재사용)
- `docs/demo/`, `docs/deployment/`, `docs/handover/`

## Files

```text
.devmd/week3/evaluation/scenarios.md                  (NEW)
.devmd/week3/evaluation/judging-criteria-fit.md       (NEW)
.devmd/week3/evaluation/agent-trace-samples/          (NEW dir)
docs/demo/agent-demo-script.md                        (NEW)
docs/demo/fallback-plan.md                            (MOD)
docs/deployment/README.md                             (MOD: agent endpoints, regulation cron)
docs/handover/README.md                               (MOD: week3 진행 결과, 다음 시작점)
README.md                                             (MOD: agent 진입점 안내)
.devmd/tools/agent-evaluation-runner.py               (NEW)
apps/backend/tests/test_agent_smoke_scenarios.py      (NEW)
```

## Tasks

### Evaluation scenarios

- [ ] `scenarios.md`에 입력 3종 + 기대 agent 행동 기록:
  1. **Standard risky**: `지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.`
     - 기대 tool 시퀀스: scan_rules → search_regulation → draft_rewrite → request_human_review → finalize_report (approve|revise).
  2. **Clean**: `본 상품은 시장 상황에 따라 손실이 발생할 수 있으며, 가입 전 상품설명서를 확인해 주세요.`
     - 기대: scan_rules → finalize_report (decision=approve, summary에 "risk_level=LOW").
  3. **Edge — partially risky**: `매월 5% 지급되는 안전한 상품` (짧고 모호).
     - 기대: scan_rules → search_regulation → request_human_review (추가 정보 요청) → resume → finalize_report.
- [ ] 각 시나리오에 대해 agent_runs/agent_steps payload를 JSON으로 저장 (`evaluation/agent-trace-samples/run-XX.json`). 실제 실행 또는 stub run.

### Evaluation runner

- [ ] `.devmd/tools/agent-evaluation-runner.py`:
  - 시나리오 JSON을 읽어 `POST /v1/agent/run` 자동 실행.
  - 결과 trace를 fixture와 비교 (tool 호출 sequence, final decision, risk_level).
  - PASS/FAIL 리포트 출력.
- [ ] `apps/backend/tests/test_agent_smoke_scenarios.py`: 같은 시나리오를 TestClient + Gemini stub으로 회귀 테스트.

### Judging criteria fit

- [ ] `judging-criteria-fit.md`에서 다음을 명시:
  - "Agent형 서비스" 명제 → `agent/runner.py` + tool registry + 함수 호출 loop 코드 위치.
  - "AI 규제 Agent가 최신 금융규제와 내부 기준을 자동으로 추적" → Day 19 ingestion + change tracking.
  - "콘텐츠 초안에 대해 규제 위반 가능성, 표현 리스크, 수정 제안을 자동으로 도출" → scan_rules + search_regulation + draft_rewrite.
  - "준법 관리자는 AI 결과를 검토·승인하는 역할 중심으로 전환" → request_human_review + frontend HumanReviewPanel.
  - "규칙 기반 판단과 LLM 판단을 결합" → scan_rules(rule) + Gemini analyze span merge + draft_rewrite(Gemini).
  - 각 항목에 코드 경로 / 파일명을 인용. 본 문서가 심사 시 "어디 보면 됩니까"의 답이 된다.

### Demo

- [ ] `docs/demo/agent-demo-script.md`:
  - 5분 시연 시나리오: 표준 risky 입력 → trace timeline 시연 → human review에서 "revise" 선택 → final report.
  - 백업 시나리오: Gemini 키 비활성 시 fallback agent 시연.
  - 시연 전 health check 순서 (Render warm-up).
- [ ] `docs/demo/fallback-plan.md` 갱신: agent run에서 Gemini/Supabase 미설정 시 fallback agent + in-memory trace 경로.

### Deployment / handover

- [ ] `docs/deployment/README.md`:
  - 신규 env: `ADMIN_API_TOKEN`, `AGENT_MAX_ITERATIONS`, `AGENT_DEADLINE_SECONDS`.
  - Render Cron Job: `python -m app.jobs.regulation_refresh --source all` (일 1회).
  - Vercel rewrite: agent SSE 경로가 통과하는지 확인.
- [ ] `docs/handover/README.md`:
  - Week 3 진행 결과 요약.
  - 다음 개발자가 시작할 지점: ① Week 4 multilingual support, ② RSS connector 실제 활성화, ③ approval → 마케팅 시스템 연계, ④ regulation diff summarization tool.
  - 미해결 known issues 목록.

### README

- [ ] 루트 `README.md`: agent run 진입점(`/v1/agent/run`, frontend `/`) 안내 추가. legacy wizard 별도 명시.

## Done When

- 3개 시나리오에 대해 agent_run trace가 fixture와 일치하거나 의도된 범위 안에 있다.
- `judging-criteria-fit.md`로 심사 시 5분 안에 평가 항목별 코드 위치를 보여줄 수 있다.
- `agent-demo-script.md`만 보고 demo 가능하다.
- `docs/handover/`로 다음 개발자가 Week 4 작업을 시작할 수 있다.
- 모든 backend/frontend test/lint/build가 통과한다.
- 공개 Render/Vercel smoke가 1회 이상 성공한다.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 90 .venv/bin/pytest -q
.venv/bin/python ../../.devmd/tools/agent-evaluation-runner.py --base-url http://localhost:8000

cd ../frontend
npm ci && npm run lint && npm run typecheck && npm run build

# 공개 smoke (Render 배포 후)
curl https://finance-safegrowth-agent.onrender.com/v1/health
curl -X POST https://finance-safegrowth-agent.onrender.com/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{"text":"표준 risky 입력 ..."}'
```

## Risks / Notes

- 평가 시 Gemini API quota 소진 위험. demo 직전 fallback path도 동작 확인.
- SSE는 Render Free tier에서 가끔 끊긴다. demo 시 polling fallback이 작동하는지 미리 확인.
- judging-criteria-fit 문서가 사실과 다르면 심사에서 가장 큰 감점 요인. 작성 후 day-17/day-18 코드와 1:1 대조 필수.
- agent_trace_samples는 평가용 fixture이므로 시드 데이터 변경 시 같이 갱신해야 한다.

## Completion Log

- Status: NOT_STARTED
- Implemented files: -
- Test commands executed: -
- Test result summary: -
- Public smoke: -
- Known issues: -
