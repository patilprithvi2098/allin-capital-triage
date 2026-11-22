import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { LOGIN_BASE } from "./servers";

// ADAPT: one entry per page/route in the app.
const PAGES = [
  { path: "/", name: "Batch and decision" },
  { path: "/kushal.html", name: "Kushal outcomes" },
  { path: "/trust.html", name: "Trust report" },
];

for (const p of PAGES) {
  test(`accessibility: ${p.name} page has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto(p.path);
    await page.waitForLoadState("networkidle");
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const summary = results.violations.map((v) => ({
      rule: v.id,
      impact: v.impact,
      help: v.help,
      count: v.nodes.length,
      examples: v.nodes.slice(0, 3).map((n) => `${n.target.join(" ")} :: ${n.failureSummary?.split("\n").slice(1).join(" ").trim()}`),
    }));
    if (summary.length) console.log(`\n[${p.name}] ${JSON.stringify(summary, null, 2)}`);
    expect(summary, `${p.name} accessibility violations`).toEqual([]);
  });
}

test("accessibility: a completed read with Riya's decision panel has no WCAG A/AA violations", async ({ page }) => {
  const read = JSON.parse(require("fs").readFileSync(__dirname + "/fixture-read.json", "utf8"));
  await page.route("**/api/read?*", (r) => r.fulfill({ json: { state: "done", read, decision: null } }));
  await page.goto("/");
  await page.getByRole("button", { name: /StockSathi/ }).click();
  await expect(page.getByRole("region", { name: "Recommendation" })).toBeVisible();
  await page.getByRole("button", { name: "Go: take the call" }).click(); // show the error state too
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const summary = results.violations.map((v) => ({ rule: v.id, count: v.nodes.length, examples: v.nodes.slice(0, 3).map((n) => n.target.join(" ")) }));
  if (summary.length) console.log(JSON.stringify(summary, null, 2));
  expect(summary).toEqual([]);
});

test("accessibility: sign-in page, including its error, has no WCAG A/AA violations", async ({ page }) => {
  await page.goto(LOGIN_BASE + "/login.html");
  await page.getByRole("button", { name: "Sign in" }).click(); // empty: shows the error state
  await expect(page.getByRole("alert")).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const summary = results.violations.map((v) => ({ rule: v.id, count: v.nodes.length, examples: v.nodes.slice(0, 3).map((n) => n.target.join(" ")) }));
  if (summary.length) console.log(JSON.stringify(summary, null, 2));
  expect(summary).toEqual([]);
});
