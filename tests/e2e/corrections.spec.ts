import { test, expect, type Page } from "@playwright/test";
import { guardDialogs, stubWrites } from "./helpers";

// Feedback loop 1 on screen: a read with an applied correction, Riya rejecting it, and Kushal's corrections log. All stubbed.
const crit = (key: string, points: number, max: number, before?: number) => ({ key, points, max, confidence: "medium", why: `Why ${key}.`,
  claims: [{ text: "c", source: "form", quote: "Both full-time", evidence_id: "" }], missing: [], rules: [], ...(before != null ? { points_before: before } : {}) });
const APPLIED = { n: 1, criterion: "evidence_quality", delta: 3, moved: 3, from: "StockSathi",
  lesson: "A deck/form CAC gap from counting founder time is an accounting difference, not unreliable numbers.",
  similar_because: "similar because both are field-led distribution with founder-time CAC" };
const READ = { id: "yatrika", company: "Yatrika", what_it_does: "Restocking app", sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 1.2 Cr",
  source: "Form", recommendation: "NO-GO", total: 60, benchmark: 65, benchmark_status: "kept", confidence: "low", why_yes: [], why_no: [], gates: [],
  criteria: [crit("founder_quality", 17, 25), crit("path_to_market", 10, 20), crit("evidence_quality", 13, 20, 10), crit("defensibility", 6, 15),
             crit("sector_fit", 8, 10), crit("capital_fit", 6, 10)],
  facts: [], evidence: [], trail: [{ field: "company", query: null, stop_reason: "no_key" }], dropped_claims: 0, injection_seen: false, notes: [],
  corrections_applied: [APPLIED], decision: "Not decided.", thesis_version: "v1", cost_usd: 0.04, seconds: 30, searched_at: "2026-11-22", created_at: "2026-11-22T13:00:00" };
const APPS = [{ id: "yatrika", company: "Yatrika", sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 1.2 Cr", source: "Form", recommendation: "NO-GO", decision: null }];

async function openRead(page: Page) {
  await page.route("**/api/applications", (r) => r.fulfill({ json: { applications: APPS, test_mode: true } }));
  await page.route("**/api/read?*", (r) => r.fulfill({ json: { state: "done", read: READ, decision: null } }));
  await page.goto("/");
  await page.getByRole("button", { name: /Yatrika/ }).click();
}

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test("applied correction shows its number, change, lesson and why it matched; the score shows what it was", async ({ page }) => {
  await openRead(page);
  const c = page.getByRole("region", { name: "Correction 1 applied" });
  await expect(c).toContainText("Correction #1 applied");
  await expect(c).toContainText("Evidence quality +3");
  await expect(c).toContainText("learned from StockSathi");
  await expect(c).toContainText("similar because");
  await expect(page.getByRole("region", { name: "Score by criterion" }).locator("tr", { hasText: "Evidence quality" })).toContainText("was 10");
  await page.screenshot({ path: `test-results/screens/correction-${test.info().project.name}.png`, fullPage: false });
});

test("Doesn't apply here removes the correction once and redraws the read", async ({ page }) => {
  await openRead(page);
  const undone = { ...READ, total: 57, corrections_applied: [], criteria: READ.criteria.map((x) => x.key === "evidence_quality" ? crit("evidence_quality", 10, 20) : x) };
  const calls = await stubWrites(page, "**/api/correction/reject", { delayMs: 400, body: { ok: true, read: undone } });
  const b = page.getByRole("button", { name: "Doesn't apply here" });
  await b.click();
  await page.getByRole("button", { name: "Undoing…" }).click({ force: true, timeout: 300 }).catch(() => {});
  await expect(page.getByText(/Correction #1 removed from this read/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Correction 1 applied" })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Recommendation" })).toContainText("57");
  expect(calls.count).toBe(1);
});

test("a refused rejection is shown in words and the button comes back", async ({ page }) => {
  await openRead(page);
  await stubWrites(page, "**/api/correction/reject", { status: 409, body: { error: "That correction is not applied to this read." } });
  await page.getByRole("button", { name: "Doesn't apply here" }).click();
  await expect(page.getByRole("alert")).toContainText("not applied to this read");
  await expect(page.getByRole("button", { name: "Doesn't apply here" })).toBeEnabled();
});

test("disagreeing tells Riya her reason becomes a correction", async ({ page }) => {
  await openRead(page);
  await stubWrites(page, "**/api/decision", { body: { ok: true, learning: true, decision: { call: "go", disagrees: true } } });
  await page.getByLabel(/Reason/).fill("Founder-time CAC again; field-led distribution fits.");
  await page.getByRole("button", { name: "Go: take the call" }).click();
  await expect(page.getByText(/becomes a correction for similar companies/)).toBeVisible();
});

test("Kushal sees the corrections log: reason, lesson, change, where used and rejected", async ({ page }) => {
  await page.route("**/api/me", (r) => r.fulfill({ json: { role: "kushal", login_required: false } }));
  await page.route("**/api/outcomes", (r) => r.fulfill({ json: { rows: [], thesis: { versions: [], current: "v1" }, corrections: [
    { n: 1, company: "StockSathi", reason: "CAC gap is founder-time accounting.", worth_storing: true, lesson: "Founder-time CAC is accounting.",
      applies_when: "field-led distribution", criterion: "evidence_quality", delta: 3, applied_to: ["dukaan-setu"], rejected_by: ["yatrika"], why_not: "" },
    { n: 2, company: "Yatrika", reason: "I know the founder.", worth_storing: false, why_not: "Only about this founder.", lesson: "", applies_when: "",
      criterion: "founder_quality", delta: 2, applied_to: [], rejected_by: [] }] } }));
  await page.goto("/kushal.html");
  const log = page.getByRole("region", { name: "Corrections log" });
  await expect(log.locator("tr", { hasText: "StockSathi" })).toContainText("Evidence quality +3");
  await expect(log.locator("tr", { hasText: "StockSathi" })).toContainText("Rejected on yatrika");
  await expect(log.locator("tr", { hasText: "I know the founder" })).toContainText("Not reused: Only about this founder.");
});
