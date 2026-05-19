# Day 11 — Rewrite Context and RAG Quality

## Goal

Rewrite와 evidence를 실제 검토 문맥에 맞게 개선한다. Gemini rewrite에는 원문, flagged spans, risk categories, evidence snippets를 넣고, evidence retrieval은 Supabase configured path를 사용한다.

참조 문서:

- `.devmd/phase2/03-p0-gemini-rewrite-context/README.md`
- `.devmd/phase2/04-p1-rag-quality/README.md`

## Target Behavior

Rewrite:

- frontend request는 `content_id`, `mode` 중심으로 유지한다.
- backend가 content/risk/evidence context를 repository에서 resolve한다.
- Gemini prompt가 original text, metadata, risk spans, evidence를 포함한다.
- fenced JSON, raw JSON, 설명 포함 JSON을 robust하게 parse한다.
- Gemini 실패 시 deterministic fallback rewrite를 반환한다.

Evidence:

- Supabase configured 상태에서는 `regulation_docs`를 query한다.
- product type과 risk categories 기반으로 filter한다.
- 결과가 없거나 DB가 없으면 fallback docs를 반환한다.

## Files

```text
apps/backend/app/services/rewrite_service.py
apps/backend/app/integrations/gemini_client.py
apps/backend/app/repositories/contents_repo.py
apps/backend/app/repositories/risk_results_repo.py
apps/backend/app/repositories/regulation_docs_repo.py
apps/backend/app/rag/retriever.py
apps/backend/app/services/evidence_service.py
apps/backend/app/schemas/evidence.py
apps/backend/tests/test_rewrite_service.py
apps/backend/tests/test_gemini_parser.py
apps/backend/tests/test_evidence_service.py
apps/backend/tests/test_regulation_docs_repo.py
```

## Tasks

- [ ] repository에 `get(content_id)`와 `get_latest_by_content_id(content_id)` 계열 조회를 추가한다.
- [ ] rewrite context resolver를 구현한다.
- [ ] Gemini prompt에 original text, metadata, flagged spans, risk categories, evidence snippets를 포함한다.
- [ ] JSON parser가 raw/fenced/substr JSON을 처리한다.
- [ ] Supabase regulation docs 조회 path를 구현한다.
- [ ] fallback evidence docs는 유지한다.
- [ ] parser edge case와 fallback rewrite tests를 추가한다.
- [ ] evidence filtering tests를 추가한다.

## Test

```bash
cd apps/backend
ruff check app tests
pytest tests/test_rewrite_service.py tests/test_gemini_parser.py tests/test_evidence_service.py tests/test_regulation_docs_repo.py
```

Smoke:

```bash
curl -X POST http://localhost:8000/v1/compliance/rewrite \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","mode":"marketing_balanced"}'

curl -X POST http://localhost:8000/v1/compliance/evidence \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","product_type":"투자상품","risk_categories":["확정 수익 오인","원금 보장 오인"]}'
```

## Done When

- rewrite response가 conservative/marketing rewrite와 changes를 안정적으로 반환한다.
- Gemini unavailable 상태에서도 demo flow가 이어진다.
- evidence API가 DB/fallback 양쪽에서 관련 snippets를 반환한다.
- 관련 tests가 통과한다.

## Completion Log

- Status: NOT_STARTED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Known issues:
  - TBD

