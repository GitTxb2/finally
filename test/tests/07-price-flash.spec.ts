import { test, expect } from '@playwright/test';
import { gotoHome, waitForFirstPrice } from './helpers';

/**
 * Verifies that price cells emit a direction signal as SSE ticks arrive.
 * The simulator updates every ~500ms, so within a few seconds we should see
 * at least one "up" or "down" tick on AAPL (it almost never stays flat).
 */
test.describe('Price flash signal', () => {
  test('AAPL emits an up or down direction within 8s', async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, 'AAPL', 5_000);

    const price = page.locator('[data-testid="watchlist-price-AAPL"]');
    await expect.poll(
      async () => price.getAttribute('data-direction'),
      { timeout: 8_000, intervals: [250] },
    ).toMatch(/^(up|down)$/);
  });
});
