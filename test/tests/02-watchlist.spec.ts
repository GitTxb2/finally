import { test, expect } from '@playwright/test';
import { gotoHome, waitForFirstPrice } from './helpers';

test.describe('Watchlist CRUD via UI', () => {
  const NEW_TICKER = 'PYPL';

  test.beforeEach(async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, 'AAPL', 5_000);
  });

  test('add a ticker via the watchlist input', async ({ page }) => {
    // Pre-condition: ticker not present
    await expect(page.locator(`[data-testid="watchlist-row-${NEW_TICKER}"]`)).toHaveCount(0);

    const input = page.locator('[data-testid="watchlist-add-input"]');
    await input.fill(NEW_TICKER);
    await page.locator('[data-testid="watchlist-add-button"]').click();

    await expect(page.locator(`[data-testid="watchlist-row-${NEW_TICKER}"]`)).toBeVisible({
      timeout: 10_000,
    });

    // A live price should arrive shortly after add (simulator seeds it immediately)
    await waitForFirstPrice(page, NEW_TICKER, 10_000);
  });

  test('remove a ticker via the row remove control', async ({ page }) => {
    // Ensure the ticker exists first (add if previous test was independent)
    const row = page.locator(`[data-testid="watchlist-row-${NEW_TICKER}"]`);
    if ((await row.count()) === 0) {
      await page.locator('[data-testid="watchlist-add-input"]').fill(NEW_TICKER);
      await page.locator('[data-testid="watchlist-add-button"]').click();
      await expect(row).toBeVisible({ timeout: 10_000 });
    }

    // Remove button is hover-revealed in the current FE-2 design — hover the
    // row first to make the control interactable, then click.
    await row.hover();
    await page.locator(`[data-testid="watchlist-remove-${NEW_TICKER}"]`).click();
    await expect(row).toHaveCount(0, { timeout: 5_000 });
  });

  test('clicking a watchlist row marks it as selected', async ({ page }) => {
    const row = page.locator('[data-testid="watchlist-row-AAPL"]');
    await row.click();
    await expect(row).toHaveAttribute('data-selected', 'true');

    // Switching to another row deselects the previous one
    const other = page.locator('[data-testid="watchlist-row-MSFT"]');
    await other.click();
    await expect(other).toHaveAttribute('data-selected', 'true');
    await expect(row).toHaveAttribute('data-selected', 'false');
  });
});
