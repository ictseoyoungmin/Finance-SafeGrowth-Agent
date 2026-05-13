# Slice 2 — RAG + Gemini

이 slice README는 agent가 해당 구현 단위를 독립적으로 수행할 수 있도록 통합 지시문, 구현 범위, 테스트 하네스, 완료 placeholder를 포함한다.


## Objective

Supabase/pgvector 기반 근거 검색과 Gemini judge/rewrite/fallback을 구현한다.

## Mapped Days

Day 4, Day 5

## Prerequisites

Slice 1 완료. Analyze API와 RuleEngine이 동작해야 한다. Supabase 프로젝트 또는 mock repository 사용 가능.

## Integrated Instructions

1. Supabase가 없어도 fallback evidence를 반환한다.
2. Gemini API key가 없어도 fallback rewrite를 반환한다.
3. RAG seed는 PoC용 샘플임을 명시한다.
4. Gemini 응답은 JSON schema로 파싱하고 파싱 실패 시 fallback한다.
5. prompt 전문은 audit에 저장하지 말고 hash만 저장할 수 있도록 interface를 둔다.

## Required Deliverables

- [x] `infra/supabase/schema.sql`
- [x] `infra/supabase/seed_regulation_docs.sql`
- [x] vector search RPC
- [x] `app/integrations/supabase_client.py`
- [x] `app/integrations/gemini_client.py`
- [x] `app/rag/retriever.py`
- [x] `app/services/evidence_service.py`
- [x] `app/services/rewrite_service.py`
- [x] `/evidence` API
- [x] `/rewrite` API
- [x] fallback evidence/rewrite tests

## Test Harness

```bash
cd apps/backend
pytest tests/test_api_evidence.py tests/test_api_rewrite.py

curl -X POST http://localhost:8000/v1/compliance/evidence \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","risk_categories":["확정 수익 오인","원금 보장 오인"],"product_type":"투자상품"}'

curl -X POST http://localhost:8000/v1/compliance/rewrite \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","mode":"marketing_balanced"}'
```

## Done Criteria

- [x] evidence_list 1개 이상 반환.
- [x] conservative/marketing 수정안 둘 다 반환.
- [x] Gemini/Supabase 미설정에도 API 200 또는 graceful fallback.
- [x] seed SQL 문서화.

## Implementation Completion Placeholder

- Status: COMPLETE
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `infra/supabase/schema.sql`
  - `infra/supabase/seed_regulation_docs.sql`
  - `infra/supabase/seed_demo_contents.sql`
  - `apps/backend/app/api/v1/compliance.py`
  - `apps/backend/app/core/config.py`
  - `apps/backend/app/schemas/evidence.py`
  - `apps/backend/app/schemas/rewrite.py`
  - `apps/backend/app/integrations/supabase_client.py`
  - `apps/backend/app/integrations/gemini_client.py`
  - `apps/backend/app/repositories/regulation_docs_repo.py`
  - `apps/backend/app/rag/chunker.py`
  - `apps/backend/app/rag/embeddings.py`
  - `apps/backend/app/rag/retriever.py`
  - `apps/backend/app/services/evidence_service.py`
  - `apps/backend/app/services/rewrite_service.py`
  - `apps/backend/tests/test_rag_retriever.py`
  - `apps/backend/tests/test_api_evidence.py`
  - `apps/backend/tests/test_api_rewrite.py`
- Test commands executed:
  - `cd apps/backend && .venv/bin/ruff check app tests`
  - `cd apps/backend && .venv/bin/pytest`
  - `cd apps/backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - `curl -X POST http://localhost:8000/v1/compliance/evidence -H 'Content-Type: application/json' -d '{"content_id":"demo-content","risk_categories":["확정 수익 오인","원금 보장 오인"],"product_type":"투자상품"}'`
  - `curl -X POST http://localhost:8000/v1/compliance/rewrite -H 'Content-Type: application/json' -d '{"content_id":"demo-content","mode":"marketing_balanced"}'`
- Test result:
  - `ruff check app tests` passed.
  - `pytest` passed: 8 tests passed, 1 upstream PendingDeprecationWarning from Starlette/python-multipart.
  - `/v1/compliance/evidence` returned fallback docs `doc-demo-001` and `doc-demo-002`.
  - `/v1/compliance/rewrite` returned conservative and marketing rewrite text plus change explanations.
- Known issues:
  - Supabase RPC/schema was authored but not executed against a live Supabase project in this environment.
  - Gemini wrapper is present, but no real Gemini call was exercised because `GEMINI_API_KEY` is not configured.
- Fallback behavior:
  - Evidence uses in-process demo regulation docs when Supabase is unavailable.
  - Rewrite uses deterministic conservative/marketing fallback text when Gemini is unavailable or returns unparsable JSON.
- Next recommended task:
  - Start Slice 3: implement frontend 5-step workflow, API client, redline rendering, evidence/rewrite screens, and approval package.
