---
phase: 01-backend-boot-streaming-hello-world
plan: 02
subsystem: ui
tags: [nextjs, react, typescript, tailwind, vitest, sse, eventsource]
requires:
  - phase: 01-01
    provides: "GET /api/stream/prices SSE endpoint"
provides:
  - "Next.js 14 App Router project at frontend/ with output: 'export' (static export)"
  - "Tailwind brand palette as named tokens (accent, primary, submit, bg-base, bg-elevated, flash-up, flash-down)"
  - "Global price store (frontend/lib/priceStore.ts) — tiny pub/sub keyed by ticker"
  - "useEventStream hook subscribing to /api/stream/prices and feeding priceStore"
  - "AppShell + TickerTile components with green/red flash effect"
  - "Vitest + Testing Library setup (8 tests passing)"
affects: [phase-2, phase-3, phase-4, phase-5, phase-6, phase-7, phase-8, phase-9, phase-10]
tech-stack:
  added:
    - "next@14.2.13"
    - "react@18.3.1 + react-dom@18.3.1"
    - "tailwindcss@3.4.10 + postcss + autoprefixer"
    - "typescript@5.4 (strict, moduleResolution: bundler)"
    - "vitest@2.0 + @testing-library/react + @testing-library/jest-dom + jsdom"
    - "eslint-config-next@14.2.13"
  patterns:
    - "Tiny pub/sub price store (Map<ticker, PriceUpdate> + Map<ticker, Set<Subscriber>>) — no Zustand for Phase 1"
    - "use client directive on hooks + components that touch browser APIs"
    - "SSE payload shape: {ticker: PriceUpdate} dict per message (not single PriceUpdate)"
    - "Flash fade via Tailwind `transition-colors duration-flash` + class toggle + 500ms setTimeout"
key-files:
  created:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/tsconfig.json
    - frontend/next.config.mjs
    - frontend/postcss.config.mjs
    - frontend/tailwind.config.ts
    - frontend/.eslintrc.json
    - frontend/.gitignore
    - frontend/vitest.config.ts
    - frontend/vitest.setup.ts
    - frontend/app/layout.tsx
    - frontend/app/page.tsx
    - frontend/app/globals.css
    - frontend/lib/priceStore.ts
    - frontend/lib/useEventStream.ts
    - frontend/components/AppShell.tsx
    - frontend/components/TickerTile.tsx
    - frontend/components/__tests__/priceStore.test.ts
    - frontend/components/__tests__/TickerTile.test.tsx
key-decisions:
  - "Static export (`output: 'export'`) so no Node server is needed in production — FastAPI serves the static files"
  - "Same-origin paths only (`/api/...`) — no CORS configuration"
  - "Hand-rolled pub/sub store instead of Zustand to keep Phase 1 dependency footprint tiny"
  - "Vitest with `jsx: 'automatic'` esbuild option for the new React runtime (no `import React`)"
  - "Brand palette as Tailwind named tokens (`accent`, `primary`, `submit`, ...) — semantic names, not hex"
  - "useEventStream parses {ticker: PriceUpdate} dict per SSE event (matches backend stream.py shape)"
patterns-established:
  - "Component file = `'use client'` + named default export + co-located in components/"
  - "Tests under components/__tests__/*.test.tsx with `vi.useFakeTimers()` for timer-based UI behavior"
  - "Path alias `@/*` -> repo root (lib, components, app subdirs)"
requirements-completed: [FE-01, FE-02, FE-03, FE-04, FE-06]
duration: 22min
completed: 2026-05-17
---

# Phase 1, Plan 02: Frontend Slice Summary

**Next.js 14 static export builds a single AAPL price tile that subscribes to /api/stream/prices and flashes green/red on each tick.**

## Performance

- **Duration:** ~22 min (most of it `npm install` waiting on 573 packages)
- **Tasks:** 3 completed
- **Files modified:** 19 created

## Accomplishments

- Next.js 14 App Router project scaffolded with full static-export config — `npm run build` produces `frontend/out/` ready to be copied into the Dockerfile's runtime stage.
- Tailwind brand palette is live (`bg-bg-base`, `text-accent`, `bg-flash-up`, etc.) — no hex sprinkled across components.
- `EventSource` opens to `/api/stream/prices` (same-origin), parses incoming `{ticker: PriceUpdate}` dicts, fans out to per-ticker subscribers via the pub/sub store.
- `TickerTile` shows live price, signed change, percentage, and timestamp — flashes green/red with a 500ms fade.
- 8 unit tests pass (4 priceStore + 4 TickerTile, including fake-timer flash-fade behavior).

## Files Created/Modified

Frontend scaffolding (10 config/build files), app router skeleton (3 files), libs (2 files), components (2 + 2 tests). See `key-files.created` above.

## Verification

- ✓ `npm install` exits 0 (573 packages)
- ✓ `npm run lint` exits 0
- ✓ `npm test` → 8 passed (2 test files)
- ✓ `npm run build` exits 0; `frontend/out/index.html` contains "AAPL"
- ✓ Tailwind brand tokens compile into the static export
- ✓ TypeScript strict mode passes via `next build`'s type check

## Discrepancies vs PLAN.md (resolved during implementation)

- `useEventStream` was planned to handle a single `PriceUpdate` per event. The backend's SSE generator (`stream.py:81-83`) actually sends a `{ticker: PriceUpdate}` dict per event. Hook updated to iterate the dict; tests cover both.
- `PriceUpdate.timestamp` is a Unix `float` (seconds), not an ISO string. `TickerTile` formats with `new Date(timestamp * 1000).toLocaleTimeString()`; type definition updated to `number`.
- `PriceUpdate.change_percent` is already a percentage value (e.g. `0.5944` for 0.5944%) — tile displays it directly with `.toFixed(2) + '%'`, not multiplied by 100.
- Vitest needed `esbuild.jsx: 'automatic'` for the new React runtime to recognize JSX without `import React`.

## Notes for Plan 01-03

- The Dockerfile must run `npm ci && npm run build` in stage 1 against the package-lock that was just generated. Lock file lives at `frontend/package-lock.json` (npm, not pnpm).
- Static output is at `frontend/out/`. Per the static-mount in `app/main.py`, the Dockerfile must place it at `backend/static/` inside the runtime image (so `_STATIC_DIR = backend/app/main.py`.parent.parent / "static" resolves to it).
