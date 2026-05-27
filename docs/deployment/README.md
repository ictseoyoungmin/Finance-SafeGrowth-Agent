# Deployment Notes

## Determinism / Consistency 권장 환경변수

backend (Render) 환경변수에 다음을 설정하면 같은 입력에 대한 응답 변동이 크게 줄어듭니다.

| Env var | 권장값 | 효과 |
| --- | --- | --- |
| `LLM_TEMPERATURE` | `0.0` 또는 `0.1` | Gemini sampling 의 무작위성을 최소화. analyze/rewrite 응답이 거의 동일하게 반복됨 |
| `GEMINI_MODELS` | `gemini-2.5-flash,gemini-3-flash,gemini-2.5-flash-lite` | quota 초과 시 자동으로 다음 모델 시도. 기본값과 동일 |

추가로, 백엔드는 **15분 TTL in-memory 응답 캐시** 가 내장되어 있어 동일한 입력 (`AnalyzeRequest` / `RewriteRequest` JSON 동일) 은 캐시 결과를 반환합니다. 강제로 새로 호출하려면 query 에 `?refresh=1` 을 붙이세요:

```
POST /v1/compliance/analyze?refresh=1
POST /v1/compliance/rewrite?refresh=1
```

## CORS

frontend(Vercel) 도메인과 vite dev 포트들을 `CORS_ORIGINS` 콤마 구분으로 추가:

```
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173,http://127.0.0.1:5173
```

## Supabase

`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` 가 채워지면 자동으로 Supabase 모드. 미설정 (또는 `replace-me`) 이면 in-memory fallback 으로 동작 — 데모는 fallback 만으로도 동작합니다.

## CI

`.github/workflows/backend-ci.yml` / `frontend-ci.yml` 은 main push / PR 시 자동 실행. 통과해야 Render / Vercel 의 자동 deploy 가 트리거됩니다.
