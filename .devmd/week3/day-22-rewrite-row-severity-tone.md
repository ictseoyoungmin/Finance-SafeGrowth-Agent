# Day 22 — Rewrite Row 위험도 톤 · 변경 없음 명시

## 배경

수정안 비교 row 에서 좌측 원문 (delete-mark) 과 우측 수정안 (add-mark) 의 색이 *모든 row 에서 동일* (delete=빨강, add=초록). 동일 텍스트가 양쪽에 그대로 들어간 케이스 (replacement === original — LLM 이 변경하지 않음) 인데도 빨강/초록 양쪽으로 표시되어 위화감이 듦.

화면 예: `4 든든한 자산관리 [빨강] → 든든한 자산관리 [초록]` 같은 단어인데 색이 충돌.

## 목표

1. **변경 없음 row** (`replacement.trim() === original.trim()`) 은 양쪽 mark 를 회색 톤 + "유지 (변경 없음)" 라벨로 표시
2. **위험도 별 mark 색 단계화**: 해당 change.original 에 매치되는 분석 결과 span 의 severity 를 lookup 해서
   - HIGH → 진한 빨강 (현재)
   - MEDIUM → amber/주황
   - LOW → 노랑/연한 톤
3. add-mark 도 비슷한 강도로 분기 (정렬감을 위해 항상 같은 톤 — 초록 단계만 살짝)

## Non-goals
- backend RewriteChange schema 변경 — severity 는 frontend 가 analyze 결과 lookup 으로 해결
- "유지" 케이스 자동 합치기 / 숨김 — 명시적으로 표시

## 변경

### `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
- `severityByOriginal: Map<string, RiskLevel>` 메모 (`state.analyze.flagged_spans` 의 `span_text` → severity)
- 매치 우선순위: 완전 일치 → original 이 span_text 를 포함 → span_text 가 original 을 포함
- row 렌더:
  - `unchanged = change.original.trim() === change.replacement.trim()`
  - mark 클래스: `delete-mark severity-${level} ${unchanged ? "is-unchanged" : ""}` 와 `add-mark ${unchanged ? "is-unchanged" : ""}`
  - row 안의 small 라벨: unchanged 면 "유지" + "원문 유지" / "변경 없음" 표기
  - reason / 개선 포인트 텍스트: unchanged 면 둘 다 "원문이 그대로 유지됩니다" 같은 텍스트 (간결화)

### `apps/frontend/src/styles.css`
- `.delete-mark.severity-HIGH` (기존 빨강 유지)
- `.delete-mark.severity-MEDIUM` amber
- `.delete-mark.severity-LOW` 노랑
- `.delete-mark.is-unchanged`, `.add-mark.is-unchanged` 회색 톤
- `.rewrite-row small.is-unchanged` 도 회색

## 검증
- 빌드 통과
- 캡처: HIGH/MEDIUM/LOW row 가 다른 톤 + unchanged row 가 회색
