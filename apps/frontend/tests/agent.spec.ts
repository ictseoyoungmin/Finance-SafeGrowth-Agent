import { expect, test } from "@playwright/test";

test("agent trace flow reaches final report", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Agent 실행" }).click();

  await expect(page.getByText("실행 Trace")).toBeVisible();
  await expect.poll(async () => page.locator(".trace-item").count()).toBeGreaterThanOrEqual(4);

  await page.getByRole("button", { name: "승인" }).first().click();
  await expect(page.getByText("최종 리포트")).toBeVisible();
});
