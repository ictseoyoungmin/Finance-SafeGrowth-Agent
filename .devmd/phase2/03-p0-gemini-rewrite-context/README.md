# Slice 03 — P0 Gemini Rewrite Context and JSON Parser

## Goal

Make rewrite generation context-aware and robust.

The current rewrite prompt only contains `content_id`, `mode`, and a response schema. Gemini does not receive the original text, flagged spans, or evidence. This makes real LLM rewrite unreliable, and the app mostly depends on fallback output.

## Problems to fix

1. `RewriteRequest` only contains `content_id` and `mode`.
2. `RewriteService._build_prompt()` does not include source text, risks, or evidence.
3. Gemini JSON parsing fails when the model returns fenced markdown JSON.
4. Gemini fallback works, but successful Gemini output is unlikely.

## Target behavior

When `/rewrite` is called:

1. Backend resolves the source context.
2. Prompt includes:
   - original text
   - product type
   - channel
   - target customer
   - language
   - flagged spans
   - risk categories
   - evidence snippets
   - required response schema
3. Gemini response is parsed even if wrapped in markdown fences.
4. If Gemini fails, deterministic fallback rewrite is returned.

## Preferred design

Keep frontend request simple:

```json
{
  "content_id": "uuid-string",
  "mode": "marketing_balanced"
}
```

Backend should fetch context from repositories:

```text
contents_repo.get(content_id)
risk_results_repo.get_latest_by_content_id(content_id)
regulation_docs_repo.search(...)
```

If persistence is unavailable, fallback to demo context.

## Files to modify

```text
apps/backend/app/schemas/rewrite.py
apps/backend/app/services/rewrite_service.py
apps/backend/app/integrations/gemini_client.py
apps/backend/app/repositories/contents_repo.py
apps/backend/app/repositories/risk_results_repo.py
apps/backend/app/repositories/regulation_docs_repo.py
apps/backend/tests/test_rewrite_service.py
apps/backend/tests/test_gemini_parser.py
```

## Gemini JSON parser requirements

Implement a parser that supports:

```json
{"key":"value"}
```

```markdown
```json
{"key":"value"}
```
```

```text
Here is the JSON:
{"key":"value"}
```

Parsing priority:

1. Try direct `json.loads(text)`.
2. Strip triple-backtick fenced code block.
3. Extract substring from first `{` to last `}` and parse.
4. Return `None` if parsing fails.

## Prompt requirements

Prompt must instruct:

```text
Return only raw JSON. Do not use markdown. Do not include explanation outside JSON.
```

Response schema:

```json
{
  "revised_text_conservative": "string",
  "revised_text_marketing": "string",
  "changes": [
    {
      "original": "string",
      "replacement": "string",
      "reason": "string"
    }
  ]
}
```

## Required Deliverables

- [x] Rewrite context resolution added.
- [x] Prompt includes original text, risk spans, and evidence.
- [x] Gemini parser supports raw JSON and fenced JSON.
- [x] Rewrite fallback still works without Gemini.
- [x] Unit tests cover parser edge cases.
- [x] Unit tests cover fallback rewrite.

## Test Harness

```bash
cd apps/backend
ruff check app tests
pytest tests/test_rewrite_service.py tests/test_gemini_parser.py
```

Manual test:

```bash
curl -X POST http://localhost:8000/v1/compliance/rewrite \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","mode":"marketing_balanced"}'
```

Expected:

- response contains both conservative and marketing rewrite
- response contains changes list
- response does not crash if Gemini is unavailable


## Implementation Completion Placeholder

- Status: COMPLETE
- Implemented files:
  - [x] `apps/backend/app/integrations/gemini_client.py`
  - [x] `apps/backend/app/services/rewrite_service.py`
  - [x] `apps/backend/tests/test_gemini_parser.py`
  - [x] `apps/backend/tests/test_rewrite_service.py`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
- Test result summary:
  - `ruff`: passed
  - `pytest`: 25 passed, 1 warning
- Known issues:
  - Gemini live output was not exercised locally; Render has `GEMINI_API_KEY` and `GEMINI_MODEL` configured for production smoke after deploy.
  - Gemini failures now log server-side diagnostics and still fall back safely.
- Next recommended step:
  - Public-smoke `/rewrite` after Render deploy and confirm fallback remains stable if Gemini errors.

## Day 11 Follow-up Verification

Status: LOCAL_COMPLETE / PUBLIC_REDEPLOY_PENDING

- Frontend approval selected revision text fix is complete.
- Gemini error logging is complete.
- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker `npm ci && npm run typecheck && npm run lint && npm run build`: passed.
- Render `/rewrite` public smoke after latest deploy: NOT_RUN.
- Gemini live behavior should be checked in Render logs because deterministic fallback also returns HTTP 200.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
