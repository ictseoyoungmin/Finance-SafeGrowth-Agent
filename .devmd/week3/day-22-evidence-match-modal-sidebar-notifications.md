# Day 22 — Evidence 매칭 · 모달 404 · 사이드바 nav · 알림 읽음

## 배경

배포 후 사용자가 발견한 5건:

1. **Evidence 매칭이 엉뚱한 근거를 보여줌**: 선택한 리스크가 "원금 보장 오인"인데 매칭된 근거 카드가 "내부 통제 규정 (과장 표현)" 으로 표시됨. 백엔드 evidence 가 1건 (`참조 근거 1` 표시) 만 반환된 환경에서, `matchEvidenceForRisk` 의 *fallback-to-first* 로직이 카테고리와 무관한 항목을 첫 카드로 강제 표시한 것.
2. **DB 인스턴스 보기 404**: 모달 안에 "Failed to fetch" 가 그대로 노출. 실제 원인은 production 배포가 아직 안 된 백엔드라 `GET /v1/compliance/regulation-versions/{id}` 엔드포인트 자체가 없음. 사용자 친화적 안내로 교체 필요.
3. **카운터 chip 살짝 우측 overflow**: 입력 화면에서 `59 / 2,000` 의 chip 이 textarea 우측 경계 밖으로 살짝 튀어나옴 (다른 step 의 카운터는 멀쩡). InputStep 의 label flex 배치가 textarea 와 정렬되지 않음.
4. **사이드바 step 클릭으로 이동 불가**: 우측 trace rail 클릭으로 이동하는 기능을 제거(?)했지만 사용자 의도는 *우측 rail = 단계 정보만 / 좌측 사이드바 = 명시적 단계 이동* 분리. 또한 이동했다 돌아와도 결과는 재 fetch 없이 그대로 보존되어야 하고, 명시적으로 "수정안 생성" 버튼을 다시 누를 때만 재 생성.
5. **알림 읽음 처리 부재**: 드롭다운에 모인 audit 이벤트를 개별 읽음 / 모두 읽음으로 치울 방법이 없음. 읽으면 빨간 배지 카운트도 그만큼 감소해야 함.

## 목표 / Non-goals

### 목표
- EvidenceStep 매칭: fallback-to-first 제거 → 명확한 빈 상태 메시지 + "같은 검토에 포함된 다른 근거" 섹션은 그대로 유지
- DB 인스턴스 모달: 404 / network 오류를 사용자 친화적 안내로 ("이 API base 에는 아직 규정 조회 엔드포인트가 배포되지 않았습니다.")
- 카운터: textarea 우측 경계 안쪽으로 정렬되도록 견고하게
- 사이드바 5-step: 각 항목을 클릭 가능한 button 으로 변환, `hasData` 인 step 만 활성. 클릭 시 store 의 `goTo` 만 호출 → fetch 재호출 없음
- 우측 trace rail: 클릭으로도 여전히 이동 가능 (사용자가 "이동 안 한다고 했다"는 인식과 달리 코드는 이동함; 명시성 강화). 좌/우 어느 쪽으로 클릭해도 결과는 보존.
- 알림: 각 항목 우측에 "읽음" 버튼 + 상단에 "모두 읽음" 버튼. 읽은 항목은 dropdown 에서 사라지고 빨간 배지 카운트 감소. dismiss 한 entry key 는 localStorage 에 저장 (세션 간 유지)

### Non-goals
- audit_logs 에 read state 컬럼 추가 (백엔드 변경) — 클라이언트 dismiss 로 충분
- production 백엔드 자동 배포 (사용자 결정 영역)
- evidence 검색 알고리즘 자체 개선 (제공된 evidence_list 안에서의 표시 로직만 정리)

## 변경 사항

### 1. EvidenceStep 매칭 로직 정리

`apps/frontend/src/features/compliance/steps/EvidenceStep.tsx`

```tsx
function matchEvidenceForRisk(items, risk) {
  if (!risk) return items;
  return items.filter(item =>
    (item.risk_categories ?? []).some(cat => cat === risk.risk_category)
  );
  // ❌ 기존: matched 비었으면 [items[0]] 로 fallback → 카테고리 무관 카드 노출
  // ✅ 변경: 빈 배열 그대로 반환. 호출부에서 명시적 empty state 표시
}
```

호출부:
- `matched.length === 0` → 메시지: `"선택한 리스크 카테고리({카테고리 한국어 라벨})에 직접 매칭된 근거가 없습니다. 같은 검토에 포함된 다른 근거를 참고하세요."`
- `otherEvidence` (matched 에 포함되지 않은 나머지) 는 그대로 표시

### 2. 모달 404 친화적 안내

`apps/frontend/src/features/compliance/api.ts`
- `fetchRegulationVersion` 호출 시 404 / network 분기:
  ```ts
  if (response.status === 404) {
    throw new ApiUnavailableError("이 백엔드에는 규정 조회 API가 아직 배포되지 않았습니다.");
  }
  ```
- 커스텀 에러 클래스 도입 (`ApiUnavailableError`)

`apps/frontend/src/features/compliance/components/EvidenceSourceModal.tsx`
- catch 블록에서 에러 인스턴스 type 검사:
  - `ApiUnavailableError` 또는 404 메시지 패턴 → "이 환경에서는 규정 원문을 조회할 수 없습니다. 백엔드 업데이트 후 다시 시도해 주세요." + 부가 안내 (요청한 versionId 표시)
  - 그 외 → 기존 generic 메시지

### 3. 카운터 chip 재배치

`apps/frontend/src/features/compliance/steps/InputStep.tsx` + `styles.css`

textarea 위에 라벨/카운터 행을 두 동시에, label 의 grid 와 textarea 의 width 가 항상 동일하게:
- `.copy-field` 가 `display: grid; grid-template-columns: minmax(0, 1fr);` 그대로
- `.copy-field > span` (라벨 행) 의 폭은 label 의 column 폭 = textarea 폭 = 100%
- chip(`.character-count`) 이 한국어 + 숫자 + 슬래시로 길어도 헤더 row 의 우측 끝에 안전하게 자리잡도록 `flex-shrink: 0`
- 추가: label 자체에 `min-width: 0` (grid 안에서 폭 cap 보장)

### 4. 사이드바 step 네비게이션

`apps/frontend/src/components/layout/AppShell.tsx`
- `STEPS` 항목을 `<div>` → `<button type="button">` 으로 (visual 동일)
- 새 prop `onNavigateStep?: (step: WorkflowStep) => void`
- 새 prop `availableSteps?: Set<WorkflowStep>` — 가능한 step set (현재 step 은 항상 포함; 데이터 있는 step 도 포함)
- 항목별 disabled = `availableSteps` 에 없거나 onNavigateStep 미정의 시
- visual: 활성 가능 step 은 cursor pointer + hover 시 미세한 배경 변화. disabled 는 opacity

`apps/frontend/src/App.tsx`
- `ComplianceWizard` 에서 `availableSteps` 계산:
  ```ts
  const available = new Set<WorkflowStep>(["input"]);
  if (state.analyze) available.add("redline");
  if (state.evidence) available.add("evidence");
  if (state.rewrite) available.add("rewrite");
  if (state.approval || state.step === "approval") available.add("approval");
  ```
- `onNavigateStep={workflow.goTo}` 전달

### 5. 알림 읽음 / 모두 읽음

`apps/frontend/src/components/NotificationsBell.tsx`
- `entryKey(entry) = ${entry.created_at}::${entry.content_id}::${entry.action}` (audit_logs 에 id 가 없으므로 합성 키)
- localStorage `notifications.dismissed.v1` 에 dismissed key Set 저장 (JSON array)
- fetch 결과에서 dismissed 항목 필터 → 보이는 entries
- 각 항목 우측 "읽음" 버튼: dismiss 추가 + 상태 갱신
- 헤더에 "모두 읽음" 버튼: 모든 보이는 entries 의 key 를 dismiss 에 추가
- 빨간 배지 카운트 = filtered entries.length

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| FE 변경 | `App.tsx`, `AppShell.tsx`, `InputStep.tsx`, `EvidenceStep.tsx`, `components/HelpHint.tsx` (해당 없음), `components/NotificationsBell.tsx`, `components/EvidenceSourceModal.tsx`, `features/compliance/api.ts`, `styles.css` |
| BE | 변경 없음 |

## 검증

- frontend `npm run build`
- 캡처:
  - EvidenceStep 매칭 없는 카테고리 선택 시 빈 상태 메시지 + 다른 근거 섹션
  - DB 인스턴스 모달 404 친화 메시지
  - 입력 카운터 chip 우측 정렬
  - 사이드바 step 클릭 → 이동 + 데이터 보존
  - 알림 드롭다운 읽음 / 모두 읽음 동작
