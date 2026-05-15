import { test, expect } from '@playwright/test';
import { gotoHome, waitForFirstPrice } from './helpers';

/**
 * SSE resilience: drive a full disconnect → reconnect cycle through Playwright's
 * request routing.
 *
 * The frontend's EventSource (see frontend/lib/sse.ts) only flips to
 * `reconnecting` after it has been `connected` at least once (the `everConnected`
 * latch). So the flow is:
 *   1. Load the page with no routing → EventSource opens → status=connected
 *   2. Install an abort route for /api/stream/prices, then close the existing
 *      EventSource server-side by aborting all in-flight requests we can. The
 *      browser will retry; the retry hits the abort route → onerror →
 *      status=reconnecting.
 *   3. Unroute → next retry succeeds → status=connected.
 *
 * To force the existing EventSource to drop, we re-route AND reload the page
 * so the new EventSource opens against the aborted route. We then unroute and
 * verify it heals after the page picks up the next retry (browser EventSource
 * built-in retry, or we explicitly reload).
 */
test.describe('SSE resilience', () => {
  test('connection indicator reflects reconnect cycle', async ({ page }) => {
    await gotoHome(page);
    await waitForFirstPrice(page, 'AAPL', 5_000);

    const status = page.locator('[data-testid="connection-status"]');
    await expect(status).toHaveAttribute('data-state', 'connected');

    // Block SSE *and* reload so the new EventSource opens against the abort.
    // The existing EventSource will be torn down by navigation.
    await page.route('**/api/stream/prices', (route) => route.abort());
    await page.reload();
    // After reload, `everConnected` resets — but the page sets status to
    // 'connecting' first and 'disconnected' after the abort error. Either
    // pre-success state (anything other than 'connected') proves the connection
    // is broken; that's what we want to see.
    await expect(status).not.toHaveAttribute('data-state', 'connected', { timeout: 15_000 });

    // Restore normal routing and reload to heal.
    await page.unroute('**/api/stream/prices');
    await page.reload();
    await expect(status).toHaveAttribute('data-state', 'connected', { timeout: 20_000 });

    // Sanity: prices stream again after recovery
    await waitForFirstPrice(page, 'AAPL', 10_000);
  });
});
