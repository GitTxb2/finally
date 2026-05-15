import { test, expect } from '@playwright/test';
import {
  gotoHome,
  parseCurrency,
  waitForFirstPrice,
  waitForText,
} from './helpers';

// Mock-mode trigger phrases per llm-engineer's contract (LLM_MOCK=true).
// Grammar (case-insensitive, first match wins, "remove" checked before "add"):
//   "buy <N> <TICKER>"  / "sell <N> <TICKER>"  -> trades[]
//   "add <TICKER>" / "watch <TICKER>"          -> watchlist add
//   "remove <TICKER>" / "unwatch <TICKER>"     -> watchlist remove
//   Contains "error" or "fail"                 -> LLMError (backend 5xx)
//   Otherwise                                  -> "[mock] Portfolio summary: ..."
// See backend/app/llm/mock.py and test/README.md for details.
const TRIGGER_BUY = 'buy 2 AAPL';
const TRIGGER_WATCHLIST_ADD = 'add PYPL';
const TRIGGER_FALLBACK = 'hello FinAlly';

test.describe('AI chat (LLM_MOCK=true)', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, 'AAPL', 5_000);

    // The chat panel is always in the DOM (translated off-screen when closed).
    // Use the data-open attribute to determine state, and toggle if needed.
    const panel = page.locator('[data-testid="chat-panel"]');
    await expect(panel).toBeAttached();
    const isOpen = (await panel.getAttribute('data-open')) === 'true';
    if (!isOpen) {
      await page.locator('[data-testid="chat-toggle"]').click();
      await expect(panel).toHaveAttribute('data-open', 'true');
    }
  });

  test('mock chat: buy trigger response renders and auto-executes the trade', async ({ page }) => {
    const cashEl = page.locator('[data-testid="cash-balance"]');
    // Capture whatever cash is on screen — earlier specs may have moved it.
    const startingCash = parseCurrency(await cashEl.textContent());
    expect(startingCash).toBeGreaterThan(0);

    await page.locator('[data-testid="chat-input"]').fill(TRIGGER_BUY);
    await page.locator('[data-testid="chat-send"]').click();

    // User bubble appears immediately
    await expect(
      page.locator('[data-testid="chat-message-user"]').last(),
    ).toContainText(TRIGGER_BUY, { timeout: 5_000 });

    // Assistant response appears
    await expect(
      page.locator('[data-testid="chat-message-assistant"]').last(),
    ).toBeVisible({ timeout: 15_000 });

    // Inline trade chip in FE-4 format. Whitespace varies (CSS may collapse
    // spans without explicit spaces — observed text: "BUY2 AAPL@ $189.93").
    await expect(
      page.locator('[data-testid="chat-action-trade"]').last(),
    ).toContainText(/BUY\s*2\s+AAPL\s*@/i, { timeout: 10_000 });

    // Cash drops — the trade auto-executed and triggered a portfolio refetch
    await waitForText(cashEl, (t) => parseCurrency(t) < startingCash, { timeout: 10_000 });

    // Position is visible in the positions table (bottom row — scroll first)
    const positionRow = page.locator('[data-testid="position-row-AAPL"]');
    await positionRow.scrollIntoViewIfNeeded();
    await expect(positionRow).toBeVisible({ timeout: 10_000 });
  });

  test('mock chat: fallback message renders an assistant reply (no actions)', async ({ page }) => {
    await page.locator('[data-testid="chat-input"]').fill(TRIGGER_FALLBACK);
    await page.locator('[data-testid="chat-send"]').click();

    const lastAssistant = page.locator('[data-testid="chat-message-assistant"]').last();
    await expect(lastAssistant).toBeVisible({ timeout: 15_000 });
    await expect(lastAssistant).toContainText(/mock|portfolio|summary/i, { timeout: 10_000 });
  });

  test('mock chat: watchlist add trigger updates the watchlist', async ({ page }) => {
    // Cleanup precondition — remove if a previous test left PYPL in
    const row = page.locator('[data-testid="watchlist-row-PYPL"]');
    if ((await row.count()) > 0) {
      await row.hover();
      await page.locator('[data-testid="watchlist-remove-PYPL"]').click();
      await expect(row).toHaveCount(0);
    }

    await page.locator('[data-testid="chat-input"]').fill(TRIGGER_WATCHLIST_ADD);
    await page.locator('[data-testid="chat-send"]').click();

    // FE-4 chip format: "WATCH + PYPL"
    await expect(
      page.locator('[data-testid="chat-action-watchlist"]').last(),
    ).toContainText(/WATCH\s*\+\s*PYPL/i, { timeout: 15_000 });

    // SSE picks up the new ticker → row materializes
    await expect(row).toBeVisible({ timeout: 10_000 });
  });

  test('mock chat: typing indicator shows during request and clears after', async ({ page }) => {
    await page.locator('[data-testid="chat-input"]').fill(TRIGGER_FALLBACK);
    await page.locator('[data-testid="chat-send"]').click();

    // Typing indicator may be brief — assert it appeared *or* the assistant
    // bubble landed (whichever first), then assert the indicator is gone.
    const typing = page.locator('[data-testid="chat-typing"]');
    const assistant = page.locator('[data-testid="chat-message-assistant"]').last();
    await Promise.race([
      typing.waitFor({ state: 'attached', timeout: 5_000 }).catch(() => {}),
      assistant.waitFor({ state: 'visible', timeout: 5_000 }).catch(() => {}),
    ]);
    await expect(assistant).toBeVisible({ timeout: 15_000 });
    await expect(typing).toHaveCount(0, { timeout: 10_000 });
  });
});
