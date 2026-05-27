# Day 22+ — Core 고도화 Roadmap (Phase 1–4 작업 슬라이스)

각 슬라이스는 **독립적으로 commit 가능한 단위**로 잘랐다. 슬라이스 ID 는 `P{phase}-{order}` 형식 (예: `P1-A`). 우선순위는 phase 안에서 A → B → C 순.

작업량 표기: **S** (≤ 0.5d) / **M** (1d) / **L** (2-3d) / **XL** (1주+).

---

## Phase 1 — Core 품질 (즉시 효과)

목표: 사용자가 데모에서 자주 만나는 3대 문제 (수정안 재입력 시 HIGH 잔존 / 결과 변동 / rule 누락) 해결.

### P1-A · Rewrite self-validation 루프 — **M**

- **무엇**: `rewrite_service.rewrite()` 가 결과를 만들고 그대로 반환하기 전, `analyze_service` 를 다시 호출해 두 revision (conservative / marketing) 모두를 self-check 한다.
- **출력**: `RewriteResponse` 에 `validation: { conservative: {risk_level, residual_high_count}, marketing: {...} }` 추가.
- **frontend**: RewriteStep 의 수정안 chip 옆에 `잔존 위험 0 / 잔존 위험 2건 (HIGH 1, MEDIUM 1)` 작은 라벨. 잔존 HIGH 가 있으면 카드에 amber 경고 + "이 수정안에도 위험 표현이 남아 있습니다" 안내.
- **선택 가능 행동**: 잔존 HIGH 가 있으면 LLM 에 1라운드만 추가 호출해 그 span 만 재수정. (옵션, P1-A-2 로 분리 가능)
- **파일**: `services/rewrite_service.py`, `services/analyze_service.py` (재사용), `schemas/rewrite.py`, `features/compliance/types.ts`, `steps/RewriteStep.tsx`, tests
- **검증**: 사용자 재현 시나리오 (보수적 수정안 재입력 → HIGH) 에서 잔존 위험 0~1 로 떨어지고, frontend 에 그 사실이 명시되는지

### P1-B · Rule engine 확장 (4 → 15+ 패턴) — **M**

- **무엇**: `rule_engine.py` 의 4개 카테고리 (과장/확정수익/안정성/원금보장) 외에 금감원 광고심사 가이드 기반 추가 패턴.
- **추가 후보** (각각 1-3 패턴):
  - 수수료·금리 누락 (`수수료\s*무료`, `중도해지\s*수수료\s*없`)
  - 비교 광고 위반 (`업계\s*1위`, `타사\s*대비`)
  - 광고심의필 누락 (광고가 "심의필" 문구 없이 끝나는 경우)
  - 민원/소비자 안내 부재
  - 보증/보장 표현 (`완벽\s*보장`, `100%`)
  - 한정 마케팅 (`단\s*\d+일`, `오늘만`)
  - 이자/금리 기간 미명시 (`고금리` 단독)
- **부산물**: `rule_engine.py` 가 길어지면 `rules/patterns/` 폴더로 카테고리별 분리.
- **파일**: `rules/rule_engine.py` (또는 분할), `tests/test_rule_engine.py` 확장
- **검증**: 각 패턴마다 positive/negative 케이스 1쌍씩 테스트

### P1-C · Prompt hash 기반 응답 캐시 — **M**

- **무엇**: 같은 (content_id, prompt_hash) 조합의 analyze / rewrite 결과를 **메모리 캐시 (TTL 15분)** → 사용자가 같은 입력으로 여러 번 돌려도 결과 일관 + LLM 호출 절감.
- **저장소**: 단순 dict + asyncio lock 또는 `functools.lru_cache`. 추후 Redis 로 교체 쉽게 인터페이스 분리.
- **bypass**: HTTP 요청 헤더 `X-Force-Refresh: 1` 또는 query `?refresh=1` 로 캐시 무시.
- **파일**: 신규 `services/_response_cache.py`, `services/analyze_service.py`, `services/rewrite_service.py`
- **검증**: 같은 입력 2번 호출 → 2번째는 LLM 미호출 (mock 으로 확인) + 응답 동일

### P1-D · LLM_TEMPERATURE=0 production 적용 — **S**

- **무엇**: Render 환경변수 `LLM_TEMPERATURE=0` 설정 안내 (코드 변경 없음). README 의 deployment 섹션에 권장값 표기.
- **파일**: `README.md`, `docs/deployment/README.md`

---

## Phase 2 — Agent / RAG 품질

### P2-A · Agent runner 를 main wizard 흐름과 통합 — **L**

- **무엇**: 현재 frontend 가 `analyze → evidence → rewrite → approval` 4개 service 를 직접 호출. 이걸 **agent 가 step 별로 tool 호출 (scan_rules, search_regulation, draft_rewrite, finalize_report) 하는 단일 stream** 으로 위임.
- **이유**: 진짜 multi-step LLM agent 흐름이 메인 화면에서 보이게 됨. AgentRunPage (`#/agent`) 는 dev/debug 용으로 유지.
- **흐름**: InputStep "준법검토 시작" → POST `/v1/agent/run` 시작 → SSE 로 step trace stream → frontend 가 step 별로 UI 갱신 (현재 trace rail 그대로 활용)
- **파일**: `api/v1/agent.py` (SSE), `features/compliance/store.ts` (run state 통합), `features/agent/hooks/useAgentRunStream.ts` 재사용
- **검증**: 한 화면에서 분석부터 승인까지 모든 step 이 agent trace 로 흐름 + 사람 review escalation 지점 정확히 동작

### P2-B · Evidence retrieval rerank + hybrid — **M**

- **무엇**: 현재 `_supabase_search` 는 chunk product_type + category 매칭 후 similarity. 다음 단계 추가:
  - BM25 score (chunk_text 의 키워드 매칭) → vector similarity 와 weighted sum
  - cross-encoder rerank (top-K 만 LLM-based scoring)
- **선택**: cross-encoder 는 외부 모델 호출 (Cohere rerank / OpenAI / Gemini second pass) — 비용 고려해 옵션화
- **파일**: `rag/retriever.py`, `rag/vector_search.py`, 신규 `rag/bm25.py`, `rag/rerank.py`
- **검증**: 같은 risk_category 에 대해 reranked top-1 의 사람 평가 적중률 측정 (수동)

### P2-C · Query rewrite for evidence — **S**

- **무엇**: risk_categories 만 evidence 검색 키로 쓰는 현재 → LLM 으로 "이 카피의 가장 위험한 표현 한 줄" 을 생성해 vector query 로 사용.
- **파일**: `services/evidence_service.py` + 1 LLM 호출 추가
- **검증**: similarity 평균 향상 + 카테고리는 일치하지만 무관한 evidence 가 줄어드는지

---

## Phase 3 — 실 규정 데이터

### P3-A · Admin upload endpoint 검증 + UI — **M**

- **무엇**: 현재 코드만 있는 `connectors/admin_upload.py` 와 admin API 의 ingestion 흐름을 실제로 동작 시키고, admin 전용 페이지에서 PDF/HTML 업로드 가능하게.
- **frontend**: 신규 `/admin/regulations` 페이지 (admin token 인증), 파일 업로드 + 처리 progress
- **파일**: `api/v1/admin.py`, `services/regulation_ingestion_service.py`, 신규 frontend page
- **검증**: 실제 PDF 업로드 → chunks 가 DB 에 저장 → evidence 검색에서 새 규정 등장

### P3-B · FSS RSS 자동 수집 cron — **M**

- **무엇**: `jobs/regulation_refresh.py` 가 이미 있음 — Render Cron Job 또는 GitHub Actions schedule 로 매일 1회 실행, 신규 announcement 수집 → 변경 사항만 새 version 적재.
- **파일**: `jobs/regulation_refresh.py` 다듬기, render.yaml 에 cron 항목, deploy 가이드 업데이트
- **검증**: 1주일 운영 후 새 version row 적재 + UI HistoryPage 에 반영

### P3-C · Embedding backfill 자동화 — **S**

- **무엇**: `jobs/backfill_embeddings.py` 가 있음. 새 chunk insert 시 자동 embedding 채워지도록 trigger 또는 background job 으로.
- **파일**: `jobs/backfill_embeddings.py`, Supabase trigger 또는 cron

---

## Phase 4 — 운영 / 확장

### P4-A · Metrics dashboard — **L**

- **무엇**: 새 admin 페이지 `/admin/metrics`:
  - 최근 24h / 7d 의 analyze 호출 수, fallback (LLM 실패) 비율, 평균 응답 시간
  - Gemini attempts 통계 (모델별 성공률, 평균 시도 횟수)
  - quota 초과 발생 시각
- **데이터 소스**: audit_logs + attempts 정보 (현재 audit log 에 attempts 가 없음 → 스키마 확장 필요)
- **파일**: `repositories/audit_logs_repo.py` 확장, 신규 `services/metrics_service.py`, frontend `admin/MetricsPage.tsx`

### P4-B · PDF export — **M**

- **무엇**: ApprovalStep 의 ReportPackagePanel 을 PDF 로 출력. 백엔드에서 `weasyprint` 또는 `wkhtmltopdf` 로 HTML→PDF, `GET /report/{content_id}/pdf` 다운로드.
- **파일**: `services/report_service.py` 에 `render_pdf`, 새 API 라우트, frontend 다운로드 버튼

### P4-C · 다단계 승인 / 다중 reviewer — **L**

- **무엇**: 현재 `approval_logs` 는 단일 decision. 1차 검토자 → 최종 승인자 단계, 코멘트 스레드, escalation rule (HIGH 면 무조건 2단계).
- **스키마 변경**: `approval_stages` 테이블 추가, reviewer role
- **파일**: 신규 `repositories/approval_stages_repo.py`, `schemas/approval.py` 확장, ApprovalStep 재구성

### P4-D · 권한 / multi-tenant — **XL**

- **무엇**: 익명 → 사용자 인증 (Supabase Auth 또는 OAuth). organization 단위로 데이터 격리.
- 별도 큰 작업. 데모/MVP 단계 끝나면 검토.

---

## 의존성 그래프

```
P1-A ─┐
P1-B  ├─ 독립 (병렬 가능)
P1-C ─┘
P1-D · 운영자 액션만

P2-A · 필요 시 P1-A 결과를 agent step 에 포함
P2-B ─ 독립
P2-C ─ 독립

P3-A → P3-B → P3-C  (실 데이터 파이프라인)

P4-A · audit_logs schema 확장 후
P4-B · 독립
P4-C · ApprovalStep 안정 후
P4-D · 별도 트랙
```

## 추천 진행 순서

1. **P1-A → P1-B → P1-C → P1-D** (Phase 1 전부)
2. **P2-B → P2-A → P2-C** (RAG 먼저, agent 통합 나중)
3. **P3-A → P3-B → P3-C** (실 데이터)
4. **P4-B → P4-A → P4-C** (운영 가벼운 것부터)

각 슬라이스는 별도 commit + 별도 설계 doc (`.devmd/week3/day-XX-{slice-id}-{topic}.md`).

진행 결정: 어느 슬라이스부터 시작할지 알려주시면 그 슬라이스의 설계 doc 부터 작성합니다.
