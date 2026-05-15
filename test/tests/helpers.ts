import { Page, expect, Locator } from '@playwright/test';

export const DEFAULT_TICKERS = [
  'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
  'NVDA', 'META', 'JPM', 'V', 'NFLX',
] as const;

export const STARTING_CASH = 10000.0;

/**
 * Parse a USD currency string like "$10,000.00" or "$9,876.54" into a number.
 * Returns NaN if the string is not a number.
 */
export function parseCurrency(text: string | null | undefined): number {
  if (!text) return NaN;
  const cleaned = text.replace(/[^0-9.\-]/g, '');
  return cleaned === '' ? NaN : Number(cleaned);
}

/**
 * Wait until a locator's text content matches a predicate. Useful for waiting
 * on live-updating values (cash balance, position quantity, etc.) without
 * coupling to a specific intermediate value.
 */
export async function waitForText(
  locator: Locator,
  predicate: (text: string) => boolean,
  options: { timeout?: number } = {},
): Promise<string> {
  const timeout = options.timeout ?? 10_000;
  const deadline = Date.now() + timeout;
  let lastText = '';
  while (Date.now() < deadline) {
    lastText = (await locator.textContent()) ?? '';
    if (predicate(lastText)) return lastText;
    await locator.page().waitForTimeout(200);
  }
  throw new Error(`waitForText timed out after ${timeout}ms. Last value: "${lastText}"`);
}

/**
 * Land on the home page and wait for hydration to be far enough along that
 * the watchlist input is interactable.
 */
export async function gotoHome(page: Page): Promise<void> {
  await page.goto('/');
  await expect(page.locator('[data-testid="watchlist-add-input"]')).toBeVisible({
    timeout: 15_000,
  });
}

/**
 * Wait for SSE prices to begin streaming. The frontend should accumulate at
 * least one non-null price for at least one of the default tickers.
 */
export async function waitForFirstPrice(page: Page, ticker = 'AAPL', timeoutMs = 5000): Promise<void> {
  const priceCell = page.locator(`[data-testid="watchlist-price-${ticker}"]`).first();
  await expect(priceCell).toBeVisible({ timeout: timeoutMs });
  await waitForText(
    priceCell,
    (t) => /\d/.test(t) && !/^[\s\-—]*$/.test(t),
    { timeout: timeoutMs },
  );
}
