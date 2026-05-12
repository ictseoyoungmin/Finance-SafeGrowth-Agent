# Global Agent Instructions

## 1. 역할

당신은 `JB SafeGrowth Agent`의 구현 agent이다. 목표는 기획/인수인계 문서에 정의된 MVP를 1주 안에 로컬 실행 및 공개 데모 가능한 상태로 만드는 것이다.

## 2. 핵심 원칙

1. **Monorepo 유지**: frontend/backend repo를 분리하지 않는다.
2. **배포 단위 분리**: `apps/frontend`는 Vercel, `apps/backend`는 Render 기준으로 독립 구성한다.
3. **비밀키 보호**: `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`은 frontend에 절대 노출하지 않는다.
4. **LLM 단독 판단 금지**: RuleEngine 결과를 먼저 만들고, Gemini는 Judge/Rewrite 보조로 사용한다.
5. **Fallback 필수**: Gemini 또는 Supabase 실패 시에도 데모가 중단되지 않도록 mock/fallback 응답을 제공한다.
6. **작은 PR 단위**: slice 또는 day 단위로 commit/PR을 나눈다.
7. **테스트 우선**: 최소 smoke test와 RuleEngine unit test는 항상 유지한다.

## 3. 작업 방식

각 작업을 시작할 때:

- 해당 `week1/day-XX-*.md` 파일을 읽는다.
- 매핑된 `slices/slice-XX-*/README.md`를 읽는다.
- `agent-guides/api-contract.md`를 확인한다.
- 기존 구현 파일이 있으면 먼저 읽고 중복 구현하지 않는다.

각 작업을 끝낼 때:

- 테스트 명령을 실행한다.
- 실패한 테스트가 있으면 원인과 임시 우회 여부를 기록한다.
- slice README의 `Implementation Completion Placeholder`를 갱신한다.

## 4. 금지 사항

- frontend에서 Gemini API를 직접 호출하지 않는다.
- frontend에서 Supabase service role key를 사용하지 않는다.
- API response schema를 임의로 자주 바꾸지 않는다.
- Redline UI에서 start/end index 없이 무조건 string replace만 사용하지 않는다. start/end가 없을 때만 fallback한다.
- 실제 금융 규정을 검증된 법률 자문처럼 단정하지 않는다. MVP seed는 PoC용 샘플 기준임을 유지한다.

## 5. Branch / Commit 권장

```text
main
feature/slice-00-bootstrap
feature/slice-01-backend-core
feature/slice-02-rag-gemini
feature/slice-03-frontend-flow
feature/slice-04-deployment-polish
```

Commit prefix:

```text
chore:
feat:
fix:
test:
docs:
ci:
```
