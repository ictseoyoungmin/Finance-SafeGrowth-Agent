# Render Deployment

Deploy only the backend from the monorepo.

## Service Settings

- Service Type: Web Service
- Root Directory: `apps/backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/v1/health`

`apps/backend/render.yaml` captures these defaults for Render Blueprint setup.

## Environment Variables

```dotenv
APP_ENV=production
CORS_ORIGINS=https://your-vercel-domain.vercel.app
GEMINI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=...
```

`GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` must stay backend-only.

## Cold Start Warm-Up

Render free services can sleep after inactivity. Before a public demo, warm the backend:

```bash
curl https://your-render-service.onrender.com/v1/health
```

Expected response:

```json
{"status":"ok","env":"production"}
```

If the first call is slow or times out, retry once after 30-60 seconds.
