# 00 Review Baseline

## Goal

Create a precise baseline of the current repository state before applying fixes.

This is a read-only slice. Do not modify code unless explicitly instructed by a later slice.

## Current implementation assumptions

The repository currently contains:

```text
apps/frontend      Vite/React frontend
apps/backend       FastAPI backend
infra/supabase     schema and seed SQL
docs               documentation
.github/workflows  frontend/backend CI skeletons
```

The backend currently has:

- `GET /v1/health`
- `POST /v1/compliance/analyze`
- `POST /v1/compliance/evidence`
- `POST /v1/compliance/rewrite`
- `RuleEngine` with deterministic fallback detection
- fallback evidence documents
- fallback rewrite result

The frontend currently has:

- 5-step workflow UI
- fallback mode when backend is unavailable
- redline rendering by `start/end` offsets

## Review checklist

Check these files before implementing:

```text
README.md
apps/backend/app/main.py
apps/backend/app/api/v1/router.py
apps/backend/app/api/v1/compliance.py
apps/backend/app/core/config.py
apps/backend/app/rules/rule_engine.py
apps/backend/app/services/analyze_service.py
apps/backend/app/services/evidence_service.py
apps/backend/app/services/rewrite_service.py
apps/backend/app/repositories/*.py
apps/backend/app/integrations/*.py
apps/backend/tests/
apps/frontend/src/App.tsx
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/features/compliance/steps/*.tsx
apps/frontend/src/components/redline/*.tsx
infra/supabase/schema.sql
infra/supabase/seed_regulation_docs.sql
docker-compose.yml
.github/workflows/*.yml
```

## Output

Create or update a local note file if useful:

```text
.devmd/fix-plan/00-review-baseline/current-state-notes.md
```

Do not commit secrets or environment values.
