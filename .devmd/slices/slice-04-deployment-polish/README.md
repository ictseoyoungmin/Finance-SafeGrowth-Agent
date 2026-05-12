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

- [ ] `apps/backend/Dockerfile`
- [ ] `docker-compose.yml`
- [ ] `.github/workflows/backend-ci.yml`
- [ ] `.github/workflows/frontend-ci.yml`
- [ ] `docs/deployment/vercel.md`
- [ ] `docs/deployment/render.md`
- [ ] `docs/deployment/supabase.md`
- [ ] `docs/demo/demo-script.md`
- [ ] `docs/demo/fallback-plan.md`

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

- [ ] backend Docker build 성공.
- [ ] backend/frontend CI workflow 존재.
- [ ] Vercel/Render/Supabase deployment docs 존재.
- [ ] public demo URL에서 표준 시나리오 1회 성공.
- [ ] fallback plan 존재.

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
