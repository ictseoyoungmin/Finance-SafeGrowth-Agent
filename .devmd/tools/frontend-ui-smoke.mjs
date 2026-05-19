import { chromium } from "playwright";

const baseUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5173";
const screenshotDir = process.env.SCREENSHOT_DIR ?? "/app/ui-smoke";

const expected = {
  redline: ["HIGH", "누구나", "연 8% 수익", "원금 걱정 없이"],
  evidence: ["근거 패널", "참조 근거", "검토 요약"],
  rewrite: ["수정안 비교", "마케팅 유지 수정안 적용", "개선 포인트"],
  approval: ["최종 승인 요약", "조건부 승인 권고", "최종 문안"],
};

await fsReady(screenshotDir);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

try {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await expectText(page, "콘텐츠 입력");
  await page.screenshot({ path: `${screenshotDir}/01-input.png`, fullPage: true });

  await page.getByRole("button", { name: /준법검토 시작/ }).click();
  await expectAll(page, expected.redline);
  await page.screenshot({ path: `${screenshotDir}/02-redline.png`, fullPage: true });

  await page.getByRole("button", { name: /근거 확인/ }).click();
  await expectAll(page, expected.evidence);
  await page.screenshot({ path: `${screenshotDir}/03-evidence.png`, fullPage: true });

  await page.getByRole("button", { name: /수정안 생성/ }).click();
  await expectAll(page, expected.rewrite);
  await page.screenshot({ path: `${screenshotDir}/04-rewrite.png`, fullPage: true });

  await page.getByRole("button", { name: /승인 패키지/ }).click();
  await expectAll(page, expected.approval);
  await page.screenshot({ path: `${screenshotDir}/05-approval.png`, fullPage: true });

  await page.setViewportSize({ width: 390, height: 900 });
  await page.screenshot({ path: `${screenshotDir}/06-approval-mobile.png`, fullPage: true });

  console.log(`UI smoke passed. Screenshots: ${screenshotDir}`);
} finally {
  await browser.close();
}

async function expectAll(page, texts) {
  for (const text of texts) {
    await expectText(page, text);
  }
}

async function expectText(page, text) {
  await page.getByText(text, { exact: false }).first().waitFor({ timeout: 15000 });
}

async function fsReady(dir) {
  const { mkdir } = await import("node:fs/promises");
  await mkdir(dir, { recursive: true });
}
