# Vercel Deployment

Deploy only the frontend from the monorepo.

## Project Settings

- Root Directory: `apps/frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Production URL: `https://finance-safe-growth-agent.vercel.app`

## Environment Variables

Set only backend API URLs in Vercel:

```dotenv
VITE_API_BASE_URL=https://finance-safegrowth-agent.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://finance-safegrowth-agent.onrender.com
```

Do not set `GEMINI_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `DATABASE_URL` in Vercel.

## Smoke Test

1. Open `https://finance-safe-growth-agent.vercel.app`.
2. Confirm the five-step workflow loads.
3. Submit the standard demo sentence.
4. Confirm the flow can continue when the backend is reachable.
5. Temporarily point `VITE_API_BASE_URL` at an unavailable URL in a preview deployment to confirm frontend fallback behavior.

## Public Smoke Result

Completed on 2026-05-20:

- Vercel public UI opened.
- Vercel UI successfully called the Render backend.
- CORS from Vercel origin to Render backend works.
- Standard 5-step demo completed without backend fallback.
- Deployed UI was checked against `.devmd/mockup`.
