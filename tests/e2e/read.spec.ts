import { test, expect, type Page } from "@playwright/test";
import { guardDialogs, stubWrites, tabUntil, hasHorizontalOverflow } from "./helpers";

// Every API call is stubbed: no Claude spend, no real reads or decisions written.
const APPS = [
  { id: "stocksathi", company: "StockSathi", sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 2 Cr", source: "Intro", recommendation: "NO-GO", decision: null },
  { id: "earnwise", company: "EarnWise", sector_label: "Fintech", stage: "Pre-seed", raise: "INR 2 Cr", source: "Form", recommendation: null, decision: null },
];
const crit = (key: string, points: number, max: number) => ({ key, points, max, confidence: "medium", why: `Why for ${key}.`,
  claims: [{ text: "c", source: "deck", quote: "8 years in FMCG distribution", evidence_id: "" }], missing: [], rules: [] });
const READ = {
  id: "stocksathi", company: "StockSathi", what_it_does: "B2B restocking app with short-term credit for small-town kirana stores.",
  sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 2 Cr", source: "Introduction through a founder in your Fund I portfolio.",
  recommendation: "NO-GO", total: 57, benchmark: 65, benchmark_status: "provisional", confidence: "low",
  why_yes: [{ text: "CEO has 8 years in FMCG distribution", source: "deck", quote: "8 years in FMCG distribution", evidence_id: "" }],
  why_no: [{ text: "Deck and form conflict on credit funding", source: "form", quote: "Credit is provided through our NBFC partner", evidence_id: "" }],
  gates: [], criteria: [crit("founder_quality", 17, 25), crit("path_to_market", 10, 20), crit("evidence_quality", 8, 20),
    crit("defensibility", 6, 15), crit("sector_fit", 9, 10), crit("capital_fit", 7, 10)],
  facts: [{ key: "customers", deck: "38 retailers onboarded", form: "42 retailers onboarded", status: "differs", material: true, why: "Traction overstated on the form." },
    { key: "raise", deck: "Raising INR 2 Cr", form: "INR 2 Cr", status: "matches" }],
  evidence: [], trail: [{ field: "company", query: null, stop_reason: "no_key" }], dropped_claims: 0, injection_seen: false,
  thesis_version: "v0-draft", cost_usd: 0.04, seconds: 28, searched_at: "2026-11-18", created_at: "2026-11-18T22:10:00",
};

async function stubBatch(page: Page, readState: unknown = { state: "done", read: READ, decision: null }) {
  await page.route("**/api/applications", (r) => r.fulfill({ json: { applications: APPS, test_mode: true } }));
  await page.route("**/api/read?*", (r) => r.fulfill({ json: readState }));
}
async function openStockSathi(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: /StockSathi/ }).click();
  await expect(page.getByRole("heading", { name: "StockSathi", level: 1 })).toBeVisible();
}

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test("read shows verdict, score against benchmark, why yes and why no with sources", async ({ page }) => {
  await stubBatch(page);
  await openStockSathi(page);
  const band = page.getByRole("region", { name: "Recommendation" });
  await expect(band).toContainText("✕ NO-GO");
  await expect(band).toContainText("57");
  await expect(band).toContainText("Benchmark 65");
  await expect(page.getByText("CEO has 8 years in FMCG distribution")).toBeVisible();
  await expect(page.getByText("Deck and form conflict on credit funding")).toBeVisible();
  await expect(page.getByRole("region", { name: "Score by criterion" }).locator("tbody tr")).toHaveCount(6);
  await expect(page.getByRole("region", { name: "Deck against form" })).toContainText("▲ Differs");
  await expect(page.getByText("Web search not run")).toBeVisible();
});

test("Go against a NO-GO without a reason is refused and sends nothing", async ({ page }) => {
  await stubBatch(page);
  const calls = await stubWrites(page, "**/api/decision");
  await openStockSathi(page);
  await page.getByRole("button", { name: "Go: take the call" }).click();
  await expect(page.getByRole("alert")).toContainText("Say why");
  await expect(page.getByLabel(/Reason/)).toBeFocused();
  expect(calls.count).toBe(0);
});

test("agreeing needs no reason; disagreeing with a reason saves it", async ({ page }) => {
  await stubBatch(page);
  const calls = await stubWrites(page, "**/api/decision", { body: { ok: true, decision: { call: "go", disagrees: true } } });
  await openStockSathi(page);
  await page.getByLabel(/Reason/).fill("CAC gap is founder-time accounting.");
  await page.getByRole("button", { name: "Go: take the call" }).click();
  await expect(page.getByText(/Saved: Go \(differs/)).toBeVisible();
  await expect(page.getByRole("button", { name: /StockSathi/ })).toContainText("You: Go");
  expect(calls.count).toBe(1);
});

test("very long reason is capped at 500 characters", async ({ page }) => {
  await stubBatch(page);
  await openStockSathi(page);
  await page.getByLabel(/Reason/).fill("x".repeat(800));
  expect((await page.getByLabel(/Reason/).inputValue()).length).toBe(500);
});

test("double click and Enter while saving send exactly one decision", async ({ page }) => {
  await stubBatch(page);
  const calls = await stubWrites(page, "**/api/decision", { delayMs: 800, body: { ok: true, decision: { call: "nogo", disagrees: false } } });
  await openStockSathi(page);
  const b = page.getByRole("button", { name: "No-go: reject" });
  await b.click();
  await b.click({ force: true });
  await page.keyboard.press("Enter");
  await expect(page.getByText(/Saved: No-go/)).toBeVisible();
  expect(calls.count).toBe(1);
});

test("server refusal is shown in words", async ({ page }) => {
  await stubBatch(page);
  await stubWrites(page, "**/api/decision", { status: 409, body: { error: "Run the read before deciding." } });
  await openStockSathi(page);
  await page.getByRole("button", { name: "No-go: reject" }).click();
  await expect(page.getByRole("alert")).toContainText("Run the read before deciding.");
});

test("keyboard only: open an application, write a reason, decide with Enter", async ({ page }) => {
  await stubBatch(page);
  const calls = await stubWrites(page, "**/api/decision", { body: { ok: true, decision: { call: "go", disagrees: true } } });
  await page.goto("/");
  expect(await tabUntil(page, ".app[data-id=stocksathi]")).toBe(true);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "StockSathi", level: 1 })).toBeVisible();
  expect(await tabUntil(page, "#reason", 60)).toBe(true);
  await page.keyboard.type("Distribution background fits.");
  await page.keyboard.press("Shift+Tab");
  await page.keyboard.press("Shift+Tab"); // back to Go
  await expect(page.getByRole("button", { name: "Go: take the call" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText(/Saved: Go/)).toBeVisible();
  expect(calls.count).toBe(1);
});

test("unread application: Run the read starts one job, shows progress, then the read", async ({ page }) => {
  let state: unknown = { state: "none" };
  await page.route("**/api/applications", (r) => r.fulfill({ json: { applications: APPS, test_mode: true } }));
  await page.route("**/api/read?*", (r) => r.fulfill({ json: state }));
  const calls = { count: 0 };
  await page.route("**/api/read", async (r) => { // like the server: the job is marked running before it answers
    if (r.request().method() !== "POST") return r.fallback();
    calls.count += 1; state = { state: "running" };
    await new Promise((res) => setTimeout(res, 300));
    await r.fulfill({ status: 202, json: { state: "running" } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: /StockSathi/ }).click();
  const run = page.getByRole("button", { name: "Run the read" });
  await run.click();
  await page.locator("#run").click({ force: true, timeout: 500 }).catch(() => {}); // disabled, then replaced: a second click must not start a second job
  await expect(page.getByRole("status")).toContainText("Reading");
  state = { state: "done", read: READ, decision: null };
  await expect(page.getByRole("region", { name: "Recommendation" })).toContainText("NO-GO", { timeout: 8000 });
  expect(calls.count).toBe(1);
});

test("failed read says what stopped and offers a rerun, never a partial read", async ({ page }) => {
  await stubBatch(page, { state: "error", error: "The Claude API was busy (HTTP 529) on 3 tries. Nothing was saved; run it again." });
  await openStockSathi(page);
  await expect(page.getByRole("alert")).toContainText("Nothing was saved");
  await expect(page.getByRole("button", { name: "Run the read again" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Recommendation" })).toHaveCount(0);
});

test("no sideways scroll and the decision buttons are reachable", async ({ page }) => {
  await stubBatch(page);
  await openStockSathi(page);
  expect(await hasHorizontalOverflow(page)).toBe(false);
  await page.getByRole("button", { name: "No-go: reject" }).scrollIntoViewIfNeeded();
  await expect(page.getByRole("button", { name: "No-go: reject" })).toBeInViewport();
});
