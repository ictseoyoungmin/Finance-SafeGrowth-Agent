# Day 7 — Deployment / CI / Demo Polish

## 목표

Vercel + Render + Supabase 무료 플랜 기준으로 공개 데모 가능한 상태를 만든다.

## 매핑 Slice

- `slices/slice-04-deployment-polish/README.md`

## 작업 범위

1. Dockerfile 검증.
2. docker-compose backend smoke.
3. backend-ci.yml 작성.
4. frontend-ci.yml 작성.
5. Vercel root directory 설정 문서화.
6. Render root directory/start command 문서화.
7. Supabase seed 적용 절차 문서화.
8. Demo script 작성.
9. Render cold start 대응.

## Required files

```text
apps/backend/Dockerfile
docker-compose.yml
.github/workflows/backend-ci.yml
.github/workflows/frontend-ci.yml
docs/deployment/vercel.md
docs/deployment/render.md
docs/deployment/supabase.md
docs/demo/demo-script.md
docs/demo/fallback-plan.md
```

## Render settings

```text
Root Directory: apps/backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Vercel settings

```text
Root Directory: apps/frontend
Build Command: npm run build
Output Directory: dist 또는 .next
```

## Smoke test

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
```

Production smoke:

```bash
curl https://your-render-service.onrender.com/v1/health
```

## 산출물

- [ ] Docker backend build success
- [ ] backend CI
- [ ] frontend CI
- [ ] deployment docs
- [ ] demo script
- [ ] fallback plan
- [ ] public URL smoke checklist

## 완료 기준

- [ ] GitHub PR에서 CI가 실행된다.
- [ ] Render `/v1/health` 응답 정상.
- [ ] Vercel public URL에서 UI 접근 가능.
- [ ] 표준 데모 시나리오가 1회 이상 성공했다.
