# Day 22 — Disclosure 후처리 (LLM spans + 자체 disclaimer 제거 + window 확장)

## 배경

사용자가 *AI 가 제안한 보수적 수정안* 을 그대로 다시 입력했는데도 HIGH 가 나옴:

> "[JB Bank] 신규 고객 특별 혜택! 프리미엄 정기예금으로 최대 연 5.0% 이자를 기대할 수 있습니다.
> 원금 손실 가능성을 유의하며 든든한 자산관리를 시작하세요. 지금 신청하세요."

3건 탐지, 모두 LLM 출처:
1. "최대 연 5.0% 이자를 기대할 수 있습니다" - 과장 표현 · LLM (HIGH)
2. "원금 손실 가능성을 유의하며" - 확정 수익 오인 · LLM (HIGH) ← **disclaimer 자체**
3. "든든한 자산관리를 시작하세요" - 안정성 오인 · LLM

근본 원인 3가지:
- (A) disclosure-aware downgrade 가 `RuleEngine.scan` 안에서만 동작 — LLM spans 는 통과
- (B) LLM 이 disclaimer 자체 ("원금 손실 가능성을 유의하며") 를 위험으로 분류 — 후처리 제거 없음
- (C) downgrade window 가 정확히 같은 sentence 만 — "원금 손실 가능성 유의" 가 들어있는 문장과 별개 문장의 위험 표현은 강등 안 됨

## 목표

1. disclosure-aware 강등을 **`AnalyzeService` 최종 단계** 로 옮겨 rule + LLM 양쪽 spans 모두에 적용
2. span 자체가 disclosure 문구를 포함하면 **spans 에서 제외** (false-positive)
3. downgrade window 를 **같은 sentence + 직전/직후 sentence** 로 확장

## 변경 사항

### 1. 공유 모듈 `apps/backend/app/rules/disclosure.py` (신규)

```python
DISCLOSURE_KEYWORDS = ( ... 기존 list ... )
SENTENCE_BOUNDARY = re.compile(r"[.!?\n]+")

def sentence_spans(text) -> list[(start, end)]: ...
def find_sentence_index(spans, pos) -> int | None: ...
def is_disclosure_span(span_text) -> bool:
    return any(k in span_text for k in DISCLOSURE_KEYWORDS)
def has_disclosure_nearby(text, sentences, sentence_index, window=1) -> bool:
    # sentence_index 기준 ±window sentence 의 텍스트에 disclosure 있으면 True
```

`rule_engine.py` 의 분리되어 있던 `_sentence_spans` / `_sentence_for` / `DISCLOSURE_KEYWORDS` / `_DOWNGRADE` 를 `disclosure.py` 로 이동. rule_engine 자체의 `_apply_disclosure_downgrade` 는 제거 (analyze_service 가 담당).

### 2. `RuleEngine.scan` 단순화
`scan` 은 raw hits + dedupe 만. downgrade / disclosure-filtering 미적용.

### 3. `AnalyzeService` 후처리

```python
flagged_spans = self._merge_spans(text, [*rule_hits, *llm_hits])
flagged_spans = self._post_process_disclosures(text, flagged_spans)
```

`_post_process_disclosures` :
- (B) `is_disclosure_span(span.span_text)` → 제외 (LLM 의 false-positive 차단)
- (A)+(C) 각 span 의 sentence index 를 구해, **±1 sentence window** 안에 disclosure 가 있으면 severity 한 단계 강등 (HIGH→MEDIUM, MEDIUM→LOW, LOW→LOW), reason 부기

### 4. `DOWNGRADE_REASON_SUFFIX` 텍스트 정리
"(같은 문장의 고지 문구로 위험도가 한 단계 완화됨)" → window 가 확장됐으므로 "(인접 고지 문구로 위험도가 한 단계 완화됨)" 으로 미세 조정.

## 테스트

`tests/test_rule_engine.py` 의 disclosure 테스트는 그대로 통과해야 함 (rule engine 만 단독으로 봤을 땐 강등 없음 — 동작이 analyze service 로 옮겨졌으므로 테스트 의미 변경 필요).

→ rule_engine 의 disclosure 테스트를 새 `tests/test_disclosure_postprocessing.py` 로 이동 + analyze_service 통과형 테스트로 작성:
- LLM-only span (rule 없이 LLM 만) 이 인접 disclosure 로 강등됨
- disclosure 자체 span 은 제거됨
- ±1 sentence window 동작
- false-positive: "원금 손실 없이" 는 disclosure 로 인식 안 됨 (강등 X)

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| `apps/backend/app/rules/disclosure.py` | 신규 (공유 helper) |
| `apps/backend/app/rules/rule_engine.py` | downgrade 로직 제거 |
| `apps/backend/app/services/analyze_service.py` | 후처리 추가 |
| `apps/backend/tests/test_rule_engine.py` | 기존 disclosure 테스트 삭제 / 이동 |
| `apps/backend/tests/test_disclosure_postprocessing.py` | 신규 (analyze_service 통한 검증) |

## 롤백
disclosure 모듈만 reset 하면 rule_engine 만 동작 (이전 동작). 안전.
