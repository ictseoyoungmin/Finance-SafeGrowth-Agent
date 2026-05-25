# Day 22 — Full Session · History Ops · 심의 도장 · Topbar

## 배경

이전 라운드들 이후 사용자가 실 사용 중에 발견한 7개:

1. **세션 부분 보존**: 우측 패널 검토 흐름에서 step 클릭으로 앞/뒤 이동 시, 이미 fetch 한 결과가 있는데도 `pending` 상태로 분류돼 클릭 시 아무 동작 안 함 또는 재호출. (현재 `buildTraceItems` 의 status 계산이 step index 비교만으로 결정)
2. **DB 인스턴스 보기 disabled**: fallback evidence 에 `version_id` 없어서 버튼 비활성. 데모에서도 그럴듯하게 동작해야 함.
3. **검토 이력 DB 삭제 불가**: 전체/단건 삭제 버튼 필요. (백엔드 endpoint + UI)
4. **위험도 색상 약함**: 좌측 리스크 카드의 위험도 차이가 작은 배지에만 표현. 카드 자체도 위험도별 시각 강도 차이.
5. **"Deterministic fallback" 영문**: RewriteStep 상단 chip 한국어화.
6. **심의 결정 도장 + 저울**: ApprovalStep 의 `approval-stamp` 가 단순 원 + 텍스트. 법원 저울 SVG + 도장 느낌 강화.
7. **상단 UI**: API 주소 chip 노출 불필요. 알림 bell 이 더미 ("3" 만 표시) — 실제 audit_logs 에서 최근 이벤트를 드롭다운으로 보여줘야 함.

## 목표 / Non-goals

### 목표
- trace rail step 클릭 시, 데이터가 있는 step 으로 자유 왕복 가능 (fetch 재호출 없음)
- fallback regulation version 1~2 건을 백엔드 부트 시 자동 시드 → DB 인스턴스 모달 정상 동작
- HistoryPage: 카드 우측 단건 삭제 X + 상단 "전체 삭제" 버튼 (confirm 후 동작)
- EvidenceStep 카드: HIGH/MEDIUM/LOW 별 좌측 색띠/배경 톤
- RewriteStep: `Deterministic fallback` → `기본 패턴 기반` 등 한국어
- ApprovalStep: 도장 SVG (저울 + 둘레 텍스트), 결정에 따라 색·문구 변화
- Topbar: API chip 제거, 알림 bell 클릭 시 최근 audit 이벤트 드롭다운

### Non-goals
- 알림 읽음/안읽음 상태 영구 저장 — 세션 동안만 카운트
- regulation 본문 편집 — 시드 데이터만
- 실시간 push (SSE) — polling 또는 페이지 진입 시 fetch

## 변경 사항

### 1. 세션 완전 보존 — trace rail

`apps/frontend/src/features/compliance/components/ComplianceTraceRail.tsx`
- `buildTraceItems` 의 `status` 계산을 데이터 보유 여부 우선으로:
  ```ts
  function statusForStep(index, currentIndex, hasData): "done" | "active" | "pending" {
    if (index === currentIndex) return "active";
    if (hasData) return "done";     // ← 데이터 있으면 무조건 done
    if (index < currentIndex) return "done";
    return "pending";
  }
  ```
- 클릭 핸들러: `item.status !== "pending"` 그대로 두되, done/active 가 늘어나므로 자연스럽게 왕복 가능
- `store.ts` 의 `loadEvidence`, `loadRewrite` 는 그대로 두되, 만일 데이터가 이미 있고 사용자가 "다시 매칭" 같은 명시적 동작 없이 step 이동만 했다면 fetch 안 함 — 이미 그렇게 동작 (rail 의 goTo 만 호출). 보강 필요 없음.

### 2. Demo regulation version 시드

`apps/backend/app/repositories/regulation_versions_repo.py`
- 모듈 import 시점에 `FALLBACK_REGULATION_VERSIONS` 에 2~3건 시드:
  - `ver-demo-001`: 금융상품 광고 심사 가이드라인
  - `ver-demo-002`: 금융소비자 보호 가이드라인
  - `ver-demo-003`: 내부 통제 규정
- 필드: id, source_id, title, version_label, effective_date, content_hash, raw_text (실제 조문 풍 한국어), chunk_count, ingested_at

`apps/backend/app/repositories/regulation_docs_repo.py`
- `FALLBACK_REGULATION_DOCS` 의 `evidence_id` → `version_id` 매핑이 가능하도록 둘 다 채움:
  - 이미 `version_id` 필드는 dataclass 에 있음. fallback 데이터에 `version_id="ver-demo-XXX"` 추가
- `version_label`, `effective_date` 도 채움
- 결과적으로 `EvidenceItem.version_id` 가 채워져 프론트 "DB 인스턴스 보기" 활성화

`apps/frontend/src/features/compliance/api.ts`
- `fallbackEvidence` 의 항목들에도 `version_id` 추가 (백엔드 실패 케이스 대비)

### 3. 검토 이력 삭제

#### 3a. 백엔드

`apps/backend/app/repositories/contents_repo.py`
- `delete(content_id)`: Supabase delete + fallback dict pop
- `delete_all()`: Supabase delete (no filter) + fallback dict clear

부수적: 연관 테이블 (risk_results, evidence?, approval_logs, audit_logs) 도 같이 정리해야 외래키 무결성 유지. fallback dict 들도 함께 비움.
- `risk_results_repo`: `delete_by_content_id`, `delete_all`
- `approval_logs_repo`: `delete_by_content_id`, `delete_all`
- `audit_logs_repo`: `delete_by_content_id`, `delete_all`

`apps/backend/app/api/v1/compliance.py`
- `DELETE /contents/{content_id}`: 단건 삭제 (위 4개 repo cascade)
- `DELETE /contents`: 전체 삭제

서비스에 묶지 않고 (단순 cascade) endpoint 에서 직접 repo 호출.

#### 3b. 프론트

`apps/frontend/src/features/compliance/api.ts`
- `deleteContent(id)`, `deleteAllContents()` fetch 래퍼

`apps/frontend/src/features/compliance/HistoryPage.tsx`
- 헤더 영역에 "전체 삭제" 위험 버튼 (confirm)
- 각 카드 우측 끝에 ✕ 단건 삭제 버튼 (event.stopPropagation, confirm)
- 삭제 성공 시 클라이언트 state 에서도 제거 + 선택 중이었으면 닫기

### 4. 위험도 색상 강조 (EvidenceStep)

CSS 만:
- `.evidence-risk-button.severity-HIGH` → 좌측 4px red bar (`box-shadow: inset 4px 0 #ef4444`)
- `.evidence-risk-button.severity-MEDIUM` → amber
- `.evidence-risk-button.severity-LOW` → green
- active 시 박스 그림자는 유지하되 좌측 bar 강조

`EvidenceStep.tsx` 에 className 에 severity 접두어 추가.

### 5. "Deterministic fallback" 한국어

`apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
- `sourceLabel` 분기:
  - `gemini` → `"Gemini 검수 결과"` (그대로)
  - else → `"기본 패턴 기반 (fallback)"`
- store 의 `actionMessage` 도 동일 한국어

### 6. 심의 도장 + 저울

`apps/frontend/src/components/icons.tsx`
- 신규: `ScalesIcon` (법원 저울)

`apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
- 기존 단순 텍스트 `.approval-stamp` → 새 컴포넌트 `<ApprovalStamp decision={state.approval?.decision} />`:
  - circular border (이중 테두리, 회색→파랑 그라데이션)
  - 가운데 ScalesIcon (혹은 결정별 다른 아이콘: 승인 ✓, 반려 ✕, 수정 ⌥)
  - 상단/하단 둘레 텍스트 "COMPLIANCE REVIEW" / "JB SAFEGROWTH"
  - 결정 라벨 (한국어) 추가
- 색상:
  - 승인/조건부 승인 → 파랑+그린 톤
  - 반려 → 빨강
  - 수정 요청 → amber
  - 미결 (initial) → 회색 + "검토 대기"

### 7. Topbar 정비

`apps/frontend/src/components/layout/AppShell.tsx`
- `.api-chip` 제거
- `.bell` 더미 → 진짜 dropdown:
  - 클릭 시 토글
  - 펼친 상태에서 `/v1/compliance/audit-log/recent?limit=10` fetch
  - 항목: 시각 + action ("analyze"/"approve") + content_id 짧게
  - 외부 클릭 시 닫힘
- 신규 백엔드 엔드포인트:
  - `audit_logs_repo.list_recent(limit)` — Supabase select_many filters={} order=desc + fallback (모든 dict 값 flatten 후 정렬)
  - `GET /v1/compliance/audit-log/recent?limit=10`
- 한국어 라벨: "분석 수행", "근거 검색", "수정안 생성", "승인 저장" 등

### 8. AuditLog 추가 schema 필드

`apps/backend/app/schemas/audit.py`
- `AuditLogEntry` 가 이미 있을 듯 — 확인 후 그대로 사용

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| 신규 | `components/Stamp.tsx` (선택), 백엔드는 신규 파일 없음 |
| 변경 (FE) | `ComplianceTraceRail.tsx`, `HistoryPage.tsx`, `EvidenceStep.tsx`, `RewriteStep.tsx`, `ApprovalStep.tsx`, `AppShell.tsx`, `api.ts`, `icons.tsx`, `styles.css`, `store.ts` (actionMessage 한글), `types.ts` |
| 변경 (BE) | `repositories/regulation_versions_repo.py`, `repositories/regulation_docs_repo.py`, `repositories/contents_repo.py`, `repositories/risk_results_repo.py`, `repositories/approval_logs_repo.py`, `repositories/audit_logs_repo.py`, `api/v1/compliance.py`, `schemas/audit.py` (필요 시) |

## 검증

- frontend `npm run build` + backend `pytest -q`
- 캡처:
  - trace rail 에서 rewrite → evidence → rewrite 왕복 (재호출 없음, 화면 즉시 전환)
  - EvidenceStep 위험도별 색띠
  - DB 인스턴스 모달 실제 backend 응답으로 렌더
  - RewriteStep "기본 패턴 기반" 한국어 chip
  - ApprovalStep 새 도장 (decision 별 색)
  - Topbar API chip 사라짐 + 알림 드롭다운에 실제 이벤트
  - HistoryPage 전체 삭제 / 단건 삭제 동작

## 롤백

각 파일 hunk 별 revert. 신규 백엔드 endpoint 는 추가만이라 기존 호출자 영향 없음.
