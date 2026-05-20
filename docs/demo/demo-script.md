# Demo Script

## Setup

1. Warm the Render backend:

   ```bash
   curl https://finance-safegrowth-agent.onrender.com/v1/health
   ```

2. Open the Vercel frontend URL:

   ```text
   https://finance-safe-growth-agent.vercel.app
   ```

3. Use the standard demo sentence:

   ```text
   지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
   ```

## Walkthrough

1. Content Input: confirm product type `투자상품`, channel `앱 푸시`, target customer `30대 직장인`, then click `준법검토 시작`.
2. Redline Risk Review: confirm highlighted spans for `누구나`, `연 8% 수익`, `안정적으로`, and `원금 걱정 없이`.
3. Evidence Panel: confirm at least one regulation evidence item and guideline snippet.
4. Rewrite Comparison: compare conservative and marketing-balanced rewrite options.
5. Approval Package: confirm conditional approval summary and final marketing-safe copy.
6. Click `승인`, then click `리포트 확인`.

## Expected Result

- Risk level: `HIGH`
- At least three flagged spans
- Evidence list has one or more entries
- Both conservative and marketing rewrite text are present
- Approval succeeds and the report loads
- Report `final_text` is the actual approved sentence, not `marketing` or `conservative`
- Demo continues even if Gemini or Supabase is unavailable
- In the public deployment smoke completed on 2026-05-20, the standard 5-step demo completed without backend fallback.

## Follow-Up Verification Status

- Latest local fix: approval sends actual selected revision text with original text fallback.
- Public Vercel UI verification after redeploy: NOT_RUN.
- Supabase UI-path `approval_logs.selected_revision` actual text check after redeploy: NOT_RUN.

## Public URLs

- Backend: `https://finance-safegrowth-agent.onrender.com`
- Frontend: `https://finance-safe-growth-agent.vercel.app`

## Demo Note

Render Free tier cold start can delay the first request. Warm up `/v1/health` before the demo.
