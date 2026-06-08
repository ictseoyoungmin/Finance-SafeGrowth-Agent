# R-B · 데모 설득력 (approval package full + real RAG)

피드백 #3 + #4. 심사용 화면의 정보 밀도와 RAG 신뢰성.

## R-B-1 · Approval Package 에 evidence / changes 채우기

### 문제
`ReportService.build()` 는 `evidence=[]`, `changes=[]` 를 그대로 반환. 마지막 승인 화면이 "최종 문안 + 결정 + 감사 로그" 뿐이라 demo 임팩트 약함. 기획된 승인 패키지의 7 요소 중 evidence / 수정 전후 / 근거 조항 누락.

### 변경
선택지 B (동적 reconstruct) 와 A (rewrite_results 테이블) 가 있으나, **두 단계로** 처리:

**B-1a · 빠른 reconstruct (먼저)**
- `ReportService.build(content_id)` 가:
  - risk_result 에서 risk_categories 추출
  - `regulation_docs.search(risk_categories, content.product_type)` 로 evidence 재조회
  - approval.selected_revision 과 content.original_text 비교 → 단순 diff 로 changes (heuristic)
- DB 변경 없음. 즉시 demo 효과.

**B-1b · 영구 저장 (선택, 본선)**
- 새 테이블 `rewrite_results` (content_id, revised_text_conservative, revised_text_marketing, changes jsonb, validation_* jsonb, source, model_version)
- migration: `infra/supabase/migrations/2026-05-29_rewrite_results.sql`
- `RewriteService.rewrite()` 가 결과를 저장
- `ReportService.build()` 가 rewrite_results 우선, 없으면 B-1a 로 fallback

### 신규 frontend
ReportPackagePanel 에 다음 섹션 추가 (필드만 채워주면 됨):
- evidence (관련 근거 N건, 각각 title/version)
- changes (원문 → 수정안 표)
이미 frontend 의 ReportResponse 타입이 evidence/changes 를 받게 되어 있으므로 backend 만 채우면 즉시 노출.

## R-B-2 · Evidence 가 real RAG 로 동작

### 문제
`EvidenceRequest` 에 risk_categories + product_type 만 → retriever 는 query 없으면 단순 category lookup. vector_search 경로 사용 안 됨.

### 변경
`schemas/evidence.py`:
```python
class EvidenceRequest(BaseModel):
    content_id: str
    risk_categories: list[str]
    product_type: str
    original_text: str | None = None
    flagged_spans: list[str] = Field(default_factory=list)
```

`services/evidence_service.py`:
```python
def retrieve(self, request):
    query_parts = [
        request.product_type,
        " ".join(request.risk_categories),
        request.original_text or "",
        " ".join(request.flagged_spans),
    ]
    query = "\n".join(p for p in query_parts if p).strip()
    docs = self._retriever.retrieve(
        risk_categories=request.risk_categories,
        product_type=request.product_type,
        query=query or None,
    )
    return EvidenceResponse(...)
```

### Frontend
`features/compliance/api.ts::fetchEvidence` 호출 시 analyze 결과 `original_text` + `flagged_spans` 도 함께 보냄 (store 에서 이미 보유).
```ts
fetchEvidence({
  content_id, risk_categories, product_type,
  original_text: state.input.original_text,
  flagged_spans: state.analyze?.flagged_spans.map(s => s.span_text) ?? [],
})
```

### 테스트
- request 에 original_text 가 들어가면 retriever.vector_search 가 호출되는지 (mock retriever)
- 빈 query (모든 옵션 비어있음) 면 category-only 경로 fallback

## 영향 범위
- backend: `services/report_service.py`, `services/evidence_service.py`, `schemas/evidence.py`, `repositories/rewrite_results_repo.py` (B-1b), migration
- frontend: `features/compliance/api.ts`, `types.ts`, ReportPackagePanel 의 evidence/changes 섹션
- tests: report/evidence service

## 검증
- pytest, ruff
- 캡처: ApprovalStep 의 ReportPackagePanel 에 evidence/changes 섹션 표시
