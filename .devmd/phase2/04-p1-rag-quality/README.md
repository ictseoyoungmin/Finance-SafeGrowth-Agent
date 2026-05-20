# Slice 04 — P1 RAG Quality and Supabase Retrieval

## Goal

Replace fallback-only evidence retrieval with real Supabase-backed retrieval when configured.

Full embedding search is ideal, but this slice may implement a staged approach:

1. Supabase table search by `product_type` and `risk_categories`.
2. Later, pgvector RPC search when embeddings are available.

## Problems to fix

1. `RegulationDocsRepository.search()` returns fallback documents even when Supabase is configured.
2. `match_regulation_docs()` exists in SQL but is not used.
3. Seed documents do not include embeddings, so pgvector search cannot work yet.
4. Evidence response should remain stable whether DB or fallback is used.

## Target behavior

### Stage A — required

If Supabase is configured:

- Query `regulation_docs`.
- Filter by product type in `{request.product_type, "공통"}`.
- Filter by overlapping risk categories if provided.
- Sort deterministically.
- Return up to `limit` results.

If no rows are found:

- fallback to local demo documents.

### Stage B — optional

If embeddings exist:

- call `match_regulation_docs()` RPC
- return similarity scores from vector search

## Files to modify

```text
apps/backend/app/repositories/regulation_docs_repo.py
apps/backend/app/rag/retriever.py
apps/backend/app/services/evidence_service.py
apps/backend/app/schemas/evidence.py
infra/supabase/schema.sql
infra/supabase/seed_regulation_docs.sql
apps/backend/tests/test_evidence_service.py
apps/backend/tests/test_regulation_docs_repo.py
```

## Implementation notes

Keep fallback documents as demo fallback. Do not delete them.

Add clear source markers if useful:

```python
source: Literal["supabase", "fallback"]
```

This is optional, but useful for debug and demo mode.

## Required Deliverables

- [x] Supabase configured path attempts real query.
- [x] Placeholder values are not treated as configured secrets.
- [x] Fallback still works.
- [x] Evidence response schema remains compatible with frontend.
- [x] Tests cover fallback retrieval.
- [x] Tests cover filtering logic.
- [x] Documentation notes how to seed `regulation_docs`.

## Test Harness

```bash
cd apps/backend
ruff check app tests
pytest tests/test_evidence_service.py tests/test_regulation_docs_repo.py
```

Manual test:

```bash
curl -X POST http://localhost:8000/v1/compliance/evidence \
  -H "Content-Type: application/json" \
  -d '{
    "content_id":"demo-content",
    "product_type":"투자상품",
    "risk_categories":["확정 수익 오인", "원금 보장 오인"]
  }'
```

Expected:

- response contains evidence items
- evidence includes relevant snippets
- no crash without Supabase


## Implementation Completion Placeholder

- Status: COMPLETE
- Implemented files:
  - [x] `apps/backend/app/repositories/regulation_docs_repo.py`
  - [x] `apps/backend/tests/test_regulation_docs_repo.py`
  - [x] `docs/deployment/supabase.md`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
- Test result summary:
  - `ruff`: passed
  - `pytest`: 25 passed, 1 warning
- Known issues:
  - Stage A table filtering is implemented. Stage B pgvector RPC remains future work because seeded docs do not include embeddings.
- Next recommended step:
  - Add embeddings and switch to `match_regulation_docs()` when production-quality semantic retrieval is needed.

## Day 11 Follow-up Verification

Status: LOCAL_COMPLETE / PUBLIC_REDEPLOY_PENDING

- Regulation evidence lookup uses Supabase table filtering before fallback.
- `.env.example` files are template-safe and do not contain project-specific Supabase keys.
- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker `npm ci && npm run typecheck && npm run lint && npm run build`: passed.
- Public Vercel UI approval/report smoke after latest deploy: NOT_RUN.
- Supabase `approval_logs.selected_revision` actual text check from UI path: NOT_RUN.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
