# FinAlly Frontend

Next.js 14 (App Router, TypeScript) static export, served by FastAPI in
production. Bloomberg-terminal aesthetic, dark theme.

## Stack

- **Next.js 14** with `output: 'export'` → `out/` is what the Dockerfile bundles
- **Tailwind CSS** with a custom palette in `tailwind.config.ts`
- **Vitest** + **React Testing Library** for unit tests
- Fonts: **Space Grotesk** (display) + **JetBrains Mono** (data)

## Layout

```
app/                  App Router pages
  layout.tsx          Root layout, fonts, metadata
  page.tsx            Workstation shell
  globals.css         Theme tokens + scanline/flash keyframes
components/           UI primitives (Header, Panel, ConnectionDot, …)
lib/
  api.ts              Typed fetchers for /api/*
  sse.ts              usePriceStream hook around EventSource
  types.ts            Domain types matching backend response shapes
  format.ts           Currency / percent / qty formatters
public/               Static assets
test/setup.ts         Vitest jest-dom setup
```

## Commands

```bash
npm install
npm run dev           # http://localhost:3000 — rewrites /api/* to :8000 in dev
npm run build         # produces ./out (static export, consumed by Dockerfile)
npm run typecheck     # tsc --noEmit
npm test              # vitest run
```

## Notes for other agents

- API contract: see `lib/types.ts`. If backend response shapes evolve, fix
  here first — components consume types, not raw fetch results.
- SSE event shape from `/api/stream/prices` is `data: {[ticker]: PriceUpdate}`.
  See `app/market/stream.py` and `PriceUpdate.to_dict()` in the backend.
- Production is same-origin — FastAPI serves `out/` and `/api/*` on :8000.
  No CORS needed. Dev mode proxies via `next.config.js` rewrites.
