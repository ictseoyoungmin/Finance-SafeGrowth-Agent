# Coding Standards

## Backend

- Python 3.10+ 또는 3.11 기준.
- FastAPI + Pydantic 기반.
- `app/main.py`는 entrypoint와 middleware만 담당한다.
- API router는 `app/api/v1`에 둔다.
- 비즈니스 로직은 `app/services`에 둔다.
- DB 접근은 `app/repositories`에 둔다.
- 외부 API client는 `app/integrations`에 둔다.
- RuleEngine은 `app/rules`에 둔다.
- RAG 관련 chunk/search/embedding은 `app/rag`에 둔다.

권장 lint/test:

```bash
cd apps/backend
ruff check app tests
pytest
```

## Frontend

- React + TypeScript 기준. Vite 또는 Next.js 중 실제 scaffold에 맞춘다.
- 화면 상태는 `features/compliance/store.ts`에 모은다.
- API client는 `features/compliance/api.ts`에 모은다.
- DTO 타입은 `features/compliance/types.ts`에 둔다.
- 화면 step은 `features/compliance/steps`에 둔다.
- 공통 레이아웃은 `components/layout`에 둔다.

권장 lint/build:

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
```

## Naming

- API: snake_case JSON field를 기본으로 한다.
- TypeScript 내부는 camelCase를 사용할 수 있으나 API 변환 함수를 명시한다.
- DB table/column은 snake_case.
- 문서 파일은 kebab-case 또는 `day-XX-name.md` 형식.

## Error Handling

Backend error response 기본 형태:

```json
{
  "error": {
    "code": "GEMINI_UNAVAILABLE",
    "message": "AI 분석 서버가 일시적으로 응답하지 않습니다.",
    "request_id": "req_xxx"
  }
}
```

Frontend는 API 오류 시:

- 사용자에게 짧은 banner 표시.
- 데모 가능한 fallback 버튼 또는 mock data 사용.
- console에는 request id와 endpoint를 남긴다.
