# Day 22 — Tooltips · 세션 보존 · Evidence DB 조회

## 배경

이전 [day-22-icons-inline-expand-polish.md](day-22-icons-inline-expand-polish.md) 까지 적용한 뒤 사용자가 추가로 발견한 6가지:

1. **`?` 마크가 장식**: InputStep 의 "상품 유형 ?", "채널 ?" 등 라벨 옆 물음표가 hover 시 아무 설명도 보여주지 않음 — 실제 도움말 툴팁이어야 함.
2. **신뢰도 의미 불명확**: RedlineStep 의 "신뢰도 93%" 표기만으로는 무엇의 신뢰도인지 모름. 옆에 `?` + 툴팁 필요.
3. **세션 휘발**: "준법검토 시작" → RedlineStep → "원문 보기" 클릭 시 InputStep 으로 돌아가지만, 거기서 다시 분석으로 가려면 또 "준법검토 시작" 을 눌러야 함 (재분석 발생). 또한 페이지 새로고침하면 모든 진행 상황 소실.
4. **카운터 여전히 잘림**: 첫 스크린샷에서 `59 / 2,000` 의 "59" 가 chip-style 원형 안에 보이지만 우측 vertical scrollbar 와 너무 가까워 시각적으로 컨테이너 밖으로 흘러나가 보임.
5. **Evidence 구조 산만**: 3개 패널 (리스크 검토 대상 문장 / 검토 요약 / 근거 패널) 이 각자 정보를 중복 제공 + "리스크 1 ↔ 근거 1" 같은 단순 인덱스 매핑은 의미 전달이 약함.
6. **DB instance 조회 부재**: 사용자가 근거 카드를 보고도 "이 근거가 실제 DB 어디서 왔는지" 확인할 길이 없음 — `원문 보기` 버튼은 동작하지 않음.

## 목표 / Non-goals

### 목표
- 모든 `?` 마크가 hover/focus 시 한국어 설명 풍선을 띄움 (접근성: keyboard focusable, role)
- 신뢰도 옆에도 동일한 `?` 적용
- localStorage 에 store state 보존 → 새로고침해도 진행 유지. InputStep 진입 시 이전 분석 결과가 있으면 "이전 검토 결과 보기" CTA 표시
- 카운터가 어떤 폭에서도 panel 안에 안전하게 위치
- EvidenceStep: 좌측 리스크 선택 → 우측 해당 리스크와 매칭된 근거 + DB 인스턴스 확인 가능한 일관된 흐름
- 백엔드: `GET /v1/compliance/regulation-versions/{version_id}` 로 raw_text / 메타데이터 노출
- 프론트: 근거 카드의 "DB 인스턴스 보기" 클릭 시 모달/패널에 raw_text snippet, version_label, effective_date, source, content_hash 표시

### Non-goals
- 새 디자인 라이브러리 추가 — tooltip 은 직접 inline CSS + React state
- regulation 편집/생성 UI — 조회만
- 풀텍스트 검색 — 단순 단건 조회

## 변경 사항

### 1. HelpHint 컴포넌트 (신규)

`apps/frontend/src/components/HelpHint.tsx`
```tsx
interface HelpHintProps { label?: string; hint: string; }
export function HelpHint({ label = "?", hint }: HelpHintProps) {
  const [open, setOpen] = useState(false);
  return (
    <span className="help-hint">
      <button
        type="button"
        className="help-hint__trigger"
        aria-label={`도움말: ${hint}`}
        aria-expanded={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(e) => { e.preventDefault(); setOpen((v) => !v); }}
      >{label}</button>
      {open ? <span role="tooltip" className="help-hint__bubble">{hint}</span> : null}
    </span>
  );
}
```
CSS: 원형 outline 트리거 + 풍선 (position: absolute, top-aligned, arrow optional). 한국어 문장 줄바꿈 허용.

### 2. InputStep — 5개 라벨에 HelpHint 적용

기존 `<small>?</small>` 를 `<HelpHint hint="...">` 로 교체. 힌트 내용:
- 상품 유형: "검토할 콘텐츠가 광고하는 금융상품 종류입니다. 규정 매칭과 리스크 분석의 1차 기준이 됩니다."
- 채널: "콘텐츠가 노출되는 매체입니다. 채널별 표현 규정과 글자수 제약이 다릅니다."
- 타겟 고객: "주요 광고 대상 고객층입니다. 위험 표현 허용도와 필수 고지 사항이 달라집니다."
- 언어: "콘텐츠 작성 언어입니다. 분석 모델과 규정 DB 선택에 사용됩니다."
- 콘텐츠 입력: "검토할 마케팅 문안을 그대로 붙여넣으세요. 2,000자까지 분석합니다."

### 3. InputStep — Resume CTA

`state.analyze` 가 있고 `state.step === "input"` 일 때, 페이지 상단에 noticeboard:
```
[이전 검토 결과가 있습니다]  분석 시각 / 위험도 요약  [검토 결과 보기 →]
```
클릭 시 `goTo("redline")`. 백엔드 호출 없음.

### 4. RedlineStep — 신뢰도 ?

신뢰도 row 에 HelpHint 추가:
- "AI가 탐지한 모든 표현의 평균 신뢰도입니다. 100% 에 가까울수록 자동 탐지 결과가 더 확실합니다. 70% 미만은 사람 검토를 권장합니다."

### 5. 세션 보존 (localStorage)

`apps/frontend/src/features/compliance/store.ts`
- `INITIAL_STATE` 를 `loadPersisted() ?? INITIAL_STATE` 로 초기화
- 모든 `setState` 후 `persist(current)` 호출 — useEffect 한 줄로 처리:
  ```ts
  useEffect(() => { persist(state); }, [state]);
  ```
- key: `compliance.workflow.v1`
- 저장 제외 필드: `isLoading`, `pendingAction`, `errorMessage`, `actionMessage` (휘발성)
- 버전 mismatch 시 무시하고 default 사용

`reset()` 호출 시 `localStorage.removeItem(...)` 도 함께.

### 6. 카운터 overflow 보강

CSS:
- `.copy-field > span` 의 padding-right 약간 추가
- `.character-count` 를 둘러싸는 chip-style:
  ```css
  .character-count {
    padding: 2px 8px;
    border-radius: 999px;
    background: #f1f5f9;
    color: #475569;
    font-size: 0.78rem;
    line-height: 1.4;
  }
  ```
- 우측 vertical scrollbar 공간을 고려해 `.step-panel` 우측 padding 살짝 확보

### 7. 백엔드 — EvidenceItem 에 version_id, GET /regulation-versions/{id}

`apps/backend/app/schemas/evidence.py`
- `EvidenceItem` 에 `version_id: str | None = None`, `effective_date: str | None = None` 추가

`apps/backend/app/services/evidence_service.py`
- EvidenceItem 생성 시 `version_id=doc.version_id`, `effective_date=doc.effective_date` 전달

`apps/backend/app/schemas/regulation.py` 는 그대로 사용.

`apps/backend/app/api/v1/compliance.py`
- `GET /regulation-versions/{version_id}` → RegulationVersion (raw_text 포함). repo 추가 메서드:
  - `RegulationVersionsRepository.get(version_id)` — Supabase select_one + fallback dict 조회

### 8. EvidenceStep 리팩토링

새 구조 (좌측 리스크 / 우측 매칭 근거 + DB 보기):
```
[panel-heading] 근거 패널 — 리스크별 매칭 규정을 확인하세요.

[two-col grid]
┌─ 리스크 목록 ──────┐  ┌─ 매칭 근거 ──────────────────────┐
│ ● 1 누구나         │  │ [선택된 리스크 카드 헤더: 1 누구나] │
│   2 연 8% 수익     │  │  ─                                │
│   3 안정적으로     │  │ ① 금융상품 광고 심사 가이드라인   │
│   4 원금 걱정 없이 │  │   "투자성 상품 ..."               │
└────────────────────┘  │   [DB 인스턴스 보기] 관련도 87%   │
                        │ ② 내부 통제 규정 ...              │
                        └───────────────────────────────────┘

[info-strip] 위 근거는 내부 규정·가이드라인 DB ...
[action-row] [Redline으로] [수정안 생성]
```
- 좌측: 모든 risk span 의 button 리스트, 선택 강조
- 우측: 선택된 risk 의 risk_category 와 매칭되는 evidence(들) 표시. 매칭 로직: doc.risk_categories 에 해당 카테고리 포함 — 백엔드는 이미 risk_categories 로 retrieve 했으므로 evidence_list 가 곧 매칭 후보. 일단 선택된 리스크의 카테고리가 evidence 의 분류와 일치하는 것 우선, 나머지는 보조로 표시
- 기존 `risk-context-panel`, `guideline-panel summary` 카드는 통합/제거하고 요약은 `panel-heading` 옆 작은 metric chip 들로 압축

### 9. DB 인스턴스 모달

`apps/frontend/src/features/compliance/components/EvidenceSourceModal.tsx` (신규)
- portal 없이 fixed overlay (간단)
- 표시 필드: 제목 / version_label / effective_date / source_id / content_hash / chunk_count / raw_text (preview, 1500자 잘림)
- 닫기 버튼, ESC 키 지원

`apps/frontend/src/features/compliance/api.ts`
- `fetchRegulationVersion(versionId: string)` 추가

EvidenceStep 의 각 근거 카드:
- 기존 동작 없던 `<button>원문 보기</button>` → `[DB 인스턴스 보기]` 로 라벨 변경, 클릭 시 모달 오픈
- `evidence.version_id` 가 없으면 비활성화 + "데모 데이터" 안내

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| 신규 | `components/HelpHint.tsx`, `components/EvidenceSourceModal.tsx` |
| 변경 | `InputStep.tsx`, `RedlineStep.tsx`, `EvidenceStep.tsx`, `store.ts`, `api.ts`, `types.ts`, `styles.css` |
| 백엔드 | `schemas/evidence.py`, `services/evidence_service.py`, `repositories/regulation_versions_repo.py` (get 메서드), `api/v1/compliance.py` |
| 영향 없음 | ApprovalStep, HistoryPage, AgentRunPage, AppShell |

## 검증

- `npm run build` 통과
- 백엔드 pytest 통과 + 가능하면 `/regulation-versions` 단건 조회 동작 확인
- 캡처:
  - InputStep 에서 `?` hover 시 풍선
  - RedlineStep 의 신뢰도 ? 풍선
  - InputStep 진입 시 resume CTA
  - 새로고침 후 step 보존 (localStorage)
  - EvidenceStep 신구조: 좌측 리스크 선택 → 우측 매칭 근거 변경
  - DB 인스턴스 모달 열림

## 롤백

각 hunk 별 revert 가능. localStorage key 는 `compliance.workflow.v1` 이라 버전 bump 또는 사용자가 직접 삭제하면 됨.
