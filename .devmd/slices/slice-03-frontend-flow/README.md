# Slice 3 — Frontend Flow and Mockup Alignment

This slice is still **IN_PROGRESS**. The React implementation exists and the automated frontend checks have passed, but the slice cannot be marked complete until the full browser workflow is manually validated and the UI is tightened against the mockups in `.devmd/mockup`.

## Objective

Finish the 5-step compliance review wizard and make the live UI closely match the provided mockup reference:

```text
.devmd/mockup/compliance_ai_html_mockup.html
.devmd/mockup/1_콘텐츠입력.png
.devmd/mockup/2_검토문장.png
.devmd/mockup/3_근거패널.png
.devmd/mockup/4_수정안비교.png
.devmd/mockup/5_최종승인요약.png
```

The UI should feel like a focused financial compliance workbench, not a marketing landing page.

## Mapped Week 1 Day

- `.devmd/week1/day-06-frontend-flow.md`

## Current State

Already implemented:

- `AppShell`
- left step sidebar
- compliance workflow state
- backend API client
- fallback analyze/evidence/rewrite data
- `InputStep`
- `RedlineStep`
- `EvidenceStep`
- `RewriteStep`
- `ApprovalStep`
- redline renderer using `start`/`end` offsets
- lint, typecheck, and production build

Still missing:

- manual browser click-through across all 5 screens
- visual comparison against `.devmd/mockup` images
- final polish for spacing, panel hierarchy, empty/loading/error states, and responsive layout

## Required Files

```text
apps/frontend/src/App.tsx
apps/frontend/src/styles.css
apps/frontend/src/components/layout/AppShell.tsx
apps/frontend/src/components/redline/RiskMark.tsx
apps/frontend/src/components/redline/renderRedline.tsx
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/steps/InputStep.tsx
apps/frontend/src/features/compliance/steps/RedlineStep.tsx
apps/frontend/src/features/compliance/steps/EvidenceStep.tsx
apps/frontend/src/features/compliance/steps/RewriteStep.tsx
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
```

## Mockup Alignment Guide

Use the mockups as visual truth. Do not embed the PNG files in the app; inspect them and reproduce the layout with React/CSS.

Global shell:

- Use a fixed left sidebar with 5 numbered steps.
- Keep the sidebar visible on desktop and collapse or stack it cleanly on small screens.
- Match the mockup's workbench feel: light gray page background, white content panels, thin borders, restrained shadows, and strong information hierarchy.
- Use blue as the primary action color, teal as a secondary accent, and red/orange/green/purple only for semantic states.
- Avoid hero sections, decorative gradients, oversized marketing copy, and nested cards inside cards.
- Use stable panel widths, grid tracks, and min/max constraints so labels, buttons, and redline text do not shift the layout.

Screen mapping:

1. Content Input (`1_콘텐츠입력.png`)
   - Product type selector
   - Channel selector
   - Target customer selector
   - Language selector
   - Large content textarea
   - Character count
   - Primary CTA: `준법검토 시작`

2. Redline Risk Review (`2_검토문장.png`)
   - Original text with inline risky span highlights
   - Risk level summary
   - Confidence or review status display
   - Risk category list
   - AI reviewer note
   - Clear next-step CTA toward evidence review

3. Evidence Panel (`3_근거패널.png`)
   - Selected risky sentence or risk context
   - Evidence cards with title, version, snippet, and relevance/similarity
   - Guideline summary area
   - Back/next actions that preserve workflow state

4. Rewrite Comparison (`4_수정안비교.png`)
   - Original text area
   - Conservative rewrite
   - Marketing-balanced rewrite
   - Change list with original/replacement/reason
   - Selected final revision state
   - Re-review action

5. Final Approval Summary (`5_최종승인요약.png`)
   - Final decision panel
   - Final text
   - Key changes
   - Remaining review items
   - Evidence summary
   - Approve, reject, request revision, and report actions

## Functional Requirements

- The workflow order is `input -> redline -> evidence -> rewrite -> approval`.
- The user must be able to move backward without losing state.
- API failure must switch to deterministic fallback data and keep the demo moving.
- The frontend must never read or expose Gemini, Supabase service-role, or backend-only secrets.
- Redline rendering must prefer numeric `start`/`end` offsets; text matching is only a fallback.
- The standard demo sentence must produce a coherent 5-screen flow:

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

Expected risky spans:

```text
누구나
연 8% 수익
안정적으로
원금 걱정 없이
```

## Verification

Run:

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual browser check:

1. Open the Vite URL.
2. Enter the standard demo sentence.
3. Confirm the input screen matches the mockup structure.
4. Start review with `준법검토 시작`.
5. Confirm redline highlights and risk summary.
6. Confirm evidence cards and guideline snippets.
7. Confirm rewrite comparison and change list.
8. Confirm approval summary and final text.
9. Repeat once with the backend unavailable and confirm fallback mode keeps working.
10. Check desktop and narrow viewport layouts for overflow or clipped text.

## Done Criteria

- [ ] Standard demo sentence completes all 5 screens in a browser.
- [ ] Backend-down fallback flow completes all 5 screens.
- [x] Each screen visually follows the mapped mockup at the implementation level.
- [ ] No obvious text overflow, overlapping panels, broken buttons, or layout shifts.
- [x] `npm run lint` passes.
- [x] `npm run typecheck` passes.
- [x] `npm run build` passes.

## Implementation Completion Placeholder

- Status: IN_PROGRESS
- Branch: main
- Commit / PR: not created
- Implemented files:
  - `apps/frontend/src/App.tsx`
  - `apps/frontend/src/styles.css`
  - `apps/frontend/src/components/layout/AppShell.tsx`
  - `apps/frontend/src/components/redline/RiskMark.tsx`
  - `apps/frontend/src/components/redline/renderRedline.tsx`
  - `apps/frontend/src/features/compliance/types.ts`
  - `apps/frontend/src/features/compliance/api.ts`
  - `apps/frontend/src/features/compliance/store.ts`
  - `apps/frontend/src/features/compliance/steps/InputStep.tsx`
  - `apps/frontend/src/features/compliance/steps/RedlineStep.tsx`
  - `apps/frontend/src/features/compliance/steps/EvidenceStep.tsx`
  - `apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
  - `apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
- Test commands executed:
  - `cd apps/frontend && npm run lint`
  - `cd apps/frontend && npm run typecheck`
  - `cd apps/frontend && npm run build`
  - `cd apps/frontend && npm run dev`
  - `curl http://172.18.208.1:5174`
  - `curl http://192.168.0.5:5174`
  - `docker run --rm -v /tmp/dacon-frontend-check-2:/app -w /app mcr.microsoft.com/playwright:v1.60.0-noble sh -c "npm ci && npm run lint && npm run typecheck && npm run build"`
- Test result:
  - Frontend lint passed.
  - Frontend typecheck passed.
  - Frontend build passed.
  - Vite dev server started and served `index.html` from the advertised network URLs.
  - 2026-05-19 update: frontend lint/typecheck/build passed in a clean Linux Docker copy under `/tmp/dacon-frontend-check-2`.
  - 2026-05-19 update: local WSL `npm` is Windows-shimmed and fails with `Could not determine Node.js install directory`; direct Docker build against the repository's existing `node_modules` fails because esbuild is installed for `win32-x64`. Use a clean Linux `npm ci` copy or reinstall dependencies on the target platform before build verification.
- Known issues:
  - Manual browser click-through across all 5 screens has not been executed in this environment.
  - Visual mockup alignment has been implemented from the reference images, but a browser screenshot comparison is still recommended before marking COMPLETE.
  - A previous Windows-side Vite process may still be serving on port 5173. Future `npm run dev` may select another available port.
- Fallback behavior:
  - API client falls back to deterministic analyze/evidence/rewrite demo data if backend requests fail.
  - Frontend does not read or expose Gemini or Supabase service-role secrets.
- Next recommended task:
  - Run manual browser validation or Playwright screenshots across all five screens, compare against `.devmd/mockup`, polish remaining mismatches, then mark this slice COMPLETE.
