import { test, expect, type Page } from "@playwright/test";
import { guardDialogs, stubWrites, countWrites, tabUntil, hasHorizontalOverflow } from "./helpers";
import { LOGIN_BASE, TEST_PW } from "./servers";

// Logins run against a test server with test-only passwords; a sign-in writes nothing but a cookie.
// Kushal's outcomes, the approval and the batch run are stubbed: no reads, decisions or approvals are saved.
test.beforeEach(async ({ page }) => { guardDialogs(page); });

async function signIn(page: Page, role: "riya" | "kushal") {
  await page.goto(LOGIN_BASE + "/login.html");
  await page.getByLabel(role === "riya" ? /Riya/ : /Kushal/).check();
  await page.getByLabel("Password").fill(TEST_PW[role]);
  await page.getByRole("button", { name: "Sign in" }).click();
}

test.describe("login", () => {
  test("signed-out visitor is sent to the login page", async ({ page }) => {
    await page.goto(LOGIN_BASE + "/");
    await expect(page).toHaveURL(/login\.html$/);
  });

  test("empty password sends nothing", async ({ page }) => {
    const posts = countWrites(page, "/api/login");
    await page.goto(LOGIN_BASE + "/login.html");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert")).toContainText("Enter your password");
    expect(posts.count).toBe(0);
  });

  test("wrong password, or Riya's password on Kushal, is refused in words", async ({ page }) => {
    await page.goto(LOGIN_BASE + "/login.html");
    await page.getByLabel(/Kushal/).check();
    await page.getByLabel("Password").fill(TEST_PW.riya);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert")).toContainText("not right");
    await expect(page).toHaveURL(/login\.html$/);
  });

  test("very long password is capped and refused", async ({ page }) => {
    await page.goto(LOGIN_BASE + "/login.html");
    await page.getByLabel("Password").fill("p".repeat(400));
    expect((await page.getByLabel("Password").inputValue()).length).toBe(200);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("double submit sends one sign-in", async ({ page }) => {
    const calls = await stubWrites(page, "**/api/login", { delayMs: 800, status: 401, body: { error: "That password is not right." } });
    await page.goto(LOGIN_BASE + "/login.html");
    await page.getByLabel("Password").fill("anything");
    const b = page.getByRole("button", { name: "Sign in" });
    await b.click();
    await page.getByRole("button", { name: "Signing in…" }).click({ force: true, timeout: 500 }).catch(() => {});
    await page.keyboard.press("Enter");
    await expect(page.getByRole("alert")).toBeVisible();
    expect(calls.count).toBe(1);
  });

  test("keyboard only: choose Kushal, type the password, press Enter", async ({ page }) => {
    await page.goto(LOGIN_BASE + "/login.html");
    expect(await tabUntil(page, 'input[value="riya"]')).toBe(true);
    await page.keyboard.press("ArrowDown"); // radio group: moves to Kushal
    await expect(page.getByLabel(/Kushal/)).toBeChecked();
    await page.keyboard.press("Tab");
    await page.keyboard.type(TEST_PW.kushal);
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/kushal\.html$/);
  });

  test("Riya lands on her screen; Kushal's page sends her back", async ({ page }) => {
    await signIn(page, "riya");
    await expect(page).toHaveURL(LOGIN_BASE + "/");
    await expect(page.getByRole("button", { name: /Read all 10/ })).toBeVisible();
    await page.goto(LOGIN_BASE + "/kushal.html");
    await expect(page).toHaveURL(LOGIN_BASE + "/");
  });

  test("Kushal lands on outcomes, has no decision buttons, and can sign out", async ({ page }) => {
    await signIn(page, "kushal");
    await expect(page).toHaveURL(/kushal\.html$/);
    await expect(page.getByRole("heading", { name: "This week's outcomes" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Go: take the call|Read all 10/ })).toHaveCount(0);
    await page.goto(LOGIN_BASE + "/");
    await expect(page).toHaveURL(/kushal\.html$/);
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/login\.html$/);
  });
});

const ROWS = [
  { id: "talkbook", company: "Talkbook", sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 2 Cr", recommendation: "NO-GO", total: 60, gates: ["portfolio overlap"], riya: "nogo", reason: "", agrees: true, meeting: "Not contacted" },
  { id: "stocksathi", company: "StockSathi", sector_label: "Consumer tech", stage: "Pre-seed", raise: "INR 2 Cr", recommendation: "NO-GO", total: 54, gates: [], riya: "go", reason: "Distribution background fits.", agrees: false, meeting: "Not contacted" },
  { id: "earnwise", company: "EarnWise", sector_label: "Fintech", stage: "Pre-seed", raise: "INR 2 Cr", recommendation: null, total: null, gates: null, riya: null, reason: null, agrees: null, meeting: "Not contacted" },
];
const crit = (key: string, name: string) => ({ key, name, max: 10, written: `Written line for ${name}.`, gap: "none",
  observed: [{ text: `Observed for ${name}.`, memo: 1, memo_name: "The ePlane Company", quote: "two people who had stayed with a hard problem" }] });
const V1 = { version: "v1", n: 1, status: "waiting for approval", built_from: ["The ePlane Company", "Petalry"], held_out: ["AeroDrop", "Giva"],
  criteria: [crit("founder_quality", "Founder quality"), crit("sector_fit", "Sector fit")] };

test.describe("Kushal's outcomes and thesis approval", () => {
  async function stubOutcomes(page: Page, thesis = { versions: [V1], current: "v0-draft" }) {
    await page.route("**/api/outcomes", (r) => r.fulfill({ json: { rows: ROWS, thesis } }));
    await page.route("**/api/me", (r) => r.fulfill({ json: { role: "kushal", login_required: false } }));
  }

  test("every application shows tool, Riya, match and reason", async ({ page }) => {
    await stubOutcomes(page);
    await page.goto("/kushal.html");
    const rows = page.getByRole("region", { name: "Outcomes" }).locator("tbody tr");
    await expect(rows).toHaveCount(3);
    await expect(rows.filter({ hasText: "Talkbook" })).toContainText("portfolio overlap");
    await expect(rows.filter({ hasText: "StockSathi" })).toContainText("▲ Disagrees");
    await expect(rows.filter({ hasText: "StockSathi" })).toContainText("Distribution background fits.");
    await expect(rows.filter({ hasText: "EarnWise" })).toContainText("not yet");
  });

  test("waiting version shows written against observed with memo quotes; Approve sends once", async ({ page }) => {
    await stubOutcomes(page);
    const calls = await stubWrites(page, "**/api/thesis/approve", { delayMs: 500, body: { ok: true, version: "v1" } });
    await page.goto("/kushal.html");
    const table = page.getByRole("region", { name: "Written against observed thesis" });
    await expect(table).toContainText("Observed for Founder quality.");
    await expect(table).toContainText("Memo · The ePlane Company");
    await expect(page.getByText(/Held out for the backtest: AeroDrop, Giva/)).toBeVisible();
    const b = page.getByRole("button", { name: "Approve v1" });
    await b.click();
    await b.click({ force: true, timeout: 300 }).catch(() => {});
    await expect(page.getByRole("status")).toContainText("v1 approved");
    expect(calls.count).toBe(1);
  });

  test("approval refused by the server is shown in words", async ({ page }) => {
    await stubOutcomes(page);
    await stubWrites(page, "**/api/thesis/approve", { status: 409, body: { error: "That version is not waiting for approval." } });
    await page.goto("/kushal.html");
    await page.getByRole("button", { name: "Approve v1" }).click();
    await expect(page.getByRole("alert")).toContainText("not waiting for approval");
  });

  test("nothing waiting: no approve button", async ({ page }) => {
    await stubOutcomes(page, { versions: [{ ...V1, status: "approved" }], current: "v1" });
    await page.goto("/kushal.html");
    await expect(page.getByText("Nothing waiting for your approval.")).toBeVisible();
    await expect(page.getByRole("button", { name: /Approve/ })).toHaveCount(0);
  });

  test("keyboard only: reach Approve and press Enter", async ({ page }) => {
    await stubOutcomes(page);
    const calls = await stubWrites(page, "**/api/thesis/approve", { body: { ok: true, version: "v1" } });
    await page.goto("/kushal.html");
    await expect(page.getByRole("button", { name: "Approve v1" })).toBeVisible();
    expect(await tabUntil(page, "#approve", 40)).toBe(true);
    await page.keyboard.press("Enter");
    await expect(page.getByRole("status")).toContainText("approved");
    expect(calls.count).toBe(1);
  });

  test("no sideways scroll on Kushal's page", async ({ page }) => {
    await stubOutcomes(page);
    await page.goto("/kushal.html");
    await expect(page.getByRole("button", { name: "Approve v1" })).toBeVisible();
    expect(await hasHorizontalOverflow(page)).toBe(false);
  });
});

test.describe("Riya's whole-batch run", () => {
  test("Read all 10 starts one run and shows progress, then the result", async ({ page }) => {
    let state = { state: "idle", done: 0, total: 10, current: null as string | null, errors: [] as unknown[] };
    await page.route("**/api/batch", async (r) => {
      if (r.request().method() === "GET") return r.fulfill({ json: state });
      return r.fallback();
    });
    const calls = await stubWrites(page, "**/api/batch", { delayMs: 300, body: { started: true, batch: { state: "running", done: 3, total: 10, current: "Settlr", errors: [] } } });
    await page.goto("/");
    const b = page.getByRole("button", { name: "Read all 10" });
    await b.click();
    await b.click({ force: true, timeout: 300 }).catch(() => {});
    await expect(page.getByText("Read 3 of 10 · now Settlr")).toBeVisible();
    state = { state: "done", done: 10, total: 10, current: null, errors: [{ id: "pumpwise", company: "Pumpwise", error: "busy" }] };
    await expect(page.getByText(/Read 9 of 10\. Stopped: Pumpwise/)).toBeVisible({ timeout: 8000 });
    expect(calls.count).toBe(1);
  });
});
