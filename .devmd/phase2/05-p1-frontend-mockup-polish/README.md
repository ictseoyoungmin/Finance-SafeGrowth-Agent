# Slice 05 — P1 Frontend Mockup Polish

## Goal

Polish the frontend to more closely match the 5 mockup images stored in:

```text
.devmd/mockup
```

Do this after P0 backend fixes unless explicitly asked otherwise.

## Current frontend status

The app already has:

- `InputStep`
- `RedlineStep`
- `EvidenceStep`
- `RewriteStep`
- `ApprovalStep`
- `AppShell`
- redline rendering
- fallback mode

But the UI is still simplified compared to the mockups.

## Mockup mapping

Use `.devmd/mockup` images as visual reference for these screens:

```text
1. Content Input
2. Redline Risk Review
3. Evidence Panel
4. Rewrite Comparison
5. Approval Package
```

Do not hardcode image assets into the UI. Use them only as design reference.

## Files to modify

```text
apps/frontend/src/components/layout/AppShell.tsx
apps/frontend/src/features/compliance/steps/InputStep.tsx
apps/frontend/src/features/compliance/steps/RedlineStep.tsx
apps/frontend/src/features/compliance/steps/EvidenceStep.tsx
apps/frontend/src/features/compliance/steps/RewriteStep.tsx
apps/frontend/src/features/compliance/steps/ApprovalStep.tsx
apps/frontend/src/features/compliance/store.ts
apps/frontend/src/features/compliance/api.ts
apps/frontend/src/features/compliance/types.ts
apps/frontend/src/styles.css
```

## Screen-specific requirements

### Input Step

Add or improve:

- product type selector
- channel selector
- target customer selector
- language selector
- content textarea
- character count
- primary CTA

### Redline Step

Add or improve:

- highlighted risky spans inside the text
- risk level summary card
- confidence display
- detected risk category list
- AI reviewer note
- next-step buttons

### Evidence Step

Add or improve:

- selected risky sentence/context
- evidence cards
- document title/version
- snippet
- similarity or relevance display
- guideline summary panel

### Rewrite Step

Add or improve:

- original vs revised comparison
- conservative rewrite
- marketing-balanced rewrite
- change list
- apply selected revision
- re-review button

### Approval Step

Add or improve:

- final decision panel
- key changes
- remaining review items
- evidence summary
- final text
- approve/reject/request revision buttons
- report button

## State requirements

Add state for:

- selected rewrite mode
- selected final text
- approval decision
- approval response
- report payload

## Required Deliverables

- [ ] UI follows mockup layout more closely.
- [ ] Language field exists in input step.
- [ ] Approval buttons call backend APIs when available.
- [ ] Fallback mode still works.
- [ ] Loading and error states are visible but not visually disruptive.
- [ ] Build passes.

## Test Harness

```bash
cd apps/frontend
npm install
npm run lint
npm run typecheck
npm run build
npm run dev
```

Manual flow:

1. Open the local frontend.
2. Use the standard demo sentence.
3. Move through all 5 steps.
4. Verify redline highlights.
5. Verify evidence cards.
6. Verify rewrite comparison.
7. Verify approval actions.
8. Repeat with backend offline and confirm fallback flow still works.


## Implementation Completion Placeholder

- Status: NOT_STARTED / IN_PROGRESS / COMPLETE / BLOCKED
- Implemented files:
  - [ ] TBD
- Test commands executed:
  - [ ] TBD
- Test result summary:
  - TBD
- Known issues:
  - TBD
- Next recommended step:
  - TBD

Do not mark this slice COMPLETE unless all Required Deliverables and Test Harness checks pass.
