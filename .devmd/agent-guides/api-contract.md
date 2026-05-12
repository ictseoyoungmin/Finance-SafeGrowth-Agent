# API Contract — MVP

Base URL:

```text
local: http://localhost:8000
production: Render service URL
```

## 1. Health

```http
GET /v1/health
```

Response:

```json
{
  "status": "ok",
  "env": "development"
}
```

## 2. Analyze

```http
POST /v1/compliance/analyze
```

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
  "content_id": "uuid-or-demo-id",
  "risk_level": "HIGH",
  "flagged_spans": [
    {
      "span_text": "누구나",
      "start": 7,
      "end": 10,
      "risk_category": "과장 표현",
      "severity": "HIGH",
      "reason": "보편적 수혜 오인 가능",
      "confidence": 0.92
    }
  ],
  "risk_categories": ["과장 표현", "확정 수익 오인", "안정성 오인", "원금 보장 오인"],
  "reviewer_notes": "투자상품 광고로 해석될 수 있으나, 수익률과 원금 관련 표현이 확정적으로 제시되어 수정이 필요합니다."
}
```

## 3. Evidence

```http
POST /v1/compliance/evidence
```

Request:

```json
{
  "content_id": "uuid-or-demo-id",
  "risk_categories": ["확정 수익 오인", "원금 보장 오인"],
  "product_type": "투자상품"
}
```

Response:

```json
{
  "content_id": "uuid-or-demo-id",
  "evidence_list": [
    {
      "evidence_id": "doc-demo-001",
      "title": "금융상품 광고 심사 가이드라인",
      "version": "demo-v1",
      "snippet": "투자성 상품 광고에서는 수익률을 확정적으로 표현하지 않아야 하며 손실 가능성을 함께 안내해야 합니다.",
      "similarity": 0.87
    }
  ],
  "guideline_snippets": [
    "수익률 확정 표현 금지",
    "원금 손실 가능성 고지 필요"
  ]
}
```

## 4. Rewrite

```http
POST /v1/compliance/rewrite
```

Request:

```json
{
  "content_id": "uuid-or-demo-id",
  "mode": "marketing_balanced"
}
```

Response:

```json
{
  "content_id": "uuid-or-demo-id",
  "revised_text_conservative": "본 상품은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, 가입 전 상품설명서와 유의사항을 반드시 확인하시기 바랍니다.",
  "revised_text_marketing": "시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. 가입 전 상품설명서와 유의사항을 확인해 주세요.",
  "changes": [
    {
      "original": "연 8% 수익을 안정적으로",
      "replacement": "시장 상황에 따라 수익은 변동될 수 있으며",
      "reason": "확정 수익 표현 완화"
    }
  ]
}
```

## 5. Approve

```http
POST /v1/compliance/approve
```

Request:

```json
{
  "content_id": "uuid-or-demo-id",
  "reviewer": "김준법 수석",
  "decision": "CONDITIONALLY_APPROVED",
  "comment": "주요 수정 사항 반영 후 배포 가능"
}
```

Response:

```json
{
  "approval_id": "approval-demo-001",
  "content_id": "uuid-or-demo-id",
  "status": "CONDITIONALLY_APPROVED",
  "audit_saved": true
}
```

## 6. Audit Log

```http
GET /v1/compliance/audit-log?content_id=uuid-or-demo-id
```

Response:

```json
{
  "content_id": "uuid-or-demo-id",
  "entries": [
    {
      "action": "analyze",
      "model_version": "gemini-demo-or-fallback",
      "doc_version": "demo-v1",
      "created_at": "2026-05-12T00:00:00Z"
    }
  ]
}
```
