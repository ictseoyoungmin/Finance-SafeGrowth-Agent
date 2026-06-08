# R-C · 데모 데이터 정합성 + cascade delete

피드백 #6 + #8.

## R-C-1 · 데모 입력의 상품 유형/문구 일치

### 문제
프론트 default `product_type="투자상품"` 인데 카피는 "프리미엄 정기예금", "연 5.0% 이자". 예금성과 투자성이 섞여 심사위원이 "정기예금에 왜 투자상품 리스크?" 의문.

### 결정 (대회용 한방 데모)
**A안 (투자상품으로 통일)** — 더 극적, rule 패턴과 자연스럽게 매치.

새 데모 카피:
> "[JB Bank] 신규 가입 특별 혜택! 누구나 가입 가능한 JB 글로벌 인컴 펀드로 연 5.0% 목표 수익을 안정적으로 받아보세요. 원금 걱정 없이 시작하는 든든한 자산관리, 지금 신청하세요."

매칭 (rule):
- "누구나" → 과장 표현 HIGH
- "연 5.0% 목표 수익" → 확정 수익 오인 HIGH (rule regex `연\s*\d+(?:\.\d+)?\s*%\s*(?:수익|수익률|이자)` 매치)
- "안정적으로" → 안정성 오인 MEDIUM
- "원금 걱정 없이" → 원금 보장 오인 HIGH

### 변경
- `frontend/src/features/compliance/api.ts::DEMO_TEXT`
- `frontend/src/features/compliance/api.ts::fallbackAnalyze` / `fallbackRewrite` 의 span 텍스트
- `backend/app/services/rewrite_service.py::_fallback_content` / `_fallback_risk_result` / `FALLBACK_REWRITE`

product_type 은 그대로 `투자상품` 유지.

---

## R-C-2 · Cascade delete 정리

### 문제
`RiskResultsRepository.delete_all()`, `ApprovalLogsRepository.delete_all()` 가 fallback dict key 만 순회 → Supabase 모드에서는 fallback 이 비어있어 실제 row 안 지움.

schema 는 `risk_results.content_id` ON DELETE CASCADE, `approval_logs.content_id` / `audit_logs.content_id` ON DELETE SET NULL.

### 변경
**delete_all 정책 통일**:
- `ContentRepository.delete_all()` 만 실제 contents row 삭제
- risk_results 는 cascade 로 자동 제거
- approval_logs / audit_logs 는 schema 의 set null 의도대로 남김 (감사 흔적 보존)
- `RiskResultsRepository.delete_all()` / `ApprovalLogsRepository.delete_all()` / `AuditLogsRepository.delete_all()` 는 **fallback memory 전용** 으로 명시 (Supabase 모드에선 no-op + docstring)

API `DELETE /contents` 가 위 4개 delete_all 모두 호출하던 패턴 → 이제 `contents.delete_all()` 만 호출하고 cascade 에 위임. fallback 모드는 각 dict.clear() 도 함께 (compose 호출).

`DELETE /contents/{id}` 도 동일 논리: contents.delete 만 호출하면 risk_results cascade. approval/audit 은 SET NULL.

### 문서
docs/deployment 에 "삭제 정책" 섹션 추가:
- contents 삭제 → risk_results 자동 cascade
- approval_logs / audit_logs 는 content 가 사라져도 감사 기록으로 보존 (content_id 만 NULL)

## 영향 범위
- backend: `contents_repo.py`, `risk_results_repo.py`, `approval_logs_repo.py`, `audit_logs_repo.py`, `api/v1/compliance.py` (delete endpoints 단순화)
- frontend: `DEMO_TEXT` + fallback 데이터
- 테스트: 영향 회귀만 확인

## 검증
- pytest, ruff
- 캡처: 입력 화면 default 가 새 카피
