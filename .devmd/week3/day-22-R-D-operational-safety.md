# R-D · 운영 안전망 (입력 한도 + timeout + fallback gating)

피드백 #7 + #9 + #10. public deploy 시 사고 방지.

## R-D-1 · 입력/업로드 크기 제한

### 문제
- `AnalyzeRequest.original_text` 는 `min_length=1` 만, max 없음 → 100MB 텍스트도 처리 시도
- `api/v1/admin.py` 의 regulation ingest 가 `await file.read()` 전체 메모리 적재

### 변경
- `schemas/compliance.py::AnalyzeRequest`: `original_text: str = Field(..., min_length=1, max_length=5000)`
- 동일하게 `RewriteRequest` 의 mode 등에 합리적 제한 (영향 작음)
- `admin.py` ingest:
  ```python
  MAX_UPLOAD_BYTES = 5 * 1024 * 1024
  raw = await file.read(MAX_UPLOAD_BYTES + 1)
  if len(raw) > MAX_UPLOAD_BYTES:
      raise HTTPException(status_code=413, detail="file too large (max 5MB)")
  ```

### 테스트
- 5001 자 text → 422 (validation error)
- 5MB+1 파일 업로드 → 413

---

## R-D-2 · Gemini timeout settings 적용

### 문제
`GeminiClient._post` 의 `urllib.request.urlopen(request, timeout=15)` 가 하드코딩. `settings.llm_timeout_seconds=600` 과 불일치. 긴 prompt 에서 15s 넘으면 fallback 으로 떨어짐.

### 변경
```python
from app.core.config import settings

with urllib.request.urlopen(request, timeout=settings.llm_timeout_seconds) as response:
    ...
```

settings 에 분리된 timeout 도입 (선택):
- `analyze_timeout_seconds: int = 20`
- `rewrite_timeout_seconds: int = 30`
- `ingest_timeout_seconds: int = 60`

호출부에서 적절히 선택. 단순화하려면 단일 `llm_timeout_seconds` 만 사용해도 OK.

### 비고
600s 는 너무 길어 사용자 응답성 저하 — 권장 default 를 30s 로 낮추는 것도 검토 (별도 PR).

---

## R-D-3 · Frontend fallback production gating

### 문제
`features/compliance/store.ts` 의 analyze/evidence/rewrite catch 블록이 production 에서도 fallback 데이터로 진행 → backend 장애가 "성공" 으로 위장.

### 변경
`api.ts` 또는 store 상단에 환경 분기:
```ts
const ENABLE_DEMO_FALLBACK =
  import.meta.env.MODE !== "production" ||
  import.meta.env.VITE_ENABLE_DEMO_FALLBACK === "true";
```

각 catch 블록에서:
- ENABLE_DEMO_FALLBACK true → 기존 fallback 데이터 진행
- false → setState 에 errorMessage 만 남기고 step 유지 (fallback 안 함)

`.env.production` 권장: `VITE_ENABLE_DEMO_FALLBACK=true` (대회 데모 한정), 실제 운영 시엔 unset.

### Frontend UX
fallback 비활성 시 사용자에게 보이는 메시지:
> "백엔드 응답이 없어 분석을 진행할 수 없습니다. 잠시 후 다시 시도해 주세요."

## 영향 범위
- backend: `schemas/compliance.py`, `api/v1/admin.py`, `integrations/gemini_client.py`
- frontend: `features/compliance/store.ts`, `features/compliance/api.ts`
- 테스트: text length validation, gemini timeout (mock urllib)

## 검증
- ruff + pytest
- production 빌드에서 fallback 흐름 비활성 확인 (manual)
