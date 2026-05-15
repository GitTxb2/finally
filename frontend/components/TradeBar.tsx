'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '@/lib/api';
import { fmtPrice } from '@/lib/format';
import type { Portfolio, PriceMap, TradeSide } from '@/lib/types';

interface TradeBarProps {
  selected: string | null;
  prices: PriceMap;
  onTraded: (portfolio: Portfolio) => void;
  onError: (text: string) => void;
  onSuccess: (text: string) => void;
}

/**
 * Market-order trade bar — ticker / qty / Buy / Sell. Submits to
 * /api/portfolio/trade and lifts the refreshed portfolio to the page
 * (saves a round-trip — see backend response shape).
 */
export function TradeBar({ selected, prices, onTraded, onError, onSuccess }: TradeBarProps) {
  const [ticker, setTicker] = useState('');
  const [qty, setQty] = useState('');
  const [busy, setBusy] = useState<TradeSide | null>(null);

  useEffect(() => {
    if (selected) setTicker(selected);
  }, [selected]);

  async function submit(side: TradeSide, e?: FormEvent) {
    e?.preventDefault();
    const normalizedTicker = ticker.trim().toUpperCase();
    const quantity = Number.parseFloat(qty);
    if (!normalizedTicker) {
      onError('Ticker required');
      return;
    }
    if (!Number.isFinite(quantity) || quantity <= 0) {
      onError('Quantity must be > 0');
      return;
    }
    setBusy(side);
    try {
      const res = await api.trade({ ticker: normalizedTicker, quantity, side });
      onTraded(res.portfolio);
      onSuccess(
        `${side === 'buy' ? 'Bought' : 'Sold'} ${quantity} ${normalizedTicker} @ $${fmtPrice(res.trade.price)}`,
      );
      setQty('');
    } catch (err) {
      onError(err instanceof ApiError ? err.message : `Trade failed for ${normalizedTicker}`);
    } finally {
      setBusy(null);
    }
  }

  const livePrice = prices[ticker.trim().toUpperCase()]?.price ?? null;
  const estimate =
    livePrice && Number.parseFloat(qty) > 0
      ? livePrice * Number.parseFloat(qty)
      : null;

  return (
    <form onSubmit={(e) => submit('buy', e)} className="grid h-full content-start gap-3 p-4">
      <div className="grid grid-cols-[1fr_1fr] gap-2">
        <Field label="Ticker">
          <input
            data-testid="trade-ticker-input"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            spellCheck={false}
            autoCapitalize="characters"
            placeholder="AAPL"
            aria-label="Ticker"
            className="w-full bg-transparent font-mono text-[14px] uppercase tracking-wider2 text-ink placeholder:text-ink-ghost focus:outline-none"
          />
        </Field>
        <Field label="Qty">
          <input
            data-testid="trade-quantity-input"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            inputMode="decimal"
            placeholder="0"
            aria-label="Quantity"
            className="w-full bg-transparent text-right font-mono text-[14px] tabular tracking-wider2 text-ink placeholder:text-ink-ghost focus:outline-none"
          />
        </Field>
      </div>

      <div className="flex items-center justify-between border-y border-edge/60 py-1.5 font-mono text-[10px] uppercase tracking-wider2 text-ink-mute">
        <span>Last</span>
        <span className="tabular text-ink-dim">
          {livePrice == null ? '—' : `$${fmtPrice(livePrice)}`}
        </span>
        <span>Est</span>
        <span className="tabular text-accent-yellow">
          {estimate == null ? '—' : `$${fmtPrice(estimate)}`}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          data-testid="trade-buy-button"
          type="submit"
          disabled={busy !== null}
          className="rounded-sm border border-tape-up/70 bg-tape-up/15 px-3 py-2 font-mono text-[12px] font-semibold uppercase tracking-wider3 text-tape-up transition hover:bg-tape-up/25 disabled:opacity-50"
        >
          {busy === 'buy' ? '…' : 'BUY'}
        </button>
        <button
          data-testid="trade-sell-button"
          type="button"
          onClick={() => submit('sell')}
          disabled={busy !== null}
          className="rounded-sm border border-tape-down/70 bg-tape-down/15 px-3 py-2 font-mono text-[12px] font-semibold uppercase tracking-wider3 text-tape-down transition hover:bg-tape-down/25 disabled:opacity-50"
        >
          {busy === 'sell' ? '…' : 'SELL'}
        </button>
      </div>

      <p className="font-mono text-[9px] uppercase tracking-wider2 text-ink-ghost">
        Market order · instant fill · no fees
      </p>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-0.5 rounded-sm border border-edge bg-bg-raised/40 px-2 py-1.5 focus-within:border-accent-yellow">
      <span className="font-mono text-[9px] uppercase tracking-wider3 text-ink-mute">{label}</span>
      {children}
    </label>
  );
}
