# Target Repository Structure

```text
jb-safegrowth-agent/
├── apps/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── layout/
│   │   │   │   ├── compliance/
│   │   │   │   ├── redline/
│   │   │   │   └── common/
│   │   │   ├── features/
│   │   │   │   └── compliance/
│   │   │   │       ├── api.ts
│   │   │   │       ├── types.ts
│   │   │   │       ├── store.ts
│   │   │   │       └── steps/
│   │   │   ├── lib/
│   │   │   └── styles/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── vercel.json
│   │   └── .env.example
│   └── backend/
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   ├── api/v1/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── rules/
│       │   ├── rag/
│       │   ├── integrations/
│       │   ├── repositories/
│       │   └── tests/
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── Dockerfile
│       ├── render.yaml
│       └── .env.example
├── infra/supabase/
│   ├── schema.sql
│   ├── seed_regulation_docs.sql
│   ├── seed_demo_contents.sql
│   └── migrations/
├── docs/
│   ├── deployment/
│   ├── demo/
│   ├── handover/
│   ├── diagrams/
│   └── mockups/
├── .github/workflows/
│   ├── backend-ci.yml
│   └── frontend-ci.yml
├── docker-compose.yml
├── .env.example
└── README.md
```

## Boundary Rules

- `apps/frontend`는 `apps/backend` 내부 파일을 import하지 않는다.
- `apps/backend`는 frontend 빌드 산출물에 의존하지 않는다.
- 공통 타입 공유가 필요하면 `packages/shared`를 추가할 수 있으나 Week 1에서는 API contract 문서 우선.
- `infra/supabase`는 DB schema와 seed data의 단일 출처로 유지한다.
