# Day 10 Fix + Day 11 Verification Work Order

Project: `Finance-SafeGrowth-Agent`  
Target repo path: `.devmd/day11-fix-verification/` or `.devmd/fix-plan/day11-followup/`  
Public backend: `https://finance-safegrowth-agent.onrender.com`  
Public frontend: `https://finance-safe-growth-agent.vercel.app`

---

## 0. Context

Day 10 and Day 11 have mostly been completed.

Accepted work:

- `POST /v1/compliance/approve` exists.
- `GET /v1/compliance/audit-log?content_id=...` exists.
- `GET /v1/compliance/report?content_id=...` exists.
- `ReportService` can compose content, latest risk result, latest approval, and audit log.
- `AuditService` supports generic `record_action`.
- `SupabaseClient` now supports `insert`, `select_one`, and `select_many`.
- `RewriteService` now resolves context from:
  - `contents`
  - latest `risk_results`
  - `regulation_docs`
- Gemini JSON parser now supports:
  - raw JSON
  - fenced JSON
  - explanation-wrapped JSON substring
- `RegulationDocsRepository` now attempts Supabase table retrieval before fallback.
- Backend checks reportedly passed:
  - `ruff`: passed
  - `pytest`: 25 passed, 1 warning
- Frontend Docker checks reportedly passed:
  - `typecheck`: passed
  - `lint`: passed

However, public redeploy/runtime verification tasks remain.

---

## 1. Required Immediate Fix — Frontend Approval `selected_revision`

### Problem

`apps/frontend/src/features/compliance/store.ts` currently sends:

```ts
selected_revision: state.selectedRevision
```

But `state.selectedRevision` is only a selector value:

```ts
"conservative" | "marketing"
```

That means the UI approval flow may store:

```text
marketing
```

or:

```text
conservative
```

instead of the actual final approved copy.

Manual curl testing succeeded because the curl request explicitly sent the actual final text. The Vercel UI path still needs to be fixed and verified.

### Required Change

In `submitApproval()`, compute the selected final text from `state.rewrite`.

Target behavior:

```ts
const selectedRevisionText =
  state.selectedRevision === "conservative"
    ? state.rewrite?.revised_text_conservative
    : state.rewrite?.revised_text_marketing;
```

Then send:

```ts
selected_revision: selectedRevisionText ?? state.input.original_text
```

### Target Patch Shape

File:

```text
apps/frontend/src/features/compliance/store.ts
```

Expected implementation pattern:

```ts
const submitApproval = async (decision: ApprovalDecision) => {
  const contentId = state.analyze?.content_id ?? "demo-content";
  const selectedRevisionText =
    state.selectedRevision === "conservative"
      ? state.rewrite?.revised_text_conservative
      : state.rewrite?.revised_text_marketing;

  setState((current) => ({ ...current, isLoading: true, errorMessage: undefined }));

  try {
    const approval = await approveContent({
      content_id: contentId,
      reviewer: "김준법 수석",
      decision,
      comment: decision === "CONDITIONALLY_APPROVED" ? "Demo approval" : undefined,
      selected_revision: selectedRevisionText ?? state.input.original_text,
    });

    setState((current) => ({
      ...current,
      approval,
      isLoading: false,
      actionMessage: `심의 결과가 저장되었습니다: ${approval.decision}`,
    }));
  } catch {
    setState((current) => ({
      ...current,
      usedFallback: true,
      isLoading: false,
      errorMessage: "승인 API 응답이 없어 화면 상태만 유지합니다.",
    }));
  }
};
```

### Acceptance Criteria

- [x] UI approval no longer sends `"marketing"` or `"conservative"` as `selected_revision`.
- [x] UI approval sends the actual approved/revised text, with original input fallback if rewrite text is unavailable.
- [ ] `GET /v1/compliance/report` returns `final_text` as the actual sentence from the Vercel UI path after redeploy.

---

## 2. Optional but Recommended — Gemini Error Logging

### Problem

`GeminiClient.generate_json()` returns `None` silently on network, timeout, or JSON parsing failure.

That is safe for fallback, but hard to debug in Render logs.

### Recommended Change

File:

```text
apps/backend/app/integrations/gemini_client.py
```

Add logger:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

Then log failures:

```python
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = json.loads(response.read().decode("utf-8"))
except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
    logger.exception("Gemini generate_json failed.")
    return None
```

Also log unparseable output:

```python
payload = parse_json_payload(text)
if payload is None:
    logger.warning("Gemini returned non-parseable JSON.")
    return None
```

### Acceptance Criteria

- [x] Gemini failure still falls back safely.
- [x] Render logs show useful failure cause when Gemini request or parsing fails.
- [x] No API key is printed to logs.

---

## 3. Recommended Cleanup — `.env.example` Should Use Placeholders

### Problem

The current diff indicates that `.env.example` / `apps/backend/.env.example` may contain a real Supabase project URL and publishable key.

Publishable keys are not as sensitive as secret keys, but `.env.example` should remain template-like.

### Required Check

Inspect:

```text
.env.example
apps/backend/.env.example
apps/frontend/.env.example
```

### Recommended Values

Root `.env.example`:

```env
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
```

Backend `.env.example`:

```env
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
GEMINI_API_KEY=replace-me
GEMINI_MODEL=gemini-1.5-flash
SUPABASE_URL=https://replace-me.supabase.co
SUPABASE_ANON_KEY=replace-me
SUPABASE_SERVICE_ROLE_KEY=replace-me
DATABASE_URL=postgresql://postgres:password@db.host:5432/postgres
```

Frontend `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Acceptance Criteria

- [x] No secret key in any `.env.example`.
- [x] No project-specific runtime secret in `.env.example`.
- [x] Real deployment values may remain documented in `.devmd/memory/MEMORY.md` or deployment notes only if they are non-secret and intentionally public.
- [x] Never commit `sb_secret_...` or legacy `service_role` JWT.

---

## 4. Backend Verification

Run:

```bash
cd apps/backend
.venv/bin/ruff check app tests
timeout 60 .venv/bin/pytest -q
```

Expected:

```text
ruff passed
pytest passed
```

Current known baseline:

```text
25 passed, 1 warning
```

If the number changes because tests are added, update documentation accordingly.

---

## 5. Frontend Verification Using Playwright Docker Image

Do not rely on local npm if this environment avoids local npm.

Run frontend checks through Docker:

```bash
docker run --rm   -v /mnt/f/NowWorking/Dacon-Fin-Agent/apps/frontend:/app   -w /app   mcr.microsoft.com/playwright:v1.60.0-noble   sh -c "npm ci && npm run typecheck && npm run lint && npm run build"
```

Expected:

```text
typecheck passed
lint passed
build passed
```

If `npm ci` is already done in the mounted workspace and the agent is intentionally avoiding reinstall, it may run the project-approved equivalent command. Document the exact command used.

---

## 6. Public Runtime Verification — Backend

After Render deploy, verify backend health:

```bash
curl -s https://finance-safegrowth-agent.onrender.com/v1/health | jq
```

Expected:

```json
{
  "status": "ok",
  "env": "production"
}
```

### 6.1 Analyze

```bash
CONTENT_ID=$(curl -s -X POST "https://finance-safegrowth-agent.onrender.com/v1/compliance/analyze"   -H "Content-Type: application/json"   -d '{
    "product_type": "투자상품",
    "channel": "앱 푸시",
    "target_customer": "30대 직장인",
    "language": "ko",
    "original_text": "지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요."
  }' | jq -r .content_id)

echo "$CONTENT_ID"
```

Expected:

- `CONTENT_ID` is a UUID.
- It does not have `content-` prefix.

### 6.2 Rewrite with Gemini Enabled

```bash
curl -s -X POST "https://finance-safegrowth-agent.onrender.com/v1/compliance/rewrite"   -H "Content-Type: application/json"   -d "{
    "content_id": "$CONTENT_ID",
    "mode": "marketing_balanced"
  }" | jq
```

Expected:

```text
revised_text_conservative exists
revised_text_marketing exists
changes exists
HTTP 200
```

Recommended manual check:

- Compare returned text against static fallback text.
- Check Render logs for Gemini errors.
- If Gemini fails, fallback is acceptable, but document the error reason.

### 6.3 Approve

Use the `revised_text_marketing` from the rewrite response or the known demo text below.

```bash
curl -s -X POST "https://finance-safegrowth-agent.onrender.com/v1/compliance/approve"   -H "Content-Type: application/json"   -d "{
    "content_id": "$CONTENT_ID",
    "reviewer": "김준법 수석",
    "decision": "CONDITIONALLY_APPROVED",
    "comment": "Public UI/API smoke approval",
    "selected_revision": "시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. 가입 전 상품설명서와 유의사항을 확인해 주세요."
  }" | jq
```

Expected:

```text
approval_id is UUID
content_id matches
decision = CONDITIONALLY_APPROVED
status = APPROVED
```

### 6.4 Audit Log

```bash
curl -s "https://finance-safegrowth-agent.onrender.com/v1/compliance/audit-log?content_id=$CONTENT_ID" | jq
```

Expected:

```text
entries include action = analyze
entries include action = approve
```

### 6.5 Report

```bash
curl -s "https://finance-safegrowth-agent.onrender.com/v1/compliance/report?content_id=$CONTENT_ID" | jq
```

Expected:

```text
risk_level = HIGH
approval is not null
audit_log contains analyze and approve
final_text is the actual revised text
final_text is not "marketing"
final_text is not "conservative"
```

---

## 7. Public Runtime Verification — Vercel UI

After Vercel redeploy, open:

```text
https://finance-safe-growth-agent.vercel.app
```

Run the standard UI flow:

```text
1. 콘텐츠 입력
2. Redline Risk Review
3. 근거 패널
4. 수정안 비교
5. 승인 패키지
6. Click 승인
7. Click 리포트 확인
```

Standard demo sentence:

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

Expected:

- No backend fallback warning.
- UI calls Render backend.
- Approval succeeds.
- Report loads.
- Report summary appears in Approval screen.
- Supabase `approval_logs.selected_revision` stores the actual final sentence.
- `report.final_text` is not `"marketing"` or `"conservative"`.

### Browser DevTools Check

In Network tab, verify:

```text
POST https://finance-safegrowth-agent.onrender.com/v1/compliance/analyze 200
POST https://finance-safegrowth-agent.onrender.com/v1/compliance/evidence 200
POST https://finance-safegrowth-agent.onrender.com/v1/compliance/rewrite 200
POST https://finance-safegrowth-agent.onrender.com/v1/compliance/approve 200
GET  https://finance-safegrowth-agent.onrender.com/v1/compliance/report?content_id=... 200
```

---

## 8. Supabase Verification

In Supabase Table Editor, verify rows are created in:

```text
contents
risk_results
approval_logs
audit_logs
```

For the latest UI approval row:

```text
approval_logs.selected_revision
```

must contain the actual approved text.

It must not contain:

```text
marketing
conservative
```

---

## 9. Documentation Updates

Update these files if present:

```text
.devmd/week2/current-state-notes.md
.devmd/phase2/03-p0-gemini-rewrite-context/README.md
.devmd/phase2/04-p1-rag-quality/README.md
.devmd/memory/MEMORY.md
docs/demo/demo-script.md
docs/deployment/render.md
docs/deployment/supabase.md
```

Add:

```markdown
## Day 11 Follow-up Verification

Status: COMPLETE / IN_PROGRESS

Completed:
- Frontend approval sends actual selected revision text.
- Gemini rewrite context includes original text, risk spans, risk categories, reviewer notes, and regulation evidence.
- Gemini JSON parser handles raw, fenced, and explanation-wrapped JSON.
- Regulation evidence lookup uses Supabase table filtering before fallback.
- Backend tests passed.
- Frontend Docker checks passed.

Public verification:
- Render `/rewrite` smoke: PASS / FAIL / NOT_RUN
- Vercel UI approval/report smoke: PASS / FAIL / NOT_RUN
- Supabase `approval_logs.selected_revision` actual text check: PASS / FAIL / NOT_RUN

Known limitations:
- Report `evidence` and `changes` are still empty until evidence/rewrite persistence or regeneration is added.
- Supabase regulation retrieval uses table filtering, not pgvector RPC, because seeded docs do not yet include embeddings.
- Gemini live behavior should be checked in Render logs because fallback also returns HTTP 200.
```

---

## 10. Completion Criteria

Mark this follow-up complete only when:

- [x] `store.ts` sends actual final text as `selected_revision`.
- [x] Frontend Docker `typecheck`, `lint`, and `build` pass.
- [x] Backend `ruff` and `pytest` pass.
- [ ] Render is redeployed.
- [ ] Vercel is redeployed.
- [ ] Public `/rewrite` smoke returns valid response.
- [ ] Public Vercel UI approval works.
- [ ] Public Vercel UI report loads.
- [ ] Supabase `approval_logs.selected_revision` stores actual text from the Vercel UI path.
- [x] Documentation/memory files are updated.

## 12. Local Completion Log

Status: LOCAL_COMPLETE / PUBLIC_REDEPLOY_PENDING

Completed:

- `apps/frontend/src/features/compliance/store.ts` sends actual selected revision text, with original input fallback.
- `apps/backend/app/integrations/gemini_client.py` logs Gemini request/parsing failures without logging API keys.
- `.env.example`, `apps/backend/.env.example`, and `apps/frontend/.env.example` are template-safe.
- Documentation and memory files were updated.

Verification:

- Backend `ruff`: passed.
- Backend `pytest`: 25 passed, 1 warning.
- Frontend Docker command:

```bash
docker run --rm -v /tmp/dacon-day11-frontend-clean:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run typecheck && npm run lint && npm run build"
```

- Frontend `typecheck`: passed.
- Frontend `lint`: passed.
- Frontend `build`: passed.

Public verification:

- Render redeploy: NOT_RUN.
- Vercel redeploy: NOT_RUN.
- Render `/rewrite` smoke: NOT_RUN.
- Vercel UI approval/report smoke: NOT_RUN.
- Supabase UI-path `selected_revision` actual text check: NOT_RUN.

---

## 11. Next Recommended Slice After This

Once this follow-up is complete, move to report enrichment:

```text
Goal:
Populate ReportResponse.evidence and ReportResponse.changes.

Options:
A. Persist evidence/rewrite outputs in Supabase.
B. Regenerate evidence/rewrite data during report generation.

Recommended for MVP speed:
B first, A later.
```
