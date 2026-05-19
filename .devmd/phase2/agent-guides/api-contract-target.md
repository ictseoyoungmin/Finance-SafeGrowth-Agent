# Target API Contract

## GET `/v1/health`

Response:

```json
{
  "status": "ok",
  "env": "development"
}
```

## POST `/v1/compliance/analyze`

Request:

```json
{
  "product_type": "투자상품",
  "channel": "앱 푸시",
  "target_customer": "30대 직장인",
  "language": "ko",
  "original_text": "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."
}
```

Response:

```json
{
  "content_id": "uuid-string",
  "risk_level": "HIGH",
  "flagged_spans": [
    {
      "span_text": "누구나",
      "start": 7,
      "end": 10,
      "risk_category": "과장 표현",
      "severity": "HIGH",
      "reason": "...",
      "confidence": 0.92
    }
  ],
  "risk_categories": ["과장 표현", "확정 수익 오인"],
  "reviewer_notes": "..."
}
```

## POST `/v1/compliance/evidence`

Request:

```json
{
  "content_id": "uuid-string",
  "risk_categories": ["확정 수익 오인", "원금 보장 오인"],
  "product_type": "투자상품"
}
```

Response:

```json
{
  "content_id": "uuid-string",
  "evidence_list": [
    {
      "evidence_id": "doc-demo-001",
      "title": "금융상품 광고 심사 가이드라인",
      "version": "demo-v1",
      "snippet": "...",
      "similarity": 0.87
    }
  ],
  "guideline_snippets": ["수익률 확정 표현 금지"]
}
```

## POST `/v1/compliance/rewrite`

Request:

```json
{
  "content_id": "uuid-string",
  "mode": "marketing_balanced"
}
```

Response:

```json
{
  "content_id": "uuid-string",
  "revised_text_conservative": "...",
  "revised_text_marketing": "...",
  "changes": [
    {
      "original": "연 8% 수익을 안정적으로",
      "replacement": "시장 상황에 따라 수익은 변동될 수 있으며",
      "reason": "확정 수익 및 안정성 오인 표현 완화"
    }
  ]
}
```

## POST `/v1/compliance/approve`

Request:

```json
{
  "content_id": "uuid-string",
  "reviewer": "김준법 수석",
  "decision": "CONDITIONALLY_APPROVED",
  "comment": "Approved after wording changes.",
  "selected_revision": "marketing"
}
```

Response:

```json
{
  "approval_id": "uuid-string",
  "content_id": "uuid-string",
  "status": "APPROVED",
  "decision": "CONDITIONALLY_APPROVED",
  "reviewer": "김준법 수석"
}
```

## GET `/v1/compliance/audit-log?content_id=...`

Response:

```json
{
  "content_id": "uuid-string",
  "entries": []
}
```

## GET `/v1/compliance/report?content_id=...`

Response:

```json
{
  "content_id": "uuid-string",
  "summary": "...",
  "risk_level": "HIGH",
  "final_text": "...",
  "evidence": [],
  "changes": [],
  "approval": {}
}
```
