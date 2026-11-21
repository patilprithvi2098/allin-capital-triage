import { test } from "@playwright/test";
import { LOGIN_BASE } from "./servers";

// Captures full-page screenshots for a visual design review. Run on demand:
//   npx playwright test tests/e2e/screens.spec.ts --project=chrome
// Output: test-results/screens/<page>-<width>.png
// ADAPT: the page list.
const PAGES = [{ path: "/", name: "batch" }, { path: "/kushal.html", name: "kushal" }];
const WIDTHS = [375, 768, 1440];

for (const p of PAGES) {
  for (const w of WIDTHS) {
    test(`screenshot: ${p.name} at ${w}px`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(p.path);
      await page.waitForLoadState("networkidle");
      await page.screenshot({ path: `test-results/screens/${p.name}-${w}.png`, fullPage: true });
    });
  }
}

for (const w of WIDTHS) {
  test(`screenshot: read at ${w}px`, async ({ page }) => {
    const read = JSON.parse(require("fs").readFileSync(__dirname + "/fixture-read.json", "utf8"));
    await page.route("**/api/read?*", (r) => r.fulfill({ json: { state: "done", read, decision: null } }));
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto("/");
    await page.getByRole("button", { name: /StockSathi/ }).click();
    await page.getByRole("region", { name: "Recommendation" }).waitFor();
    await page.screenshot({ path: `test-results/screens/read-${w}.png`, fullPage: true });
  });
}

for (const w of WIDTHS) {
  test(`screenshot: login at ${w}px`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto(LOGIN_BASE + "/login.html");
    await page.screenshot({ path: `test-results/screens/login-${w}.png`, fullPage: true });
  });
}
