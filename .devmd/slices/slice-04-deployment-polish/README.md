# Slice 4 — Deployment, CI, Demo Polish, and Public Smoke

This slice is still **IN_PROGRESS**. Local Docker and build checks have passed, and deployment documentation exists, but the slice cannot be marked complete until the public Render/Vercel deployment is smoke-tested and Slice 3's browser UI flow is validated.

## Objective

Finish the Week 1 deployment/demo layer:

- CI workflows for backend and frontend
- Docker backend validation
- Render backend deployment guide
- Vercel frontend deployment guide
- Supabase setup and seed guide
- demo script and fallback plan
- public URL smoke checklist
- final visual check against `.devmd/mockup`

## Mapped Week 1 Day

- `.devmd/week1/day-07-deploy-ci-polish.md`

## Prerequisites

- Slice 0, Slice 1, and Slice 2 are complete.
- Slice 3 must at least run locally.
- Before marking this slice complete, Slice 3 must pass manual 5-screen browser validation.

## Current State

Already implemented:

- backend Dockerfile
- `docker-compose.yml`
- backend CI workflow
- frontend CI workflow
- Render deployment notes
- Vercel deployment notes
- Supabase setup notes
- demo script
- fallback plan
- local Docker health smoke

Still missing:

- public Render deployment smoke test
- public Vercel deployment smoke test
- public full demo scenario
- final confirmation that deployed UI matches `.devmd/mockup`

## Required Files

```text
apps/backend/Dockerfile
apps/backend/render.yaml
apps/frontend/vercel.json
docker-compose.yml
.github/workflows/backend-ci.yml
.github/workflows/frontend-ci.yml
docs/deployment/vercel.md
docs/deployment/render.md
docs/deployment/supabase.md
docs/demo/demo-script.md
docs/demo/fallback-plan.md
```

## Deployment Requirements

Render backend:

- Root Directory: `apps/backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health endpoint: `/v1/health`
- Document expected free-tier cold start behavior.

Vercel frontend:

- Root Directory: `apps/frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Set `VITE_API_BASE_URL` to the deployed Render backend URL.
- Do not expose backend-only secrets to Vercel.

Supabase:

- Apply `infra/supabase/schema.sql`.
- Apply `infra/supabase/seed_regulation_docs.sql`.
- Apply `infra/supabase/seed_demo_contents.sql` if demo records are needed.
- Store service-role keys only in backend runtime environment.

## Mockup and Demo Polish Requirements

Before public demo approval, confirm that the deployed frontend still follows the mockup set:

```text
.devmd/mockup/1_콘텐츠입력.png
.devmd/mockup/2_검토문장.png
.devmd/mockup/3_근거패널.png
.devmd/mockup/4_수정안비교.png
.devmd/mockup/5_최종승인요약.png
```

Public UI acceptance:

- The sidebar stepper is visible and highlights the current stage.
- Each screen uses the same core layout hierarchy as its mockup.
- Primary CTAs are obvious and consistently placed.
- Risk highlights are readable and do not break line flow.
- Evidence and rewrite cards fit without text clipping.
- Approval summary shows final text, risk information, evidence summary, and decision actions.
- Fallback mode is visible but not visually disruptive.
- Desktop and narrow viewport layouts have no overlapping text or controls.

## Verification

Local:

```bash
cd apps/backend
.venv/bin/ruff check app tests
.venv/bin/pytest

cd ../frontend
npm run lint
npm run typecheck
npm run build

cd ../..
docker compose up --build backend
curl http://localhost:8000/v1/health
docker compose down
```

Public smoke:

```bash
curl https://your-render-service.onrender.com/v1/health
```

Manual public demo:

1. Open the Vercel URL.
2. Confirm the frontend is calling the Render backend.
3. Run the standard demo sentence:

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

4. Complete all five screens.
5. Confirm fallback behavior is documented and acceptable if Supabase or Gemini is unavailable.

## Done Criteria

- [ ] Backend CI exists and passes on PR.
- [ ] Frontend CI exists and passes on PR.
- [x] Backend Docker build succeeds locally.
- [x] Dockerized backend `/v1/health` succeeds locally.
- [x] Render deployment docs exist.
- [x] Vercel deployment docs exist.
- [x] Supabase setup docs exist.
- [x] Demo script exists.
- [x] Fallback plan exists.
- [x] Docker Compose no longer uses `.env.example` as backend runtime env.
- [ ] Render public `/v1/health` succeeds.
- [ ] Vercel public UI opens.
- [ ] Public UI completes the standard 5-screen demo scenario.
- [ ] Deployed UI is checked against `.devmd/mockup`.

## Implementation Completion Placeholder

- Status: IN_PROGRESS
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `apps/backend/Dockerfile`
  - `apps/backend/render.yaml`
  - `apps/frontend/vercel.json`
  - `docker-compose.yml`
  - `.github/workflows/backend-ci.yml`
  - `.github/workflows/frontend-ci.yml`
  - `docs/deployment/vercel.md`
  - `docs/deployment/render.md`
  - `docs/deployment/supabase.md`
  - `docs/demo/demo-script.md`
  - `docs/demo/fallback-plan.md`
- Test commands executed:
  - `cd apps/backend && .venv/bin/ruff check app tests`
  - `cd apps/backend && .venv/bin/pytest`
  - `cd apps/frontend && npm run build`
  - `docker compose config`
  - `docker compose up --build backend`
  - `curl http://localhost:8000/v1/health`
  - `docker compose down`
- Test result:
  - Backend lint passed.
  - Backend pytest passed: 8 tests passed, 1 upstream PendingDeprecationWarning from Starlette/python-multipart.
  - Frontend build passed.
  - Docker Compose backend build succeeded.
  - Dockerized backend health returned `{"status":"ok","env":"development"}`.
  - 2026-05-19 update: `docker compose config` passed after changing backend env loading from `.env.example` to optional `apps/backend/.env`.
  - 2026-05-19 update: Dockerized backend rebuilt successfully and `/v1/health` returned `{"status":"ok","env":"development"}`.
- Known issues:
  - Public Render/Vercel deployment was not performed in this local environment.
  - Production URL smoke tests remain open.
  - Slice 3 still needs manual browser click-through or screenshot-based validation.
- Fallback behavior:
  - Demo fallback plan is documented in `docs/demo/fallback-plan.md`.
  - Backend and frontend remain deterministic if Gemini, Supabase, or backend API calls are unavailable.
- Next recommended task:
  - Complete Slice 3 browser and mockup validation, deploy backend/frontend to Render/Vercel, run public smoke tests, then mark Slice 3 and Slice 4 COMPLETE.
