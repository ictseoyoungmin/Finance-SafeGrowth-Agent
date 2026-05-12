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

- [ ] `infra/supabase/schema.sql`
- [ ] `infra/supabase/seed_regulation_docs.sql`
- [ ] vector search RPC
- [ ] `app/integrations/supabase_client.py`
- [ ] `app/integrations/gemini_client.py`
- [ ] `app/rag/retriever.py`
- [ ] `app/services/evidence_service.py`
- [ ] `app/services/rewrite_service.py`
- [ ] `/evidence` API
- [ ] `/rewrite` API
- [ ] fallback evidence/rewrite tests

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

- [ ] evidence_list 1개 이상 반환.
- [ ] conservative/marketing 수정안 둘 다 반환.
- [ ] Gemini/Supabase 미설정에도 API 200 또는 graceful fallback.
- [ ] seed SQL 문서화.

## Implementation Completion Placeholder

- Status: [ ] Not Started / [ ] In Progress / [ ] Completed
- Branch:
- Commit / PR:
- Implemented files:
  - 
- Test commands executed:
  - 
- Test result:
  - 
- Known issues:
  - 
- Fallback behavior:
  - 
- Next recommended task:
  -
