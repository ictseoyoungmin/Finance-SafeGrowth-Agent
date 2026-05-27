# JB SafeGrowth Agent

JB SafeGrowth Agent is a monorepo MVP for a financial advertising compliance workflow:

1. Content input
2. Redline risk review
3. Evidence lookup
4. Rewrite comparison
5. Approval package

The frontend and backend are deployed separately, but developed together in this repository.

## Repository Layout

```text
apps/frontend      Vercel-targeted React/Vite app
apps/backend       Render-targeted FastAPI app
infra/supabase     Supabase schema, migrations, and seed data
docs               Demo, deployment, handover, and diagram notes
.github/workflows  Separate frontend/backend CI skeletons
```

## Local Backend

```bash
cd apps/backend
virtualenv --always-copy .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional local secrets live in `apps/backend/.env`. Leave it absent, or leave placeholder values such as
`replace-me`, to run the deterministic fallback demo without Gemini or Supabase.

Health check:

```bash
curl http://localhost:8000/v1/health
```

## Local Frontend

```bash
cd apps/frontend
npm ci
npm run dev
```

The Vite dev server defaults to `http://localhost:5173`.

## Docker Compose

The backend service reads `apps/backend/.env` when it exists. If the file is absent, the app starts in deterministic fallback mode and must still support the demo workflow without Gemini or Supabase.

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
```

Do not use `.env.example` as a runtime env file. It is only a template for local setup.

Frontend Docker verification should also use lockfile-based installs:

```bash
cd apps/frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

## Secret Boundaries

- Frontend only receives backend API base URL values such as `VITE_API_BASE_URL`.
- `GEMINI_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` are backend-only.
- Set `LLM_PROVIDER=openai_compatible` with `OPENAI_BASE_URL=http://host.docker.internal:18080/v1` when the backend container should use the shared local LLM server.
- Rule-based compliance detection must work without Gemini or Supabase.

## Determinism

For stable analyze/rewrite responses set `LLM_TEMPERATURE=0.0` (or `0.1`) on the backend.
Identical inputs are also served from an in-memory cache (TTL 15min). Bypass with `?refresh=1`.
See `docs/deployment/README.md` for the full env-var list.
