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

- [x] `app/main.py`
- [x] `app/core/config.py`
- [x] `app/api/v1/router.py`
- [x] `app/api/v1/compliance.py`
- [x] `app/schemas/compliance.py`
- [x] `app/rules/rule_engine.py`
- [x] `app/services/analyze_service.py`
- [x] `app/services/audit_service.py`
- [x] repository skeleton
- [x] health/analyze/rule tests

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

- [x] health test 통과.
- [x] RuleEngine test 통과.
- [x] analyze API에서 `risk_level=HIGH`.
- [x] flagged_spans 3개 이상 반환.

## Implementation Completion Placeholder

- Status: COMPLETE
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `apps/backend/app/main.py`
  - `apps/backend/app/api/v1/router.py`
  - `apps/backend/app/api/v1/compliance.py`
  - `apps/backend/app/core/errors.py`
  - `apps/backend/app/core/logging.py`
  - `apps/backend/app/schemas/compliance.py`
  - `apps/backend/app/rules/rule_engine.py`
  - `apps/backend/app/services/analyze_service.py`
  - `apps/backend/app/services/audit_service.py`
  - `apps/backend/app/repositories/contents_repo.py`
  - `apps/backend/app/repositories/risk_results_repo.py`
  - `apps/backend/tests/test_rule_engine.py`
  - `apps/backend/tests/test_api_analyze.py`
- Test commands executed:
  - `cd apps/backend && .venv/bin/ruff check app tests`
  - `cd apps/backend && .venv/bin/pytest`
  - `cd apps/backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - `curl http://localhost:8000/v1/health`
  - `curl -X POST http://localhost:8000/v1/compliance/analyze -H 'Content-Type: application/json' -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."}'`
- Test result:
  - `ruff check app tests` passed.
  - `pytest` passed: 5 tests passed, 1 upstream PendingDeprecationWarning from Starlette/python-multipart.
  - `/v1/health` returned `{"status":"ok","env":"development"}`.
  - `/v1/compliance/analyze` returned `risk_level=HIGH` with four flagged spans: `누구나`, `연 8% 수익`, `안정적으로`, `원금 걱정 없이`.
- Known issues:
  - Repositories and audit service are deterministic in-process skeletons only; persistence is deferred to the Supabase/RAG slice.
- Fallback behavior:
  - Analyze works without Gemini or Supabase. RuleEngine fixes the candidate spans, and repository/audit writes are no-op local skeletons.
- Next recommended task:
  - Start Slice 2: add Supabase schema/seed data, RAG retrieval skeleton/RPC design, Gemini wrapper, evidence/rewrite APIs, and deterministic fallbacks.
