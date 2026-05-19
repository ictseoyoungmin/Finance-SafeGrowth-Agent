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

- [ ] 표준 demo sentence 기준 5-step script를 갱신한다.
- [ ] backend health, analyze, evidence, rewrite, approve, report smoke test를 문서화한다.
- [ ] fallback mode 의도와 한계를 정리한다.
- [ ] deployment checklist를 최신 env/API 기준으로 갱신한다.
- [ ] known issues와 workaround를 작성한다.
- [ ] 필요하면 regulation-impact placeholder API를 추가한다.
- [ ] handover README에 다음 개발자가 시작할 지점을 남긴다.

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

- Status: NOT_STARTED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Known issues:
  - TBD

