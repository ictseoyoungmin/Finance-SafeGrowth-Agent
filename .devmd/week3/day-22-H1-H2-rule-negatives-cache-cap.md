# Phase 1 Hardening · H1 (Rule negative tests) + H2 (Cache cap/stats)

Phase 1 은 기능 추가였고, 이 슬라이스는 회귀·견고성을 보강한다. H1/H2 를 한 묶음으로 진행.

---

## H1 · Rule pattern negative tests + regex 보강

### 배경
P1-B 에서 추가한 12개 카테고리는 **positive 테스트만** 있음. 정상 광고/일반 문장을 잘못 잡는 false-positive 검출이 없다.

### 목표
- 신규(+기존) 카테고리마다 *비매칭이어야 하는* 문장 케이스 추가
- 잘못 매칭되면 regex 를 lookahead/경계로 보강

### 잠재 false-positive 후보 (검증 대상)
| 패턴 | 오탐 의심 문장 | 기대 |
| --- | --- | --- |
| `최고의?` | "최고의 기회를 신중히 검토하세요" | 음... "최고" 자체가 과장 표현이라 매칭이 맞을 수도. **정책 결정**: "최고/최고의" 는 광고 맥락상 과장이므로 매칭 유지. 단 "최고경영자(CEO)", "최고치" 같은 합성어는 제외 |
| `오늘만` | "오늘만 해도 벌써 100명이 신청" | 시간 한정 마케팅 표현 → 매칭 유지 타당. 단 "오늘만큼은" 같은 표현은? → 드물어 무시 |
| `단\s*\d+\s*(일\|시간\|분)\s*한정` | "단 3일 동안 진행" (한정 단어 없음) | 현재 패턴은 "한정" 필수라 안전. "단 3일 늦었다" 비매칭 확인 |
| `1\s*위\s*수상` | "고객 만족도 조사에서 좋은 평가" | 비매칭 확인 |
| `고금리(?!\s*\d)` | "고금리 시대의 재테크 전략" (정보성) | 매칭됨 — 정책상 광고 카피면 매칭 타당하나, 정보성 표현 오탐 가능. lookahead 로 "고금리 상품/혜택/특판" 등 광고 맥락에 한정 검토 |
| `절대\s*안전` | "절대 안전을 보장할 수 없습니다" (부정문) | **오탐!** "절대 안전" 매칭되나 문맥은 안전을 부정. → disclosure post-processing (analyze_service) 이 인접 disclosure 로 강등하므로 부분 완화. negative 테스트로 명시 |
| `100\s*%\s*(보장\|성공\|수익\|확실)` | "100% 충전 완료" | "충전" 은 캡처 그룹에 없어 비매칭. 확인 |
| `누구나` | "누구나 알 만한 상식" | 광고 맥락상 매칭 유지 (보편 수혜 톤). 단 검증만 |

### 변경
- `tests/test_rule_engine.py` 에 `test_*_negative` 케이스 추가 (카테고리별 1개씩, 총 ~10개)
- 오탐 확정 시 `rules/patterns.py` regex 보강:
  - `고금리` → `고금리\s*(?:상품|특판|혜택|적금|예금)` 로 광고 맥락 한정 (정보성 "고금리 시대" 제외)
  - `최고의?` → 합성어 제외: `최고(?:의|치|급)?(?!경영|치|위원|급)` 정도로 — 과도하면 단순 유지. **보수적으로 "고금리" 만 손보고 나머지는 negative 테스트로 현 동작 고정**

### 검증
- 새 negative 테스트 통과 (오탐 없음 확인)
- 기존 positive 테스트 유지

---

## H2 · ResponseCache LRU cap + 통계 + stats endpoint

### 배경
`ResponseCache` 가 TTL 만 있고 size cap 없음 → 다양한 입력이 쌓이면 메모리 무한 증가. 운영 가시성(hit/miss)도 없음.

### 목표
- `max_entries` (기본 256) 초과 시 **가장 오래된 항목 eviction** (insertion-order = `dict` 순서 활용)
- `hits` / `misses` 카운터
- admin `GET /v1/health/cache-stats` 로 노출 (analyze + rewrite 캐시 각각)

### 변경

`services/_response_cache.py`:
```python
class ResponseCache(Generic[T]):
    def __init__(self, ttl_seconds=..., max_entries: int = 256):
        ...
        self._max = max_entries
        self.hits = 0
        self.misses = 0

    def get(self, key):
        # 만료/부재 시 misses += 1, 적중 시 hits += 1 + move-to-end (LRU)
    def set(self, key, value):
        # 초과 시 가장 앞(오래된) 항목 pop
    def stats(self) -> dict:
        return {"entries": len(self), "hits": ..., "misses": ..., "ttl_seconds": ..., "max_entries": ...}
```

LRU 갱신: `dict` 는 insertion order 보존. `get` 적중 시 `pop` 후 재삽입으로 최신화. `set` 시 `len >= max` 면 `next(iter(self._store))` 제거.

`api/v1/health.py` (또는 compliance):
```python
@router.get("/cache-stats")
def cache_stats():
    from app.services.analyze_service import _ANALYZE_CACHE
    from app.services.rewrite_service import _REWRITE_CACHE
    return {"analyze": _ANALYZE_CACHE.stats(), "rewrite": _REWRITE_CACHE.stats()}
```
(admin token 게이트는 기존 admin 라우터 패턴 따름. health 하위면 공개여도 민감정보 없음 → 공개로 둠)

### 테스트
`tests/test_response_cache.py` 확장:
- max_entries 초과 시 oldest eviction
- hits/misses 카운트 정확
- LRU: 적중한 항목은 eviction 우선순위에서 밀려남

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| `rules/patterns.py` | 고금리 등 일부 regex 보강 |
| `tests/test_rule_engine.py` | negative 케이스 |
| `services/_response_cache.py` | LRU cap + stats |
| `api/v1/health.py` | cache-stats 엔드포인트 |
| `tests/test_response_cache.py` | cap/LRU/통계 테스트 |

## 검증
- ruff + pytest
