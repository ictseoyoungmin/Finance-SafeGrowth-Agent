# Day 16 — Tool Extraction and Registry

## Goal

기존 service layer를 손대지 않고, agent가 호출 가능한 **6개 tool 함수**로 감싸는 어댑터를 만든다. 동시에 Gemini function-calling이 바로 쓸 수 있는 `Tool(function_declarations=[...])` 직렬화를 제공한다.

핵심 원칙: **agent는 service를 직접 import하지 않는다.** 항상 `ToolRegistry.invoke(name, args, state)`를 통한다. 이렇게 해야 Day 17 agent runner가 tool 호출을 가로채 trace에 기록하고 validation을 일관되게 적용할 수 있다.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §4
- `.devmd/week3/day-15-agent-contracts-and-state.md` (schema/state 의존)

## Files

```text
apps/backend/app/agent/tools/__init__.py             (NEW)
apps/backend/app/agent/tools/base.py                 (NEW)
apps/backend/app/agent/tools/registry.py             (NEW)
apps/backend/app/agent/tools/fetch_content.py        (NEW)
apps/backend/app/agent/tools/scan_rules.py           (NEW)
apps/backend/app/agent/tools/search_regulation.py    (NEW)
apps/backend/app/agent/tools/draft_rewrite.py        (NEW)
apps/backend/app/agent/tools/request_human_review.py (NEW)
apps/backend/app/agent/tools/finalize_report.py      (NEW)
apps/backend/tests/test_agent_tools_fetch_content.py     (NEW)
apps/backend/tests/test_agent_tools_scan_rules.py        (NEW)
apps/backend/tests/test_agent_tools_search_regulation.py (NEW)
apps/backend/tests/test_agent_tools_draft_rewrite.py     (NEW)
apps/backend/tests/test_agent_tools_finalize_report.py   (NEW)
apps/backend/tests/test_agent_tools_registry.py          (NEW)
```

수정 파일:

```text
apps/backend/app/services/*  (NOT modified — read-only from tool wrappers)
```

## Tasks

- [ ] `tools/base.py`에 다음을 정의한다.
  - `class Tool(Protocol)` — `name: str`, `description: str`, `args_model: type[BaseModel]`, `result_model: type[BaseModel] | None`, `def run(args, state) -> BaseModel`.
  - `gemini_declaration(tool: Tool) -> FunctionDeclaration` — Pydantic schema를 Gemini schema로 변환. enum/배열/optional 처리.
  - `ToolError(Exception)` — invalid args / upstream failure 구분 필드 포함.
- [ ] `tools/registry.py`에 `ToolRegistry`.
  - `register(tool)`, `get(name)`, `declarations()`, `invoke(name, raw_args, state)`.
  - `invoke`는 (1) `args_model`로 raw_args 검증, (2) `tool.run(args, state)` 호출, (3) 결과를 `result_model`로 검증, (4) `ToolError`는 잡아서 `{ "error": ..., "retryable": bool }` 형태로 반환. trace 기록은 Day 17 agent runner가 담당.
- [ ] 도구 6개 구현. 각 도구는 기존 service를 직접 호출하되 **agent state에서 필요한 context를 채워준다**.
  - `fetch_content`: `ContentRepository.get(content_id)`. 미존재 시 `request_human_review`를 유도하는 `ToolError("content_not_found")` 발생.
  - `scan_rules`: `RuleEngine().scan(text)` + risk_level 계산 (`AnalyzeService._risk_level` 로직 재사용 — 내부 함수가 private면 helper로 추출).
  - `search_regulation`: `RegulationRetriever.retrieve(risk_categories, product_type, limit)`. Day 19 이후 `query` 인자가 들어오면 vector_search로 위임.
  - `draft_rewrite`: `RewriteService.rewrite(RewriteRequest(...))`. agent가 original_text/flagged_spans/evidence를 직접 넘기는 경로도 지원(stateless rewrite).
  - `request_human_review`: side-effect 없음. 단순히 결과 payload를 반환하고, agent runner가 이를 감지하여 `awaiting_human`으로 전환.
  - `finalize_report`: `ApprovalService.record(...)` + `ReportService.build(...)` + `agent_runs.final_report` 갱신.
- [ ] `tools/__init__.py`에서 default registry 인스턴스 생성 (`get_default_registry()`).
- [ ] 각 tool의 인자/결과 모델은 `schemas/tools.py` 재사용.
- [ ] 도구별 단위 테스트:
  - 정상 input → 정상 output
  - 잘못된 input → `ToolError("invalid_args")`로 변환됨
  - upstream service 예외 → `ToolError("upstream_failed", retryable=True)`
  - fallback 경로 (Supabase/Gemini 미설정)
- [ ] `tests/test_agent_tools_registry.py`: declarations() 결과가 Gemini SDK가 받는 schema와 호환되는지 (직렬화/역직렬화 round-trip).

## Tool surface details

각 tool의 `description` 필드는 **Gemini가 도구 선택 정확도를 결정한다**. 간결하면서 호출 조건을 분명히 한다.

예시:

```python
fetch_content.description = (
    "Load the original advertisement text and metadata for a given content_id. "
    "Call this first if content_id is provided but text was not supplied in the user message."
)

scan_rules.description = (
    "Run the deterministic Korean financial-ad rule scanner over a text. "
    "Returns flagged spans, risk categories, and overall risk level. "
    "Fast and free; prefer this before calling search_regulation or draft_rewrite."
)
```

description 텍스트는 코드와 함께 lint한다 (`tests/test_tool_descriptions.py`는 추후 추가 가능).

## Done When

- `ToolRegistry.declarations()`가 Gemini `Tool` 객체로 변환 가능하다.
- 6개 tool 모두 단위 테스트 통과.
- 각 tool이 기존 service 동작과 1:1로 일치한다 (회귀 테스트가 기존 service 결과를 비교).
- agent state 없이도(즉, dummy state로) tool 함수가 호출 가능하다 — 단위 테스트 작성 편의.
- `ruff check app tests`, `pytest` 통과.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q tests/test_agent_tools_*.py
```

## Risks / Notes

- `RewriteService.rewrite`는 현재 repository에서 context를 다시 fetch한다. stateless 호출 경로를 새로 노출하지 않으면 tool에서 같은 context를 두 번 조회하게 된다. `draft_rewrite` tool은 우선 기존 경로를 그대로 쓰고, 성능 측정 후 Day 17~18에서 최적화 여부 결정.
- `request_human_review`는 결과 payload를 그대로 반환하지만, agent runner에서 이를 "특수 시그널"로 인식해야 한다. tool 자체는 단순하게 유지.
- `finalize_report`의 side-effect(승인 저장 + 리포트 build + agent_runs.final_report 갱신)가 한 트랜잭션이 아니다. 부분 실패 시 cleanup 로직을 Day 17 agent runner에서 다룬다.

## Completion Log

- Status: COMPLETE (2026-05-24)
- Implemented files:
  - [x] `apps/backend/app/agent/tools/__init__.py`
  - [x] `apps/backend/app/agent/tools/base.py`
  - [x] `apps/backend/app/agent/tools/registry.py`
  - [x] `apps/backend/app/agent/tools/fetch_content.py`
  - [x] `apps/backend/app/agent/tools/scan_rules.py`
  - [x] `apps/backend/app/agent/tools/search_regulation.py`
  - [x] `apps/backend/app/agent/tools/draft_rewrite.py`
  - [x] `apps/backend/app/agent/tools/request_human_review.py`
  - [x] `apps/backend/app/agent/tools/finalize_report.py`
  - [x] `apps/backend/tests/test_agent_tools_fetch_content.py`
  - [x] `apps/backend/tests/test_agent_tools_scan_rules.py`
  - [x] `apps/backend/tests/test_agent_tools_search_regulation.py`
  - [x] `apps/backend/tests/test_agent_tools_draft_rewrite.py`
  - [x] `apps/backend/tests/test_agent_tools_request_human_review.py`
  - [x] `apps/backend/tests/test_agent_tools_finalize_report.py`
  - [x] `apps/backend/tests/test_agent_tools_registry.py`
- Test commands executed (via docker):

```bash
docker build -t dacon-backend-dev -f apps/backend/Dockerfile apps/backend
docker run --rm \
  -v "$PWD/apps/backend:/app" -w /app \
  dacon-backend-dev sh -c \
  "pip install --no-cache-dir -q -r requirements-dev.txt && ruff check app tests && pytest -q"
```

- Test result summary:
  - ruff: All checks passed
  - pytest (full suite): 77 passed, 1 warning (existing starlette/python_multipart deprecation)
  - 28 new Day-16 tests added; 49 prior tests still green (no regression)
- Local sanity command (registry import + declarations dump):

```bash
docker run --rm \
  -v "$PWD/apps/backend:/app" -w /app \
  dacon-backend-dev sh -c \
  "pip install -q -r requirements-dev.txt && python -c 'from app.agent.tools import get_default_registry; r = get_default_registry(); print(r.names())'"
# -> ['fetch_content', 'scan_rules', 'search_regulation', 'draft_rewrite', 'request_human_review', 'finalize_report']
```

- Design notes carried out:
  - Existing service layer (`AnalyzeService`, `RewriteService`, `RegulationRetriever`, `ApprovalService`, `ReportService`) is **not modified** — tools are pure wrappers.
  - Each tool takes its dependencies via constructor injection; default factory uses production `get_*` helpers.
  - `ToolRegistry.invoke` catches `ValidationError`, `ToolError`, and arbitrary `Exception`s and returns them as JSON-serializable payloads (the agent loop never raises mid-iteration).
  - `gemini_declaration` produces a Gemini-compatible JSON schema dict (inlines `$defs`, drops `title`, collapses `Optional[T]` `anyOf` into `nullable: true`) — Day 17 wraps these into `Tool(function_declarations=[...])`.
  - `request_human_review` mutates `state.pending_human` and `state.status = "awaiting_human"`; Day 17 runner detects this and halts the loop.
  - `finalize_report` writes through to `ApprovalService`, builds the `ReportResponse`, mutates `state.final`/`state.status="done"`, and patches `agent_runs.final_report` via the Day 15 repository.
- Known notes:
  - `SearchRegulationArgs.query` is accepted but not yet routed — Day 19 wires it into vector search.
  - `FinalizeReportTool` performs three side-effects (approval insert + report build + agent_runs patch) in sequence and is not transactional. Day 17 runner handles partial failure by leaving the run in `running` and surfacing the `ToolError` in the trace.
  - `DraftRewriteTool` calls `RewriteService` which re-reads context from repositories. Day 17/18 may optimize to share resolved context, but for now the redundancy is acceptable.
