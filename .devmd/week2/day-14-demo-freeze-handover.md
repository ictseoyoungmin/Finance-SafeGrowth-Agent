# Day 14 — Demo Freeze and Handover

## Goal

공개 데모 평가를 위해 안정적인 demo path를 고정하고, smoke test와 known issues를 문서화한다.

참조 문서:

- `.devmd/phase2/07-p2-demo-hardening/README.md`
- `docs/demo/`
- `docs/deployment/`
- `docs/handover/`

## Files

```text
README.md
docs/demo/README.md
docs/demo/demo-script.md
docs/demo/fallback-plan.md
docs/deployment/README.md
docs/handover/README.md
```

선택 구현:

```text
apps/backend/app/schemas/regulation_impact.py
apps/backend/app/services/regulation_impact_service.py
apps/backend/app/api/v1/compliance.py
```

## Tasks

- [x] 표준 demo sentence 기준 5-step script를 갱신한다.
- [ ] backend health, analyze, evidence, rewrite, approve, report smoke test를 문서화한다.
- [x] fallback mode 의도와 한계를 정리한다.
- [ ] deployment checklist를 최신 env/API 기준으로 갱신한다.
- [ ] known issues와 workaround를 작성한다.
- [ ] 필요하면 regulation-impact placeholder API를 추가한다.
- [ ] handover README에 다음 개발자가 시작할 지점을 남긴다.

## Added Hardening Scope

The first Day 14 implementation pass focused on the scoring risk reported by the user:

- Previously, Gemini-unavailable rewrite responses returned fixed demo copy, so alternate input could still show standard demo correction text.
- The UI did not distinguish parsed Gemini output from backend deterministic fallback because both returned HTTP 200.
- RuleEngine coverage was narrow enough that non-demo risky financial phrasing could be under-highlighted.

Implemented:

- `/v1/compliance/rewrite` now returns `source: "gemini" | "fallback"`.
- Gemini parse success sets `source = "gemini"`.
- Backend deterministic fallback now generates rewrite text from the stored/fallback original text and detected spans.
- Rewrite UI shows either `Gemini 검수 결과` or `Deterministic fallback`.
- RuleEngine now detects additional common financial ad risk variants:
  - `업계 최고`, `최고`
  - `확정 수익률`, `고정 수익`, `매월 N% 지급`
  - `위험 없이`, `리스크 없이`, `걱정 없이`
  - `원금 손실 없이`, `손실 없이`
- Overlapping rule hits are deduplicated so longer, clearer spans are highlighted.

## Demo Freeze Checklist

- [ ] frontend URL이 열린다.
- [ ] backend `/v1/health`가 OK를 반환한다.
- [ ] Supabase seed data가 준비되어 있거나 fallback mode가 명확하다.
- [ ] Gemini API key가 설정되어 있거나 fallback rewrite가 의도적으로 켜져 있다.
- [ ] standard demo sentence가 5개 화면을 통과한다.
- [ ] analyze 결과가 HIGH risk를 반환한다.
- [ ] evidence가 관련 snippets를 반환한다.
- [ ] rewrite가 conservative/marketing variants를 반환한다.
- [ ] approval 저장 또는 fallback 저장이 성공한다.
- [ ] report payload를 확인할 수 있다.
- [ ] known issues가 문서화되어 있다.

## Full Check

```bash
cd apps/backend
ruff check app tests
pytest

cd ../frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

## Done When

- demo path가 문서와 실제 동작에서 일치한다.
- 배포/평가자가 README와 docs만 보고 smoke test를 실행할 수 있다.
- 남은 risk가 known issues로 정리되어 있다.

## Completion Log

- Status: IN_PROGRESS
- Implemented files:
  - [x] `apps/backend/app/schemas/rewrite.py`
  - [x] `apps/backend/app/services/rewrite_service.py`
  - [x] `apps/backend/app/rules/rule_engine.py`
  - [x] `apps/backend/tests/conftest.py`
  - [x] `apps/backend/tests/test_api_rewrite.py`
  - [x] `apps/backend/tests/test_rewrite_service.py`
  - [x] `apps/backend/tests/test_rule_engine.py`
  - [x] `apps/frontend/src/features/compliance/api.ts`
  - [x] `apps/frontend/src/features/compliance/store.ts`
  - [x] `apps/frontend/src/features/compliance/types.ts`
  - [x] `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
  - [x] `apps/frontend/src/styles.css`
  - [x] `docs/demo/README.md`
  - [x] `docs/demo/demo-script.md`
  - [x] `docs/demo/fallback-plan.md`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 90 .venv/bin/pytest -q`
  - [x] `docker run --rm -v /tmp/dacon-day14-frontend-full:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"`
- Known issues:
  - Public Vercel/Render smoke after redeploy is still pending.
  - Frontend `npm ci` reports existing npm audit warnings.
  - TestClient requests can hang inside the sandbox because of isolation/proxy behavior, so backend pytest verification was run outside the sandbox.
