# Day 22 — Gemini Fallback Chain · 사용 모델 표기

## 배경

production 에서 무료 티어 Gemini API 가 RPM/RPD 한도에 자주 막혀 호출이 실패한다. 현재 코드 (`GeminiClient._post`) 는 모든 예외를 `urllib.error.URLError | TimeoutError | json.JSONDecodeError` 로 잡고 `None` 만 반환 — 429 (`RESOURCE_EXHAUSTED`) 와 진짜 네트워크 오류를 구분 못 함. 그래서 한도 초과 시에도 그냥 fallback (rule-based) 으로 떨어진다.

사용자 요청:

1. **Fallback 모델 chain**: `gemini-2.5-flash`, `gemini-3-flash`, `gemini-2.5-flash-lite` 등 무료로 접근 가능한 모델 list 를 사전 구성. 첫 모델이 quota 초과면 다음 모델로 자동 재시도.
2. **호출 진행 표시**: "Agent 호출 중 … n/M" 형식 (예: "Gemini 시도 2/3").
3. **활성 모델명 노출**: 사용자가 어느 모델 응답을 봤는지 알 수 있게.

## 목표 / Non-goals

### 목표
- `gemini_models` settings (콤마구분 리스트) 추가, 기본값: `gemini-2.5-flash,gemini-3-flash,gemini-2.5-flash-lite`
- 429 / `RESOURCE_EXHAUSTED` / quotaExceeded 명시적 감지 → 다음 모델 시도
- 그 외 오류 (5xx, 네트워크, 형식) 도 다음 모델로 fallback (단 4xx 인증 같은 영구 오류는 chain 즉시 종료)
- 호출 결과에 `attempts: list[{model, status, error?}]` + `active_model` 메타 노출
- `RewriteResponse` 의 `source` 외에 `model_version`, `attempts` 추가 → frontend 가 표시
- frontend: rewrite source chip 옆에 사용 모델명 + (fallback 모델이 실제로 동작한 경우) "1/3 → 2/3 → 성공 (3/3)" 같은 한 줄 요약

### Non-goals
- SSE / streaming 진행 표시 — 동기 호출 후 응답 메타로 한 번에 표시 (호출 자체는 짧음)
- 모델 cooldown / 사용량 추적 (다음 호출에 sticky 우선순위) — 매번 첫 모델부터 시도
- OpenAI compatible provider 의 fallback — Gemini 만 대상

## 변경 사항

### 1. settings

`apps/backend/app/core/config.py`
- 새 필드:
  ```python
  gemini_models: str = "gemini-2.5-flash,gemini-3-flash,gemini-2.5-flash-lite"
  ```
- 기존 `gemini_model` 은 단일 모델 (deprecated 안 함, fallback chain 의 첫 모델로 사용 가능)
- 새 cached property:
  ```python
  @cached_property
  def gemini_models_list(self) -> list[str]:
      raw = self.gemini_models or self.gemini_model
      models = [m.strip() for m in raw.split(",") if m.strip()]
      return models or [self.gemini_model]
  ```

### 2. GeminiClient — 명시적 quota error + chain

`apps/backend/app/integrations/gemini_client.py`

- 새 데이터 클래스 `GeminiAttempt(model, status, error_code?)`
- `GeminiResult` / `GeminiToolResponse` 에 `attempts: list[GeminiAttempt]` 추가
- 새 예외 `class QuotaExceededError(Exception)`
- `_post` 가 `urllib.error.HTTPError` 를 구분:
  - 429 → `QuotaExceededError("rate_limited", code=429)`
  - 403 with body `RESOURCE_EXHAUSTED` → `QuotaExceededError`
  - 401 → `AuthError` (chain 종료 신호)
  - 5xx → `TransientError` (다음 모델로 fallback)
  - 그 외 → 기존대로 None
- `GeminiClient` 에 모델 list 지원: `__init__` 에 `models: list[str] | None = None`
  - 단일 모델 list 면 chain 길이 1, 기존 동작과 동일
- 새 public 메서드 `generate_json` / `generate_with_tools` 가 chain 루프 :
  ```python
  attempts = []
  for model in self._models:
      try:
          raw = self._post(body, model=model)
      except QuotaExceededError as e:
          attempts.append(GeminiAttempt(model=model, status="rate_limited", error_code=e.code))
          continue
      except AuthError:
          attempts.append(...)
          break
      ...
      attempts.append(GeminiAttempt(model=model, status="ok"))
      return GeminiResult(..., model_version=model, attempts=attempts)
  return None  # 모두 실패
  ```
- model_version 은 실제 성공한 모델

### 3. provider / schemas 변경

`apps/backend/app/integrations/llm/base.py`
- `LlmJsonResult`, `LlmToolResponse` 에 `attempts: list[dict]` 필드 추가 (model, status)

`apps/backend/app/integrations/llm/gemini.py`
- result wrapping 시 attempts 같이 전달

`apps/backend/app/schemas/rewrite.py`
- 새 필드:
  ```python
  model_version: str | None = None
  attempts: list[dict[str, Any]] = Field(default_factory=list)
  ```

`apps/backend/app/services/rewrite_service.py`
- `_parse_response` 가 `LlmJsonResult` 의 `model_version` / `attempts` 를 결과에 채움
- fallback 응답은 `model_version=None`, `attempts=[]`

(approve 는 LLM 호출 없음, 그대로 둠)

### 4. Frontend

`apps/frontend/src/features/compliance/types.ts`
- `RewriteResponse` 에 `model_version`, `attempts` 추가

`apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
- chip 표시 보강:
  - source === `gemini` 또는 `llm`: `"Gemini 검수 결과 · {model_version}"` + attempts 가 1보다 크면 작은 텍스트 `"1/3 → 2/3 → 성공 (2/3)"`
  - source === `fallback`: 기존 chip 유지 + attempts 가 있으면 `"3/3 시도 모두 실패 → 기본 패턴 기반"` 추가 라인

### 5. Test

`apps/backend/tests/test_gemini_parser.py` 에는 이미 parser 단위 테스트 존재. fallback chain 자체는 GeminiClient 의 model loop. 가벼운 추가 테스트:
- `GeminiClient` 가 첫 모델 429 → 두 번째 모델 성공 → attempts 길이 2, model_version 은 두 번째
- 모두 429 → None, attempts 길이 N

(시간상 핵심 케이스만)

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| 백엔드 | `core/config.py`, `integrations/gemini_client.py`, `integrations/llm/base.py`, `integrations/llm/gemini.py`, `schemas/rewrite.py`, `services/rewrite_service.py` |
| 프론트엔드 | `features/compliance/types.ts`, `features/compliance/steps/RewriteStep.tsx`, `styles.css` (chip 보조 라인) |
| 테스트 | `tests/test_gemini_parser.py` 또는 신규 `tests/test_gemini_client_fallback.py` |

## 검증
- backend pytest
- 캡처:
  - RewriteStep chip 에 모델명 표시
  - fallback chain 동작 시 한 줄 요약 표시

## 롤백
- `gemini_models` 미설정 시 단일 `gemini_model` 사용 → 기존 동작 동일
- 각 hunk 단위 revert
