# Day 4 — Supabase Schema / Seed / RAG Skeleton

## 목표

Supabase PostgreSQL + pgvector 기반 데이터 구조와 RAG seed를 준비한다.

## 매핑 Slice

- `slices/slice-02-rag-gemini/README.md`

## 작업 범위

1. `infra/supabase/schema.sql` 작성.
2. `seed_regulation_docs.sql` 작성.
3. `seed_demo_contents.sql` 작성.
4. vector search RPC 작성.
5. backend Supabase client skeleton.
6. RegulationDocs repository.
7. Retriever skeleton.

## Required files

```text
infra/supabase/schema.sql
infra/supabase/seed_regulation_docs.sql
infra/supabase/seed_demo_contents.sql
apps/backend/app/integrations/supabase_client.py
apps/backend/app/repositories/regulation_docs_repo.py
apps/backend/app/rag/retriever.py
apps/backend/app/rag/chunker.py
apps/backend/app/rag/embeddings.py
```

## Tables

- contents
- risk_results
- regulation_docs
- approval_logs
- audit_logs

## Seed documents

최소 3개 seed:

1. 금융상품 광고 심사 가이드라인 — 수익률 확정 표현 금지.
2. 금융소비자 보호 가이드라인 — 원금 손실 가능성 고지.
3. 내부 통제 규정 — 마케팅 커뮤니케이션 심의 절차.

## 테스트 / 검증

Supabase SQL Editor 또는 CLI에서:

```sql
select count(*) from regulation_docs;
select title, version, product_type from regulation_docs;
```

Backend mock test:

```bash
cd apps/backend
pytest tests/test_rag_retriever.py
```

## 산출물

- [ ] schema.sql
- [ ] seed_regulation_docs.sql
- [ ] match_regulation_docs RPC
- [ ] Supabase client wrapper
- [ ] RegulationDocs repository
- [ ] Retriever interface

## 완료 기준

- [ ] Supabase에 seed 문서 3개 이상 존재.
- [ ] product_type 기준 필터가 가능하다.
- [ ] backend에서 evidence 후보를 list 형태로 받을 수 있다.
- [ ] Supabase 미연결 시 fallback evidence가 반환된다.
