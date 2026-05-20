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

## Expected Result

- Risk level: `HIGH`
- At least three flagged spans
- Evidence list has one or more entries
- Both conservative and marketing rewrite text are present
- Demo continues even if Gemini or Supabase is unavailable
- In the public deployment smoke completed on 2026-05-20, the standard 5-step demo completed without backend fallback.

## Public URLs

- Backend: `https://finance-safegrowth-agent.onrender.com`
- Frontend: `https://finance-safe-growth-agent.vercel.app`

## Demo Note

Render Free tier cold start can delay the first request. Warm up `/v1/health` before the demo.
