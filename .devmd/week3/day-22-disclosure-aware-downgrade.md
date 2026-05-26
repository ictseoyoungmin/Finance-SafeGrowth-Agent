# Day 22 — Disclosure-aware 위험도 강등

## 배경

사용자가 AI 수정안 ("연 8% 수익률을 기대할 수 있으며, 투자 위험을 충분히 인지하고 시작하세요.") 을 그대로 다시 입력했더니 여전히 HIGH 로 분류되었다. 검증 루프 자체는 정상이지만 `RuleEngine` 이 단순 정규식 키워드 매칭이라 같은 문장에 함께 노출된 disclaimer ("투자 위험", "유의사항", "원금 손실" 등) 를 고려하지 못한다.

규제 가이드라인은 사실 *위험 표현 + 필수 고지의 균형* 을 따지므로, 같은 문장 안에 disclosure 가 동시에 나오면 위험도가 한 단계 완화되어야 한다.

## 목표

- `RuleEngine.scan` 의 결과를 *문장 단위 windowing* 으로 후처리:
  - 매칭된 span 이 포함된 sentence 에 disclosure 키워드가 1개 이상 있으면 `severity` 한 단계 강등 (HIGH → MEDIUM, MEDIUM → LOW)
  - LOW 인 경우는 그대로 (혹은 confidence -0.1)
  - `reason` 에 "(주변 고지 문구로 위험도가 한 단계 완화됨)" 부기
- analyze 응답에는 강등된 span 이 그대로 들어가되, 화면에서 LOW/MEDIUM 으로 정상 표시
- 사용자 의도: "수정안에 disclosure 를 잘 추가했으면 같은 위험 단어가 일부 남아 있어도 강등 인식"

### Non-goals
- LLM 기반 컨텍스트 추론 (별도 라운드)
- "수정안 self-validation" (rewrite step 에서 재분석) — 후속 작업
- disclosure 가 없을 때 severity 상향

## 변경 사항

### `RuleEngine` (`apps/backend/app/rules/rule_engine.py`)

1. 클래스 상단에 disclosure 키워드 set:
   ```python
   DISCLOSURE_KEYWORDS = (
       "투자 위험", "투자위험", "원금 손실", "원금손실",
       "손실 가능성", "변동 가능성", "유의사항", "상품설명서",
       "예금자보호", "운용 책임",
   )
   ```
2. sentence split: `[^.!?\n]+[.!?\n]?` 정규식 또는 단순 `re.split` 으로 문장 단위 토큰화. 각 sentence 의 (start, end) 인덱스 보관
3. scan 결과 hit 마다:
   - span 의 start 가 속하는 sentence 찾기
   - 그 sentence 에 disclosure 가 있으면 severity 강등 + reason 부기
4. severity 강등 후 confidence 도 0.05 ~ 0.1 감소 (선택)

### 테스트 (`apps/backend/tests/test_rule_engine.py`)

- 기존 케이스 (disclosure 없을 때 HIGH 유지)
- 추가:
  - 같은 문장에 "투자 위험" → "연 8% 수익률" 매치가 MEDIUM 으로 강등 + reason 에 안내 부기
  - 다른 문장의 disclosure 는 강등에 영향 없음

## 영향 범위
- `apps/backend/app/rules/rule_engine.py`
- `apps/backend/tests/test_rule_engine.py`
- analyze_service / risk_level 계산 로직은 그대로 (강등된 severity 가 자연스럽게 반영)

## 검증
- ruff
- pytest (기존 + 신규)
- 캡처: 사용자 시나리오 (`...투자 위험을 충분히 인지하고...`) 가 MEDIUM 또는 LOW 로 잡힘
