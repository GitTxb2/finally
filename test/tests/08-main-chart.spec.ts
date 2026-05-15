import { test, expect } from '@playwright/test';
import { gotoHome, waitForFirstPrice } from './helpers';

/**
 * Clicking a watchlist row updates the main chart's `data-ticker` synchronously.
 * The chart re-paths rather than re-mounts — the <svg> is stable, only the path
 * `d` attribute and header change. We use the data-ticker attribute as the
 * authoritative signal because it updates synchronously and survives the
 * "AWAITING TAPE…" placeholder state.
 */
test.describe('Main chart selection', () => {
  test('clicking a watchlist row updates the main chart ticker', async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, 'AAPL', 5_000);

    const chart = page.locator('[data-testid="main-chart"]');
    await expect(chart).toBeVisible();

    await page.locator('[data-testid="watchlist-row-AAPL"]').click();
    await expect(chart).toHaveAttribute('data-ticker', 'AAPL');

    await page.locator('[data-testid="watchlist-row-MSFT"]').click();
    await expect(chart).toHaveAttribute('data-ticker', 'MSFT');

    // Watchlist row selection state mirrors the chart
    await expect(page.locator('[data-testid="watchlist-row-MSFT"]')).toHaveAttribute(
      'data-selected',
      'true',
    );
    await expect(page.locator('[data-testid="watchlist-row-AAPL"]')).toHaveAttribute(
      'data-selected',
      'false',
    );
  });
});
