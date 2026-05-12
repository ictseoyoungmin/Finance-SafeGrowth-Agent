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

Health check:

```bash
curl http://localhost:8000/v1/health
```

## Local Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

The Vite dev server defaults to `http://localhost:5173`.

## Secret Boundaries

- Frontend only receives backend API base URL values such as `VITE_API_BASE_URL`.
- `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` are backend-only.
- Rule-based compliance detection must work without Gemini or Supabase.
