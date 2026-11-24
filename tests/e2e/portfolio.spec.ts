import { test, expect } from "@playwright/test";
import { guardDialogs, countWrites, hasHorizontalOverflow, tabUntil } from "./helpers";

// Kushal's Portfolio (read-only, real /api/portfolio: it writes nothing) and the drop-down brief in Outcomes (stubbed).
test.beforeEach(async ({ page }) => { guardDialogs(page); });

const ROW = { id: "stocksathi", company: "StockSathi", sector_label: "Consumer tech", stage: "Pre-seed", raise: "₹2 Cr", source: "s",
  recommendation: "NO-GO", total: 58, benchmark: 65, gates: [], riya: "go", reason: "Founder-time CAC is accounting", agrees: false,
  meeting: "Booked Thu 26 Nov, 2:00 PM IST", what_it_does: "B2B restocking app with short-term credit for kirana stores",
  founders: ["Aarav Deshmukh (CEO)", "Pooja Nair (CTO)"], why_yes: [{ text: "CEO has 8 years in FMCG distribution", source: "deck" }],
  why_no: [{ text: "CAC excludes founder time", source: "form" }] };

test.describe("portfolio", () => {
  test("money strip, public source, donut and every company with a health label", async ({ page }) => {
    const posts = countWrites(page, "/api/");
    await page.goto("/portfolio.html");
    const money = page.getByRole("region", { name: "Money" });
    for (const l of ["Total invested", "Cash in the bank", "Incoming capital", "Free to deploy"]) await expect(money).toContainText(l);
    await expect(page.getByText(/first close INR 85 Cr/)).toContainText("March 2025");
    await expect(page.locator(".donut path")).toHaveCount(6);
    await expect(page.locator(".legend li")).toHaveCount(6);
    await expect(page.locator(".legend")).toContainText("Other");
    const rows = page.locator("table.pf tbody tr:not(.brief)");
    await expect(rows).toHaveCount(12);
    for (const r of await rows.all()) await expect(r).toContainText(/(✓ Healthy|▲ Watch|✕ At risk)/);
    expect(posts.count).toBe(0);
  });

  test("nothing on screen says simulated or sample", async ({ page }) => {
    for (const path of ["/portfolio.html", "/kushal.html"]) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await page.locator(".exp").first().waitFor();
      for (const b of await page.locator(".exp").all()) await b.click();
      expect(await page.locator("body").innerText()).not.toMatch(/simulat|sample|dummy|fake/i);
    }
  });

  test("a company opens and closes its brief, by mouse and by keyboard", async ({ page }) => {
    await page.goto("/portfolio.html");
    const b = page.getByRole("button", { name: "Shelfwise" });
    await b.click();
    await expect(b).toHaveAttribute("aria-expanded", "true");
    const brief = page.locator("#" + (await b.getAttribute("aria-controls")));
    await expect(brief).toBeVisible();
    await expect(brief).toContainText("Founders");
    await expect(brief).toContainText("At risk");
    await b.click();
    await expect(brief).toBeHidden();
    await page.reload();
    await page.locator(".exp").first().waitFor();
    expect(await tabUntil(page, ".exp", 40)).toBe(true);
    await page.keyboard.press("Enter");
    await expect(page.locator(".exp:focus")).toHaveAttribute("aria-expanded", "true");
  });

  test("an error is shown in words", async ({ page }) => {
    await page.route("**/api/portfolio", (r) => r.fulfill({ status: 500, json: { error: "The app hit an error (KeyError). Try again." } }));
    await page.goto("/portfolio.html");
    await expect(page.getByRole("alert")).toContainText("The app hit an error");
  });

  test("Outcomes links to Portfolio; no sideways scroll on a phone", async ({ page }) => {
    await page.goto("/kushal.html");
    await page.getByRole("link", { name: "Portfolio" }).click();
    await expect(page).toHaveURL(/portfolio\.html$/);
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();
    await expect(page.locator("table.pf")).toBeVisible();
    expect(await hasHorizontalOverflow(page)).toBe(false);
  });
});

test.describe("outcomes brief", () => {
  test("a row opens a brief with what it does, founders, raise and top reasons", async ({ page }) => {
    await page.route("**/api/outcomes", (r) => r.fulfill({ json: { rows: [ROW], thesis: { current: "v1", versions: [] }, corrections: [] } }));
    await page.goto("/kushal.html");
    await expect(page.locator("#rows tr:not(.brief)").first()).toContainText("Booked Thu 26 Nov");
    await page.getByRole("button", { name: "StockSathi" }).click();
    const brief = page.locator("#ob0");
    await expect(brief).toContainText("B2B restocking app");
    await expect(brief).toContainText("Aarav Deshmukh (CEO), Pooja Nair (CTO)");
    await expect(brief).toContainText("Pre-seed · ₹2 Cr");
    await expect(brief).toContainText("58 against a benchmark of 65");
    await expect(brief.getByRole("heading", { name: "Why yes" })).toBeVisible();
    await expect(brief).toContainText("CAC excludes founder time");
  });
});
