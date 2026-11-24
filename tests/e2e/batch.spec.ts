import { test, expect } from "@playwright/test";
import { guardDialogs, countWrites, hasHorizontalOverflow } from "./helpers";

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

test("no setup check on Riya's screen", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#apps .app")).toHaveCount(10);
  await expect(page.getByText("Setup check")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Check setup" })).toHaveCount(0);
});

test("no sideways scroll and Read all 10 is in view", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#apps .app")).toHaveCount(10);
  expect(await hasHorizontalOverflow(page)).toBe(false);
  await expect(page.getByRole("button", { name: "Read all 10" })).toBeInViewport();
});
