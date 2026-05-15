import { test, expect } from '@playwright/test';
import {
  DEFAULT_TICKERS,
  STARTING_CASH,
  gotoHome,
  parseCurrency,
  waitForFirstPrice,
} from './helpers';

test.describe('Fresh start', () => {
  test('shows 10 default tickers, $10,000 cash, and streaming prices within 5s', async ({ page }) => {
    await gotoHome(page);

    // Each default ticker should appear in the watchlist
    for (const ticker of DEFAULT_TICKERS) {
      await expect(
        page.locator(`[data-testid="watchlist-row-${ticker}"]`),
        `watchlist row for ${ticker}`,
      ).toBeVisible();
    }

    // Cash balance equals the seed value
    const cashEl = page.locator('[data-testid="cash-balance"]');
    await expect(cashEl).toBeVisible();
    const cashText = (await cashEl.textContent()) ?? '';
    expect(parseCurrency(cashText)).toBeCloseTo(STARTING_CASH, 2);

    // Prices begin streaming within 5 seconds
    await waitForFirstPrice(page, 'AAPL', 5_000);

    // Connection status indicator reports a live connection
    await expect(page.locator('[data-testid="connection-status"]')).toHaveAttribute(
      'data-state',
      /connected|live|open/i,
    );
  });
});
