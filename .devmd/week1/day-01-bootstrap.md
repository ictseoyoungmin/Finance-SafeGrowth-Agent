# Day 1 — Bootstrap / Monorepo Foundation

## 목표

clone 후 frontend/backend가 각각 독립적으로 실행될 수 있는 monorepo 골격을 만든다.

## 매핑 Slice

- `slices/slice-00-bootstrap/README.md`

## 작업 범위

1. Repository root 구조 생성.
2. `apps/frontend` scaffold 생성.
3. `apps/backend` scaffold 생성.
4. `.env.example` 파일 3종 생성.
5. `.gitignore`, root `README.md`, docs skeleton 생성.
6. GitHub Actions CI skeleton 생성.
7. Docker Compose skeleton 생성.

## 구현 상세

### 1. Root structure

```text
jb-safegrowth-agent/
├── apps/frontend
├── apps/backend
├── infra/supabase
├── docs
├── .github/workflows
├── docker-compose.yml
├── .env.example
└── README.md
```

### 2. Frontend scaffold

Vite React TypeScript 기준 예시:

```bash
cd apps
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

Next.js를 택한다면 `apps/frontend` root만 유지하고 Vercel root directory를 동일하게 잡는다.

### 3. Backend scaffold

```bash
mkdir -p apps/backend/app/{api/v1,core,schemas,services,rules,rag,integrations,repositories,tests}
touch apps/backend/app/main.py
```

### 4. Environment files

- root `.env.example`
- `apps/frontend/.env.example`
- `apps/backend/.env.example`

`agent-guides/env-and-secrets.md`를 기준으로 작성한다.

## 테스트 / 검증

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

## 산출물

- [x] root project tree
- [x] frontend scaffold
- [x] backend scaffold
- [x] env examples
- [x] CI skeleton
- [x] docker-compose skeleton
- [x] README local run guide

## 완료 기준

- [x] backend `/v1/health`가 응답한다.
- [x] frontend dev server가 실행된다.
- [x] `.env.example`에 secret 이름만 있고 실제 key는 없다.
- [x] slice-00 README의 완료 placeholder가 갱신되었다.

## 완료 상태

- Status: COMPLETE
- 완료 근거: `.devmd/slices/slice-00-bootstrap/README.md`
