# Day 22 — Icons · Inline Expand · Side Polish

## 배경

[day-22-sticky-shell-report-history.md](day-22-sticky-shell-report-history.md) 까지 적용한 뒤 사용자가 발견한 후속 이슈 7가지:

1. **검토 이력 inline expand 위치**: 항목을 클릭하면 리포트가 *리스트 맨 밑* 에 붙어 표시됨 — 어떤 항목을 골랐는지 시선이 끊김. 클릭한 카드 *바로 아래* 에 펼쳐져야 함.
2. **사이드바 가이드 카드 항상 펼침**: "규정 기반 검토 가이드" 가 항상 펼쳐져 있음. 사용자는 이전 구조에서 "자세히 보기" 를 눌렀을 때 가이드가 나오는 토글을 원했음.
3. **사이드바 step 텍스트만**: 이전에 유니코드 도형 (□ ○ ▤ ⇄ ▱) 제거 후 텍스트만 남았는데 너무 심심함. 규정 검토 워크플로우 의미와 어울리는 깔끔한 **SVG 아이콘** 을 다시 부착.
4. **`59 / 2,000` 카운터가 컨테이너 밖으로**: textarea 아래 별도 row 로 두니 우측 rail 과 시각적으로 겹쳐 보임. 카운터를 label 헤더 우측 (질문 라벨 옆) 으로 이동.
5. **History 로딩 메시지에 spinner 없음**: 버튼 spinner 와 동일한 회전 표시를 텍스트에도.
6. **검토 이력 ↔ 검토 화면 왕복 어려움**: HistoryPage 에 "검토로 돌아가기" back 링크.
7. **사이드바 "검토 이력" 앞 아이콘**: 책/아카이브 SVG 아이콘 부착.

## 목표 / Non-goals

### 목표
- 클릭한 history 카드 바로 아래에 ReportPackagePanel 펼쳐짐 (시각적 연결)
- 가이드 카드 default closed → "자세히 보기 ▾" 클릭 시 열림
- 5-step 사이드바 항목에 의미 있는 SVG 아이콘 부착
- 카운터가 viewport 폭에 관계없이 panel 안에서만 표시
- `aria-busy` 와 동일한 회전 spinner 가 텍스트 로딩 상태에서도 표시
- HistoryPage 좌상단 "← 검토로 돌아가기"
- 사이드바 "검토 이력" 링크 앞 책 SVG

### Non-goals
- 새로운 라이브러리 (heroicons 등) 추가 — 직접 inline SVG 컴포넌트로 작성
- AgentRunPage 영향 없음
- ApprovalStep 의 ReportPackagePanel 동작 변경 없음 (스타일만 공유)

## 변경 사항

### 1. 신규 아이콘 컴포넌트 — `apps/frontend/src/components/icons.tsx`

작은 stateless 함수형 컴포넌트들. 모두 `currentColor` 기반 stroke 로 그려 CSS 컬러에 자동 맞춤.

```tsx
export const DocumentIcon = (props: IconProps) => <svg ... />;       // 콘텐츠 입력
export const RiskIcon = (props: IconProps) => <svg ... />;           // 리스크 분석 (삼각경고)
export const EvidenceIcon = (props: IconProps) => <svg ... />;       // 근거 패널 (책)
export const CompareIcon = (props: IconProps) => <svg ... />;        // 수정안 비교 (양방향 화살표)
export const ApproveIcon = (props: IconProps) => <svg ... />;        // 승인 패키지 (체크 배지)
export const ArchiveIcon = (props: IconProps) => <svg ... />;        // 검토 이력 (책장)
export const ChevronIcon = (props: IconProps) => <svg ... />;        // 가이드 토글
export const ArrowLeftIcon = (props: IconProps) => <svg ... />;      // 뒤로 가기
```

크기 기본 18px, `aria-hidden`, `focusable=false`.

### 2. AppShell — 사이드바 정비

`apps/frontend/src/components/layout/AppShell.tsx`

- `STEPS` 배열에 `Icon` 필드 추가:
  ```tsx
  { id: "input", label: "콘텐츠 입력", title: "콘텐츠 입력", Icon: DocumentIcon },
  ...
  ```
- step-item 렌더 부분: 번호 동그라미와 라벨 사이에 `<Icon className="step-item__icon" />` 삽입
- side-foot 의 "검토 이력" 링크 앞에 `<ArchiveIcon />` 부착
- 가이드 카드:
  - `useState<boolean>(false)` `guideOpen` 상태
  - 헤더 row 를 버튼으로: `"규정 기반 검토 가이드"` 텍스트 + `ChevronIcon` (rotated when open)
  - `guideOpen` 일 때만 본문(설명 + API/모드 meta) 노출

### 3. Step item layout 조정

CSS (`styles.css`)

- `.step-item` 그리드: `38px 24px minmax(0, 1fr)` (번호 / 아이콘 / 라벨)
- `.step-item__icon { color: #6b7280 }`, active 시 `var(--blue)` 로
- 1080px breakpoint: 아이콘 숨김 (가로 모바일에서 공간 부족)

### 4. 가이드 토글 CSS

- `.side-guide-toggle`: 전체-너비 버튼 스타일 (border 없음, 좌우 padding, hover 시 배경 미세 변경)
- `.side-guide-toggle__chevron`: `transition: transform 0.18s`, `[aria-expanded="true"]` 일 때 180deg 회전
- `.side-guide-body`: 닫혔을 때 `display: none`

### 5. 카운터를 헤더 우측으로

`InputStep.tsx`
- label 의 첫 row (`<span>콘텐츠 입력 ?</span>`) 를 flex 컨테이너로 만들고, 그 안에 `<small className="character-count">` 를 함께 배치 (textarea 아래의 별도 row 에서 제거)

CSS:
- `.copy-field span { display: flex; align-items: center; gap: 8px }` 그대로 + `.character-count` 를 `margin-left: auto` 로 우측 정렬
- 기존 `justify-self: end` 제거

ApprovalStep 의 `<small>{finalText?.length ?? 0} / 2,000</small>` 도 동일한 패턴인지 확인 — 이미 panel-heading 안에 있음. OK.

### 6. HistoryPage 개편

`apps/frontend/src/features/compliance/HistoryPage.tsx`

- 최상단에 back 링크:
  ```tsx
  <a className="back-link" href="#/">
    <ArrowLeftIcon /> 검토로 돌아가기
  </a>
  ```
- 리스트 렌더 시 selected 한 항목 바로 아래에 ReportPackagePanel 펼침:
  ```tsx
  {state.items.map((item) => (
    <li key={item.id}>
      <button .../>
      {selectedId === item.id ? (
        <div className="history-item__report">
          {reportLoading ? <p className="loading-block" aria-busy>리포트 불러오는 중...</p> : null}
          {reportError ? <div className="notice">...</div> : null}
          {report ? <ReportPackagePanel report={report} ... /> : null}
        </div>
      ) : null}
    </li>
  ))}
  ```
- 하단의 `<div className="history-report">` 블록 제거 (위치 이동)
- 로딩 메시지 `"최근 검토 목록을 불러오는 중..."` 에 `aria-busy` + `.loading-block` 클래스 (spinner CSS 적용 대상)

### 7. 인라인 spinner 유틸

CSS:
```css
.loading-block,
p[aria-busy="true"] {
  position: relative;
  padding-left: 36px;
}

.loading-block::before,
p[aria-busy="true"]::before {
  content: "";
  position: absolute;
  left: 12px;
  top: 50%;
  width: 14px;
  height: 14px;
  margin-top: -7px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-right-color: transparent;
  opacity: 0.85;
  animation: button-spin 0.7s linear infinite;
}
```

기존 `button[aria-busy="true"]` 의 keyframes (`button-spin`) 재사용.

### 8. Polish

- 사이드바 number badge 와 아이콘이 active 시 같은 파란색으로 강조 (이미 number는 처리됨, 아이콘 색상 추가)
- 가이드 토글 영역에 `cursor: pointer` 명시
- HistoryPage 의 history-item active 시 box-shadow 강화로 어떤 게 펼침 상태인지 명확하게
- topbar 의 `.api-chip` 에 `max-width: 320px; overflow: hidden; text-overflow: ellipsis` (이미 부분적으로 보임 — 명시적으로)

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| 신규 | `apps/frontend/src/components/icons.tsx` |
| 변경 | `AppShell.tsx`, `HistoryPage.tsx`, `InputStep.tsx`, `styles.css` |
| 영향 없음 | 백엔드, ApprovalStep, ComplianceTraceRail, AgentRunPage |

## 검증 계획

- `npm run build` 통과
- 캡처:
  - `/` 사이드바: 5-step 각각에 아이콘, 검토 이력 앞 책 아이콘, 가이드 카드 collapsed
  - 가이드 카드 expanded (CDP 불가 시 default state 잠시 토글로 검증 후 원복)
  - `/#/history` 리스트 + back 링크 + (시드 데이터로) 첫 항목 선택 시 리포트가 그 아래에 펼침
  - `/` 입력 화면: 카운터가 textarea 헤더 우측에 위치, panel 안에 안전하게 들어감

## 롤백

각 파일 hunk 단위. 신규 `icons.tsx` 는 삭제만 하면 됨.
