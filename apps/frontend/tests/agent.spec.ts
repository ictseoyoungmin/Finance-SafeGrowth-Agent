import { expect, test } from "@playwright/test";

test("agent trace flow reaches final report", async ({ page }) => {
  await page.goto("/#/agent");
  await page.getByRole("button", { name: "Agent 실행" }).click();

  await expect(page.getByText("실행 Trace")).toBeVisible();
  await expect.poll(async () => page.locator(".trace-item").count()).toBeGreaterThanOrEqual(4);
  await expect(page.getByText("도구 호출").first()).toBeVisible();
  await expect(page.getByText("도구 결과").first()).toBeVisible();
  await page.getByRole("button", { name: /RAG 근거 검색/ }).last().click();
  await expect(page.getByText("실제 함수")).toBeVisible();
  await expect(page.getByText("search_regulation")).toBeVisible();
  await expect(page.getByText(/RAG 근거 \d+건 사용/).first()).toBeVisible();

  await page.locator(".human-review-panel").getByRole("button", { name: "승인", exact: true }).click();
  await expect(page.getByRole("heading", { name: "최종 리포트" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("CONDITIONALLY_APPROVED")).not.toBeVisible();
});

test("legacy approval feedback is visible and localized", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "준법검토 시작" }).click();
  await page.getByRole("button", { name: "근거 확인", exact: true }).click();
  await page.getByRole("button", { name: "수정안 생성", exact: true }).click();
  await page.getByRole("button", { name: "승인 패키지", exact: true }).click();

  await page.getByRole("button", { name: "조건부 승인", exact: true }).click();

  await expect(page.getByText("심의 결과: 조건부 승인")).toBeVisible();
  await expect(page.getByText("방금 김준법 수석 이름으로 조건부 승인 결과가 저장되었습니다.")).toBeVisible();
  await expect(page.getByText("CONDITIONALLY_APPROVED")).not.toBeVisible();
});
