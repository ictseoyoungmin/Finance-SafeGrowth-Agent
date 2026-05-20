# Day 13 — CI, Docker, Env, and Test Cleanup

## Goal

P0/P1 구현 후 regression을 막기 위해 CI, Docker, env handling, API contract tests를 정리한다.

참조 문서:

- `.devmd/phase2/06-p1-test-ci-docker/README.md`

## Files

```text
.github/workflows/backend-ci.yml
.github/workflows/frontend-ci.yml
docker-compose.yml
apps/backend/app/core/config.py
apps/backend/app/integrations/supabase_client.py
apps/backend/tests/
apps/frontend/package.json
README.md
```

## Tasks

- [x] backend CI path filter에 `infra/supabase/**`를 포함한다.
- [x] frontend CI는 lockfile 기준 `npm ci`를 사용한다.
- [x] Docker Compose가 `.env.example`을 runtime env로 사용하지 않게 한다.
- [x] `.env`가 없을 때 fallback/demo mode 기대 동작을 README에 문서화한다.
- [x] placeholder secret 값이 configured로 취급되지 않는지 test한다.
- [x] API contract tests를 health/analyze/evidence/rewrite/approve/report까지 확장한다.
- [x] backend와 frontend local checks를 실행한다.

## Test

Backend:

```bash
cd apps/backend
ruff check app tests
pytest
```

Frontend:

```bash
cd apps/frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

Docker:

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
```

## Done When

- CI commands와 local commands가 일치한다.
- Docker env 경계가 README와 compose 파일에서 명확하다.
- 핵심 API가 tests로 보호된다.

## Completion Log

- Status: COMPLETE
- Implemented files:
  - [x] `.github/workflows/backend-ci.yml`
  - [x] `.github/workflows/frontend-ci.yml`
  - [x] `docker-compose.yml`
  - [x] `apps/backend/app/integrations/gemini_client.py`
  - [x] `apps/backend/tests/test_api_approval_report.py`
  - [x] `apps/backend/tests/test_gemini_parser.py`
  - [x] `README.md`
- Test commands executed:
  - [x] `cd apps/backend && .venv/bin/ruff check app tests`
  - [x] `cd apps/backend && timeout 60 .venv/bin/pytest -q`
  - [x] `docker run --rm -v /tmp/dacon-day13-frontend-clean:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"`
  - [x] `docker compose -f docker-compose.yml up --build backend`
  - [x] `docker compose -f docker-compose.yml run --rm -p 18000:8000 backend`
  - [x] `curl -s -i http://localhost:18000/v1/health`
- Known issues:
  - Port `8000` was already allocated in the local environment, so the compose image was built with `docker compose up --build backend`, then the backend container health check was verified on host port `18000`.
  - Frontend Docker verification reported existing npm audit warnings but typecheck, lint, and build passed.
