# Slice 1 — Backend Core

이 slice README는 agent가 해당 구현 단위를 독립적으로 수행할 수 있도록 통합 지시문, 구현 범위, 테스트 하네스, 완료 placeholder를 포함한다.


## Objective

FastAPI 기반 backend, RuleEngine, analyze API, audit 기초를 구현한다.

## Mapped Days

Day 2, Day 3

## Prerequisites

Slice 0 완료. `apps/backend`가 존재하고 virtualenv 실행 가능.

## Integrated Instructions

1. RuleEngine이 LLM보다 먼저 위험 후보를 고정한다.
2. Analyze API는 Gemini/Supabase 미설정 상태에서도 fallback repository로 동작해야 한다.
3. start/end index를 가능한 한 정확히 반환한다.
4. `risk_level`은 가장 높은 severity 기준으로 산정한다.
5. audit service는 실제 DB 저장이 아직 없어도 interface를 먼저 고정한다.

## Required Deliverables

- [ ] `app/main.py`
- [ ] `app/core/config.py`
- [ ] `app/api/v1/router.py`
- [ ] `app/api/v1/compliance.py`
- [ ] `app/schemas/compliance.py`
- [ ] `app/rules/rule_engine.py`
- [ ] `app/services/analyze_service.py`
- [ ] `app/services/audit_service.py`
- [ ] repository skeleton
- [ ] health/analyze/rule tests

## Test Harness

```bash
cd apps/backend
ruff check app tests
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/v1/health
curl -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."}'
```

## Done Criteria

- [ ] health test 통과.
- [ ] RuleEngine test 통과.
- [ ] analyze API에서 `risk_level=HIGH`.
- [ ] flagged_spans 3개 이상 반환.

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
