'use client';

import { useEffect, useState } from 'react';
import { setPrice, type PriceUpdate } from './priceStore';

type EventStreamState = { connected: boolean };

// Server sends one SSE event containing the full {ticker: PriceUpdate} dict
// per tick (see backend/app/market/stream.py).
type StreamPayload = Record<string, PriceUpdate>;

export function useEventStream(
  url: string = '/api/stream/prices',
): EventStreamState {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return; // SSR / static export safety
    const es = new EventSource(url);

    es.onopen = () => setConnected(true);

    es.onmessage = (event) => {
      try {
        const data: StreamPayload = JSON.parse(event.data);
        for (const ticker of Object.keys(data)) {
          setPrice(data[ticker]);
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn('useEventStream: failed to parse SSE payload', err);
      }
    };

    es.onerror = () => {
      // EventSource auto-reconnects; just surface the state.
      setConnected(false);
    };

    return () => {
      es.close();
    };
  }, [url]);

  return { connected };
}
