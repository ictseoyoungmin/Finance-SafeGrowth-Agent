# Slice 0 — Bootstrap

이 slice README는 agent가 해당 구현 단위를 독립적으로 수행할 수 있도록 통합 지시문, 구현 범위, 테스트 하네스, 완료 placeholder를 포함한다.


## Objective

단일 monorepo 골격을 만들고 frontend/backend가 각각 로컬 실행 가능한 상태를 만든다.

## Mapped Days

Day 1

## Prerequisites

빈 repository 또는 기존 repository root. Node/Python/virtualenv/Docker가 설치되어 있어야 한다.

## Integrated Instructions

1. repo는 분리하지 않는다.
2. `apps/frontend`와 `apps/backend`를 명확히 분리한다.
3. Vercel/Render root directory 설정을 전제로 폴더를 만든다.
4. 실제 secret 값은 절대 commit하지 않는다.
5. 초기에는 shared package 없이 frontend/backend 타입 중복을 허용한다.

## Required Deliverables

- [x] `apps/frontend` scaffold
- [x] `apps/backend` scaffold
- [x] `infra/supabase` directory
- [x] `docs` directory
- [x] `.github/workflows` directory
- [x] `.env.example`, `apps/frontend/.env.example`, `apps/backend/.env.example`
- [x] root `README.md`
- [x] `docker-compose.yml` skeleton

## Test Harness

```bash
cd apps/backend
virtualenv --always-copy .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/v1/health
```

```bash
cd apps/frontend
npm install
npm run dev
```

## Done Criteria

- [x] clone 후 backend health check 성공.
- [x] frontend dev server 실행.
- [x] env example 존재.
- [x] CI skeleton 존재.

## Implementation Completion Placeholder

- Status: COMPLETE
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `README.md`
  - `.env.example`
  - `.gitignore`
  - `docker-compose.yml`
  - `.github/workflows/backend-ci.yml`
  - `.github/workflows/frontend-ci.yml`
  - `apps/backend/.env.example`
  - `apps/backend/Dockerfile`
  - `apps/backend/requirements.txt`
  - `apps/backend/requirements-dev.txt`
  - `apps/backend/pyproject.toml`
  - `apps/backend/app/main.py`
  - `apps/backend/app/api/v1/health.py`
  - `apps/backend/app/core/config.py`
  - `apps/backend/app/schemas/health.py`
  - `apps/backend/tests/test_api_health.py`
  - `apps/frontend/.env.example`
  - `apps/frontend/package.json`
  - `apps/frontend/package-lock.json`
  - `apps/frontend/index.html`
  - `apps/frontend/vite.config.ts`
  - `apps/frontend/eslint.config.js`
  - `apps/frontend/tsconfig.json`
  - `apps/frontend/tsconfig.app.json`
  - `apps/frontend/tsconfig.node.json`
  - `apps/frontend/src/App.tsx`
  - `apps/frontend/src/main.tsx`
  - `apps/frontend/src/styles.css`
  - `apps/frontend/src/vite-env.d.ts`
  - `infra/supabase/schema.sql`
  - `infra/supabase/seed_regulation_docs.sql`
  - `infra/supabase/seed_demo_contents.sql`
  - `infra/supabase/migrations/.gitkeep`
  - `docs/deployment/README.md`
  - `docs/demo/README.md`
  - `docs/handover/README.md`
  - `docs/diagrams/.gitkeep`
  - `docs/mockups/.gitkeep`
- Test commands executed:
  - `cd apps/backend && virtualenv --always-copy .venv`
  - `cd apps/backend && .venv/bin/pip install -r requirements-dev.txt`
  - `cd apps/backend && .venv/bin/ruff check app tests`
  - `cd apps/backend && .venv/bin/pytest`
  - `cd apps/backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - `curl http://localhost:8000/v1/health`
  - `cd apps/frontend && npm install`
  - `cd apps/frontend && npm run lint`
  - `cd apps/frontend && npm run typecheck`
  - `cd apps/frontend && npm run build`
  - `cd apps/frontend && npm run dev`
  - `curl http://172.18.208.1:5173`
  - `curl http://192.168.0.5:5173`
- Test result:
  - Backend lint passed.
  - Backend pytest passed: 1 test passed, 1 upstream PendingDeprecationWarning from Starlette/python-multipart.
  - Backend health returned `{"status":"ok","env":"development"}`.
  - Frontend install passed after pinning Vite 4 / ESLint 8-compatible dependencies for the available Node 16 runtime.
  - Frontend lint, typecheck, and build passed.
  - Frontend dev server started with Vite and served `index.html` from the advertised network URLs.
- Known issues:
  - This WSL shell exposes Windows `npm`/`node.exe` v16.17.1, but not a Linux `node` binary. Vite reported `http://localhost:5173`, yet WSL `curl http://localhost:5173` was refused; the advertised network URLs responded successfully.
  - `npm install` reports audit findings in transitive frontend dependencies; no `npm audit fix --force` was applied because it may introduce breaking changes.
- Fallback behavior:
  - Slice 0 has no Gemini or Supabase calls. Backend health and frontend scaffold run without external services.
- Next recommended task:
  - Start Slice 1: implement backend compliance schemas, RuleEngine, `/v1/compliance/analyze`, service/repository skeletons, and analyze tests.
