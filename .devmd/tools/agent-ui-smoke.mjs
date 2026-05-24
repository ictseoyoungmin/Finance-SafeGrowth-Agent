import { chromium } from "playwright";

const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5173";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

try {
  await page.goto(frontendUrl, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Agent 실행" }).click();
  await page.getByText("실행 Trace").waitFor({ timeout: 15_000 });
  await page.waitForFunction(() => document.querySelectorAll(".trace-item").length >= 4, null, {
    timeout: 30_000,
  });

  const approveButton = page.getByRole("button", { name: "승인" }).first();
  await approveButton.waitFor({ timeout: 30_000 });
  await approveButton.click();
  await page.getByText("최종 리포트").waitFor({ timeout: 30_000 });

  console.log("agent-ui-smoke: ok");
} finally {
  await browser.close();
}
