# Phase 1 Hardening · H3 (Dockerized e2e) + H4 (Audit rule_categories meta)

H3/H4 묶음. Playwright/frontend 는 docker 로 실행 (WSL↔Windows 네트워크 트랩 회피).

---

## H4 · Audit log 에 rule_categories 메타 기록

### 배경
운영 가시성 데이터 소스. cache hit 비율은 H2 의 `/health/cache-stats` 로 이미 충족되므로, audit 에는 **어떤 위반 카테고리가 자주 탐지되는지** (rule_categories) 만 추가.

### 변경
- `AuditService.record_analysis(content_id, rule_categories: list[str] | None = None)`
- `AuditRecord` 에 `rule_categories: list[str]` 필드
- `AuditLogsRepository.save(..., metadata: dict | None = None)`:
  - fallback memory: payload 에 `metadata` 그대로 저장
  - Supabase: `metadata` jsonb 컬럼에 저장. 컬럼이 없으면 insert 가 실패하나 기존 except → fallback 으로 안전 강등 (noise 로그만)
- `analyze_service.analyze()` 가 `risk_categories` 를 record_analysis 에 전달
- migration: `infra/supabase/migrations/0002_audit_metadata.sql` — `alter table audit_logs add column if not exists metadata jsonb`

### 테스트
- record_analysis 가 rule_categories 를 AuditRecord + 저장 payload 에 포함하는지 (fallback repo mock)

---

## H3 · Dockerized Playwright wizard e2e

### 배경
지금 e2e (`agent.spec.ts`) 는 2개. wizard 전체 흐름 (입력→분석→근거→수정안 validation chip→승인) e2e 가 없어, Phase 1 변경이 frontend 동선을 깼는지 자동 검증이 안 됨. WSL 에서 Playwright 직접 실행은 Node16/네트워크 문제 → **docker 로 실행**.

### 구성
`docker-compose.yml` 에 e2e 전용 서비스 추가 (별도 포트로 기존 finskillos-* 와 충돌 회피):

```yaml
  backend-e2e:
    build: { context: ./apps/backend }
    environment:
      CORS_ORIGINS: "http://frontend-e2e:5199,http://localhost:5199"
      LLM_PROVIDER: gemini      # 키 없으면 fallback 자동
    profiles: [e2e]

  frontend-e2e:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "npm ci && npm run dev -- --host 0.0.0.0 --port 5199"
    environment:
      VITE_API_BASE_URL: http://backend-e2e:8000
    volumes: [ ./apps/frontend:/app ]
    profiles: [e2e]

  playwright:
    image: mcr.microsoft.com/playwright:v1.60.0-noble
    working_dir: /app
    depends_on: [frontend-e2e]
    environment:
      PLAYWRIGHT_BASE_URL: http://frontend-e2e:5199
    volumes: [ ./apps/frontend:/app ]
    command: sh -c "npm ci && npx playwright test"
    profiles: [e2e]
```

`playwright.config.ts`:
- `baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5173"`
- docker 안에서는 webServer 비활성 (frontend-e2e 가 이미 서버) → `webServer` 를 `process.env.PLAYWRIGHT_BASE_URL` 있을 때 생략

### 신규 spec `tests/wizard.spec.ts`
```
1. goto "/"
2. 준법검토 시작 → 리스크 분석 화면 (위험도 배지)
3. 근거 확인 → 근거 패널 (탐지 리스크 목록)
4. 수정안 생성 → "잔존 위험" validation chip 보이는지 (P1-A)
5. 승인 패키지 → 조건부 승인 → 심의 결과 확인
```
- 실행은 fallback 모드 (LLM 키 없음) 라 결정적. validation chip 텍스트 "잔존 위험" 존재만 확인.

### 실행
```bash
docker compose --profile e2e run --rm playwright
```

### Non-goals
- CI 에 docker e2e 통합 (frontend-ci.yml 변경) — 별도. 지금은 로컬 docker 실행 검증만.

## 영향 범위

| 파일 | 변경 |
| --- | --- |
| `services/audit_service.py` | rule_categories 파라미터 |
| `services/analyze_service.py` | record_analysis 호출에 risk_categories 전달 |
| `repositories/audit_logs_repo.py` | save metadata 파라미터 |
| `infra/supabase/migrations/0002_audit_metadata.sql` | 신규 |
| `tests/test_audit_service.py` 또는 기존 | rule_categories 검증 |
| `docker-compose.yml` | e2e profile 서비스 3종 |
| `apps/frontend/playwright.config.ts` | env 기반 baseURL |
| `apps/frontend/tests/wizard.spec.ts` | 신규 e2e |

## 검증
- backend ruff + pytest
- `docker compose --profile e2e run --rm playwright` 통과 (3 spec)
