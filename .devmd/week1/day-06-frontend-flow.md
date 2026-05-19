# Day 6 — Frontend 5-Step Flow and Mockup Alignment

## Goal

Implement and validate the 5-step compliance review wizard, connect it to the backend APIs, and align the UI with the mockups in `.devmd/mockup`.

Mapped slice:

- `.devmd/slices/slice-03-frontend-flow/README.md`

## Current Status

Complete as of 2026-05-19. The frontend flow has been implemented, automated checks passed in a Playwright Docker container, and the 5-screen workflow was validated with screenshots.

## Work Scope

1. App shell with sidebar, header, and step container.
2. Compliance workflow state machine.
3. API client for analyze, evidence, and rewrite.
4. Content input screen.
5. Redline risk review screen.
6. Evidence panel screen.
7. Rewrite comparison screen.
8. Approval package screen.
9. Deterministic fallback data for backend-down demos.
10. Visual polish against `.devmd/mockup`.

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

## State Flow

```text
input -> redline -> evidence -> rewrite -> approval
```

Backward navigation must preserve state.

## Redline Rendering Rule

1. Prefer numeric `start`/`end` split rendering.
2. If offsets are unavailable, fall back to the first matching `span_text`.
3. Use separate classes by severity.
4. Highlighted spans must remain readable and must not break the paragraph layout.

## Mockup Reference

Use these files as visual targets:

```text
.devmd/mockup/1_콘텐츠입력.png
.devmd/mockup/2_검토문장.png
.devmd/mockup/3_근거패널.png
.devmd/mockup/4_수정안비교.png
.devmd/mockup/5_최종승인요약.png
.devmd/mockup/compliance_ai_html_mockup.html
```

Required alignment:

- Fixed or clearly persistent left stepper on desktop.
- Light gray workspace background with white panels.
- Blue primary actions and semantic state colors.
- No marketing hero layout.
- No nested cards inside cards.
- Consistent panel spacing and clear CTA placement.
- No clipped text, overlapping panels, or button label overflow.

## Verification

```bash
cd apps/frontend
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual browser check:

- Enter the standard demo sentence.
- Confirm the input screen matches the mockup structure.
- Confirm redline highlights and risk summary.
- Confirm evidence cards and snippets.
- Confirm rewrite comparison and change list.
- Confirm approval package.
- Repeat with backend unavailable and confirm fallback flow.
- Check both desktop and narrow viewport widths.

## Deliverables

- [x] 5-step UI
- [x] API client
- [x] workflow store
- [x] redline renderer
- [x] fallback mock data
- [x] build success
- [x] manual/Playwright 5-screen browser validation
- [x] mockup alignment implementation pass

## Done Criteria

- [x] Standard demo sentence completes all 5 steps.
- [x] Backend-down fallback completes all 5 steps.
- [x] Every screen has been updated to follow `.devmd/mockup`.
- [x] Primary CTA is clear on every screen.
- [x] No text overflow, overlapping UI, or broken responsive layout in captured Playwright desktop/mobile screenshots.
