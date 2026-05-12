# Day 2 — Backend Foundation

## 목표

FastAPI backend의 기본 구조, config, router, error handling, health endpoint, test foundation을 구현한다.

## 매핑 Slice

- `slices/slice-01-backend-core/README.md`

## 작업 범위

1. `app/main.py` FastAPI entrypoint.
2. `app/core/config.py` settings.
3. `app/core/errors.py` 공통 예외.
4. `app/api/v1/router.py`와 `compliance.py` router skeleton.
5. `requirements.txt`, `requirements-dev.txt`.
6. `tests/test_api_health.py`.
7. CORS 설정.

## 구현 상세

### Required files

```text
apps/backend/app/main.py
apps/backend/app/core/config.py
apps/backend/app/core/errors.py
apps/backend/app/core/logging.py
apps/backend/app/api/v1/router.py
apps/backend/app/api/v1/compliance.py
apps/backend/tests/test_api_health.py
```

### Health endpoint

```http
GET /v1/health
```

기대 응답:

```json
{"status":"ok","env":"development"}
```

### Config rule

- `CORS_ORIGINS`는 comma-separated string을 list로 변환한다.
- env 값 누락 시 local 기본값을 제공하되 production에서는 명확히 실패하도록 설계한다.

## 테스트 / 검증

```bash
cd apps/backend
ruff check app tests
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/v1/health
```

## 산출물

- [ ] FastAPI app starts
- [ ] `/v1/health`
- [ ] Router skeleton
- [ ] Config object
- [ ] Health test
- [ ] Basic ruff/pytest scripts

## 완료 기준

- [ ] `pytest` 통과.
- [ ] `/docs`에서 API 문서가 열린다.
- [ ] frontend localhost가 CORS allow_origins에 포함된다.
