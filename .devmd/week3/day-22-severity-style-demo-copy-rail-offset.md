# Day 22 — 위험도 단계별 표시 · 데모 문구 · Rail sticky 보정

## 배경

3가지 후속 폴리시:

1. **위험도 표시 단계 무차별**: `risk-score::before` 가 항상 빨강 `!` 원형이고 strong 색도 항상 빨강. MEDIUM/LOW 에서도 같은 빨강이 표시되어 톤이 부적절.
2. **데모 문구가 한 종류**: 입력 기본 문구가 항상 "지금 가입하면 누구나 연 8% 수익..." 인데 너무 노골적이고 데모 인상이 강함. 실제 광고 카피 톤으로 교체.
3. **우측 rail 윗부분 잘림**: 스크롤 내릴 때 rail 의 상단이 topbar(82px sticky) 뒤로 가려진 채 따라옴. `top: 18px` 이라 topbar 와 충돌.

## 변경 사항

### 1. severity 별 risk-score 스타일

`apps/frontend/src/styles.css`
- 베이스 `.risk-score::before` 의 빨강 hardcode 제거
- `.risk-score.risk-high::before` → `!` + 빨강 (#ef4444)
- `.risk-score.risk-medium::before` → `⚠` 또는 `!` + amber (#f59e0b)
- `.risk-score.risk-low::before` → `✓` + 초록 (#10b981)
- `.risk-score strong` 색도 클래스별 분기

### 2. rail sticky 보정

```css
.compliance-trace-rail {
  position: sticky;
  top: 100px;             /* topbar(82px) + 18px gap */
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}
```

- topbar 와 겹치지 않도록 offset
- viewport 보다 길어지면 rail 자체에서 스크롤

### 3. 데모 카피 교체

`apps/frontend/src/features/compliance/api.ts` (`DEMO_TEXT`) + `apps/backend/app/services/rewrite_service.py` (`_fallback_content`) + `apps/backend/tests/test_rule_engine.py` (DEMO_TEXT 갱신 — 필요 시)

새 카피 (실제 은행 광고 톤 유지 + rule engine 패턴 매칭):

> "[JB Bank] 신규 고객 특별 혜택! 누구나 가입 가능한 프리미엄 정기예금으로 연 5.0% 이자를 안정적으로 받아보세요. 원금 걱정 없이 시작하는 든든한 자산관리, 지금 신청하세요."

매칭되는 위험 표현:
- "누구나" → 과장 표현 HIGH
- "연 5.0% 이자" → 확정 수익 오인 HIGH
- "안정적으로" → 안정성 오인 MEDIUM
- "원금 걱정 없이" → 원금 보장 오인 HIGH

기존 DEMO_TEXT 를 참조하는 테스트는 그대로 동작 (스니펫 단위가 아닌 카테고리 단위).

## 영향 범위

- `apps/frontend/src/features/compliance/api.ts`
- `apps/backend/app/services/rewrite_service.py` (fallback content)
- `apps/frontend/src/styles.css`
- `apps/backend/tests/test_rule_engine.py` (DEMO_TEXT 상수)

## 검증

- pytest, ruff
- 스크린샷: MEDIUM 화면에서 amber 톤 + ⚠ / LOW 에서 초록 ✓
- 스크롤 후 우측 rail 상단이 잘리지 않고 topbar 아래에 안정적으로 고정
