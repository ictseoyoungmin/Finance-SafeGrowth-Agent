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

- [ ] Backend CI path filters include Supabase infra changes.
- [ ] Frontend CI uses `npm ci`.
- [ ] Docker Compose no longer uses `.env.example` as real env.
- [ ] Placeholder secrets are not treated as configured.
- [ ] Backend API tests added.
- [ ] README updated with correct env and Docker instructions.

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


## Implementation Completion Placeholder

- Status: NOT_STARTED / IN_PROGRESS / COMPLETE / BLOCKED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Test result summary:
  - TBD
- Known issues:
  - TBD
- Next recommended step:
  - TBD

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
