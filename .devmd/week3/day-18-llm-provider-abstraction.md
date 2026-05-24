# Day 18 — LLM Provider Abstraction and Local LLM Switching

## Goal

Gemini 전용 호출 경계를 `LlmProvider` 추상화로 감싸고, Dockerized backend가 shared local LLM server의 OpenAI-compatible endpoint와 Gemini 사이를 환경변수만으로 전환할 수 있게 한다.

Stable local endpoint:

```text
OPENAI_BASE_URL=http://host.docker.internal:18080/v1
OPENAI_API_KEY=local-not-required
OPENAI_MODEL=gemma-4-local
LLM_PROVIDER=openai_compatible
```

Host-only development:

```text
OPENAI_BASE_URL=http://127.0.0.1:18080/v1
```

## Files

```text
apps/backend/app/core/config.py
apps/backend/app/integrations/llm/__init__.py
apps/backend/app/integrations/llm/base.py
apps/backend/app/integrations/llm/gemini.py
apps/backend/app/integrations/llm/openai_compatible.py
apps/backend/app/integrations/llm/factory.py
apps/backend/app/agent/runner.py
apps/backend/app/agent/transcript.py
apps/backend/app/services/analyze_service.py
apps/backend/app/services/rewrite_service.py
apps/backend/tests/conftest.py
apps/backend/tests/test_openai_compatible_provider.py
apps/backend/tests/test_local_llm_integration.py
```

## Tasks

- [x] Add LLM env vars to `core/config.py`.
- [x] Create `app/integrations/llm/` package with base protocol, Gemini adapter, OpenAI-compatible adapter, and factory.
- [x] Refactor `AgentRunner` and transcript construction to call `LlmProvider.generate_with_tools`.
- [x] Refactor `AnalyzeService` and `RewriteService` to call `LlmProvider.generate_json`.
- [x] Default tests to `LLM_PROVIDER=openai_compatible` in `conftest.py`.
- [x] Rename Gemini-specific fakes to scripted LLM provider stubs.
- [x] Add OpenAI-compatible provider unit tests with fake `httpx` client.
- [x] Add local LLM integration smoke test that skips when `OPENAI_BASE_URL` is unreachable.

## Completion Log

- 2026-05-24: Implemented provider abstraction and local OpenAI-compatible switching.
- 2026-05-24: Preserved `gemini_client.py` as the Gemini API adapter/parser while moving application dependencies to `LlmProvider`.
- 2026-05-24: Added fake-httpx provider tests and a skip-safe local LLM smoke test.
- 2026-05-24: Validation passed in Docker via `docker run --rm --add-host=host.docker.internal:host-gateway -e OPENAI_BASE_URL=http://host.docker.internal:18080/v1 ... "ruff check app tests && pytest"`: 95 passed, 1 warning. The local LLM integration smoke executed against the live endpoint.
