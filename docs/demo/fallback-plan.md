# Fallback Plan

The MVP must keep the demo path working when external services are unavailable.

## Backend

- RuleEngine runs before any LLM-dependent behavior.
- `/v1/compliance/analyze` returns rule-based spans without Gemini or Supabase.
- `/v1/compliance/evidence` returns in-process demo regulation documents if Supabase is not configured.
- `/v1/compliance/rewrite` returns deterministic conservative and marketing-balanced copy if Gemini is unavailable or returns unparsable JSON.

## Frontend

- The API client catches failed backend requests and supplies deterministic demo data.
- Fallback mode is surfaced in the UI with a `Fallback` badge and notice.
- No frontend fallback path uses backend-only secrets.

## Demo Recovery

1. If Render is sleeping, warm `/v1/health` and retry.
2. If backend remains unavailable, continue the frontend demo through fallback data.
3. If Gemini fails, use the deterministic rewrite response.
4. If Supabase fails, use the deterministic evidence response.
5. Record skipped external dependencies in the slice README before marking completion.
