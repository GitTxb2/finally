import { test, expect } from '@playwright/test';
import {
  gotoHome,
  parseCurrency,
  waitForFirstPrice,
  waitForText,
} from './helpers';

const TICKER = 'AAPL';
const QTY = 5;

test.describe('Buy and sell shares via trade bar', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, TICKER, 5_000);
  });

  test('buy → cash decreases, position appears, heatmap and positions table update', async ({ page }) => {
    const cashEl = page.locator('[data-testid="cash-balance"]');
    const startingCash = parseCurrency(await cashEl.textContent());
    expect(startingCash).toBeGreaterThan(0);

    await page.locator('[data-testid="trade-ticker-input"]').fill(TICKER);
    await page.locator('[data-testid="trade-quantity-input"]').fill(String(QTY));
    await page.locator('[data-testid="trade-buy-button"]').click();

    // Cash must drop (we paid for shares)
    await waitForText(cashEl, (t) => parseCurrency(t) < startingCash, { timeout: 10_000 });

    // Position row appears in the positions table (scroll into view — it's on the bottom row)
    const positionRow = page.locator(`[data-testid="position-row-${TICKER}"]`);
    await positionRow.scrollIntoViewIfNeeded();
    await expect(positionRow).toBeVisible({ timeout: 10_000 });
    // Frontend strips trailing zeros, so the integer QTY appears as-is
    await expect(positionRow).toContainText(String(QTY));

    // Heatmap renders at least one position tile
    const tile = page.locator(`[data-testid="heatmap-tile-${TICKER}"]`);
    await tile.scrollIntoViewIfNeeded();
    await expect(tile).toBeVisible({ timeout: 10_000 });
  });

  test('buy with insufficient cash shows an error toast and does not move funds', async ({ page }) => {
    const cashEl = page.locator('[data-testid="cash-balance"]');
    const cashBefore = parseCurrency(await cashEl.textContent());

    // Wildly oversized order — far more than the $10k cash will cover at any
    // realistic price. Backend should reject; UI should surface trade-error-toast.
    await page.locator('[data-testid="trade-ticker-input"]').fill(TICKER);
    await page.locator('[data-testid="trade-quantity-input"]').fill('100000');
    await page.locator('[data-testid="trade-buy-button"]').click();

    await expect(page.locator('[data-testid="trade-error-toast"]')).toBeVisible({
      timeout: 10_000,
    });

    // Cash unchanged
    const cashAfter = parseCurrency(await cashEl.textContent());
    expect(cashAfter).toBeCloseTo(cashBefore, 2);
  });

  test('sell → position reduces or disappears, cash increases', async ({ page }) => {
    // Ensure we own shares to sell — buy if needed
    const positionRow = page.locator(`[data-testid="position-row-${TICKER}"]`);
    if ((await positionRow.count()) === 0) {
      await page.locator('[data-testid="trade-ticker-input"]').fill(TICKER);
      await page.locator('[data-testid="trade-quantity-input"]').fill(String(QTY));
      await page.locator('[data-testid="trade-buy-button"]').click();
      await positionRow.scrollIntoViewIfNeeded();
      await expect(positionRow).toBeVisible({ timeout: 10_000 });
    }

    const cashEl = page.locator('[data-testid="cash-balance"]');
    const cashBeforeSell = parseCurrency(await cashEl.textContent());

    await page.locator('[data-testid="trade-ticker-input"]').fill(TICKER);
    await page.locator('[data-testid="trade-quantity-input"]').fill(String(QTY));
    await page.locator('[data-testid="trade-sell-button"]').click();

    // Cash increases after a sell
    await waitForText(cashEl, (t) => parseCurrency(t) > cashBeforeSell, { timeout: 10_000 });

    // Position is gone (sold full quantity) OR reduced to zero
    await expect.poll(async () => (await positionRow.count()) === 0, { timeout: 10_000 }).toBe(true);
  });
});
