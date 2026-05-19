# Day 9 — Persistence, ID, and Audit

## Goal

`/analyze` 결과가 실제로 저장되도록 하고, Supabase UUID schema와 맞지 않는 fake `content-{uuid}` 형식을 제거한다.

참조 문서:

- `.devmd/phase2/01-p0-backend-persistence/README.md`

## Target Behavior

Supabase configured:

- `contents`에 원문과 metadata를 insert한다.
- `risk_results`에 분석 결과를 insert한다.
- `audit_logs`에 analyze action을 insert한다.
- API response의 `content_id`는 UUID string이다.

Supabase not configured:

- fallback mode로 crash 없이 동작한다.
- fallback `content_id`도 UUID-compatible string이다.
- fallback mode 여부가 로그나 service 경계에서 명확하다.

## Files

```text
apps/backend/app/core/config.py
apps/backend/app/integrations/supabase_client.py
apps/backend/app/repositories/contents_repo.py
apps/backend/app/repositories/risk_results_repo.py
apps/backend/app/repositories/audit_logs_repo.py
apps/backend/app/services/audit_service.py
apps/backend/app/services/analyze_service.py
apps/backend/tests/
```

## Tasks

- [ ] placeholder env 값(`replace-me`, empty string 등)을 configured로 보지 않게 한다.
- [ ] `ContentRepository.save_original()`이 real insert 또는 fallback UUID를 반환하게 한다.
- [ ] `RiskResultsRepository.save_analysis()`를 real/fallback 저장으로 구현한다.
- [ ] `AuditService.record_analysis()`가 audit log를 저장하게 한다.
- [ ] analyze API response shape를 유지한다.
- [ ] no-Supabase fallback test를 추가한다.
- [ ] analyze API contract test를 추가하거나 갱신한다.

## Test

```bash
cd apps/backend
ruff check app tests
pytest
```

Smoke:

```bash
curl -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"product_type":"투자상품","channel":"앱 푸시","target_customer":"30대 직장인","language":"ko","original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."}'
```

## Done When

- `content_id`가 UUID-compatible이다.
- Supabase 미설정 상태에서도 `/analyze`가 성공한다.
- analyze 결과, risk result, audit action 저장 경로가 모두 구현되어 있다.
- 관련 tests가 통과한다.

## Completion Log

- Status: NOT_STARTED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Known issues:
  - TBD

