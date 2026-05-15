'use client';

import { useEffect, useState, useTransition, type FormEvent } from 'react';
import { Sparkline } from './Sparkline';
import { FlashCell } from './FlashCell';
import { api, ApiError } from '@/lib/api';
import { fmtPrice, fmtPct } from '@/lib/format';
import type { PriceMap, WatchlistEntry } from '@/lib/types';

interface WatchlistProps {
  prices: PriceMap;
  history: Record<string, number[]>;
  selected: string | null;
  onSelect: (ticker: string) => void;
  /**
   * Monotonic counter that triggers a refetch of /api/watchlist when it
   * increments. The page bumps this after a chat-driven watchlist
   * mutation; in-component add/remove maintain local state directly.
   */
  refreshSignal?: number;
}

export function Watchlist({ prices, history, selected, onSelect, refreshSignal = 0 }: WatchlistProps) {
  const [tickers, setTickers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [mutateError, setMutateError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');

  // Fetch on mount and any time refreshSignal increments (e.g. after
  // a chat-driven watchlist add/remove). The SSE stream keeps prices
  // fresh but doesn't tell us which tickers should be rendered.
  useEffect(() => {
    let cancelled = false;
    api
      .getWatchlist()
      .then((rows: WatchlistEntry[]) => {
        if (cancelled) return;
        setTickers(rows.map((r) => r.ticker));
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setLoadError(e instanceof ApiError ? e.message : 'Watchlist unavailable');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshSignal]);

  function addTicker(e: FormEvent) {
    e.preventDefault();
    const raw = draft.trim().toUpperCase();
    if (!raw) return;
    setMutateError(null);
    setDraft('');
    startTransition(async () => {
      try {
        const res = await api.addWatchlist(raw);
        setTickers((curr) => (curr.includes(res.ticker) ? curr : [...curr, res.ticker]));
      } catch (err) {
        setMutateError(err instanceof ApiError ? err.message : `Could not add ${raw}`);
      }
    });
  }

  function removeTicker(ticker: string) {
    setMutateError(null);
    startTransition(async () => {
      try {
        await api.removeWatchlist(ticker);
        setTickers((curr) => curr.filter((t) => t !== ticker));
        if (selected === ticker) onSelect('');
      } catch (err) {
        setMutateError(err instanceof ApiError ? err.message : `Could not remove ${ticker}`);
      }
    });
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <form
        onSubmit={addTicker}
        className="flex items-center gap-1.5 border-b border-edge px-2 py-1.5"
      >
        <span className="font-mono text-[9px] uppercase tracking-wider3 text-ink-mute">ADD</span>
        <input
          data-testid="watchlist-add-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          maxLength={8}
          spellCheck={false}
          autoCapitalize="characters"
          placeholder="TICKER"
          aria-label="Add ticker to watchlist"
          className="flex-1 bg-transparent font-mono text-[12px] uppercase tracking-wider2 text-ink placeholder:text-ink-ghost focus:outline-none"
        />
        <button
          data-testid="watchlist-add-button"
          type="submit"
          disabled={pending || !draft.trim()}
          className="rounded-sm border border-edge bg-bg-raised px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider2 text-ink-dim hover:border-accent-yellow hover:text-accent-yellow disabled:cursor-not-allowed disabled:opacity-40"
        >
          +
        </button>
      </form>

      {mutateError ? (
        <div className="border-b border-tape-down/30 bg-tape-down/10 px-2 py-1 font-mono text-[10px] tracking-wider2 text-tape-down">
          {mutateError}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? (
          <Empty label="Loading watchlist…" />
        ) : loadError ? (
          <Empty label={loadError} tone="error" />
        ) : tickers.length === 0 ? (
          <Empty label="Empty — add a ticker above" />
        ) : (
          <ul role="list" className="divide-y divide-edge/60">
            {tickers.map((t) => (
              <WatchlistRow
                key={t}
                ticker={t}
                price={prices[t]?.price ?? null}
                changePct={prices[t]?.change_percent ?? null}
                series={history[t] ?? []}
                selected={selected === t}
                onSelect={() => onSelect(t)}
                onRemove={() => removeTicker(t)}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function WatchlistRow({
  ticker,
  price,
  changePct,
  series,
  selected,
  onSelect,
  onRemove,
}: {
  ticker: string;
  price: number | null;
  changePct: number | null;
  series: number[];
  selected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}) {
  const positive = (changePct ?? 0) > 0;
  const negative = (changePct ?? 0) < 0;
  return (
    <li
      data-testid={`watchlist-row-${ticker}`}
      data-selected={selected ? 'true' : 'false'}
      className={`group relative grid cursor-pointer grid-cols-[1fr_auto_auto] items-center gap-2 px-2 py-1.5 transition-colors ${
        selected ? 'bg-accent-yellow/[0.06]' : 'hover:bg-bg-raised/60'
      }`}
      onClick={onSelect}
    >
      {selected ? (
        <span className="absolute left-0 top-0 h-full w-[2px] bg-accent-yellow" aria-hidden="true" />
      ) : null}
      <div className="flex min-w-0 items-center gap-2 pl-1">
        <span className="font-mono text-[12px] font-semibold tracking-wider2 text-ink">{ticker}</span>
        <Sparkline data={series} width={64} height={18} className="opacity-90" />
      </div>
      <div className="flex flex-col items-end leading-tight">
        <FlashCell
          value={price}
          format={fmtPrice}
          testId={`watchlist-price-${ticker}`}
          className="tabular font-mono text-[12px] text-ink"
        />
        <span
          className={`tabular font-mono text-[10px] ${
            positive ? 'text-tape-up' : negative ? 'text-tape-down' : 'text-ink-mute'
          }`}
        >
          {changePct == null ? '—' : fmtPct(changePct)}
        </span>
      </div>
      <button
        data-testid={`watchlist-remove-${ticker}`}
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        aria-label={`Remove ${ticker} from watchlist`}
        className="ml-1 rounded-sm border border-transparent px-1.5 py-0.5 font-mono text-[10px] text-ink-ghost opacity-0 transition group-hover:opacity-100 hover:border-tape-down/40 hover:text-tape-down"
      >
        ×
      </button>
    </li>
  );
}

function Empty({ label, tone = 'mute' }: { label: string; tone?: 'mute' | 'error' }) {
  return (
    <div
      className={`flex h-full items-center justify-center p-4 font-mono text-[11px] uppercase tracking-wider2 ${
        tone === 'error' ? 'text-tape-down' : 'text-ink-mute'
      }`}
    >
      {label}
    </div>
  );
}
