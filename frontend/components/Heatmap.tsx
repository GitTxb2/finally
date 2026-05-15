'use client';

import { useMemo, useRef, useEffect, useState } from 'react';
import { squarify } from '@/lib/treemap';
import { fmtPct } from '@/lib/format';
import type { Position } from '@/lib/types';

interface HeatmapProps {
  positions: Position[];
  totalMarketValue: number;
  selected: string | null;
  onSelect: (ticker: string) => void;
}

/**
 * Treemap of portfolio positions. Each tile is sized by market_value
 * (weight in the portfolio) and tinted by unrealized P&L %. Positions
 * with null market value (no cached price) are excluded — they
 * contribute 0 to total_market_value on the backend anyway.
 */
export function Heatmap({ positions, totalMarketValue, selected, onSelect }: HeatmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 320, h: 160 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const rect = entry.contentRect;
        setDims({ w: Math.max(1, rect.width), h: Math.max(1, rect.height) });
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const tiles = useMemo(() => {
    const items = positions
      .filter((p): p is Position & { market_value: number } => (p.market_value ?? 0) > 0)
      .map((p) => ({ data: p, value: p.market_value }));
    return squarify(items, dims.w, dims.h);
  }, [positions, dims]);

  if (positions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4 font-mono text-[11px] uppercase tracking-wider2 text-ink-mute">
        No positions to map
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden">
      {tiles.map((tile) => {
        const pos = tile.data;
        const pct = pos.unrealized_pnl_pct ?? 0;
        const intensity = Math.min(1, Math.abs(pct) / 5); // 5% = full saturation
        const isUp = pct >= 0;
        const bg = isUp
          ? `rgba(61, 220, 151, ${0.08 + intensity * 0.5})`
          : `rgba(255, 95, 109, ${0.08 + intensity * 0.5})`;
        const border = isUp ? 'rgba(61, 220, 151, 0.45)' : 'rgba(255, 95, 109, 0.45)';
        const isSelected = selected === pos.ticker;
        const minTextW = 48;
        const minTextH = 28;
        return (
          <button
            key={pos.ticker}
            data-testid={`heatmap-tile-${pos.ticker}`}
            onClick={() => onSelect(pos.ticker)}
            title={`${pos.ticker} · ${fmtPct(pct)} · ${((pos.market_value! / Math.max(1, totalMarketValue)) * 100).toFixed(1)}%`}
            style={{
              position: 'absolute',
              left: tile.x,
              top: tile.y,
              width: tile.w,
              height: tile.h,
              background: bg,
              border: `1px solid ${isSelected ? '#ecad0a' : border}`,
              outline: isSelected ? '1px solid #ecad0a' : 'none',
            }}
            className="overflow-hidden text-left transition-opacity hover:opacity-90"
          >
            {tile.w >= minTextW && tile.h >= minTextH ? (
              <div className="flex h-full flex-col justify-between p-1.5 font-mono leading-tight">
                <span className="text-[11px] font-semibold tracking-wider2 text-ink">{pos.ticker}</span>
                <span
                  className={`tabular text-[10px] ${
                    isUp ? 'text-tape-up' : 'text-tape-down'
                  }`}
                >
                  {fmtPct(pct)}
                </span>
              </div>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
