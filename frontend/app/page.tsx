'use client';

import { useCallback, useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Panel } from '@/components/Panel';
import { Watchlist } from '@/components/Watchlist';
import { MainChart } from '@/components/MainChart';
import { PositionsTable } from '@/components/PositionsTable';
import { Heatmap } from '@/components/Heatmap';
import { PnlChart } from '@/components/PnlChart';
import { TradeBar } from '@/components/TradeBar';
import { ChatPanel } from '@/components/ChatPanel';
import { ToastStack } from '@/components/Toast';
import { useToasts } from '@/lib/useToasts';
import { usePriceStream } from '@/lib/sse';
import { api, ApiError } from '@/lib/api';
import type { Portfolio, PortfolioSnapshot } from '@/lib/types';

const HISTORY_POLL_MS = 30_000;
const PORTFOLIO_REFRESH_MS = 15_000;

export default function Home() {
  const { prices, history, status, lastUpdate } = usePriceStream();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [watchlistRefreshSignal, setWatchlistRefreshSignal] = useState(0);
  const { toasts, push, dismiss } = useToasts();

  const fetchPortfolio = useCallback(async () => {
    try {
      const p = await api.getPortfolio();
      setPortfolio(p);
    } catch (e) {
      if (e instanceof ApiError) push('error', e.message);
      else push('error', 'Backend unreachable');
    }
  }, [push]);

  const fetchHistory = useCallback(async () => {
    try {
      const h = await api.getPortfolioHistory(240);
      setSnapshots(h.snapshots);
    } catch {
      // Non-critical; the P&L chart shows a placeholder when empty.
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
    fetchHistory();
    const portfolioTimer = window.setInterval(fetchPortfolio, PORTFOLIO_REFRESH_MS);
    const historyTimer = window.setInterval(fetchHistory, HISTORY_POLL_MS);
    return () => {
      window.clearInterval(portfolioTimer);
      window.clearInterval(historyTimer);
    };
  }, [fetchPortfolio, fetchHistory]);

  // Default the focused ticker to the first symbol once the tape starts.
  useEffect(() => {
    if (selected) return;
    const first = Object.keys(prices).sort()[0];
    if (first) setSelected(first);
  }, [prices, selected]);

  const tickerCount = Object.keys(prices).length;

  return (
    <div className="relative z-10 flex h-screen flex-col">
      <Header
        totalValue={portfolio?.total_value ?? null}
        cashBalance={portfolio?.cash_balance ?? null}
        status={status}
        asOf={lastUpdate}
      />

      <main className="grid min-h-0 flex-1 grid-cols-12 grid-rows-[minmax(0,1.1fr)_minmax(0,1fr)] gap-3 p-3">
        <Panel
          title="Watchlist"
          badge="LIVE"
          className="col-span-3 row-span-2"
          bodyClassName="overflow-hidden"
        >
          <Watchlist
            prices={prices}
            history={history}
            selected={selected}
            onSelect={(t) => setSelected(t || null)}
            refreshSignal={watchlistRefreshSignal}
          />
        </Panel>

        <Panel
          title="Chart"
          badge={selected ?? '—'}
          className="col-span-6"
          bodyClassName="overflow-hidden"
        >
          <MainChart
            ticker={selected}
            series={selected ? history[selected] ?? [] : []}
            latest={selected ? prices[selected] ?? null : null}
          />
        </Panel>

        <Panel
          title="Trade"
          badge="MKT"
          className="col-span-3"
          bodyClassName="overflow-hidden"
        >
          <TradeBar
            selected={selected}
            prices={prices}
            onTraded={(p) => {
              setPortfolio(p);
              fetchHistory();
            }}
            onError={(msg) => push('error', msg)}
            onSuccess={(msg) => push('success', msg)}
          />
        </Panel>

        <Panel title="Heatmap" badge="P&amp;L" className="col-span-3" bodyClassName="overflow-hidden p-2">
          <Heatmap
            positions={portfolio?.positions ?? []}
            totalMarketValue={portfolio?.total_market_value ?? 0}
            selected={selected}
            onSelect={setSelected}
          />
        </Panel>

        <Panel
          title="P&amp;L"
          badge={
            portfolio
              ? portfolio.total_unrealized_pnl >= 0
                ? `+${portfolio.total_unrealized_pnl.toFixed(2)}`
                : portfolio.total_unrealized_pnl.toFixed(2)
              : '—'
          }
          className="col-span-3"
          bodyClassName="overflow-hidden p-2"
        >
          <PnlChart snapshots={snapshots} />
        </Panel>

        <Panel
          title="Positions"
          badge={portfolio ? String(portfolio.positions.length) : '—'}
          className="col-span-6"
          bodyClassName="overflow-hidden"
        >
          <PositionsTable
            positions={portfolio?.positions ?? []}
            prices={prices}
            selected={selected}
            onSelect={setSelected}
          />
        </Panel>
      </main>

      <footer className="border-t border-edge px-5 py-2 font-mono text-[10px] uppercase tracking-wider2 text-ink-mute">
        <span>FINALLY · v0.1 · simulated · </span>
        <span>{tickerCount} symbols on tape</span>
      </footer>

      <ChatPanel
        open={chatOpen}
        onToggle={() => setChatOpen((o) => !o)}
        onActionsCommitted={(kinds) => {
          if (kinds.trades) {
            fetchPortfolio();
            fetchHistory();
          }
          if (kinds.watchlist) {
            setWatchlistRefreshSignal((n) => n + 1);
          }
        }}
      />

      <ToastStack toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
