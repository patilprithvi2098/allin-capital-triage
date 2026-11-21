import { defineConfig, devices } from "@playwright/test";
import { OPEN_PORT, LOGIN_PORT, TEST_PW } from "./tests/e2e/servers";

// ADAPT: port, dev command and ready URL to the project.
// Next.js allows one dev server per project, so reuse the one on the usual port if it is already running.
const PORT = OPEN_PORT; // never the dev server on 8331: that one has real logins and real reads

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  workers: 1, // two Chrome instances beside the dev server timed out on this Mac; one worker is stable
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  // Runs in the user's installed Google Chrome (channel "chrome"), not Playwright's bundled engines.
  // Each run gets a clean temporary profile, so tests never touch real cookies, history or logins.
  projects: [
    { name: "chrome", use: { ...devices["Desktop Chrome"], channel: "chrome" } },
    { name: "chrome-375", use: { ...devices["Desktop Chrome"], channel: "chrome", viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: `RIYA_PASSWORD= KUSHAL_PASSWORD= PORT=${OPEN_PORT} python3 app/httpd.py`, url: `http://127.0.0.1:${OPEN_PORT}/`, reuseExistingServer: false, timeout: 60_000 },
    { command: `RIYA_PASSWORD=${TEST_PW.riya} KUSHAL_PASSWORD=${TEST_PW.kushal} PORT=${LOGIN_PORT} python3 app/httpd.py`, url: `http://127.0.0.1:${LOGIN_PORT}/`, reuseExistingServer: false, timeout: 60_000 },
  ],
});
