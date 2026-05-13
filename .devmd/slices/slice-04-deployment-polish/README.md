# Slice 4 — Deployment & Polish

이 slice README는 agent가 해당 구현 단위를 독립적으로 수행할 수 있도록 통합 지시문, 구현 범위, 테스트 하네스, 완료 placeholder를 포함한다.


## Objective

CI/CD, Docker, Vercel/Render/Supabase 배포 문서와 데모 안정화를 완료한다.

## Mapped Days

Day 7

## Prerequisites

Slice 0~3 완료. frontend/backend가 로컬에서 최소 동작해야 한다.

## Integrated Instructions

1. CD는 Vercel/Render GitHub 연동을 우선 사용한다.
2. GitHub Actions는 PR 품질 검증 중심으로 둔다.
3. Render free cold start를 전제로 `/v1/health` warm-up 가이드를 문서화한다.
4. Supabase migration/seed 절차를 명확히 쓴다.
5. 공개 URL smoke test checklist를 남긴다.

## Required Deliverables

- [x] `apps/backend/Dockerfile`
- [x] `docker-compose.yml`
- [x] `.github/workflows/backend-ci.yml`
- [x] `.github/workflows/frontend-ci.yml`
- [x] `docs/deployment/vercel.md`
- [x] `docs/deployment/render.md`
- [x] `docs/deployment/supabase.md`
- [x] `docs/demo/demo-script.md`
- [x] `docs/demo/fallback-plan.md`

## Test Harness

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health

cd apps/backend && pytest
cd apps/frontend && npm run build
```

Production smoke:

```bash
curl https://your-render-service.onrender.com/v1/health
```

## Done Criteria

- [x] backend Docker build 성공.
- [x] backend/frontend CI workflow 존재.
- [x] Vercel/Render/Supabase deployment docs 존재.
- [ ] public demo URL에서 표준 시나리오 1회 성공.
- [x] fallback plan 존재.

## Implementation Completion Placeholder

- Status: IN_PROGRESS
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `apps/backend/Dockerfile`
  - `apps/backend/render.yaml`
  - `apps/frontend/vercel.json`
  - `docker-compose.yml`
  - `.github/workflows/backend-ci.yml`
  - `.github/workflows/frontend-ci.yml`
  - `docs/deployment/vercel.md`
  - `docs/deployment/render.md`
  - `docs/deployment/supabase.md`
  - `docs/demo/demo-script.md`
  - `docs/demo/fallback-plan.md`
- Test commands executed:
  - `cd apps/backend && .venv/bin/ruff check app tests`
  - `cd apps/backend && .venv/bin/pytest`
  - `cd apps/frontend && npm run build`
  - `docker compose up --build backend`
  - `curl http://localhost:8000/v1/health`
  - `docker compose down`
- Test result:
  - Backend lint passed.
  - Backend pytest passed: 8 tests passed, 1 upstream PendingDeprecationWarning from Starlette/python-multipart.
  - Frontend build passed.
  - Docker Compose backend build succeeded.
  - Dockerized backend health returned `{"status":"ok","env":"development"}`.
- Known issues:
  - Public Render/Vercel deployment was not performed in this local environment, so production URL smoke and full public demo validation remain open.
  - Slice 3 still needs manual browser click-through before it can be marked COMPLETE.
- Fallback behavior:
  - Demo fallback plan documented in `docs/demo/fallback-plan.md`.
  - Backend and frontend remain deterministic if Gemini, Supabase, or backend API calls are unavailable.
- Next recommended task:
  - Complete manual browser validation for Slice 3, deploy backend/frontend to Render/Vercel, run public URL smoke tests, then mark Slice 3 and Slice 4 COMPLETE.
