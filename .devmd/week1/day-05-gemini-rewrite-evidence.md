# Day 5 — Gemini Judge / Evidence API / Rewrite API

## 목표

근거 검색, Gemini judge/rewrite, fallback 응답을 연결하여 Agent가 “근거를 찾고 수정안을 생성하는” 단계까지 구현한다.

## 매핑 Slice

- `slices/slice-02-rag-gemini/README.md`

## 작업 범위

1. Gemini client wrapper 구현.
2. Prompt builder 구현.
3. EvidenceService 및 `/evidence` API 구현.
4. RewriteService 및 `/rewrite` API 구현.
5. Gemini failure fallback 구현.
6. evidence/rewrite API tests.

## Required files

```text
apps/backend/app/integrations/gemini_client.py
apps/backend/app/services/evidence_service.py
apps/backend/app/services/rewrite_service.py
apps/backend/app/schemas/evidence.py
apps/backend/app/schemas/rewrite.py
apps/backend/tests/test_api_evidence.py
apps/backend/tests/test_api_rewrite.py
```

## Gemini Client Rule

- 모든 Gemini 호출은 `integrations/gemini_client.py`에서만 수행한다.
- API key는 backend env에서만 읽는다.
- 응답은 JSON schema로 파싱한다.
- 실패 시 fallback 응답을 반환한다.

## Fallback Rewrite

Gemini 실패 시 최소 응답:

```json
{
  "revised_text_conservative": "본 상품은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, 가입 전 상품설명서와 유의사항을 반드시 확인하시기 바랍니다.",
  "revised_text_marketing": "시장 상황에 따라 수익은 변동될 수 있으며 원금 손실 가능성이 있습니다. 가입 전 상품설명서와 유의사항을 확인해 주세요."
}
```

## 테스트 / 검증

```bash
cd apps/backend
pytest tests/test_api_evidence.py tests/test_api_rewrite.py
```

Smoke:

```bash
curl -X POST http://localhost:8000/v1/compliance/evidence \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","risk_categories":["확정 수익 오인","원금 보장 오인"],"product_type":"투자상품"}'

curl -X POST http://localhost:8000/v1/compliance/rewrite \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","mode":"marketing_balanced"}'
```

## 산출물

- [x] GeminiClient
- [x] JSON prompt builder
- [x] Evidence API
- [x] Rewrite API
- [x] fallback evidence
- [x] fallback rewrite
- [x] tests

## 완료 기준

- [x] evidence_list 1개 이상 반환.
- [x] conservative/marketing rewrite 둘 다 반환.
- [x] Gemini key가 없어도 fallback으로 API가 200 응답 가능.

## 완료 상태

- Status: COMPLETE
- 완료 근거: `.devmd/slices/slice-02-rag-gemini/README.md`
