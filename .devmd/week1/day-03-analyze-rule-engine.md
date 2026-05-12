# Day 3 — Analyze API / RuleEngine / Audit Foundation

## 목표

표준 데모 문구를 분석하여 위험 span을 반환하는 `/v1/compliance/analyze`를 구현한다.

## 매핑 Slice

- `slices/slice-01-backend-core/README.md`

## 작업 범위

1. Pydantic schema 작성.
2. RuleEngine 구현.
3. AnalyzeService 구현.
4. Repository stub 또는 Supabase repository skeleton 작성.
5. audit service skeleton 작성.
6. RuleEngine unit test.
7. Analyze API test.

## Required files

```text
apps/backend/app/schemas/compliance.py
apps/backend/app/rules/rule_engine.py
apps/backend/app/services/analyze_service.py
apps/backend/app/services/audit_service.py
apps/backend/app/repositories/contents_repo.py
apps/backend/app/repositories/risk_results_repo.py
apps/backend/tests/test_rule_engine.py
apps/backend/tests/test_api_analyze.py
```

## RuleEngine MVP rules

- `누구나|무조건|반드시` → 과장 표현 / HIGH
- `연\s*\d+(\.\d+)?\s*%\s*수익` → 확정 수익 오인 / HIGH
- `안정적으로|안전하게` → 안정성 오인 / MEDIUM
- `원금\s*걱정\s*없이|원금\s*보장` → 원금 보장 오인 / HIGH

## API contract

`agent-guides/api-contract.md`의 Analyze section을 따른다.

## 테스트 / 검증

```bash
cd apps/backend
pytest tests/test_rule_engine.py tests/test_api_analyze.py
```

API smoke:

```bash
curl -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."}'
```

## 산출물

- [ ] AnalyzeRequest / AnalyzeResponse
- [ ] RuleEngine.scan()
- [ ] AnalyzeService.analyze()
- [ ] RuleEngine tests
- [ ] Analyze endpoint test
- [ ] audit record interface

## 완료 기준

- [ ] 표준 문구에서 3개 이상 위험 span 탐지.
- [ ] `risk_level=HIGH` 반환.
- [ ] 각 span에 start/end 또는 span_text fallback이 존재.
- [ ] DB 미연결 상태에서도 fallback repository로 API smoke 가능.
