# Fallback Plan

The MVP must keep the demo path working when external services are unavailable.

## Backend

- RuleEngine runs before any LLM-dependent behavior.
- `/v1/compliance/analyze` returns rule-based spans without Gemini or Supabase.
- `/v1/compliance/evidence` returns in-process demo regulation documents if Supabase is not configured.
- `/v1/compliance/rewrite` returns deterministic conservative and marketing-balanced copy if Gemini is unavailable or returns unparsable JSON.
- Rewrite fallback is input-aware: it uses the persisted/fallback original text plus detected risky spans, so alternate demo text does not collapse back to the fixed standard sentence.
- Rewrite responses include `source`, with `gemini` for parsed Gemini output and `fallback` for deterministic fallback output.

## Frontend

- `/` is the Agent run trace view. The old 5-step workflow remains available at `#/legacy/wizard` for regression checks and emergency demos.
- The API client catches failed backend requests and supplies deterministic demo data.
- Fallback mode is surfaced in the UI with a `Fallback` badge and notice.
- Rewrite comparison also shows a source badge: `Gemini 검수 결과` or `Deterministic fallback`.
- No frontend fallback path uses backend-only secrets.

## Demo Recovery

1. If Render is sleeping, warm `/v1/health` and retry.
2. If backend remains unavailable, continue the frontend demo through fallback data.
3. If Gemini fails, use the deterministic rewrite response.
4. If Supabase fails, use the deterministic evidence response.
5. Record skipped external dependencies in the slice README before marking completion.

## Public Deployment Status

Public smoke completed on 2026-05-20:

- Render backend: `https://finance-safegrowth-agent.onrender.com`
- Vercel frontend: `https://finance-safe-growth-agent.vercel.app`
- Render `/v1/health` succeeded.
- Render `/v1/compliance/analyze` succeeded.
- Vercel UI successfully called the Render backend.
- CORS from Vercel origin to Render backend is working.
- Standard 5-step demo completed without backend fallback.

Known issue:

- Render Free tier cold start can delay the first request. Warm up `/v1/health` before demo.
