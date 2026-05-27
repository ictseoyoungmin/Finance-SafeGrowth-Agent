# P1-C · Prompt Hash 기반 응답 캐시

## 배경

LLM 호출은 비용·시간·일관성 모두에 영향. 같은 입력 (`content_id` + prompt 동일) 으로 여러 번 분석/수정안 호출 시:
- 매번 LLM 다시 호출 → quota 소모
- 응답이 미세하게 달라짐 → 사용자가 혼란

P1 의 일관성 패키지로, 동일 입력은 15분간 캐시된 응답 반환.

## 목표

- 단순한 **in-memory TTL cache** (서비스별 dict + 만료 시각)
- 키: `prompt_hash` (SHA256, rewrite_service 의 `prompt_hash` 와 동일 방식)
- `analyze_service.analyze()` / `rewrite_service.rewrite()` 두 곳에 적용
- **bypass**: HTTP 헤더 `X-Force-Refresh: 1` 또는 query `?refresh=1` 로 캐시 무시
- 추후 Redis 로 교체 쉽게 인터페이스 분리

### Non-goals
- 분산 캐시 (Redis 등) — 인터페이스만, 구현은 dict
- DB 결과 (risk_results 등) 캐시 — LLM 응답만 (DB 조회는 어차피 빠름)

## 구현

### `apps/backend/app/services/_response_cache.py` (신규)

```python
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

DEFAULT_TTL_SECONDS = 15 * 60


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float


class ResponseCache(Generic[T]):
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _Entry[T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: T) -> None:
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + self._ttl)

    def clear(self) -> None:
        self._store.clear()
```

### `analyze_service.py`

- 클래스에 `_cache: ResponseCache[AnalyzeResponse]` 추가
- `analyze(request, force_refresh: bool = False)`:
  - key = sha256(JSON of request)
  - `if not force_refresh and (cached := self._cache.get(key)): return cached`
  - 기존 로직 실행 후 결과를 cache.set
- DB 저장은 캐시 미적용 (매번 audit log 남김)
  - 하지만 매번 audit + content insert 가 부담 → 캐시 적중 시 audit 만 (analysis_cached 같은 action) 또는 skip
  - **결정**: 캐시 적중 시 모두 skip (재실행 아니므로). DB 에 이미 동일 결과 저장됨.

### `rewrite_service.py`

- 같은 패턴. `rewrite(request, force_refresh)` + ResponseCache

### API 라우터

`api/v1/compliance.py` 의 `analyze` / `rewrite` 핸들러에 `refresh: bool = Query(False)` 추가, service에 전달.

### Tests

`tests/test_response_cache.py` (신규):
- get/set + TTL 만료 + force refresh
- analyze 2번 호출 시 LLM 1번만 호출되는지 (mock counter)
- `?refresh=1` 일 때는 매번 호출되는지

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| 신규 | `services/_response_cache.py`, `tests/test_response_cache.py` |
| 변경 | `services/analyze_service.py`, `services/rewrite_service.py`, `api/v1/compliance.py` |

## 검증
- ruff
- pytest 통과 + 캐시 hit/miss 단위 테스트
