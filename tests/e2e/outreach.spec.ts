import { test, expect, type Page } from "@playwright/test";
import { guardDialogs, stubWrites, tabUntil, hasHorizontalOverflow } from "./helpers";

// Riya's email drafts (send form) and read-only scheduling dashboard. Every call is stubbed: nothing is sent.
const DRAFT = { id: "grainkind", company: "GrainKind", founder: "Ritu", founder_email: "ritu@grainkind.example", deeptech: false, status: "draft",
  draft: { subject: "A call with All In Capital [AIC-grainkind]", body: "Hi Ritu,\n\nThe team liked your repeat rate..." },
  slots: ["2026-11-26T09:00:00Z", "2026-12-01T09:30:00Z"], round: 0, followups: 0, history: [] };
const SENT = { ...DRAFT, id: "stocksathi", company: "StockSathi", status: "sent", sent_at: "2026-11-22T06:00:00Z", next: { what: "Follow-up 1 if no reply", at: "2026-11-25T06:00:00Z" },
  history: [{ at: "2026-11-22T06:00:00Z", kind: "sent", text: "Riya sent the email (edited)." }] };
const BOOKED = { ...DRAFT, id: "pumpwise", company: "Pumpwise", deeptech: true, status: "booked", booked: "2026-11-26T09:00:00Z", round: 1, sent_at: "2026-11-20T06:00:00Z",
  next: { what: "Meeting booked", at: "2026-11-26T09:00:00Z" },
  history: [{ at: "2026-11-21T06:00:00Z", kind: "reply", text: "Founder replied (interested): Thursday works" }, { at: "2026-11-21T06:05:00Z", kind: "booked", text: "Meeting booked for Thu 26 Nov, 2:30 PM IST." }] };
const ESC = { ...DRAFT, id: "talkbook", company: "Talkbook", status: "needs_human", sent_at: "2026-11-21T06:00:00Z", next: { what: "Riya to read the reply", at: null }, history: [] };

async function stub(page: Page, rows: unknown[], alerts: unknown[] = []) {
  await page.route("**/api/outreach", (r) => r.fulfill({ json: { outreach: rows, test_mode: true, alerts } }));
  await page.route("**/api/me", (r) => r.fulfill({ json: { role: "riya", login_required: false } }));
}

test.beforeEach(async ({ page }) => { guardDialogs(page); });

test.describe("email drafts", () => {
  test("draft shows recipient, slots, test-mode bar and editable fields", async ({ page }) => {
    await stub(page, [DRAFT, SENT]);
    await page.goto("/drafts.html");
    await expect(page.getByText("Test mode.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "GrainKind" })).toBeVisible();
    await expect(page.getByText(/ritu@grainkind.example/)).toBeVisible();
    await expect(page.locator("p", { hasText: "Proposed slots:" })).toContainText("IST");
    await expect(page.getByLabel("Subject")).toHaveValue(/AIC-grainkind/);
    await expect(page.getByRole("heading", { name: "StockSathi" })).toHaveCount(0); // sent ones are not drafts
  });

  test("empty subject or message sends nothing", async ({ page }) => {
    await stub(page, [DRAFT]);
    const calls = await stubWrites(page, "**/api/outreach/send");
    await page.goto("/drafts.html");
    await page.getByLabel("Message").fill("   ");
    await page.getByRole("button", { name: "Send" }).click();
    await expect(page.getByRole("alert")).toContainText("Write a subject and a message");
    expect(calls.count).toBe(0);
  });

  test("very long message is capped at 4,000 characters", async ({ page }) => {
    await stub(page, [DRAFT]);
    await page.goto("/drafts.html");
    await page.getByLabel("Message").fill("x".repeat(5000));
    expect((await page.getByLabel("Message").inputValue()).length).toBe(4000);
  });

  test("edited send goes once, then the draft is replaced by a confirmation", async ({ page }) => {
    await stub(page, [DRAFT]);
    const calls = await stubWrites(page, "**/api/outreach/send", { delayMs: 500, body: { ok: true, outreach: { ...DRAFT, status: "sent" } } });
    await page.goto("/drafts.html");
    await page.getByLabel("Message").fill("Hi Ritu, edited by Riya.");
    const b = page.getByRole("button", { name: "Send" });
    await b.click();
    await page.getByRole("button", { name: "Sending…" }).click({ force: true, timeout: 300 }).catch(() => {});
    await page.keyboard.press("Enter");
    await expect(page.getByRole("status")).toContainText("Sent. The agent takes it from here");
    expect(calls.count).toBe(1);
  });

  test("a refused send is shown in words and can be retried", async ({ page }) => {
    await stub(page, [DRAFT]);
    await stubWrites(page, "**/api/outreach/send", { status: 409, body: { error: "Not sent: ritu@grainkind.example asked not to be contacted." } });
    await page.goto("/drafts.html");
    await page.getByRole("button", { name: "Send" }).click();
    await expect(page.getByRole("alert")).toContainText("asked not to be contacted");
    await expect(page.getByRole("button", { name: "Send" })).toBeEnabled();
  });

  test("keyboard only: reach the message, edit, send with Enter", async ({ page }) => {
    await stub(page, [DRAFT]);
    const calls = await stubWrites(page, "**/api/outreach/send", { body: { ok: true, outreach: {} } });
    await page.goto("/drafts.html");
    await expect(page.getByLabel("Message")).toBeVisible();
    expect(await tabUntil(page, "textarea", 40)).toBe(true);
    await page.keyboard.type(" Thanks!");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "Send" })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("status")).toBeVisible();
    expect(calls.count).toBe(1);
  });

  test("no drafts: says how they appear", async ({ page }) => {
    await stub(page, [SENT]);
    await page.goto("/drafts.html");
    await expect(page.getByText(/No drafts waiting/)).toBeVisible();
  });
});

test.describe("scheduling dashboard (read-only)", () => {
  test("every sent email with status, next step and round; no action buttons", async ({ page }) => {
    await stub(page, [DRAFT, SENT, BOOKED, ESC]);
    await page.goto("/scheduling.html");
    const t = page.getByRole("region", { name: "Conversations" });
    await expect(t.locator("tbody tr")).toHaveCount(3);
    await expect(t.locator("tr", { hasText: "Pumpwise" })).toContainText("✓ Booked");
    await expect(t.locator("tr", { hasText: "StockSathi" })).toContainText("Follow-up 1 if no reply");
    await expect(t.locator("tr", { hasText: "Talkbook" })).toContainText("▲ Needs you");
    await expect(page.getByRole("button", { name: /Send|Approve|Book/ })).toHaveCount(0);
  });

  test("choosing a company shows its email history", async ({ page }) => {
    await stub(page, [BOOKED]);
    await page.goto("/scheduling.html");
    await page.getByRole("button", { name: "Pumpwise" }).click();
    await expect(page.getByText("Email history · Pumpwise")).toBeVisible();
    await expect(page.getByText(/Meeting booked for Thu 26 Nov/)).toBeVisible();
  });

  test("an alert for a booking whose record failed is shown", async ({ page }) => {
    await stub(page, [BOOKED], [{ company: "Pumpwise", text: "The meeting for Pumpwise is booked, but saving the record failed (OSError).", at: "2026-11-22T06:00:00Z" }]);
    await page.goto("/scheduling.html");
    await expect(page.getByRole("alert")).toContainText("saving the record failed");
  });

  test("nothing sent yet, and no sideways scroll", async ({ page }) => {
    await stub(page, [DRAFT]);
    await page.goto("/scheduling.html");
    await expect(page.getByText(/Nothing sent yet/)).toBeVisible();
    expect(await hasHorizontalOverflow(page)).toBe(false);
  });
});
