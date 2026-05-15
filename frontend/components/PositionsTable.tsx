'use client';

import { FlashCell } from './FlashCell';
import { fmtPrice, fmtPct, fmtSignedUSD, fmtQty } from '@/lib/format';
import type { PriceMap, Position } from '@/lib/types';

interface PositionsTableProps {
  positions: Position[];
  prices: PriceMap;
  selected: string | null;
  onSelect: (ticker: string) => void;
}

export function PositionsTable({ positions, prices, selected, onSelect }: PositionsTableProps) {
  if (positions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4 font-mono text-[11px] uppercase tracking-wider2 text-ink-mute">
        No positions yet — buy something
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <table className="w-full font-mono text-[11px] tabular">
        <thead className="sticky top-0 bg-bg-panel/95 text-[9px] uppercase tracking-wider3 text-ink-mute">
          <tr className="border-b border-edge">
            <th className="px-3 py-1.5 text-left">Sym</th>
            <th className="px-3 py-1.5 text-right">Qty</th>
            <th className="px-3 py-1.5 text-right">Avg</th>
            <th className="px-3 py-1.5 text-right">Last</th>
            <th className="px-3 py-1.5 text-right">P&amp;L</th>
            <th className="px-3 py-1.5 text-right">%</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => {
            const live = prices[p.ticker]?.price ?? p.current_price;
            const positive = (p.unrealized_pnl ?? 0) > 0;
            const negative = (p.unrealized_pnl ?? 0) < 0;
            const isSelected = selected === p.ticker;
            return (
              <tr
                key={p.ticker}
                data-testid={`position-row-${p.ticker}`}
                onClick={() => onSelect(p.ticker)}
                className={`cursor-pointer border-b border-edge/40 transition-colors ${
                  isSelected ? 'bg-accent-yellow/[0.06]' : 'hover:bg-bg-raised/60'
                }`}
              >
                <td className="px-3 py-1.5 text-left text-ink">{p.ticker}</td>
                <td className="px-3 py-1.5 text-right text-ink-dim">{fmtQty(p.quantity)}</td>
                <td className="px-3 py-1.5 text-right text-ink-dim">${fmtPrice(p.avg_cost)}</td>
                <td className="px-3 py-1.5 text-right">
                  <FlashCell
                    value={live ?? null}
                    format={(n) => `$${fmtPrice(n)}`}
                    className="text-ink"
                  />
                </td>
                <td
                  className={`px-3 py-1.5 text-right ${
                    positive ? 'text-tape-up' : negative ? 'text-tape-down' : 'text-ink-dim'
                  }`}
                >
                  {p.unrealized_pnl == null ? '—' : fmtSignedUSD(p.unrealized_pnl)}
                </td>
                <td
                  className={`px-3 py-1.5 text-right ${
                    positive ? 'text-tape-up' : negative ? 'text-tape-down' : 'text-ink-dim'
                  }`}
                >
                  {p.unrealized_pnl_pct == null ? '—' : fmtPct(p.unrealized_pnl_pct)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
