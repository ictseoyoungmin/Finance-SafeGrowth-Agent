# Demo Notes

Use these files for the public demo path:

- `demo-script.md`: step-by-step Vercel/Render walkthrough.
- `fallback-plan.md`: behavior when Gemini, Supabase, or the backend is unavailable.

Important demo-hardening rule:

- Rewrite output must visibly identify whether it came from Gemini or deterministic fallback.
- Deterministic fallback rewrite must be based on the submitted sentence and detected risky spans, not only the fixed standard demo sentence.
