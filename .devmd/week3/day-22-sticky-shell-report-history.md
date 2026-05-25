# Day 22 — Sticky Shell · 리포트 UX · 검토 이력

## 배경

이전 폴리시 작업 [day-22-ux-polish-loading-responsive-nav.md](day-22-ux-polish-loading-responsive-nav.md) 이후 사용자가 발견한 4가지 추가 이슈:

1. **상단/좌측 패널이 스크롤에 따라 같이 움직임** — 5단계 progress, 검토 ID 등 상시 참조해야 하는 컨텍스트가 사라짐
2. **좌측 사이드바 하단 빈 공간** — 5-step 리스트와 작은 안내 카드 사이에 큰 white-space, 안내 카드의 "자세히 보기" 도 placeholder
3. **리포트 확인 버튼 UX** — 누르면 `리포트: Approval package generated with decision REVISION_REQUESTED.` 같은 영문 백엔드 로그 문구가 "관련 근거" 카드 끝에 한 줄 추가됨. 사용자는 이게 무슨 의미인지 모름
4. **이전 작업 열람 불가** — Supabase/fallback DB 에 저장된 과거 검토건을 다시 볼 방법이 UI 에 없음

사용자가 명시한 방향:
- 상단/좌측 패널 sticky
- 좌측 패널 하단 문구 잘 보이게 + placeholder 채우기
- 리포트 확인 시 무엇이 일어났는지 명확하게
- DB에 저장된 이전 작업들 열람 가능

## 목표 / Non-goals

### 목표
- `.topbar`, `.sidebar` 가 페이지 스크롤과 무관하게 viewport 에 고정
- 좌측 사이드바 빈 공간을 의미 있는 정보로 채움 + "검토 이력" 으로 이동하는 명확한 링크
- "리포트 확인" 클릭 시 결과를 **전용 패널** 로 표시 (영문 로그 X, 한국어 라벨링)
- `/#/history` 라우트: 최근 검토 N건 리스트, 클릭 시 리포트 패키지 표시

### Non-goals
- 이전 작업의 **편집** 기능 (조회만)
- 페이지네이션 / 검색 / 필터 — 일단 최근 20건 노출
- 인증/권한 — 데모 단계라 익명 접근
- AgentRunPage 의 영향 — 별도 라우트 (`#/agent`) 그대로

## 변경 사항

### 1. Sticky 셸 (frontend CSS 만)

`apps/frontend/src/styles.css`

- `.topbar`:
  - 현재: `min-height: 82px; flex-wrap: wrap; padding: 14px 28px`
  - 추가: `position: sticky; top: 0; z-index: 20; background: #ffffff`
  - 이미 `position: relative` 였으므로 sticky 로 교체 (global-progress 의 `position: absolute` 는 계속 동작)
- `.sidebar`:
  - 현재: `position: sticky; top: 0; grid-template-rows: 104px 1fr auto; min-height: 100vh;`
  - 변경: `height: 100vh; overflow-y: auto` 로 사이드바 자체가 viewport 높이에 고정되고 내용이 길면 사이드바 안에서 스크롤
- `.app-frame`:
  - 현재: `display: grid; grid-template-columns: 308px minmax(0, 1fr); min-height: 100vh; background: var(--panel)`
  - 그대로 유지. `position: sticky` 가 sidebar/topbar 에 동작하려면 부모가 scrolling container 가 아니어야 함 — `min-height: 100vh` 라 body 가 scroller, 사이드바 sticky 정상 동작
- 1080px breakpoint:
  - `.sidebar { position: static; height: auto }` 로 모바일에서는 sticky 해제 (이미 부분적으로 처리됨, 보강)
  - `.topbar { position: static }` 모바일에서도 해제

### 2. 사이드바 하단 안내 정비

`apps/frontend/src/components/layout/AppShell.tsx`

- 기존 `.side-card` (브랜드 아이콘 + 한 줄 안내 + "자세히 보기" placeholder) 를 다음 구조로 교체:
  ```
  <div className="side-foot">
    <a className="side-link" href="#/history">
      <span aria-hidden>📋</span>  // (텍스트로: "검토 이력")
      <div>
        <strong>검토 이력</strong>
        <small>DB에 저장된 최근 검토 보기</small>
      </div>
    </a>
    <div className="side-info-card">
      <p className="side-info-title">규정 기반 검토 가이드</p>
      <p className="side-info-desc">
        리스크 분석은 규정·가이드라인 매칭 결과를 기준으로 진행됩니다.
        Gemini 응답이 없을 때는 입력 문장 기반 fallback 으로 작동합니다.
      </p>
      <dl className="side-info-meta">
        <div><dt>API</dt><dd>{apiBaseUrl}</dd></div>
        <div><dt>버전</dt><dd>week3-day22</dd></div>
      </dl>
    </div>
  </div>
  ```
- 사용자 요청 "특수 문자 X, 텍스트만" 을 따라 이모지 대신 텍스트 라벨만 사용
- placeholder "자세히 보기" 는 명시적인 액션 (검토 이력 이동) 으로 대체
- `brand-kicker.small` 의 빈 그라데이션 아이콘은 제거 — 그 자리에 진짜 콘텐츠가 들어감

CSS 신규:
- `.side-foot { display: grid; gap: 14px; padding: 0 18px 28px; align-self: end; }`
- `.side-link { display: grid; grid-template-columns: 28px 1fr; gap: 10px; padding: 12px; border: 1px solid var(--line); border-radius: 8px; text-decoration: none; color: inherit; transition: border-color 0.12s; }`
- `.side-link:hover { border-color: var(--blue); background: var(--blue-soft); }`
- `.side-info-card { padding: 14px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; }`
- `.side-info-meta { display: grid; gap: 6px; margin: 12px 0 0; }`
- `.side-info-meta div { display: grid; grid-template-columns: 44px 1fr; gap: 8px; font-size: 0.72rem; }`
- `.side-info-meta dt { color: #94a3b8; font-weight: 800; }`
- `.side-info-meta dd { color: #475569; word-break: break-all; }`

### 3. 백엔드: 최근 검토 리스트 + 단건 상세

`apps/backend/app/schemas/compliance.py` (또는 새 파일 `schemas/history.py`)
- `RecentContentItem`: `id`, `created_at`, `product_type`, `channel`, `target_customer`, `language`, `original_text_preview`, `risk_level?`, `decision?`
- `RecentContentsResponse`: `items: list[RecentContentItem]`

`apps/backend/app/repositories/contents_repo.py`
- 추가: `list_recent(limit: int = 20) -> list[dict]`
  - Supabase: `select_many("contents", filters={}, order="created_at.desc", limit=limit)`
  - Fallback: `list(FALLBACK_CONTENTS.values())[-limit:]` (생성순 보존 안 되지만 데모 OK)

`apps/backend/app/services/report_service.py`
- 신규: `list_recent(limit) -> RecentContentsResponse`
  - contents 마다 risk_result + approval 을 fetch 해 요약 객체로 변환
  - `original_text_preview` 는 앞 80자 cut

`apps/backend/app/api/v1/compliance.py`
- 신규 라우트: `GET /v1/compliance/contents/recent?limit=20` → `RecentContentsResponse`

### 4. 리포트 UX 개편

#### 4a. 백엔드: 한국어 요약 + 구조화

`apps/backend/app/services/report_service.py` 의 `_summary` 를 한국어로:
- 영문 백엔드 로그 메시지를 사용자에게 노출하지 않는다.
- 새 메서드 `_summary_ko(risk_level, approval)` 로 분기:
  - approval 있음: `"{decision_label} (이)가 {reviewer} 이름으로 저장되었습니다."` — but decision 라벨링은 frontend 책임. 백엔드는 그냥 `summary` 를 비우고 frontend 에서 조립하는 것이 더 깔끔.
- **결정**: backend `summary` 는 호환을 위해 그대로 두되 (다른 호출자가 있을 수 있음), frontend 에서는 `state.report.summary` 를 화면에 직접 출력하지 않고, `state.report` 의 다른 필드 (`approval`, `audit_log`, `risk_level`, `final_text`) 만 구조적으로 출력.

#### 4b. Frontend: 리포트 패널 분리

`apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
- 기존 "관련 근거" 카드 안쪽의 `리포트: {summary}`, `감사 로그 N건` 두 줄 제거
- 별도 섹션 `<section className="report-package">` 추가: `state.report` 가 존재할 때만 렌더
  - 헤더: "리포트 패키지" + "저장 완료" pill
  - 그리드 항목:
    - 검토 ID
    - 심의 결정 (라벨)
    - 검토자
    - 최종 문안 (preview)
    - 감사 로그 건수
    - 리스크 레벨
  - 하단 안내: "이 리포트는 DB에 저장되었습니다. 좌측 '검토 이력' 에서 다시 조회할 수 있습니다."
- "리포트 확인" 버튼 라벨 변경: `"리포트 확인"` → `"리포트 패키지 다시 보기"` (이미 한 번 클릭하면 패널이 노출되므로)

### 5. 검토 이력 페이지

`apps/frontend/src/features/compliance/HistoryPage.tsx` (신규)
- `fetchRecentContents()` 호출, 로딩 중 spinner, 빈 결과 안내
- 리스트 카드:
  - 날짜 (relative + absolute)
  - 채널 / 상품 유형 / 타겟
  - 원문 미리보기 (80자)
  - 리스크 배지 (HIGH/MEDIUM/LOW) — 없으면 "미분석"
  - 심의 결정 배지 — 없으면 "미승인"
  - 클릭 시 우측 슬라이드 패널 또는 inline expand 로 `fetchReport(id)` 호출 → 4b 와 동일한 리포트 패키지 UI 표시
- API base 가 응답하지 않으면 안내 메시지 ("백엔드 미연결 — 이전 데모 검토 결과를 표시할 수 없습니다")

`apps/frontend/src/features/compliance/api.ts`
- `fetchRecentContents(limit?: number): Promise<RecentContentsResponse>`
- 타입 추가

`apps/frontend/src/App.tsx`
- 라우트 추가: `"/history"` → `<HistoryPage />` (AppShell 안에)
- `currentStep` 은 undefined 로 둠 → 사이드바 5-step 활성 없음

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| Frontend layout | `App.tsx`, `components/layout/AppShell.tsx`, `styles.css` |
| Frontend feature | `features/compliance/steps/ApprovalStep.tsx`, `features/compliance/HistoryPage.tsx` (신규), `features/compliance/api.ts`, `features/compliance/types.ts` |
| Backend API | `api/v1/compliance.py` |
| Backend domain | `services/report_service.py`, `repositories/contents_repo.py`, `schemas/compliance.py` (또는 `schemas/history.py`) |
| Tests | Playwright e2e — 영향 없음 (history 라우트는 별도). Backend `test_api_*` — recent 엔드포인트 신규 테스트는 시간상 후속으로. |

## 검증 계획

- `npm run build` (TS) 통과
- backend: 기존 pytest 통과 + 신규 `list_recent` fallback 케이스 1건 (가능 시)
- Headless Edge 캡처:
  - 스크롤 시 topbar, sidebar 가 viewport 에 고정되는지 (긴 페이지에서 스크롤한 스냅샷 비교)
  - 사이드바 하단 안내가 placeholder 가 아닌 실제 콘텐츠로 채워졌는지
  - ApprovalStep 에서 "리포트 패키지 다시 보기" 클릭 → 전용 패널 표시 (영문 summary 노출 없음)
  - `/#/history` 진입 시 리스트 표시 (백엔드 없으면 안내 메시지)

## 롤백

- Sticky 변경은 CSS hunk 1개 — 간단
- 리포트 패널은 `ApprovalStep.tsx` 의 추가/삭제 hunk
- HistoryPage 는 신규 파일 + App.tsx 라우트 한 줄. 두 군데 revert 로 원복
- 백엔드 신규 엔드포인트는 추가만이라 기존 호출자에 영향 없음
