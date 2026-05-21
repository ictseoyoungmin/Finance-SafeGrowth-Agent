# Slice 07 Cleanup — Redline/Rewrite Alignment

## Problem

The Redline Risk Review and Rewrite Comparison screens can disagree.

Current behavior:

- Redline Risk Review is driven by backend `RuleEngine` output from `/v1/compliance/analyze`.
- Gemini is only called during `/v1/compliance/rewrite`.
- Gemini can identify additional risky phrases during rewrite, but those phrases are not available to the Redline screen.
- Gemini can return `changes[].original` as an empty string or as text that is not present in the original copy.
- The rewrite table renders empty `original` values as a tiny red mark with no visible text.

Visible issues:

- Redline highlights only predefined/rule-based spans.
- Rewrite Comparison can show different or extra risky expressions.
- Rewrite row 3 can show no red text when `changes[].original` is empty.

## Required Fixes

- Add optional Gemini-assisted analysis augmentation in `/v1/compliance/analyze`.
- Merge Gemini-detected spans with rule-engine spans.
- Validate Gemini spans:
  - `span_text` must be non-empty.
  - span must exist in the original text.
  - offsets must match or be recovered from text search.
  - overlapping duplicate spans must be deduped.
- Mark span source so UI/debugging can distinguish rule and Gemini findings.
- Tighten rewrite prompt:
  - `changes[].original` must be an exact original-text substring.
  - No blank `original` values.
  - Prefer detected flagged spans.
- Sanitize Gemini rewrite changes before returning them:
  - Never return blank `original` to the UI.
  - Preserve valid Gemini rewrite text.
  - Add safe display fallback for whole-document changes when needed.
- Keep deterministic fallback working when Gemini is unavailable.

## Verification

Backend:

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 90 .venv/bin/pytest -q
```

Frontend:

Use Playwright Docker, not local npm:

```bash
docker run --rm -v /tmp/dacon-slice07-cleanup-frontend:/app -w /app \
  mcr.microsoft.com/playwright:v1.60.0-noble \
  sh -c "npm ci && npm run typecheck && npm run lint && npm run build"
```

Manual/public smoke after redeploy:

1. Enter a non-standard text such as:

   ```text
   지금 가입하면 누구나 연 금리 23%. 2년 안에 못 갚으면 무려 50% 및 증가!
   ```

2. Run analyze.
3. Confirm Redline highlights both rule and Gemini-detected risky phrases.
4. Run rewrite.
5. Confirm rewrite table rows have visible original text.
6. Confirm rewrite changes do not contradict Redline findings.
7. Confirm source badge still shows `Gemini 검수 결과` or `Deterministic fallback`.

## Status

- Status: COMPLETE locally

Implemented files:

- `apps/backend/app/schemas/compliance.py`
- `apps/backend/app/services/analyze_service.py`
- `apps/backend/app/schemas/rewrite.py`
- `apps/backend/app/services/rewrite_service.py`
- `apps/backend/tests/test_analyze_service.py`
- `apps/backend/tests/test_rewrite_service.py`
- `apps/frontend/src/features/compliance/types.ts`
- `apps/frontend/src/features/compliance/steps/RedlineStep.tsx`

Completed:

- `/v1/compliance/analyze` now runs rule-based detection first and augments with Gemini-detected spans when Gemini is configured.
- Gemini analyze spans are validated against the original text before being merged.
- Invalid/empty Gemini spans are ignored.
- Overlapping duplicate spans are deduped.
- `FlaggedSpan.source` marks `rule` or `gemini`.
- Redline UI shows each span source in the risk inspector.
- Rewrite prompt now tells Gemini to return only exact original-text substrings in `changes[].original`.
- Rewrite response sanitizes Gemini changes so blank original values are not returned to the UI.
- If Gemini returns no usable changes, rewrite response falls back to detected spans or `전체 문안`.

Verification results:

- Backend `ruff`: passed.
- Backend `pytest`: `30 passed, 1 warning`.
- Frontend Playwright Docker `npm ci && npm run typecheck && npm run lint && npm run build`: passed.

Known notes:

- Frontend `npm ci` still reports existing npm audit warnings.
- Backend pytest was run outside the sandbox because FastAPI `TestClient` can hang under sandbox proxy/network isolation.
- Public Vercel/Render smoke after redeploy is still required.
