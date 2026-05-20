# Slice 06 — P1 Tests, CI, Docker, and Env Cleanup

## Goal

Make the project safer to change and easier to deploy by improving test coverage, CI workflows, Docker validation, and environment handling.

## Problems to fix

1. Backend CI does not include `infra/supabase/**` path changes.
2. Frontend CI uses `npm install` even though `package-lock.json` exists.
3. Docker Compose currently uses `.env.example` as an env file.
4. Placeholder env values may be treated as real configured secrets.
5. There are not enough API contract tests.

## Files to modify

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

## CI requirements

### Backend CI

Path filters should include:

```yaml
paths:
  - "apps/backend/**"
  - "infra/supabase/**"
  - ".github/workflows/backend-ci.yml"
```

Commands:

```bash
ruff check app tests
pytest
```

### Frontend CI

Use `npm ci` if `package-lock.json` exists.

Commands:

```bash
npm ci
npm run lint
npm run typecheck
npm run build
```

## Docker requirements

Use real local env file:

```yaml
env_file:
  - ./apps/backend/.env
```

Do not use `.env.example` for actual service execution unless explicitly running in demo fallback mode.

If `.env` is missing, document the expected behavior clearly.

## Backend test requirements

Add or confirm tests for:

- `RuleEngine`
- `/v1/health`
- `/v1/compliance/analyze`
- `/v1/compliance/evidence`
- `/v1/compliance/rewrite`
- `/v1/compliance/approve`
- fallback mode without Supabase/Gemini
- Gemini JSON parser

## Required Deliverables

- [x] Backend CI path filters include Supabase infra changes.
- [x] Frontend CI uses `npm ci`.
- [x] Docker Compose no longer uses `.env.example` as real env.
- [x] Placeholder secrets are not treated as configured.
- [x] Backend API tests added.
- [x] README updated with correct env and Docker instructions.

## Test Harness

```bash
# backend
cd apps/backend
ruff check app tests
pytest

# frontend
cd apps/frontend
npm ci
npm run lint
npm run typecheck
npm run build

# docker
cd ../..
docker compose up --build backend
curl http://localhost:8000/v1/health
```


## Implementation Completion

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
- Test result summary:
  - Backend ruff passed.
  - Backend pytest passed: `26 passed, 1 warning`.
  - Frontend Docker `npm ci`, typecheck, lint, and build passed.
  - Backend Docker image built successfully.
  - Backend container health check returned HTTP 200 on `http://localhost:18000/v1/health`.
- Known issues:
  - Local port `8000` was already allocated, so the final container health check used host port `18000`.
  - Frontend `npm ci` reported existing npm audit warnings.
- Next recommended step:
  - Proceed to the next Week 2 slice after redeploying the CI/Docker cleanup changes if public verification is needed.

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
