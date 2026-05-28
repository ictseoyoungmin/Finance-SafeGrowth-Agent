import { expect, test } from "@playwright/test";

// Full 5-step wizard happy path, including the P1-A self-validation chip.
// Runs against the fallback backend (no LLM/Supabase keys) so it is deterministic.
// Each step transition is asserted via the *next* step's action button, which
// Playwright auto-waits for (covering async analyze/evidence/rewrite latency).
test("wizard: input → analyze → evidence → rewrite(validation) → approval", async ({ page }) => {
  await page.goto("/");

  // Step 1 → 2 (분석): redline step exposes "근거 확인"
  await page.getByRole("button", { name: "준법검토 시작" }).click();
  const evidenceBtn = page.getByRole("button", { name: "근거 확인", exact: true });
  await expect(evidenceBtn).toBeVisible({ timeout: 30_000 });

  // Step 2 → 3 (근거): evidence step exposes "수정안 생성"
  await evidenceBtn.click();
  const rewriteBtn = page.getByRole("button", { name: "수정안 생성", exact: true });
  await expect(rewriteBtn).toBeVisible({ timeout: 30_000 });

  // Step 3 → 4 (수정안): rewrite step shows the self-validation chip (P1-A)
  await rewriteBtn.click();
  const approvalBtn = page.getByRole("button", { name: "승인 패키지", exact: true });
  await expect(approvalBtn).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("잔존 위험").first()).toBeVisible();

  // Step 4 → 5 (승인): approval step
  await approvalBtn.click();
  const decisionBtn = page.getByRole("button", { name: "조건부 승인", exact: true });
  await expect(decisionBtn).toBeVisible({ timeout: 30_000 });

  await decisionBtn.click();
  await expect(page.getByText("심의 결과: 조건부 승인")).toBeVisible({ timeout: 30_000 });
});
