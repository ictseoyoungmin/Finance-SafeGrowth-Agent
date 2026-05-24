# Render Deployment

Deploy only the backend from the monorepo.

## Service Settings

- Service Type: Web Service
- Root Directory: `apps/backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/v1/health`
- Production URL: `https://finance-safegrowth-agent.onrender.com`

`apps/backend/render.yaml` captures these defaults for Render Blueprint setup.

## Environment Variables

```dotenv
APP_ENV=production
CORS_ORIGINS=https://finance-safe-growth-agent.vercel.app
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
LLM_PROVIDER=gemini
OPENAI_BASE_URL=http://host.docker.internal:18080/v1
OPENAI_API_KEY=local-not-required
OPENAI_MODEL=gemma-4-local
LLM_TIMEOUT_SECONDS=600
LLM_THINKING_ENABLED=false
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.2
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=...
```

`GEMINI_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` must stay backend-only.

Current Gemini production setup:

- Render has the selected `LLM_PROVIDER` settings. Gemini requires `GEMINI_API_KEY`; local/OpenAI-compatible mode requires `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.
- Vercel does not need Gemini secrets or model settings.
- Gemini request/parsing failures are logged server-side and fall back safely; logs must not include API keys.

Current Supabase production setup:

- Render has `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.
- `SUPABASE_URL` is the project base URL: `https://eszuojttibhkazrtqrqx.supabase.co`.
- `SUPABASE_URL` must not include `/rest/v1/`; the backend adds the REST path internally.
- Vercel does not contain Supabase secrets.
- If Supabase REST returns `403 Forbidden`, check that SQL grants were applied for the public tables used by the Data API.

## Cold Start Warm-Up

Render free services can sleep after inactivity. Before a public demo, warm the backend:

```bash
curl https://finance-safegrowth-agent.onrender.com/v1/health
```

Expected response:

```json
{"status":"ok","env":"production"}
```

If the first call is slow or times out, retry once after 30-60 seconds.

## Public Smoke Result

Completed on 2026-05-20:

- `/v1/health` succeeded.
- `/v1/compliance/analyze` succeeded.
- CORS from `https://finance-safe-growth-agent.vercel.app` to this Render backend works.
- Supabase schema and regulation seed SQL were applied successfully.
- Initial Supabase REST insert returned `403 Forbidden`; SQL grants were applied through Supabase SQL Editor.
- Public `/v1/compliance/analyze` smoke returned HTTP 200, `risk_level=HIGH`, and a UUID-compatible `content_id`.

Live persistence verification:

- API smoke: verified.
- Supabase Table Editor row check: verify `contents`, `risk_results`, and `audit_logs(action=analyze)` after the grant.

Known issue:

- Render Free tier cold start can delay the first request. Warm up `/v1/health` before demo.
- After redeploying Day 11 follow-up changes, run a public `/v1/compliance/rewrite` smoke and inspect Render logs to distinguish Gemini success from deterministic fallback.
