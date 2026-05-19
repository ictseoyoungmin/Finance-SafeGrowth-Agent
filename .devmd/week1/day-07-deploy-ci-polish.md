# Day 7 — Deployment, CI, Demo Polish, and Public Smoke

## Goal

Prepare the project for a public demo using Vercel, Render, and Supabase free-tier friendly deployment paths.

Mapped slice:

- `.devmd/slices/slice-04-deployment-polish/README.md`

## Current Status

Local Docker/build checks and deployment documentation exist. This day remains open until public Render/Vercel smoke tests and the full public demo scenario are completed.

## Work Scope

1. Validate backend Dockerfile.
2. Run Docker Compose backend smoke.
3. Maintain backend CI workflow.
4. Maintain frontend CI workflow.
5. Document Vercel root directory and build settings.
6. Document Render root directory and start command.
7. Document Supabase schema and seed process.
8. Maintain demo script.
9. Document Render cold-start handling.
10. Confirm deployed UI still matches `.devmd/mockup`.

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

## Render Settings

```text
Root Directory: apps/backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check: /v1/health
```

## Vercel Settings

```text
Root Directory: apps/frontend
Build Command: npm run build
Output Directory: dist
Environment: VITE_API_BASE_URL=<Render backend URL>
```

Frontend deployment must not expose Gemini, Supabase service-role, or database secrets.

## Smoke Tests

Local:

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
docker compose down
```

Production:

```bash
curl https://your-render-service.onrender.com/v1/health
```

## Public Demo Scenario

1. Open the Vercel URL.
2. Confirm the app calls the Render backend.
3. Use the standard demo sentence:

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

4. Complete all 5 screens.
5. Confirm fallback behavior if Gemini or Supabase is unavailable.
6. Compare the deployed UI against `.devmd/mockup`.

## Deliverables

- [x] Docker backend build success
- [x] backend CI
- [x] frontend CI
- [x] deployment docs
- [x] demo script
- [x] fallback plan
- [x] docker compose uses optional `apps/backend/.env` instead of `.env.example`
- [ ] public Render health smoke
- [ ] public Vercel UI smoke
- [ ] public 5-screen demo
- [ ] deployed mockup alignment pass

## Done Criteria

- [ ] CI runs on GitHub PRs.
- [ ] Render `/v1/health` returns OK.
- [ ] Vercel public URL opens the UI.
- [ ] The standard demo scenario succeeds at least once.
- [ ] The deployed UI has been checked against the mockups.
