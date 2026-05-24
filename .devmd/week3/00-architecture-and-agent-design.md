# Architecture and Agent Design — Week 3 Baseline

이 문서는 Week 3 전 작업의 설계 기준이다. Day 15~21 문서는 이 설계를 변형 없이 따른다. 결정 변경이 필요하면 이 문서를 먼저 수정한 뒤 day 문서를 업데이트한다.

## 1. Why this is not yet an Agent

현재 Week 2 종료 시점 구현물은 다음과 같다.

- `apps/backend/app/services/analyze_service.py`: RuleEngine 정규식 + Gemini single-shot JSON 호출, 결과 merge.
- `apps/backend/app/services/evidence_service.py`: 3개 demo doc 또는 Supabase 단순 필터 검색.
- `apps/backend/app/services/rewrite_service.py`: Gemini single-shot JSON 호출, 실패 시 deterministic fallback.
- `apps/backend/app/services/approval_service.py`, `report_service.py`: 사람이 누른 버튼을 그대로 저장/조회.
- Frontend `apps/frontend/src/features/compliance`: 5-step wizard. 다음 단계로 이동할지는 **사람이 버튼을 눌러서** 결정한다.

판정:

- 자율적 의사결정 없음. 어떤 도구를 다음에 호출할지 결정하는 주체는 frontend store다.
- Tool use / function calling 없음. Gemini는 고정 프롬프트로 호출되는 JSON 생성기다.
- 외부 규제 추적 없음. `FALLBACK_REGULATION_DOCS`는 3건 더미고 Supabase seed도 동일 수준이다.
- Agent 프레임워크 의존성 0개. `requirements.txt`에 fastapi, httpx, pydantic, uvicorn뿐.

대회 명세상 핵심 명제("Agent형 서비스", "AI 규제 Agent")가 충족되지 않는다. Week 3 작업은 이 진단을 출발점으로 한다.

## 2. Target architecture

```text
+--------------------+
|  Frontend (React)  |
|  - Input form      |
|  - Agent run view  |
|    * trace stream  |
|    * tool calls    |
|    * observations  |
|    * pending action|
|  - Approval modal  |
|  - Legacy wizard   |
+----------+---------+
           |
           v
+--------------------+         +-----------------------+
|  /v1/agent/run     |         |  /v1/agent/runs/{id}  |
|  /v1/agent/runs/   |<------->|  /v1/agent/approve    |
+----------+---------+         +-----------------------+
           |
           v
+----------------------------------------------------+
|              AgentRunner (backend)                  |
|  - State machine: idle -> thinking -> calling_tool  |
|                   -> observing -> awaiting_human    |
|                   -> finalizing -> done | failed    |
|  - Loop: Gemini function-calling                    |
|    * declarations = ToolRegistry.declarations()     |
|    * tool_config  = AUTO / forced as needed         |
|  - Trace recorder writes every step                 |
|  - Iteration cap, time cap, cost cap                |
|  - Deterministic fallback agent (rule-only)         |
+--------------+---------------------+----------------+
               |                     |
               v                     v
   +-----------------------+   +-------------------------------+
   |     ToolRegistry      |   |         TraceStore            |
   |  scan_rules           |   |  agent_runs                   |
   |  search_regulation    |   |  agent_steps                  |
   |  draft_rewrite        |   |  in-memory fallback           |
   |  request_human_review |   +-------------------------------+
   |  finalize_report      |
   |  fetch_content        |
   +----------+------------+
              |
              v
   +---------------------------------------+
   |  Existing service layer (unchanged)   |
   |  RuleEngine                           |
   |  RegulationRetriever -> repo          |
   |  RewriteService                       |
   |  ApprovalService / AuditService       |
   +-----------+---------------------------+
               |
               v
   +---------------------------------------+
   |  Supabase                             |
   |  contents / risk_results / approval_  |
   |  logs / audit_logs                    |
   |  regulation_docs + regulation_chunks  |
   |  (NEW) agent_runs / agent_steps       |
   |  (NEW) regulation_sources / versions  |
   +---------------------------------------+
```

핵심 디자인:

- Agent layer는 **새로** 만든다.
- 기존 service 코드는 **건드리지 않는다.** Agent는 tool wrapper를 통해서만 service를 호출한다.
- Frontend는 agent run 화면이 기본이고, Week 1/2 5-step wizard는 `/legacy` 라우트로 보존한다.

## 3. Framework decision — Gemini native function calling (no LangGraph)

후보:

1. Gemini native function calling + 자체 루프
2. LangGraph
3. Pydantic-AI / Google ADK

**결정: 1. Gemini native function calling + 자체 ReAct 루프**

사유:

- 단일 LLM(Gemini) 전제이므로 SDK 변경 비용이 큰 LangGraph는 효용이 작다.
- `requirements.txt` 의존성을 최소화한다 (`google-generativeai` 1개만 추가). 기존 fastapi/httpx 스택 유지.
- Trace를 명시적으로 만들 수 있어 frontend agent trace UI 구현이 단순하다.
- 대회 심사 시 "직접 구현한 agent loop"가 설명 가능성에서 유리하다.

거절 사유:

- LangGraph: dependency footprint 큼. Supabase persistence와 충돌하지 않지만 state checkpointer 도입 시 환경 복잡도 상승. Week 3 일정에 비해 과투자.
- ADK: Gemini 사용 시 정합성 좋으나 한국어 자료/실전 사례 부족, 종속 가속화 위험.

대신 약속:

- Agent 루프 코드는 **표준 ReAct 패턴**을 따르고 함수 시그니처를 LangChain 친화적으로 두어, 후일 교체가 필요해도 tool 정의는 재사용 가능하게 한다.

## 4. Tool contract

ToolRegistry는 다음 6개 도구를 노출한다. 모두 순수 함수처럼 호출 가능하고, side-effect는 repository를 거친다.

| Name | Purpose | Inputs | Outputs (요약) |
|---|---|---|---|
| `fetch_content` | content_id로 원문/메타 로드. 입력 누락시 agent가 먼저 호출. | `content_id: str` | `{original_text, product_type, channel, target_customer, language}` |
| `scan_rules` | RuleEngine 실행. 빠르고 무료. | `text: str` | `{flagged_spans: [...], risk_level, risk_categories}` |
| `search_regulation` | RAG 검색. 카테고리/제품/쿼리 텍스트 기반. | `query: str, risk_categories: [str], product_type: str, limit?: int` | `{evidence: [{evidence_id, title, version, snippet, similarity}]}` |
| `draft_rewrite` | Gemini 또는 deterministic fallback rewrite 생성. | `content_id, mode, original_text, flagged_spans, evidence` | `{revised_text_conservative, revised_text_marketing, changes, source}` |
| `request_human_review` | Agent가 추가 정보·확정·기각이 필요할 때 사용. Agent run을 `awaiting_human` 상태로 전환하고 종료. | `question: str, options?: [str], proposed_action?: dict` | (호출 즉시 loop 종료, 사용자 응답이 들어오면 같은 run 재개) |
| `finalize_report` | 모든 판단 종료 후 최종 리포트 생성. Agent run을 종료. | `content_id, decision, selected_revision, summary` | `ReportResponse 동등 payload` |

Tool declaration는 Gemini `Tool(function_declarations=[...])` 스키마로 자동 직렬화한다 (`tool_registry.declarations()`).

호출 정책:

- Agent는 매 iteration마다 모델이 `function_call`을 반환하면 해당 tool을 실행하고 결과를 `function_response`로 다음 prompt에 추가한다.
- 모델이 자연어 텍스트만 반환하면 `final answer` 로 간주하고 종료한다.
- 단, 종료 전에 `finalize_report` 또는 `request_human_review`가 반드시 한 번은 호출되어야 한다. 미호출 종료는 `incomplete` 상태로 기록.

## 5. Agent state and trace schema

### 5.1 State (in-memory during run)

```python
@dataclass
class AgentState:
    run_id: UUID
    content_id: UUID | None
    user_message: str
    iteration: int
    max_iterations: int
    started_at: datetime
    deadline: datetime
    transcript: list[AgentTurn]   # 모델 입력/출력 누적
    pending_human: HumanPrompt | None
    final: AgentFinal | None
```

### 5.2 Trace tables (Supabase)

`infra/supabase/migrations/2026-05-25_agent_tables.sql` 로 신규 추가.

```sql
create table agent_runs (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id),
  status text not null check (status in ('running','awaiting_human','done','failed','cancelled')),
  initiator text,                      -- user|scheduled
  user_message text,
  final_decision text,                 -- approve|reject|revise|none
  final_summary text,
  final_report jsonb,                  -- ReportResponse 동등 payload (Day 17 finalize_report 갱신)
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  token_input int,
  token_output int,
  model text
);

create table agent_steps (
  id bigserial primary key,
  run_id uuid not null references agent_runs(id) on delete cascade,
  step_index int not null,
  step_type text not null check (step_type in ('thought','tool_call','tool_result','human_prompt','human_response','final')),
  tool_name text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index on agent_steps (run_id, step_index);
```

Fallback storage: Supabase 미설정 시 in-memory `FALLBACK_AGENT_RUNS`, `FALLBACK_AGENT_STEPS` (process-local, demo 한정).

## 6. Agent loop

의사코드:

```python
def run(initial: AgentRunRequest) -> AgentRunResult:
    state = init_state(initial)
    record_thought(state, "starting compliance review")

    while state.iteration < state.max_iterations and not state.final and not state.pending_human:
        if time_exceeded(state):
            return fail(state, "deadline exceeded")

        response = gemini.generate_content(
            model=settings.gemini_model,
            contents=build_transcript(state),
            tools=[Tool(function_declarations=registry.declarations())],
            tool_config=tool_config_for(state),
            generation_config=GenerationConfig(temperature=0.2),
        )

        call = first_function_call(response)
        if call is None:
            text = response.text or ""
            if not finalized_via_tool(state):
                # 모델이 finalize_report 호출 없이 끝내려 함 -> 보정 호출
                force_finalize(state, text)
            return done(state)

        result = registry.invoke(call.name, call.args, state)
        record_tool(state, call, result)

        if call.name == "request_human_review":
            state.pending_human = HumanPrompt(**call.args)
            persist(state)
            return paused(state)

        if call.name == "finalize_report":
            state.final = AgentFinal(**result)
            persist(state)
            return done(state)

        state.iteration += 1

    if not state.final and not state.pending_human:
        return fail(state, "max iterations")
    return done(state)
```

가드:

- `max_iterations`: default 8. Tool 호출 폭주 방지.
- `deadline`: 시작 후 60s. 평가 환경에서 hang 방지.
- `tool_config_for`: 첫 iteration에서는 AUTO. `awaiting_human` 재개 시에는 ANY로 finalize 강제.
- 모든 tool 호출 인자는 server-side validation으로 다시 한번 검증한다 (모델이 잘못된 인자를 줄 때 fallback).

### Deterministic fallback agent

Gemini 미설정/오류 시:

```text
1. scan_rules
2. search_regulation
3. draft_rewrite
4. request_human_review (mode=approve_or_reject)
```

이 4단계는 코드로 고정하여 demo 흐름을 보장한다. UI는 fallback 배지를 표시한다(`source: fallback_agent`).

## 7. API surface (Week 3 추가분)

```text
POST /v1/agent/run                    body: { content_id?, text?, mode? }
GET  /v1/agent/runs/{run_id}
GET  /v1/agent/runs/{run_id}/stream   server-sent events, step별 push
POST /v1/agent/runs/{run_id}/respond  body: { response: str | dict }   (human reply)
POST /v1/agent/runs/{run_id}/cancel
```

기존 `/v1/compliance/*`는 그대로 유지. Agent는 내부적으로 이 endpoint들을 호출하지 않고 service layer를 직접 사용한다 (HTTP 자가 호출 비용 회피).

## 8. Regulation tracking (Day 18)

문제: `regulation_docs`가 사실상 상수다. "최신 규제 자동 추적" 명제 불충족.

설계:

- `regulation_sources` 테이블: 소스 URL, fetch method, last_polled_at, content_hash.
- 최소 1개 connector를 실제 구현한다: 후보 우선순위 — (a) 금융감독원 보도자료/규정 RSS, (b) 금융투자협회 표준약관/광고심사 사례, (c) 금융위 보도자료 RSS.
  - 자동 크롤링이 정책상 불확실할 경우, 사용자가 PDF/HTML을 업로드하는 `POST /v1/admin/regulations/ingest` 경로를 1차 구현으로 한다. "수동 ingest + 자동 hash 기반 변경 감지"도 "추적"으로 인정된다.
- `regulation_versions`: 원문 hash, 발효일, ingested_at, diff_summary, supersedes_id.
- 배치: APScheduler 또는 `python -m app.jobs.regulation_refresh` CLI. Render Cron Job으로 등록.
- 변경 감지 시 agent에 노출되는 RAG index도 갱신한다.

## 9. Vector RAG (Day 19)

- 현재 `app/rag/embeddings.py`는 character-code sum placeholder. 폐기.
- 새 embedding: Gemini `text-embedding-004` (or fallback: deterministic local hash for offline tests).
- Supabase pgvector column `regulation_chunks.embedding vector(768)`.
- `RegulationDocsRepository.search` 보조 메서드 `vector_search(query_text, top_k)` 추가. tool `search_regulation`이 이를 우선 사용하고, 결과 부족 시 카테고리 필터로 보조.
- 청크 단위는 600자(기존 `chunker.chunk_text` 유지) 또는 문단 기준 중 선택. Day 19에서 결정.

## 10. Frontend agent trace UI (Day 20)

목표: "5-step wizard"를 "agent run viewer"로 재구성.

- 진입: 입력 화면(현 InputStep) → `submit` → `/v1/agent/run` 호출 → run_id 반환.
- Run view: 좌측 trace timeline (`scan_rules`, `search_regulation`, ...), 우측 상세 패널.
- Streaming: SSE 또는 polling 1s 둘 중 선택(Day 20에서 결정). 둘 다 backend `/stream`은 SSE.
- Human-in-the-loop: agent가 `request_human_review` 호출 시 우측 패널에 승인/거절/추가지시 입력 UI.
- 최종 리포트: agent가 `finalize_report` 호출 후 표시. 기존 `ReportStep` 디자인 재사용.
- Legacy route `/legacy/wizard`로 기존 5-step 페이지 보존. demo fallback 용도.

## 11. Backwards compatibility

- 기존 endpoint `/v1/compliance/*`는 동작 보장. 일부 데모/심사용 스크립트가 사용 중.
- 기존 schema 컬럼 변경 없음. 추가 컬럼·테이블만 도입.
- `docs/demo/demo-script.md`는 agent run 시나리오로 갱신하되, 부록에 legacy wizard 흐름을 남긴다.

## 12. Test strategy

- Tool 단위 테스트: 각 tool 함수의 입력 validation + service 위임 mock.
- Agent loop 단위 테스트: Gemini 응답을 fake stub으로 주입하여 정상 경로 / 도구 폭주 / human pause / fallback 경로 검증.
- Regulation ingestion: fixture HTML/PDF에서 chunk → embed (mock) → store → search 검증.
- Frontend: agent run viewer는 mock SSE로 Playwright 시나리오 작성.
- E2E: 표준 데모 문장 + 무위험 문장(예: 안내문만 있는 sentence) 각각에 대해 agent가 다른 행동을 취하는지 확인.

## 13. Out of scope (Week 3 명시 제외)

- 다국어(영어/베트남어 등) compliance — 명세 한계점에 언급되어 있으나 Week 4 이후로 미룬다.
- 실시간 규제 변경 알림 (이메일/슬랙) — 단순 표시까지만.
- Approval 결과의 마케팅 시스템 연계 — 명세상 "자동 연계"가 있지만 인터페이스 협의 전이라 placeholder.
- Cost dashboard, 사용량 기반 라우팅.

## 14. Open decisions (Closed on Day 15, 2026-05-24)

1. **SSE + polling fallback** (closed). Backend는 SSE를 1차 채널로 노출하고 25초 heartbeat를 보낸다. Frontend는 EventSource 실패/끊김 시 1초 polling으로 자동 전환한다. §7, §10에 반영.
2. **Admin-upload-first** (closed). Day 18의 첫 connector는 `admin_upload`로 한정한다. FSS/금융위 RSS connector는 메타데이터-only 모드로 placeholder만 만들고, 본문 fetch는 정책 검토 후 Week 4로 미룬다. §8에 반영.
3. **text-embedding-004, 768d, ivfflat lists=100** (closed). Provider 인터페이스는 차원 가변으로 두되, 운영 default는 768. Chunk 수가 적은 동안은 ivfflat가 sequential scan보다 느릴 수 있다는 점은 Day 19에서 모니터링한다. §9에 반영.
4. **Report payload 위치** (closed). `agent_runs.final_report jsonb` 컬럼을 신규 추가하고, `/v1/compliance/report` 응답은 기존 schema(`ReportResponse`)를 유지한다. `finalize_report` tool은 양쪽 모두에 동기 기록한다. §4, §5.2, §11에 반영.
