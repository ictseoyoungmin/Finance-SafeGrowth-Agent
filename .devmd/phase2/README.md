# Finance SafeGrowth Agent Fix Plan

This folder contains the English fix plan for the current `Finance-SafeGrowth-Agent` codebase.

The project already has a good Week 1 skeleton:

- monorepo layout
- Vite/React frontend
- FastAPI backend
- rule-based risk scanner
- fallback demo flow
- Supabase schema/seed files
- basic CI workflows

However, the current implementation is still mostly a clickable MVP. The main gaps are:

1. Backend repositories do not persist to Supabase yet.
2. `content_id` currently uses a fake `content-{uuid}` format that does not match the Supabase UUID schema.
3. Evidence retrieval still returns fallback documents even when Supabase is configured.
4. Rewrite generation does not receive the original text, risk spans, or evidence context.
5. Approval, audit-log, and report APIs are missing.
6. The frontend approval step does not call a backend approval endpoint.
7. Docker/CI/env handling needs cleanup before deployment.
8. The UI needs to be polished against mockup images stored in `.devmd/mockup`.

## Recommended location inside the repository

Extract this folder into:

```bash
.devmd/fix-plan
```

Then start from:

```bash
.devmd/fix-plan/work-orders/agent-start-instruction.md
```

## Slice order

```text
00-review-baseline
01-p0-backend-persistence
02-p0-approval-audit-report
03-p0-gemini-rewrite-context
04-p1-rag-quality
05-p1-frontend-mockup-polish
06-p1-test-ci-docker
07-p2-demo-hardening
```

## Priority rule

Complete P0 slices before spending time on UI polish.

P0 closes product correctness:

- actual persistence
- approval/audit/report APIs
- rewrite with real content/evidence context

P1 improves quality:

- RAG retrieval
- frontend mockup polish
- CI/test/docker cleanup

P2 prepares the demo:

- regulation impact placeholder
- demo freeze
- operational hardening
