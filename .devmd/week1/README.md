# Week 1 Daily Plan

1주차는 “구조 생성 → backend core → RAG/Gemini → frontend flow → 배포 검증” 순서로 진행한다.

## 일별 계획

| Day | 문서 | 목표 |
|---|---|---|
| Day 1 | `day-01-bootstrap.md` | COMPLETE — monorepo, env, scaffold, CI skeleton |
| Day 2 | `day-02-backend-foundation.md` | COMPLETE — FastAPI foundation, config, router |
| Day 3 | `day-03-analyze-rule-engine.md` | COMPLETE — analyze API, RuleEngine, audit 기초 |
| Day 4 | `day-04-supabase-rag-seed.md` | COMPLETE — Supabase schema, seed, RAG skeleton |
| Day 5 | `day-05-gemini-rewrite-evidence.md` | COMPLETE — Gemini, evidence, rewrite, fallback |
| Day 6 | `day-06-frontend-flow.md` | COMPLETE — 5단계 frontend flow |
| Day 7 | `day-07-deploy-ci-polish.md` | COMPLETE — Docker, CI/CD, Vercel/Render/Supabase, demo polish |

## Week 1 상태

- Status: COMPLETE
- Render: `https://finance-safegrowth-agent.onrender.com`
- Vercel: `https://finance-safe-growth-agent.vercel.app`
- 다음 단계: `.devmd/week2/README.md`

## 운영 원칙

- 매일 작업 전 해당 day 문서와 slice README를 모두 읽는다.
- 매일 작업 종료 시 최소 smoke test를 실행한다.
- 외부 API가 실패하더라도 fallback으로 데모 플로우가 이어져야 한다.
- 구현 완료 후 slice README 하단 placeholder를 갱신한다.
