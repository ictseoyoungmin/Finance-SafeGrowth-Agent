# P1-B · Rule Engine 확장 (4 → 15+ 패턴)

## 배경

현재 `rule_engine.py` 의 4개 카테고리:
1. 과장 표현 (`누구나|무조건|반드시|절대|업계 최고|최고의`)
2. 확정 수익 오인 (`연 N% 수익|확정 수익|매월 N% 지급`)
3. 안정성 오인 (`안정적으로|안전하게|위험 없이|리스크 없이|걱정 없이`)
4. 원금 보장 오인 (`원금 걱정 없이|원금 보장|원금 손실 없이`)

문제: 금감원 광고심사 실 가이드 대비 너무 적음. 데모에서 실제 광고 카피의 흔한 위반들이 잡히지 않음.

또한 P1-A 작업 중 발견: `반드시` 가 보수적 disclaimer 문구 ("반드시 확인하시기 바랍니다") 에서도 매칭되어 false-positive 발생.

## 목표

1. **카테고리 4 → 9개 추가 (총 13)** + 패턴 4 → 15+ 개로 확장
2. **`반드시` false-positive 정리** — 단독으로 위험 단어 아니므로 제거. 대신 "절대 100%" 같은 강한 강조에 한정
3. 카테고리별 정의를 `rules/patterns.py` 로 분리 (가독성)

### 추가 카테고리/패턴

| 카테고리 | severity | 정규식 (간략) | 사유 |
| --- | --- | --- | --- |
| 과장 표현 (기존) | HIGH | `누구나|무조건|절대|업계\s*1?위|업계\s*최고|최고의?` | "반드시" 제거 |
| 확정 수익 오인 (기존) | HIGH | `연\s*\d+%\s*(수익|수익률|이자)|확정\s*수익|매월\s*\d+%\s*지급` | 기존 + 보강 |
| 안정성 오인 (기존) | MEDIUM | `안정적으로|안전하게|위험\s*없이|리스크\s*없이|걱정\s*없이` | |
| 원금 보장 오인 (기존) | HIGH | `원금\s*걱정\s*없이|원금\s*보장|원금\s*손실\s*없이|손실\s*없이` | |
| **보증/장담** (신규) | HIGH | `완벽\s*보장|100%\s*(보장|성공|수익)|장담|확실히` | 강한 약속 |
| **한정 마케팅** (신규) | MEDIUM | `오늘만|마감\s*임박|선착순|단\s*\d+(?:일|시간|분)\s*한정|마지막\s*기회` | 충동 유도 |
| **수수료/금리 누락** (신규) | MEDIUM | `수수료\s*무료|수수료\s*없음|중도해지\s*수수료\s*없` | 실제 발생 가능한 부담 미고지 |
| **비교 광고** (신규) | MEDIUM | `타사\s*대비|타\s*상품\s*보다|업계\s*최저|시중\s*최저` | 객관 근거 미제시 |
| **수상/검증 과장** (신규) | LOW | `1위\s*수상|대상\s*수상|공식\s*인증|국가\s*인증` | 출처 명시 필요 |
| **시급성/감정 호소** (신규) | LOW | `놓치지\s*마|지금\s*아니면|후회\s*없는|딱\s*하나` | 감정 자극 |
| **이자/금리 기간 미명시** (신규) | LOW | `고금리|초저금리(?!\s*\d)` | 기간/조건 미명시 |
| **광고심의필 누락 안내** (신규) | LOW | (간접: `심의필` 단어 없으면 별도 체크 — 별도 PR) | 부재 검출은 다른 방식 필요 — 이번에는 생략 |
| **개인정보/보안 오인** (신규) | MEDIUM | `절대\s*안전|보안\s*100%|해킹\s*걱정\s*없` | |

총 신규: 8개 카테고리, 패턴은 20+.

## 변경 사항

### `apps/backend/app/rules/patterns.py` (신규)

```python
"""Pattern definitions for the rule engine.

Keep them in one place so adding/tuning is independent from the engine logic.
Each entry is (pattern, risk_category, severity, reason, confidence).
"""

from app.schemas.compliance import RiskLevel

PATTERN_DEFINITIONS: list[tuple[str, str, RiskLevel, str, float]] = [
    # === 과장 표현 ===
    (r"누구나|무조건|절대(?!\s*안전)|업계\s*1\s*위|업계\s*최고|최고의?",
     "과장 표현", RiskLevel.HIGH,
     "보편적 수혜 또는 조건 없는 혜택으로 오인될 수 있습니다.", 0.92),
    # ...
]
```

### `apps/backend/app/rules/rule_engine.py`

`__init__` 에 `PATTERN_DEFINITIONS` 를 import 해 자동 Rule 생성.

### 기존 테스트 영향

`test_rule_engine.py`:
- `누구나` (HIGH) 그대로
- `반드시` 가 매칭되던 DEMO_TEXT 의 "누구나" 만 잡힘 (반드시 제외) → 기존 카테고리 assertion 그대로
- "원금 손실 없이" → 원금 보장 오인 HIGH 그대로

### 새 테스트

`test_rule_engine.py` 에 신규 카테고리별 positive 1건씩.

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| 신규 | `rules/patterns.py` |
| 변경 | `rules/rule_engine.py` (단순 wrapper) |
| 테스트 | `tests/test_rule_engine.py` 확장 |

## 검증

- ruff
- pytest 기존 + 신규 모두 통과
- P1-A 의 보수적 rewrite 텍스트 ("…유의사항을 반드시 확인…") 에서 "반드시" 매칭 사라짐 → 잔존 위험 LOW
