# Week 2 Work Slice Plan

2주차는 `.devmd/phase2`의 보강 계획을 실제 작업 순서로 재구성한다.

현재 프로젝트는 Week 1 기준으로 FastAPI backend, React/Vite frontend, Supabase schema/seed, fallback demo flow가 갖춰져 있다. 다만 Phase 2 문서 기준으로는 실제 저장, 승인/감사/리포트 API, rewrite 문맥 주입, Supabase evidence 조회, UI polish, CI/Docker 정리가 남아 있다.

## 작업 원칙

- P0 슬라이스를 먼저 완료한다.
- Supabase/Gemini가 없어도 fallback demo flow는 항상 동작해야 한다.
- API 응답 shape는 frontend와 tests를 함께 갱신한다.
- 각 day 종료 시 해당 문서의 완료 기록을 갱신한다.
- Phase 2 원본 슬라이스 README는 상세 스펙으로 유지하고, Week 2 문서는 실행 순서와 체크포인트 역할을 한다.

## 일별 슬라이스

| Day | 문서 | Phase 2 참조 | 목표 |
|---|---|---|---|
| Day 8 | `day-08-baseline-triage.md` | `00-review-baseline` | 현재 구현/테스트/갭 재확인 |
| Day 9 | `day-09-persistence-id-audit.md` | `01-p0-backend-persistence` | UUID 호환 content_id, contents/risk/audit 저장 |
| Day 10 | `day-10-approval-report-api.md` | `02-p0-approval-audit-report` | approve, audit-log, report API와 frontend 연결 |
| Day 11 | `day-11-rewrite-rag-context.md` | `03-p0-gemini-rewrite-context`, `04-p1-rag-quality` | rewrite 문맥 주입, Gemini parser, evidence 조회 품질 |
| Day 12 | `day-12-frontend-mockup-polish.md` | `05-p1-frontend-mockup-polish` | 5단계 UI mockup 반영과 approval UX 보강 |
| Day 13 | `day-13-ci-docker-test-cleanup.md` | `06-p1-test-ci-docker` | CI, Docker, env, API contract tests 정리 |
| Day 14 | `day-14-demo-freeze-handover.md` | `07-p2-demo-hardening` | demo freeze, smoke docs, known issues, handover |

## 표준 데모 문장

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

기대 risky expression:

```text
누구나
연 8% 수익
안정적으로
원금 걱정 없이
```

## 공통 완료 기준

- Backend: `ruff check app tests`, `pytest`
- Frontend: `npm run lint`, `npm run typecheck`, `npm run build`
- 수동 flow: 입력 -> redline -> evidence -> rewrite -> approval/report
- backend offline 또는 외부 API key 미설정 상황에서도 fallback flow 유지

