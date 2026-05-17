// Tiny pub/sub price store. No external state library needed for Phase 1.
// Backend shape matches `PriceUpdate.to_dict()` from backend/app/market/models.py.

export type PriceUpdate = {
  ticker: string;
  price: number;
  previous_price: number;
  timestamp: number; // Unix seconds (float in Python, number in JSON)
  change: number;
  change_percent: number; // already a percentage value (e.g. 0.5944 for 0.5944%)
  direction: 'up' | 'down' | 'flat';
};

type Subscriber = (update: PriceUpdate) => void;

const prices: Map<string, PriceUpdate> = new Map();
const subscribers: Map<string, Set<Subscriber>> = new Map();

export function setPrice(update: PriceUpdate): void {
  prices.set(update.ticker, update);
  const tickerSubs = subscribers.get(update.ticker);
  if (tickerSubs) {
    tickerSubs.forEach((fn) => fn(update));
  }
}

export function getPrice(ticker: string): PriceUpdate | undefined {
  return prices.get(ticker);
}

export function subscribe(ticker: string, fn: Subscriber): () => void {
  let tickerSubs = subscribers.get(ticker);
  if (!tickerSubs) {
    tickerSubs = new Set();
    subscribers.set(ticker, tickerSubs);
  }
  tickerSubs.add(fn);
  return () => {
    tickerSubs!.delete(fn);
    if (tickerSubs!.size === 0) {
      subscribers.delete(ticker);
    }
  };
}

// Test-only: reset module-level state between tests.
export function __resetForTests(): void {
  prices.clear();
  subscribers.clear();
}
