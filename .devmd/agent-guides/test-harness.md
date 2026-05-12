# Test Harness and Smoke Test Guide

이 문서는 agent가 각 slice 구현 후 실행해야 하는 최소 테스트 명령을 정의한다.

## 1. Backend Local Smoke Test

```bash
cd apps/backend
virtualenv --always-copy .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

다른 터미널:

```bash
curl http://localhost:8000/v1/health
```

기대 응답:

```json
{"status":"ok","env":"development"}
```

## 2. Analyze API Smoke Test

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

필수 확인:

- `risk_level`이 `HIGH`.
- `flagged_spans`에 `누구나`, `연 8% 수익`, `안정적으로`, `원금 걱정 없이` 중 3개 이상 포함.
- 각 span에 `risk_category`, `severity`, `reason`, `confidence` 존재.

## 3. Backend Unit Test

```bash
cd apps/backend
pytest
```

최소 테스트 파일:

```text
apps/backend/tests/test_rule_engine.py
apps/backend/tests/test_api_health.py
apps/backend/tests/test_api_analyze.py
```

RuleEngine 최소 테스트:

```python
def test_rule_engine_detects_investment_risks():
    text = "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."
    hits = RuleEngine().scan(text)
    categories = {h.risk_category for h in hits}
    assert "확정 수익 오인" in categories
    assert "원금 보장 오인" in categories
    assert "과장 표현" in categories
```

## 4. Frontend Local Smoke Test

```bash
cd apps/frontend
npm install
npm run dev
```

브라우저에서 확인:

```text
http://localhost:5173
```

필수 확인:

- 콘텐츠 입력 화면이 열린다.
- 표준 데모 문구 입력 후 Redline 화면으로 이동한다.
- API 실패 시에도 mock/fallback으로 화면이 깨지지 않는다.

## 5. Frontend Build Test

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
```

## 6. Docker Smoke Test

```bash
docker compose up --build backend
curl http://localhost:8000/v1/health
```

전체 profile이 준비된 경우:

```bash
docker compose --profile full up --build
```

## 7. End-to-End Demo Checklist

- [ ] `/v1/health` 응답 정상
- [ ] 입력 화면에서 표준 문구 제출 가능
- [ ] Redline 화면에서 위험 표현 하이라이트 표시
- [ ] 근거 패널에서 seed 규정 1개 이상 표시
- [ ] 수정안 비교에서 보수적/마케팅 유지 수정안 표시
- [ ] 승인 패키지에서 조건부 승인 권고 표시
- [ ] approve 호출 후 audit log 저장 또는 fallback 표시
