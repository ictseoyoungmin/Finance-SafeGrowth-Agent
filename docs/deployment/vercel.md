# Vercel Deployment

Deploy only the frontend from the monorepo.

## Project Settings

- Root Directory: `apps/frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

## Environment Variables

Set only backend API URLs in Vercel:

```dotenv
VITE_API_BASE_URL=https://your-render-service.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

Do not set `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `DATABASE_URL` in Vercel.

## Smoke Test

1. Open the Vercel URL.
2. Confirm the five-step workflow loads.
3. Submit the standard demo sentence.
4. Confirm the flow can continue when the backend is reachable.
5. Temporarily point `VITE_API_BASE_URL` at an unavailable URL in a preview deployment to confirm frontend fallback behavior.
