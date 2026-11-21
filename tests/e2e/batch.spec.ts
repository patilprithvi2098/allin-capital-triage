import { test, expect } from "@playwright/test";
import { guardDialogs, stubWrites, countWrites, tabUntil, hasHorizontalOverflow } from "./helpers";

const READY = { claude: { ok: true, detail: "Key accepted." }, judge: { ok: false, detail: "Not set. Put JUDGE_PROVIDER in .env." },
  tavily: { ok: false, detail: "Not set. Add TAVILY_API_KEY to .env." }, resend: { ok: false, detail: "Not set. Add RESEND_API_KEY to .env." },
  storage: { ok: true, detail: "Saved in files on this computer." } };

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test("batch lists the 10 applications with label, stage and raise", async ({ page }) => {
  const posts = countWrites(page, "/api/");
  await page.goto("/");
  const apps = page.locator("#apps .app");
  await expect(apps).toHaveCount(10);
  await expect(apps.filter({ hasText: "Settlr" })).toContainText("Series A");
  await expect(apps.filter({ hasText: "CareCorner" })).toContainText("Other (Healthcare)");
  await expect(page.getByText("Test mode.")).toBeVisible();
  expect(posts.count).toBe(0); // loading the page never runs the key checks
});

test("setup check shows each service with an icon and a label", async ({ page }) => {
  const calls = await stubWrites(page, "**/api/setup-check", { body: READY });
  await page.goto("/");
  await page.getByRole("button", { name: "Check setup" }).click();
  const rows = page.locator("#checks li");
  await expect(rows).toHaveCount(5);
  await expect(rows.filter({ hasText: "Claude" })).toContainText("✓ Ready");
  await expect(rows.filter({ hasText: "Tavily" })).toContainText("✕ Not ready");
  expect(calls.count).toBe(1);
});

test("double click and Enter while checking send exactly one request", async ({ page }) => {
  const calls = await stubWrites(page, "**/api/setup-check", { body: READY, delayMs: 800 });
  await page.goto("/");
  const b = page.locator("#check"); // its label changes to "Checking…" while the request runs
  await b.click();
  await expect(b).toBeDisabled();
  await b.click({ force: true });
  await page.keyboard.press("Enter");
  await expect(page.locator("#checks li")).toHaveCount(5);
  expect(calls.count).toBe(1);
  await expect(b).toBeEnabled();
});

test("server error is shown in words", async ({ page }) => {
  await stubWrites(page, "**/api/setup-check", { status: 500, body: { error: "The app hit an error (KeyError). Try again." } });
  await page.goto("/");
  await page.getByRole("button", { name: "Check setup" }).click();
  await expect(page.getByRole("alert")).toContainText("The app hit an error");
});

test("keyboard only: Tab to Check setup and press Enter", async ({ page }) => {
  const calls = await stubWrites(page, "**/api/setup-check", { body: READY });
  await page.goto("/");
  await expect(page.locator("#apps .app")).toHaveCount(10);
  expect(await tabUntil(page, "#check")).toBe(true);
  await page.keyboard.press("Enter");
  await expect(page.locator("#checks li")).toHaveCount(5);
  expect(calls.count).toBe(1);
});

test("no sideways scroll and the button is in view", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#apps .app")).toHaveCount(10);
  expect(await hasHorizontalOverflow(page)).toBe(false);
  await page.getByRole("button", { name: "Check setup" }).scrollIntoViewIfNeeded();
  await expect(page.getByRole("button", { name: "Check setup" })).toBeInViewport();
});
