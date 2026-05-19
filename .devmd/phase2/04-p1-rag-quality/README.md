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

- [ ] Supabase configured path attempts real query.
- [ ] Placeholder values are not treated as configured secrets.
- [ ] Fallback still works.
- [ ] Evidence response schema remains compatible with frontend.
- [ ] Tests cover fallback retrieval.
- [ ] Tests cover filtering logic.
- [ ] Documentation notes how to seed `regulation_docs`.

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

- Status: NOT_STARTED / IN_PROGRESS / COMPLETE / BLOCKED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Test result summary:
  - TBD
- Known issues:
  - TBD
- Next recommended step:
  - TBD

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
