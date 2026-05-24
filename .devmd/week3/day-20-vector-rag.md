# Day 20 — Vector RAG Upgrade

## Goal

`app/rag/embeddings.py`의 character-code-sum placeholder를 폐기하고, 실제 벡터 검색을 도입한다. agent tool `search_regulation`이 query text 기반 semantic search를 사용할 수 있게 한다.

전제: Day 19에서 `regulation_chunks.embedding vector(3072)` 컬럼과 ingestion 파이프라인이 준비되어 있다.

참조 문서:

- `.devmd/week3/00-architecture-and-agent-design.md` §9
- `.devmd/week3/day-19-regulation-ingestion.md`

## Files

```text
apps/backend/app/rag/embeddings.py             (REWRITE)
apps/backend/app/rag/embedding_provider.py     (NEW)
apps/backend/app/rag/vector_search.py          (NEW)
apps/backend/app/repositories/regulation_docs_repo.py  (MOD: add vector_search)
apps/backend/app/agent/tools/search_regulation.py      (MOD: use query text)
apps/backend/app/services/regulation_ingestion_service.py (MOD: embed on ingest)
infra/supabase/migrations/2026-05-27_pgvector_indexes.sql (NEW)
apps/backend/app/jobs/backfill_embeddings.py   (NEW)
apps/backend/tests/test_embedding_provider.py  (NEW)
apps/backend/tests/test_vector_search.py       (NEW)
apps/backend/tests/test_search_regulation_tool_query.py (NEW)
```

## Tasks

### Embedding provider

- [ ] `embedding_provider.py`에 두 구현:
  - `GeminiEmbeddingProvider`: `gemini-embedding-001`, 3072차원, batch 호출 지원.
  - `DeterministicHashEmbeddingProvider`: 오프라인/테스트용. 동일 입력은 동일 벡터 보장. (단순 SHA → float 변환).
- [ ] factory `get_embedding_provider()`: 설정 우선순위 = Gemini key 있음 → Gemini, 없음 → deterministic. 운영 환경에서 deterministic으로 떨어지면 startup 경고 로그.
- [ ] 기존 `app/rag/embeddings.py`는 위 두 구현을 re-export하는 얇은 facade로 축소. 직접 호출하던 코드는 모두 provider 경유로 변경.

### Vector search

- [ ] `vector_search.py`:
  - `cosine_search(supabase, embedding, top_k, filters) -> list[RegulationChunkHit]`.
  - SQL: `select id, version_id, chunk_text, risk_categories, product_type, 1 - (embedding <=> :embedding) as similarity from regulation_chunks where ... order by embedding <=> :embedding limit :k`.
  - Supabase RPC 대안: pgvector를 SQL Editor에서 인덱스만 만들고 REST PostgREST `rpc/`로 호출. function `match_regulation_chunks(query_embedding, match_count, product_type, risk_categories)` 생성.
- [ ] `infra/supabase/migrations/2026-05-27_pgvector_indexes.sql`:
  - `create extension if not exists vector;`
  - `create index on regulation_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);`
  - `match_regulation_chunks` SQL function.

### Repository integration

- [ ] `regulation_docs_repo.py`에 `vector_search(query_text, risk_categories, product_type, limit) -> list[RegulationDoc]`.
  - 흐름: query_text → embedding → cosine_search → version 메타 join → dedupe by version_id → top N.
  - Gemini 미설정 시 deterministic provider 사용 (관련도는 낮지만 demo는 가능).
- [ ] 기존 `search()` 메서드는 보존. agent tool은 `vector_search`를 1차로 호출하고 결과 부족(top_similarity < threshold) 시 기존 카테고리 필터 결과로 보강.

### Tool 변경

- [ ] `search_regulation` tool 입력에 `query: str` 추가. 우선순위: query 있음 → vector_search, 없음 → 기존 search.
- [ ] System prompt(Day 17)에 안내 추가: "Prefer providing a focused query string when calling search_regulation."

### Ingestion 통합

- [ ] `regulation_ingestion_service.py`에서 chunk insert 직전에 embedding 계산. batch (예: 32개씩) 호출.
- [ ] embedding 실패 시 chunk는 NULL embedding으로 저장하고 warning 기록. backfill job이 이후에 채움.

### Backfill job

- [ ] `app/jobs/backfill_embeddings.py`: `regulation_chunks where embedding is null` 배치 처리. CLI `python -m app.jobs.backfill_embeddings --batch 64`.

### Tests

- [ ] `test_embedding_provider.py`: deterministic provider 동일 입력 동일 출력, gemini provider는 fake transport.
- [ ] `test_vector_search.py`: in-memory fake Supabase. embedding 비교 로직(코사인) 단위 테스트.
- [ ] `test_search_regulation_tool_query.py`: tool에 query 주면 vector path, 안 주면 category path. 결과 schema 검증.

## Done When

- 새 ingestion 시 chunk가 embedding과 함께 저장된다.
- `search_regulation` tool이 query text 기반으로 의미적으로 가까운 chunk를 반환한다.
- Gemini 미설정 환경에서도 deterministic embedding으로 demo path가 동작한다 (정확도 낮음 표시).
- `match_regulation_chunks` RPC가 Supabase에서 호출 가능하다.
- `pytest`, `ruff` 통과.

## Test Harness

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q tests/test_embedding_provider.py tests/test_vector_search.py tests/test_search_regulation_tool_query.py

# 수동: agent run에 query를 강제
curl -X POST http://localhost:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{"text": "원금 보장처럼 보이는 표현이 들어있는지 확인해줘"}'

# backfill
.venv/bin/python -m app.jobs.backfill_embeddings --batch 64
```

## Risks / Notes

- pgvector 인덱스 `ivfflat lists=100`은 chunk 수가 적을 때(<10000) 오히려 sequential scan보다 느릴 수 있다. 데이터 양에 따라 `hnsw`로 교체 검토. Day 19 종료 시점에는 ivfflat로 충분.
- Gemini embedding API 요금/쿼터 확인. 1회 ingestion 시 chunk 수가 폭증하면 batch 제한 필요.
- 한국어 임베딩 품질은 모델별 편차가 있다. `gemini-embedding-001`가 한국어를 잘 다루지 못하면 Week 4에서 `gemini-embedding-2` 또는 multilingual-e5 등으로 교체 가능하도록 provider 인터페이스를 유지.
- query 인자가 너무 길거나 짧으면 검색 품질이 떨어진다. tool layer에서 길이 검증(예: 5~300자) 후 truncation/expansion.

## Completion Log

- Status: DONE (2026-05-24)
- Implemented files:
  - `apps/backend/app/rag/embedding_provider.py`
  - `apps/backend/app/rag/embeddings.py`
  - `apps/backend/app/rag/vector_search.py`
  - `apps/backend/app/repositories/regulation_docs_repo.py`
  - `apps/backend/app/services/regulation_ingestion_service.py`
  - `apps/backend/app/jobs/backfill_embeddings.py`
  - `infra/supabase/migrations/2026-05-27_pgvector_indexes.sql`
  - `apps/backend/tests/test_embedding_provider.py`
  - `apps/backend/tests/test_vector_search.py`
  - `apps/backend/tests/test_search_regulation_tool_query.py`
- Test commands executed:
  - `ruff check app tests`
  - `docker run --rm --add-host=host.docker.internal:host-gateway -e OPENAI_BASE_URL=http://host.docker.internal:18080/v1 ... "ruff check app tests && pytest"`
- Test result summary: Docker backend validation passed: 109 passed, 1 warning. Local LLM integration smoke executed and passed.
- Known issues:
  - Gemini embedding provider is implemented, fake-transport tested, and smoke-tested with the real API key using `gemini-embedding-001`/`gemini-embedding-2`. The removed `text-embedding-004` default returned 404.
  - Supabase backfill job uses the existing REST helper and scans a limited batch; larger production backfills may need pagination.
