import { execSync } from 'node:child_process';

/**
 * Reset the application container to a known-fresh state before the test suite.
 *
 * Strategy: stop and remove any existing `finally-e2e` container, then start a
 * new one from the `finally:e2e` image (assumed already built; see
 * `test/README.md`). This wipes the SQLite database that lives inside the
 * container so every run starts with $10,000 cash, no positions, and the
 * default 10-ticker watchlist.
 *
 * Skipped automatically when `BASE_URL` points at something other than
 * `http://localhost:8000` (e.g. inside docker-compose, where the app is the
 * `app` service and is already fresh per `compose up`).
 */
export default async function globalSetup(): Promise<void> {
  const baseUrl = process.env.BASE_URL ?? 'http://localhost:8000';
  if (!baseUrl.includes('localhost:8000')) {
    console.log(`[global-setup] BASE_URL=${baseUrl} — skipping container reset`);
    return;
  }
  if (process.env.SKIP_CONTAINER_RESET === 'true') {
    console.log('[global-setup] SKIP_CONTAINER_RESET=true — skipping container reset');
    return;
  }

  const image = process.env.FINALLY_IMAGE ?? 'finally:e2e';
  const name = 'finally-e2e';

  console.log(`[global-setup] resetting container ${name} from ${image}`);

  const run = (cmd: string, opts: { allowFail?: boolean } = {}) => {
    try {
      execSync(cmd, { stdio: 'pipe' });
    } catch (err) {
      if (!opts.allowFail) throw err;
    }
  };

  // Tear down any leftover container — ignore failure if it's not there.
  run(`docker rm -f ${name}`, { allowFail: true });

  // Start the app with LLM_MOCK=true and a throwaway OPENROUTER_API_KEY.
  run(
    `docker run -d --name ${name} -p 8000:8000 ` +
      `-e LLM_MOCK=true -e OPENROUTER_API_KEY=test-key-not-used ${image}`,
  );

  // Poll /api/health until it returns 200 (max ~30s).
  const start = Date.now();
  const deadline = start + 30_000;
  let healthy = false;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${baseUrl}/api/health`);
      if (res.ok) {
        healthy = true;
        break;
      }
    } catch {
      // Container still starting — keep polling.
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  if (!healthy) {
    throw new Error(`[global-setup] app did not become healthy within 30s at ${baseUrl}`);
  }
  console.log(`[global-setup] app healthy in ${((Date.now() - start) / 1000).toFixed(1)}s`);
}
