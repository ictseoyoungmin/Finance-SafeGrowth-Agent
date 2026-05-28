import { defineConfig, devices } from "@playwright/test";

// In docker the frontend is served by a sibling container, so PLAYWRIGHT_BASE_URL
// is set and we must NOT spawn a local webServer. Locally (no env) we fall back
// to the dev server on 5173 and let Playwright start it.
const externalBaseUrl = process.env.PLAYWRIGHT_BASE_URL;
const baseURL = externalBaseUrl ?? "http://127.0.0.1:5173";

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: externalBaseUrl
    ? undefined
    : {
        command: "npm run dev -- --host 127.0.0.1",
        url: "http://127.0.0.1:5173",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
