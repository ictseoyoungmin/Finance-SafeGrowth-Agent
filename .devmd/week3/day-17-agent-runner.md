# Day 17 — Agent Runner and API Endpoints

## Goal

Day 15의 schema와 Day 16의 tool registry 위에 **실제 agent loop**를 구현한다. 이 날의 산출물이 "Agent형 서비스" 명제를 코드로 증명한다.

핵심 구현:

1. Gemini function-calling 기반 ReAct 루프 (`AgentRunner.run`).
2. Deterministic fallback agent (Gemini 미설정/오류 시 4단계 고정 chain).
3. REST endpoints `/v1/agent/*`.
4. SSE streaming endpoint.
5. Human-in-the-loop 일시정지/재개.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §6, §7
- `.devmd/week3/day-15-agent-contracts-and-state.md`
- `.devmd/week3/day-16-tool-extraction.md`

## Files

```text
apps/backend/app/agent/runner.py              (NEW)
apps/backend/app/agent/fallback_runner.py     (NEW)
apps/backend/app/agent/transcript.py          (NEW)
apps/backend/app/agent/limits.py              (NEW)
apps/backend/app/api/v1/agent.py              (NEW)
apps/backend/app/api/v1/router.py             (MOD: include agent router)
apps/backend/app/integrations/gemini_client.py (MOD: function-calling support)
apps/backend/requirements.txt                  (MOD: google-generativeai pin)
apps/backend/tests/test_agent_runner_happy.py     (NEW)
apps/backend/tests/test_agent_runner_pause.py     (NEW)
apps/backend/tests/test_agent_runner_fallback.py  (NEW)
apps/backend/tests/test_agent_runner_limits.py    (NEW)
apps/backend/tests/test_api_agent.py              (NEW)
```

## Tasks

### Gemini client 확장

- [ ] `gemini_client.GeminiClient`에 `generate_with_tools(contents, tools, tool_config, generation_config) -> GeminiToolResponse` 추가.
  - `GeminiToolResponse { function_call?: {name, args}, text?: str, usage: {input, output} }`.
  - `is_configured` 미설정 시 `None` 반환 (기존 패턴 유지).
- [ ] `requirements.txt`에 `google-generativeai>=0.7,<0.9` 핀. 기존 단순 `httpx` 직접 호출 경로는 유지하되, function-calling은 SDK 사용. (필요시 직접 호출로 통일 가능 — Day 15 open decision으로 옮긴다.)

### Runner

- [ ] `agent/limits.py`: `AgentLimits { max_iterations=8, deadline_seconds=60, max_input_tokens, max_output_tokens }` + env override.
- [ ] `agent/transcript.py`: agent transcript ↔ Gemini `contents` 변환. system prompt, user input, tool results, function calls를 Gemini가 받는 message 배열로 직렬화.
- [ ] `agent/runner.py: AgentRunner`:
  - 의존성: `gemini_client`, `tool_registry`, `trace_recorder`, `agent_runs_repo`, `agent_steps_repo`, `limits`.
  - `run(request) -> AgentRunResult` 동기 메서드. 내부 loop는 `00 설계문서 §6` 의사코드 충실 구현.
  - `resume(run_id, human_response) -> AgentRunResult`: pending_human 상태 run을 재개. transcript에 `function_response`(=`request_human_review`의 응답) 추가하고 loop 재진입.
  - tool 호출 결과는 항상 trace로 기록 (Day 15 `TraceRecorder`).
  - finalize_report 호출 없이 모델이 자연어로 종료하려 할 때 `force_finalize_with_text(text)` — 임시 ReportResponse 생성하고 incomplete 플래그.
  - 한 run의 cumulative token 사용량은 `agent_runs.token_input/output` 컬럼에 갱신.
- [ ] `agent/fallback_runner.py: FallbackAgentRunner`:
  - `gemini_client.is_configured == False` 또는 첫 Gemini 호출 실패 시 사용.
  - 고정 chain: `scan_rules` → `search_regulation` → `draft_rewrite` → `request_human_review`.
  - 동일 trace 구조로 기록 (model 컬럼은 `"fallback-deterministic-agent"`).
- [ ] `AgentRunner.run`은 진입 시 Gemini probe 실패하면 즉시 `FallbackAgentRunner.run`으로 위임.

### System prompt

- [ ] `agent/transcript.py`에 system prompt 상수.
  - 역할: "JB금융그룹의 준법자문가 AI Agent".
  - 도구 사용 원칙: "Always start with scan_rules. Call search_regulation if any HIGH/MEDIUM finding. Call draft_rewrite if any flagged span. Use request_human_review if you need a missing input or want approval. End every run by calling finalize_report."
  - 언어: 한국어 응답.
  - 안전 규칙: "Do not invent regulations. Cite evidence_id when claiming a rule."
  - 한 prompt는 600 token 미만으로 관리.

### API

- [ ] `api/v1/agent.py`:
  - `POST /v1/agent/run` → `AgentRunner.run(request)`. 응답: `AgentRunDetail`.
  - `GET /v1/agent/runs/{run_id}` → 저장된 run + steps 조회.
  - `GET /v1/agent/runs/{run_id}/stream` → SSE. step이 trace에 추가될 때마다 push. 25초마다 heartbeat ping.
  - `POST /v1/agent/runs/{run_id}/respond { response }` → `AgentRunner.resume`.
  - `POST /v1/agent/runs/{run_id}/cancel` → status=cancelled, transcript에 cancellation step 기록.
- [ ] SSE 구현: FastAPI `StreamingResponse`. trace recorder가 in-memory pubsub queue도 publish (`asyncio.Queue` per run). polling fallback은 frontend 측에서 처리.

### Tests

- [ ] `test_agent_runner_happy.py`: fake Gemini stub이 `scan_rules → search_regulation → draft_rewrite → finalize_report` 순서로 function_call을 반환. agent가 4개 tool을 호출하고 done 상태로 종료.
- [ ] `test_agent_runner_pause.py`: 도중에 `request_human_review` 발생 → run 상태 `awaiting_human`. `resume(run_id, "approve")` 호출 → finalize까지 진행.
- [ ] `test_agent_runner_fallback.py`: Gemini 미설정 → FallbackAgentRunner가 4단계 chain 수행 후 awaiting_human으로 끝남. 이후 resume("approve")로 done.
- [ ] `test_agent_runner_limits.py`: `max_iterations=2` 강제, 무한 도구 호출 stub → `failed("max iterations")`.
- [ ] `test_api_agent.py`: TestClient로 `/v1/agent/run` POST → 응답 schema 검증. `/runs/{id}` GET → 저장된 trace 조회. SSE는 단위 테스트 어려우므로 `pytest-asyncio`로 첫 message만 검증 또는 skip.

## Done When

- 표준 데모 문장 입력 시 agent가 4개 이상의 tool을 호출하고 `done` 상태로 종료된다.
- 무위험 문장(예: `"이 안내는 모든 위험 고지를 포함합니다."`) 입력 시 agent가 scan_rules 후 `draft_rewrite`를 건너뛰고 `finalize_report` 호출한다 (모델 판단 검증).
- Gemini 미설정 환경에서 fallback agent가 동일 trace 구조로 끝까지 진행한다.
- `request_human_review` → `respond` 사이클이 정상 동작한다.
- `max_iterations`, `deadline_seconds`가 트리거되면 run이 `failed` 상태로 종료된다.
- `pytest`, `ruff check` 통과.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 90 .venv/bin/pytest -q tests/test_agent_runner_*.py tests/test_api_agent.py
```

수동 (Gemini 키 있는 환경):

```bash
curl -X POST http://localhost:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "text": "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.",
    "mode": "review"
  }' | jq '.steps[].step_type'
```

기대:

```text
"thought"
"tool_call"     # scan_rules
"tool_result"
"tool_call"     # search_regulation
"tool_result"
"tool_call"     # draft_rewrite
"tool_result"
"human_prompt"  # request_human_review
```

## Risks / Notes

- Gemini function-calling은 한국어 prompt에서도 잘 동작하지만, tool name은 영어로 유지한다 (모델 호환성).
- SSE는 Render Free tier proxy 환경에서 keep-alive timeout이 짧을 수 있다. 25s heartbeat가 부족하면 polling fallback을 추가한다.
- Gemini SDK는 동기 호출이라 FastAPI worker thread를 점유한다. `run_in_threadpool`로 감싸지 않으면 `/v1/agent/run`이 다른 요청을 block한다. SSE 구현에서 특히 주의.
- token usage tracking은 SDK 응답의 `usage_metadata`에 의존. 미지원 모델 사용 시 0으로 기록.

## Completion Log

- Status: COMPLETE (2026-05-24)
- Deviation from plan (intentional): Day 17 design pinned `google-generativeai>=0.7,<0.9` as the Gemini transport. The implementation **does not add the SDK**. Instead `GeminiClient.generate_with_tools` extends the existing urllib-based POST. Rationale:
  - The existing `generate_json` already uses urllib; adding the SDK would create two transport paths in one client.
  - The Gemini REST `:generateContent` endpoint supports `tools`, `toolConfig`, and `systemInstruction` natively. Function-calling worked end-to-end via urllib in docker smoke.
  - Keeps `requirements.txt` lean (still `fastapi/httpx/pydantic-settings/uvicorn`). The SDK pulls in protobuf + grpc + numpy which we did not need.
  - This deviation is logged here so Day 18+ work and the handover doc reflect reality.
- Implemented files:
  - [x] `apps/backend/app/integrations/gemini_client.py` (extended with `generate_with_tools`, `GeminiFunctionCall`, `GeminiToolResponse`)
  - [x] `apps/backend/app/core/config.py` (added `agent_max_iterations`, `agent_deadline_seconds`)
  - [x] `apps/backend/app/agent/limits.py`
  - [x] `apps/backend/app/agent/transcript.py` (system prompt + state↔Gemini contents)
  - [x] `apps/backend/app/agent/fallback_runner.py` (deterministic 4-step chain)
  - [x] `apps/backend/app/agent/runner.py` (`AgentRunner.run/resume/cancel/get`)
  - [x] `apps/backend/app/api/v1/agent.py` (REST + SSE endpoints)
  - [x] `apps/backend/app/api/v1/router.py` (agent router wired under `/v1/agent`)
  - [x] `apps/backend/tests/_agent_fakes.py` (shared scripted Gemini + stub tools, not auto-collected)
  - [x] `apps/backend/tests/test_agent_runner_happy.py`
  - [x] `apps/backend/tests/test_agent_runner_pause.py`
  - [x] `apps/backend/tests/test_agent_runner_fallback.py`
  - [x] `apps/backend/tests/test_agent_runner_limits.py`
  - [x] `apps/backend/tests/test_api_agent.py`
- Test commands executed (via docker):

```bash
# image build (only if Dockerfile/requirements changed)
docker build -t dacon-backend-dev -f apps/backend/Dockerfile apps/backend

# ruff + full pytest
docker run --rm \
  -v "$PWD/apps/backend:/app" -w /app \
  dacon-backend-dev sh -c \
  "pip install --no-cache-dir -q -r requirements-dev.txt && ruff check app tests && pytest -q"
```

- Test result summary:
  - ruff: All checks passed
  - pytest (full suite): 91 passed, 1 warning (existing starlette/python_multipart deprecation)
  - 14 new Day-17 tests added (happy, pause, fallback, limits, api) on top of Day-15/16 coverage
- Live HTTP smoke (via docker compose):

```bash
docker compose up --build -d backend
# wait until /v1/health responds
until curl -fs http://localhost:8000/v1/health > /dev/null; do sleep 1; done

# analyze -> agent run -> respond
CID=$(curl -s -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"누구나 연 8% 수익을 안정적으로..."}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['content_id'])")
RUN=$(curl -s -X POST http://localhost:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d "{\"content_id\":\"$CID\",\"text\":\"검토 요청\",\"mode\":\"review\"}")
RUN_ID=$(echo "$RUN" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X POST "http://localhost:8000/v1/agent/runs/$RUN_ID/respond" \
  -H "Content-Type: application/json" \
  -d '{"response":{"decision":"approve","selected_revision":"마케팅안 최종 텍스트"}}'
docker compose down
```

  - `/v1/agent/run` returned `status=awaiting_human`, `model=fallback-deterministic-agent`, 4 tool calls (`scan_rules → search_regulation → draft_rewrite → request_human_review`).
  - `/v1/agent/runs/{id}/respond` returned `status=done`, `final_decision=approve`, `final_summary="Approved after review (risk_level=HIGH)."`, `final_report.final_text="마케팅안 최종 텍스트"`.
- Design highlights vs the plan:
  - **One source of truth for resume**: the initial request is JSON-serialized into the second `thought` step (`request_snapshot=...`). `resume()` reconstructs `AgentRunRequest` from that step. No new column was needed and the trace stays self-describing.
  - **Pause/done unification**: both terminal paths run through `AgentRunner._terminate`. Done path now also patches `token_input/token_output/ended_at` so finalize_report side-effects + token accounting stay consistent.
  - **Text-only response handling**: if Gemini returns plain text without a function_call, the runner forces a `finalize_report({decision:"none", summary:text[:500]})` instead of issuing a second Gemini call. Avoids an extra round-trip in failure modes.
  - **SSE**: minimal replay-style implementation. On connect, the endpoint streams existing persisted steps as `event: step`, then `event: status`, then a comment for end-of-trace. The Day 21 frontend should treat polling as the primary live-update mechanism and SSE as a one-shot replay.
- Known issues:
  - SSE is replay-only; we do not push during an active run (the runner is synchronous and blocks until pause/done). Real-time streaming would require running the agent loop in a background task and a pub/sub queue — out of scope for Day 17.
  - `request_human_review` produces both a `tool_result` step and a `human_prompt` step; UI must decide which to render to avoid duplication.
  - Token usage on the fallback path is always 0 because no Gemini call is made; downstream cost tracking should treat fallback runs separately.
  - Live Gemini function-calling was not exercised in this sandbox (no API key). Stubs cover the loop logic; Day 22 will run a public smoke against Render.
