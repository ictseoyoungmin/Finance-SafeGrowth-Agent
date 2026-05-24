# Day 15 — Agent Contracts and State Schema

## Goal

Week 3 작업의 토대를 만든다. Agent runner/tool/trace의 **계약(스키마와 시그니처)**을 먼저 확정하고, 그 위에 코드와 DB 마이그레이션을 얹는다. 이 날의 산출물이 흔들리면 Day 16~21의 모든 코드가 흔들린다.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §3, §4, §5
- `apps/backend/app/schemas/`
- `infra/supabase/schema.sql`

## Files

```text
apps/backend/app/schemas/agent.py              (NEW)
apps/backend/app/schemas/tools.py              (NEW)
apps/backend/app/agent/__init__.py             (NEW)
apps/backend/app/agent/state.py                (NEW)
apps/backend/app/agent/trace.py                (NEW)
apps/backend/app/repositories/agent_runs_repo.py     (NEW)
apps/backend/app/repositories/agent_steps_repo.py    (NEW)
infra/supabase/migrations/2026-05-25_agent_tables.sql (NEW)
apps/backend/tests/test_agent_schemas.py       (NEW)
apps/backend/tests/test_agent_trace.py         (NEW)
```

기존 파일 수정은 이날 거의 없다. Day 16에서 service → tool 추출 시 본격적으로 손댄다.

## Tasks

- [ ] §14 open decisions 4건을 확정하고 `00-architecture-and-agent-design.md` 본문에 역반영한다.
- [ ] `schemas/agent.py`에 다음 Pydantic 모델을 정의한다.
  - `AgentRunRequest { content_id?: UUID, text?: str, mode: Literal["review","rewrite_only","explain"], user_message?: str }`
  - `AgentStepType = Literal["thought","tool_call","tool_result","human_prompt","human_response","final"]`
  - `AgentStep { run_id, step_index, step_type, tool_name?, payload }`
  - `AgentRunStatus = Literal["running","awaiting_human","done","failed","cancelled"]`
  - `AgentRunSummary { id, status, started_at, ended_at?, content_id?, final_decision?, final_summary? }`
  - `AgentRunDetail = AgentRunSummary + steps: list[AgentStep] + pending_human?: HumanPrompt`
  - `HumanPrompt { question, options?, proposed_action? }`
  - `AgentFinal { decision: Literal["approve","reject","revise","none"], selected_revision?: str, summary, report?: ReportResponse }`
- [ ] `schemas/tools.py`에 각 도구 입출력 모델을 정의한다 (도구 6종, §4 표 참조).
- [ ] `agent/state.py`에 dataclass `AgentState`, helper `init_state`, `time_exceeded`, `build_transcript` skeleton 추가 (실제 transcript 생성은 Day 17).
- [ ] `agent/trace.py`에 `TraceRecorder` 인터페이스를 정의. `record_thought/record_tool_call/record_tool_result/record_human_prompt/record_human_response/record_final` 6개 메서드. 구현체 2개: `InMemoryTraceRecorder`, `SupabaseTraceRecorder`. 둘 다 동일 인터페이스.
- [ ] `repositories/agent_runs_repo.py`, `agent_steps_repo.py` 작성. `FALLBACK_AGENT_RUNS`, `FALLBACK_AGENT_STEPS` 모듈 변수. Supabase 미설정 시 자동 fallback (`integrations/supabase_client.SupabaseClient.is_configured` 패턴 유지).
- [ ] `infra/supabase/migrations/2026-05-25_agent_tables.sql` 작성. §5.2 SQL 그대로 + 권한 grant.
  - `grant select, insert, update on table agent_runs to service_role, authenticated, anon`
  - `agent_steps`도 동일. (기존 day-09~10 grant 패턴 따름)
- [ ] `tests/test_agent_schemas.py`: enum 정합성, required 필드, JSON round-trip.
- [ ] `tests/test_agent_trace.py`: InMemoryTraceRecorder write → read 일치, step_index monotonic 증가, Supabase recorder는 fake client로 인서트 호출 검증.

## Open decisions to close on Day 15

§14 4건 — 확정 후 문서·코드에 반영:

1. **SSE vs polling**: 기본 SSE. Render Free tier에서 SSE keep-alive가 5분 timeout으로 끊기는지 사전 확인. 끊기면 25s heartbeat ping 추가.
2. **Regulation connector 첫 대상**: admin-upload-first로 결정 권장. 외부 사이트 크롤링 정책 리스크 회피, Day 19에서 RSS connector를 그 위에 얹는다.
3. **Embedding 차원**: 768 (text-embedding-004 default). pgvector ivfflat lists 100으로 시작.
4. **Report payload 위치**: `agent_runs.final_report jsonb` 컬럼 추가, `/v1/compliance/report` 응답은 기존 schema 유지. 동기화는 finalize_report tool에서 양쪽 다 기록.

## Done When

- 신규 schema/모델이 import 가능하고 round-trip 가능하다.
- Supabase 마이그레이션 SQL이 SQL Editor에서 에러 없이 적용된다(로컬 검증 또는 dry-run).
- `agent_runs_repo`, `agent_steps_repo`가 Supabase 설정 / 미설정 두 경로에서 동일 인터페이스를 제공한다.
- `pytest tests/test_agent_schemas.py tests/test_agent_trace.py`가 통과한다.
- `ruff check app tests`가 통과한다.
- 00 문서의 §14가 closed로 갱신되고, 결과가 §3~§10에 반영되어 있다.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q tests/test_agent_schemas.py tests/test_agent_trace.py
```

수동:

```bash
# Supabase SQL Editor에 붙여넣어 검증
cat infra/supabase/migrations/2026-05-25_agent_tables.sql
```

## Risks / Notes

- 스키마 결정이 Day 16~21 작업 전체를 잠근다. 변경 비용이 가장 큰 결정이므로 시간 분배의 50%를 schema/계약 리뷰에 쓴다.
- Supabase 설정 자동 감지 로직(`is_configured`)이 placeholder 값(`replace-me`)을 거르는지 day-09 회귀 테스트로 같이 확인.

## Completion Log

- Status: COMPLETE (2026-05-24)
- Implemented files:
  - [x] `infra/supabase/migrations/2026-05-25_agent_tables.sql`
  - [x] `apps/backend/app/schemas/agent.py`
  - [x] `apps/backend/app/schemas/tools.py`
  - [x] `apps/backend/app/agent/__init__.py`
  - [x] `apps/backend/app/agent/state.py`
  - [x] `apps/backend/app/agent/trace.py`
  - [x] `apps/backend/app/repositories/agent_runs_repo.py`
  - [x] `apps/backend/app/repositories/agent_steps_repo.py`
  - [x] `apps/backend/app/integrations/supabase_client.py` (added `patch` method)
  - [x] `apps/backend/tests/test_agent_schemas.py`
  - [x] `apps/backend/tests/test_agent_trace.py`
- Test commands executed (via docker):
  - [x] `docker run --rm -v $PWD/apps/backend:/app -w /app dacon-backend-dev sh -c "pip install -q -r requirements-dev.txt && ruff check app tests"`
  - [x] `docker run --rm -v $PWD/apps/backend:/app -w /app dacon-backend-dev sh -c "pip install -q -r requirements-dev.txt && pytest -q tests/test_agent_schemas.py tests/test_agent_trace.py"`
  - [x] `docker run --rm -v $PWD/apps/backend:/app -w /app dacon-backend-dev sh -c "pip install -q -r requirements-dev.txt && pytest -q"` (full regression)
- Test result summary:
  - ruff: All checks passed
  - new tests: 19 passed
  - full suite: 49 passed, 1 warning (existing starlette/python_multipart deprecation)
- Open decisions closed (reflected in `00-architecture-and-agent-design.md` §3, §5.2, §7, §8, §9, §10, §14):
  - SSE + 25s heartbeat + 1s polling fallback
  - Day 19 first connector = `admin_upload` only; RSS placeholder metadata-only
  - Embedding default = text-embedding-004, 768d, ivfflat lists=100
  - `agent_runs.final_report jsonb` column added; `ReportResponse` shape preserved
- Schema additions surfaced (Day 15 only):
  - `agent_runs(id, content_id, status, initiator, user_message, final_decision, final_summary, final_report jsonb, started_at, ended_at, token_input, token_output, model)`
  - `agent_steps(id bigserial, run_id, step_index, step_type, tool_name, payload jsonb, created_at)`
  - service_role grants on both + sequence usage
- Known notes:
  - Supabase migration file was not applied against a live project in this sandbox; SQL was sanity-checked locally only. Apply via Supabase SQL Editor (paste contents, not file path).
  - `agent_runs_repo.update` now routes through `SupabaseClient.patch` (newly added). Other repositories continue to use existing insert/select-only patterns.
  - `request_human_review` and `finalize_report` tool *args* schemas are wired here, but tool *implementations* are deferred to Day 16.
