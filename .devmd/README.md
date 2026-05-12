# JB SafeGrowth Agent — Week 1 Agent Workplan

이 문서 묶음은 `JB SafeGrowth Agent 개발자 인수인계 상세본`을 바탕으로, 코딩 agent가 1주차 개발을 바로 수행할 수 있도록 일별 작업과 슬라이스별 구현 지시문을 분리한 실행형 작업 문서이다.

## 0. 확정된 개발 전략

- Repository 전략: **단일 GitHub monorepo**.
- 배포 단위: `apps/frontend`는 Vercel, `apps/backend`는 Render로 독립 배포.
- DB/RAG: Supabase PostgreSQL + pgvector.
- LLM: Gemini API. 단, 모든 LLM 호출은 backend에서만 수행한다.
- 개발 환경: 평소 개발은 `virtualenv + npm dev`, 통합 검증은 Docker Compose.
- CI/CD: GitHub Actions로 frontend/backend CI를 분리하고, CD는 Vercel/Render GitHub 연동을 우선 사용한다.

## 1. Week 1 목표

1주차의 목표는 **clone 후 실행 가능한 monorepo를 만들고, 표준 데모 문구로 `콘텐츠 입력 → Redline → 근거 → 수정안 → 승인 패키지` 흐름이 로컬에서 동작하는 상태**까지 도달하는 것이다.

최종 완료 기준:

- `apps/backend`에서 `/v1/health`, `/v1/compliance/analyze`, `/v1/compliance/evidence`, `/v1/compliance/rewrite`, `/v1/compliance/approve`가 동작한다.
- `apps/frontend`에서 5단계 화면 전환이 가능하다.
- Supabase schema와 seed SQL이 존재한다.
- Gemini API 실패 시 fallback 응답으로 데모가 중단되지 않는다.
- `docker compose up --build backend`가 성공한다.
- GitHub Actions CI skeleton이 존재한다.

## 2. 문서 구조

```text
week1/
  README.md
  day-01-bootstrap.md
  day-02-backend-foundation.md
  day-03-analyze-rule-engine.md
  day-04-supabase-rag-seed.md
  day-05-gemini-rewrite-evidence.md
  day-06-frontend-flow.md
  day-07-deploy-ci-polish.md

slices/
  slice-00-bootstrap/README.md
  slice-01-backend-core/README.md
  slice-02-rag-gemini/README.md
  slice-03-frontend-flow/README.md
  slice-04-deployment-polish/README.md

agent-guides/
  global-agent-instructions.md
  coding-standards.md
  test-harness.md
  api-contract.md
  env-and-secrets.md
  done-template.md
```

## 3. 실행 순서

권장 실행 순서:

1. `agent-guides/global-agent-instructions.md`를 먼저 읽는다.
2. `agent-guides/api-contract.md`와 `agent-guides/env-and-secrets.md`를 확인한다.
3. 해당 날짜의 `week1/day-XX-*.md`를 수행한다.
4. 날짜와 매핑되는 `slices/slice-XX-*/README.md`의 완료 기준을 체크한다.
5. 구현 후 `agent-guides/test-harness.md`의 smoke test를 실행한다.

## 4. Day ↔ Slice 매핑

| Day | 주요 범위 | Slice |
|---|---|---|
| Day 1 | Monorepo bootstrap, env, CI skeleton | Slice 0 |
| Day 2 | FastAPI foundation, config, health, router | Slice 1 |
| Day 3 | analyze API, RuleEngine, audit 기초 | Slice 1 |
| Day 4 | Supabase schema, seed, vector/RAG skeleton | Slice 2 |
| Day 5 | Gemini judge/rewrite, evidence/rewrite API, fallback | Slice 2 |
| Day 6 | Frontend 5-step wizard, Redline/evidence/rewrite/approval UI | Slice 3 |
| Day 7 | Docker, CI, Vercel/Render/Supabase 설정, demo polish | Slice 4 |

## 5. 표준 데모 문구

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

기대 탐지 항목:

- `누구나`: 과장 표현
- `연 8% 수익`: 확정 수익 오인
- `안정적으로`: 안정성 오인
- `원금 걱정 없이`: 원금 보장 오인

## 6. 구현 완료 기록

- [ ] Slice 0 완료
- [ ] Slice 1 완료
- [ ] Slice 2 완료
- [ ] Slice 3 완료
- [ ] Slice 4 완료

완료 기록은 각 slice의 `README.md` 하단 placeholder에 남긴다.
