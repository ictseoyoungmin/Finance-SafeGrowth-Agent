# R-A · 분석 정확성 (cache content_id + disclosure 부정문)

피드백 #2 + #5. 분석 결과의 감사 추적과 false-positive 방지.

## R-A-1 · Analyze cache 와 content_id 분리

### 문제
`AnalyzeService.analyze()` 가 cache hit 시 캐시된 `AnalyzeResponse` 를 그대로 반환 → 새 요청에도 **이전 content_id 가 재사용**. 같은 입력이 15분 안에 두 번 들어오면 두 번째 요청은 `save_original()` / `record_analysis()` 호출도 안 됨. 결과: B 사용자의 승인/수정이 A 사용자의 content 에 이어붙음 → 감사 로그가 꼬임.

### 변경
- cache 대상을 **AnalyzeResponse 전체 → "risk body"** (flagged_spans, risk_level, risk_categories, reviewer_notes) 만으로 좁힘.
- 매 요청은 항상:
  1. `save_original(request)` 로 새 content_id 생성
  2. cache key = `sha256(normalized_text + product_type + channel + target_customer + language)` (input identity, not content_id)
  3. cache hit → risk body 재사용 + 새 content_id 로 risk_results / audit 저장
  4. cache miss → rule + LLM scan → 후처리 → cache.set + DB 저장
- `force_refresh=True` 면 cache 무시 (그대로 유지)

### 구현 디테일
```python
def analyze(self, request, *, force_refresh=False):
    content_id = self._content_repository.save_original(request)
    cache_key = self._risk_cache_key(request)

    if not force_refresh and (cached := self._cache.get(cache_key)):
        risk_body = cached
    else:
        spans = self._merge_spans(...)
        spans = self._post_process_disclosures(...)
        risk_body = RiskBody(
            flagged_spans=spans,
            risk_level=self._risk_level(spans),
            risk_categories=self._risk_categories(spans),
            reviewer_notes=self._reviewer_notes(request, spans),
        )
        self._cache.set(cache_key, risk_body)

    # always persist into the new content_id
    self._risk_results_repository.save_analysis(content_id=content_id, ...risk_body...)
    self._audit_service.record_analysis(content_id, rule_categories=risk_body.risk_categories)

    return AnalyzeResponse(content_id=content_id, **risk_body)
```

신규 internal dataclass `RiskBody` (또는 dict). cache 값은 immutable hashable 객체.

### Non-goals
- 캐시를 LLM 호출 결과만으로 좁히는 더 세밀한 분리 (rule scan 은 매번 빠르니 같이 묶어도 OK)
- Supabase rewriting of cached analyze results (DB 는 매 요청마다 새 row)

### 테스트
- 같은 입력 2회: content_id 달라야 함, LLM 1회만 호출 (mock counter)
- save_original / record_analysis 매번 호출 (FakeContentRepository.calls 카운트)

---

## R-A-2 · Disclosure 부정문 false-strip 방지

### 문제
`is_disclosure_span()` 이 keyword 포함만으로 판정 → "원금 손실 가능성 없음", "원금 손실 가능성이 전혀 없습니다" 같은 **위험 표현** 도 disclosure 로 오인되어 spans 에서 strip 됨. 실제로는 원금 보장 오인 HIGH 인데 누락.

### 변경
`rules/disclosure.py`:
```python
NEGATION_NEAR_DISCLOSURE: tuple[str, ...] = (
    "없음", "없이", "없습니다", "없어요",
    "전혀 없", "걱정 없",
    "무관",
)

def is_disclosure_span(span_text: str) -> bool:
    if any(neg in span_text for neg in NEGATION_NEAR_DISCLOSURE):
        return False
    return any(keyword in span_text for keyword in DISCLOSURE_KEYWORDS)
```

`apply_to_spans` 의 sentence-level downgrade 도 동일하게 영향:
- "원금 손실 가능성 없음" 가 들어있는 sentence 에서 그 phrase 를 disclosure 로 보지 않아야 인접 위험 표현이 잘못 강등되지 않음
- 따라서 sentence-level `has_disclosure_nearby` 도 keyword 매치 직후 negation guard.

### 테스트
- `"원금 손실 가능성이 전혀 없습니다"` → 결과 spans 에 "원금 손실 가능성이 전혀 없습니다" (또는 매칭 위험 표현) HIGH 유지
- 기존 disclaimer "원금 손실 가능성을 유의하며 시작하세요." → 여전히 strip 됨 (positive case 회귀 없음)

## 영향 범위
- `services/analyze_service.py`
- `rules/disclosure.py`
- `tests/test_analyze_service.py`, `tests/test_rule_engine.py`

## 검증
- ruff
- pytest 모든 케이스 통과 (analyze + audit + disclosure)
