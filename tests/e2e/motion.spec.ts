import { test, expect, type Page } from "@playwright/test";
import { guardDialogs } from "./helpers";

// Phase 6 motion. Every API call is stubbed: nothing is read, decided or sent.
const APPS = ["StockSathi", "EarnWise", "Talkbook"].map((c) => ({ id: c.toLowerCase(), company: c, sector_label: "Fintech", stage: "Pre-seed",
  raise: "INR 2 Cr", source: "Form", recommendation: null, decision: null }));
const crit = (key: string) => ({ key, points: 8, max: 10, confidence: "medium", why: "w", claims: [], missing: [], rules: [] });
const READ = { id: "stocksathi", company: "StockSathi", what_it_does: "Restocking app.", sector_label: "Fintech", stage: "Pre-seed", raise: "INR 2 Cr",
  source: "Form", recommendation: "NO-GO", total: 57, benchmark: 65, confidence: "low", gates: [], facts: [], evidence: [],
  why_yes: [{ text: "CEO has 8 years in FMCG distribution", source: "deck", quote: "8 years in FMCG distribution", evidence_id: "" }], why_no: [],
  criteria: ["founder_quality", "sector_fit"].map(crit), trail: [{ field: "company", query: null, stop_reason: "no_key" }], dropped_claims: 0,
  injection_seen: false, thesis_version: "v1", cost_usd: 0.04, seconds: 28, searched_at: "2026-11-18", created_at: "2026-11-18T22:10:00",
  corrections_applied: [{ n: 1, criterion: "evidence_quality", moved: 3, from: "Dukaan Setu", lesson: "l", similar_because: "s" }] };

async function stub(page: Page, batch: unknown = { state: "idle", done: 0, total: 0, current: null, errors: [] }) {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("**/api/me", (r) => r.fulfill({ json: { role: "riya", login_required: false } }));
  await page.route("**/api/applications", (r) => r.fulfill({ json: { applications: APPS, test_mode: true } }));
  await page.route("**/api/read?*", (r) => r.fulfill({ json: { state: "done", read: READ, decision: null } }));
  await page.route("**/api/batch", (r) => r.fulfill({ json: batch }));
  return errors;
}

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test("read reveal: verdict and score land on their final values, ambient on the band, no console errors", async ({ page }) => {
  const errors = await stub(page);
  await page.goto("/");
  await page.locator(".app", { hasText: "StockSathi" }).click();
  const band = page.getByRole("region", { name: "Recommendation" });
  await expect(band.locator(".verdict")).toHaveText("✕ NO-GO");
  await expect(band.locator(".num").first()).toHaveText("57 / 100");
  await expect(band.locator("canvas.amb")).toHaveCount(1);
  await expect(page.locator(".corr strong.pulse")).toHaveCount(1);
  expect(errors).toEqual([]);
});

test("reduced motion: final values at once, no ambient canvas", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await stub(page);
  await page.goto("/");
  await page.locator(".app", { hasText: "StockSathi" }).click();
  const band = page.getByRole("region", { name: "Recommendation" });
  expect(await band.locator(".num").first().textContent()).toBe("57 / 100"); // read immediately, no waiting
  await expect(band.locator("canvas.amb")).toHaveCount(0);
});

test("evidence beam: clicking a sourced reason draws the beam", async ({ page }) => {
  await stub(page);
  await page.goto("/");
  await page.locator(".app", { hasText: "StockSathi" }).click();
  const li = page.locator(".reasons li.traceable").first();
  await li.click();
  await expect(li).toHaveClass(/beam/);
});

test("hero shows real batch progress while running and goes away when done", async ({ page }) => {
  const errors = await stub(page, { state: "running", done: 1, total: 3, current: "EarnWise", errors: [] });
  await page.goto("/");
  const hero = page.locator("#hero");
  await expect(hero).toBeVisible();
  await expect(hero).toContainText("Read 1 of 3");
  await expect(hero).toContainText("now EarnWise");
  await expect(hero.locator(".node")).toHaveCount(5);
  await page.unroute("**/api/batch");
  await page.route("**/api/batch", (r) => r.fulfill({ json: { state: "done", done: 3, total: 3, current: null, errors: [] } }));
  await expect(hero).toBeHidden({ timeout: 8000 });
  expect(errors).toEqual([]);
});

test("a newly booked meeting snaps in once", async ({ page }) => {
  const row = { id: "pumpwise", company: "Pumpwise", status: "booked", booked: "2026-11-26T08:30:00Z", round: 1, sent_at: "2026-11-20T06:00:00Z",
    next: { what: "Meeting booked", at: "2026-11-26T08:30:00Z" }, history: [] };
  await page.route("**/api/me", (r) => r.fulfill({ json: { role: "riya", login_required: false } }));
  await page.route("**/api/outreach", (r) => r.fulfill({ json: { outreach: [row], test_mode: true, alerts: [] } }));
  await page.goto("/scheduling.html");
  await expect(page.locator("tr.snap")).toHaveCount(1);
  await page.reload();
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tr.snap")).toHaveCount(0);
});

test("phone: no ambient canvas and the hero stays still", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await stub(page, { state: "running", done: 0, total: 3, current: "StockSathi", errors: [] });
  await page.goto("/");
  await expect(page.locator("#hero")).toBeVisible();
  await expect(page.locator("#hero canvas.amb")).toHaveCount(0);
  const pos = () => page.locator("#hero .dot").first().getAttribute("transform");
  const a = await pos(); await page.waitForTimeout(400);
  expect(await pos()).toBe(a);
});
