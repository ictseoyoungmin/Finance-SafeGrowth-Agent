import { expect, test } from "@playwright/test";

test("agent trace flow reaches final report", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Agent 실행" }).click();

  await expect(page.getByText("실행 Trace")).toBeVisible();
  await expect.poll(async () => page.locator(".trace-item").count()).toBeGreaterThanOrEqual(4);
  await expect(page.getByText("도구 호출").first()).toBeVisible();
  await expect(page.getByText("도구 결과").first()).toBeVisible();

  await page.getByRole("button", { name: "승인" }).first().click();
  await expect(page.getByText("최종 리포트")).toBeVisible();
  await expect(page.getByText("CONDITIONALLY_APPROVED")).not.toBeVisible();
});

test("legacy approval feedback is visible and localized", async ({ page }) => {
  await page.goto("/#/legacy/wizard");
  await page.getByRole("button", { name: "준법검토 시작" }).click();
  await page.getByRole("button", { name: "근거 확인", exact: true }).click();
  await page.getByRole("button", { name: "수정안 생성", exact: true }).click();
  await page.getByRole("button", { name: "승인 패키지", exact: true }).click();

  await page.getByRole("button", { name: "조건부 승인", exact: true }).click();

  await expect(page.getByText("조건부 승인으로 저장되었습니다.").first()).toBeVisible();
  await expect(page.getByText("심의 결과: 조건부 승인")).toBeVisible();
  await expect(page.getByText("CONDITIONALLY_APPROVED")).not.toBeVisible();
});
