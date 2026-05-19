# Target Test Harness

## Backend checks

From `apps/backend`:

```bash
ruff check app tests
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health:

```bash
curl http://localhost:8000/v1/health
```

Analyze:

```bash
curl -X POST http://localhost:8000/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_type":"투자상품",
    "channel":"앱 푸시",
    "target_customer":"30대 직장인",
    "language":"ko",
    "original_text":"지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."
  }'
```

Evidence:

```bash
curl -X POST http://localhost:8000/v1/compliance/evidence \
  -H "Content-Type: application/json" \
  -d '{
    "content_id":"demo-content",
    "product_type":"투자상품",
    "risk_categories":["확정 수익 오인", "원금 보장 오인"]
  }'
```

Rewrite:

```bash
curl -X POST http://localhost:8000/v1/compliance/rewrite \
  -H "Content-Type: application/json" \
  -d '{"content_id":"demo-content","mode":"marketing_balanced"}'
```

## Frontend checks

From `apps/frontend`:

```bash
npm ci
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual acceptance:

1. Open local frontend.
2. Use standard demo sentence.
3. Complete all five screens.
4. Confirm fallback mode works when backend is offline.
5. Confirm backend mode works when backend is online.

## Docker checks

From repo root:

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
```

If full frontend container validation is needed:

```bash
docker compose --profile full up --build
```
