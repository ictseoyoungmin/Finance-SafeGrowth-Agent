# Global Fix Instructions

You are modifying the `Finance-SafeGrowth-Agent` monorepo.

## Primary objective

Turn the current clickable MVP skeleton into a more reliable demo-grade application by closing backend persistence, approval/audit/report APIs, Gemini context handling, RAG retrieval, tests, CI, Docker, and frontend polish.

## Mandatory rules

1. Do not split frontend and backend into separate repositories.
2. Keep the monorepo layout:

```text
apps/frontend
apps/backend
infra/supabase
docs
.github/workflows
.devmd
```

3. Do not expose backend secrets to the frontend.
4. `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `DATABASE_URL` are backend-only.
5. Rule-based risk detection must work without Gemini.
6. Any Gemini-dependent feature must have deterministic fallback.
7. Supabase must be optional for local fallback mode, but real persistence should work when configured.
8. Keep the standard demo sentence working at all times.
9. Prefer small, reviewable commits per slice.
10. Update the slice completion placeholder before marking work complete.

## Standard demo sentence

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

Expected risky expressions:

```text
누구나
연 8% 수익
안정적으로
원금 걱정 없이
```

## Work order

Complete slices in this order:

1. `01-p0-backend-persistence`
2. `02-p0-approval-audit-report`
3. `03-p0-gemini-rewrite-context`
4. `04-p1-rag-quality`
5. `05-p1-frontend-mockup-polish`
6. `06-p1-test-ci-docker`
7. `07-p2-demo-hardening`

Read `00-review-baseline` first if you have not reviewed the repository yet.
