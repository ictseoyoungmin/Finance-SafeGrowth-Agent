# P1-A · Rewrite Self-Validation 루프

## 배경

현재 흐름:
```
analyze (HIGH) → evidence → rewrite (LLM) → 사용자에게 보여줌 → 끝
```

문제: LLM 이 만든 수정안 자체에 위험 표현이 잔존해도 알 길 없음.
- 사용자가 본 시나리오: "보수적 수정안을 다시 입력했더니 HIGH" — 즉 LLM rewrite 결과가 다시 분석되면 HIGH가 나옴
- 이걸 사용자가 직접 다시 입력해서 확인할 것이 아니라 시스템이 미리 검사해야 함

## 목표

`rewrite_service.rewrite()` 가 두 revision (conservative, marketing) 을 만든 뒤, 각각을 같은 `RuleEngine` + disclosure post-processor 로 self-check 한다.
결과:
- frontend 가 "이 수정안의 잔존 위험: HIGH 0건, MEDIUM 1건" 처럼 명시
- 잔존 HIGH 있으면 amber 경고 노출 → 사용자가 한눈에 파악

### Non-goals
- 자동 re-LLM round (잔존 HIGH 시 다시 호출) — 별도 슬라이스 (P1-A-2) 로 분리
- LLM-only re-check (RuleEngine 만 사용해도 충분)

## 변경 사항

### Backend

**`apps/backend/app/schemas/rewrite.py`**
```python
class RevisionValidation(BaseModel):
    risk_level: str          # LOW | MEDIUM | HIGH
    residual_high: int       # HIGH 잔존 표현 수
    residual_medium: int
    residual_low: int
    residual_spans: list[dict[str, str]]  # {span_text, risk_category, severity}

class RewriteResponse(BaseModel):
    # ... 기존 필드 ...
    validation_conservative: RevisionValidation | None = None
    validation_marketing: RevisionValidation | None = None
```

**`apps/backend/app/services/rewrite_service.py`**
- 신규 의존성 주입: `rule_engine: RuleEngine` 과 disclosure 후처리 helper
- `rewrite()` 마지막에 두 revision text 를 각각 `_validate_revision(text)` 호출
- `_validate_revision(text)`:
  - rule_engine.scan(text) → disclosure post-processing 적용 (analyze_service 와 동일 로직 재사용)
  - residual_spans 집계 + risk_level 계산
- LLM 결과 path 와 fallback path 양쪽 모두 validation 채움

**중복 제거**: disclosure 후처리 로직이 현재 `analyze_service._post_process_disclosures` 안에 있음. 같은 코드를 rewrite_service 도 호출하려면 helper 함수로 분리해야 함. `rules/disclosure.py` 에 `apply_to_spans(text, spans)` 같은 public 함수 추가.

### Frontend

**`apps/frontend/src/features/compliance/types.ts`**
- `RevisionValidation` 추가, `RewriteResponse` 에 두 validation 필드

**`apps/frontend/src/features/compliance/steps/RewriteStep.tsx`**
- 현재 conservative/marketing 선택 버튼 (revision-actions) 위에 작은 validation chip:
  - "보수안 · 잔존 위험 LOW (HIGH 0 · MEDIUM 0)" - 초록
  - "마케팅안 · 잔존 위험 MEDIUM (HIGH 0 · MEDIUM 1 · LOW 2)" - amber
  - HIGH 잔존 시 빨강 + "추가 검토 권장" 텍스트
- "최종 선택 문안" 패널에도 같은 validation 표시 — 현재 선택된 revision 의 잔존 위험 강조

### Tests

`apps/backend/tests/test_rewrite_service.py`:
- analyze + rule 매칭되는 위험 텍스트 입력 → rewrite 응답에 validation 채워지는지
- 보수적 rewrite ("...상품설명서와 유의사항을 반드시 확인...") → residual_high 0 인지
- 마케팅 rewrite 가 위험 표현 일부 유지 시 residual count 정확한지

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| schemas | `schemas/rewrite.py` |
| services | `services/rewrite_service.py` (DI + validation 추가) |
| disclosure helper | `rules/disclosure.py` (apply_to_spans 추출) |
| service factory | `services/rewrite_service.py::get_rewrite_service` (rule_engine 주입) |
| frontend types | `features/compliance/types.ts` |
| frontend UI | `features/compliance/steps/RewriteStep.tsx`, `styles.css` |
| tests | `tests/test_rewrite_service.py`, 가능하면 `tests/test_api_rewrite.py` |

## 검증

- 백엔드 pytest 통과
- 캡처: RewriteStep 에 "잔존 위험" chip 노출, HIGH 잔존 시 amber 경고
- 사용자 재현 시나리오: 보수적 수정안의 validation 결과가 "HIGH 0건" 으로 표시 → 사용자가 다시 입력해 확인할 필요 없음
