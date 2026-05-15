import { test, expect } from '@playwright/test';
import { gotoHome, waitForFirstPrice } from './helpers';

const TICKER = 'AAPL';
const QTY = 3;

test.describe('Portfolio visualizations', () => {
  test('heatmap renders with a position and P&L chart accumulates data points', async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, TICKER, 5_000);

    // Buy something so heatmap has at least one tile
    await page.locator('[data-testid="trade-ticker-input"]').fill(TICKER);
    await page.locator('[data-testid="trade-quantity-input"]').fill(String(QTY));
    await page.locator('[data-testid="trade-buy-button"]').click();

    // Portfolio views are on the bottom row — scroll into view before asserting
    const tile = page.locator(`[data-testid="heatmap-tile-${TICKER}"]`);
    await tile.scrollIntoViewIfNeeded();
    await expect(tile).toBeVisible({ timeout: 10_000 });

    // P&L chart container is rendered. We expect at least one data point after a
    // trade (BE-2 records a snapshot immediately on trade execution per PLAN.md
    // §7). FE-3 ships inline <svg><path> + a <circle> for the last point.
    const pnlChart = page.locator('[data-testid="pnl-chart"]');
    await pnlChart.scrollIntoViewIfNeeded();
    await expect(pnlChart).toBeVisible();
    await expect.poll(
      async () => pnlChart.locator('svg path, svg circle, [data-testid="pnl-point"]').count(),
      { timeout: 35_000, intervals: [1000] },
    ).toBeGreaterThan(0);
  });
});
