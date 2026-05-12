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

- [ ] `apps/frontend` scaffold
- [ ] `apps/backend` scaffold
- [ ] `infra/supabase` directory
- [ ] `docs` directory
- [ ] `.github/workflows` directory
- [ ] `.env.example`, `apps/frontend/.env.example`, `apps/backend/.env.example`
- [ ] root `README.md`
- [ ] `docker-compose.yml` skeleton

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

- [ ] clone 후 backend health check 성공.
- [ ] frontend dev server 실행.
- [ ] env example 존재.
- [ ] CI skeleton 존재.

## Implementation Completion Placeholder

- Status: [ ] Not Started / [ ] In Progress / [ ] Completed
- Branch:
- Commit / PR:
- Implemented files:
  - 
- Test commands executed:
  - 
- Test result:
  - 
- Known issues:
  - 
- Fallback behavior:
  - 
- Next recommended task:
  -
