import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for FinAlly E2E tests.
 *
 * Tests target a running app instance. By default we hit the app container
 * started by `docker-compose.test.yml` at http://app:8000. Override with the
 * `BASE_URL` env var (e.g. `BASE_URL=http://localhost:8000` for local runs).
 */
const BASE_URL = process.env.BASE_URL ?? 'http://app:8000';

export default defineConfig({
  testDir: './tests',
  globalSetup: './global-setup.ts',
  fullyParallel: false, // Single-user simulated state — keep deterministic
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
