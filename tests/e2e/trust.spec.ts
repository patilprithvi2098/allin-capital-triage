import { test, expect, type Page } from "@playwright/test";
import { guardDialogs, hasHorizontalOverflow } from "./helpers";

// Trust report is read-only; the data is stubbed so the page is tested in each state.
const RUN = {
  run_at: "2026-11-21T12:30:00", total: 254, passed: 250,
  by_severity: { Critical: { pass: 90, fail: 1, error: 0 }, High: { pass: 110, fail: 2, error: 0 }, Low: { pass: 50, fail: 1, error: 0 } },
  by_point: { gates: { total: 31, passed: 31 }, overlap: { total: 48, passed: 47 }, read: { total: 30, passed: 29 } },
  kill_criteria: {
    K1: { text: "A planted portfolio overlap is not flagged", cases: 40, failed: 1, status: "broken" },
    K2: { text: "A claim reaches a read with no source", cases: 60, failed: 0, status: "held" },
    K4: { text: "An email goes out without approval", cases: 0, failed: 0, status: "not built yet: Phase 5 (email)" },
    K5: { text: "Text inside a deck changes a score", cases: 0, failed: 0, status: "no cases" },
  },
  self_checks: { forced_wrong_caught: "11 of 11", same_verdict_twice: "147 of 147", should_fail_failed: true },
  judge: { used: false, provider: null, judged: 0, judge_failed: 0 },
  failures: [{ id: "OVERLAP-031", severity: "Critical", kill: "K1", partition: "Label trap", detail: "verdict: expected overlap, got none", output: {} }],
};
const BT = { benchmark: 36, build_agree: "5 of 6", held_out_agree: "5 of 6", held_out_invested_caught: "2 of 3", held_out_passed_caught: "3 of 3",
  caveats: ["6 held-out cases is far too few to trust a rate."], leak_check: "decision and opinions removed",
  rows: [{ company: "Giva", actual: "INVESTED", set: "held_out", total: 35, gates: [], call: "NO-GO", agrees: false },
         { company: "AeroDrop", actual: "PASSED", set: "held_out", total: 32, gates: [], call: "NO-GO", agrees: true }] };

async function stub(page: Page, body: unknown) {
  await page.route("**/api/trust", (r) => r.fulfill({ json: body }));
  await page.route("**/api/me", (r) => r.fulfill({ json: { role: "kushal", login_required: false } }));
}

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test("shows severity counts, kill criteria, backtest, failures and the small-sample caveat", async ({ page }) => {
  await stub(page, { run: RUN, backtest: BT, audit: null, benchmark: 65, benchmark_status: "provisional" });
  await page.goto("/trust.html");
  await expect(page.getByRole("note")).toContainText("Small sample");
  await expect(page.getByText("250 of 254 cases passed")).toBeVisible();
  const kills = page.getByRole("region", { name: "Kill criteria" });
  await expect(kills.locator("tr", { hasText: "K1" })).toContainText("✕ Broken");
  await expect(kills.locator("tr", { hasText: "K2" })).toContainText("✓ Held");
  await expect(kills.locator("tr", { hasText: "K4" })).toContainText("Not built yet");
  await expect(kills.locator("tr", { hasText: "K5" })).toContainText("No cases yet");
  await expect(page.getByRole("region", { name: "Backtest" }).locator("tr", { hasText: "Giva" })).toContainText("✕ Miss");
  await expect(page.getByText(/live benchmark is still 65/)).toBeVisible();
  await expect(page.getByText("OVERLAP-031")).toBeVisible();
  await expect(page.getByText(/Not run yet: no judge-model key/)).toBeVisible();
  await expect(page.getByText(/Not done yet: no one has graded a sample of reads blind/)).toBeVisible();
});

test("before any run it says the checks have not run", async ({ page }) => {
  await stub(page, { run: null, backtest: null, audit: null, benchmark: 65, benchmark_status: "provisional" });
  await page.goto("/trust.html");
  await expect(page.getByText(/No checks have been run yet/)).toBeVisible();
});

test("server error is shown in words", async ({ page }) => {
  await page.route("**/api/trust", (r) => r.fulfill({ status: 500, json: { error: "The app hit an error (KeyError). Try again." } }));
  await page.goto("/trust.html");
  await expect(page.getByRole("alert")).toContainText("The app hit an error");
});

test("Kushal's nav reaches the trust report; no sideways scroll", async ({ page }) => {
  await stub(page, { run: RUN, backtest: BT, audit: null, benchmark: 65, benchmark_status: "provisional" });
  await page.route("**/api/outcomes", (r) => r.fulfill({ json: { rows: [], thesis: { versions: [], current: "v1" } } }));
  await page.goto("/kushal.html");
  await page.getByRole("link", { name: "Trust report" }).click();
  await expect(page).toHaveURL(/trust\.html$/);
  await expect(page.getByText("250 of 254 cases passed")).toBeVisible();
  expect(await hasHorizontalOverflow(page)).toBe(false);
});
