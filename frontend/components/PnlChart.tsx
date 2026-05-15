'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import { fmtUSD } from '@/lib/format';
import type { PortfolioSnapshot } from '@/lib/types';

interface PnlChartProps {
  snapshots: PortfolioSnapshot[];
}

/**
 * Inline-SVG line chart of total portfolio value over time. Auto-fits
 * the chart to its container via ResizeObserver. Color toggles based on
 * net direction (first → last snapshot).
 */
export function PnlChart({ snapshots }: PnlChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 320, h: 140 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const r = entry.contentRect;
        setDims({ w: Math.max(60, r.width), h: Math.max(60, r.height) });
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const layout = useMemo(() => {
    if (snapshots.length < 2) return null;
    const pad = 16;
    const innerW = dims.w - pad * 2;
    const innerH = dims.h - pad * 2;
    const values = snapshots.map((s) => s.total_value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const step = innerW / (snapshots.length - 1);
    const pts = snapshots.map((s, i) => {
      const x = pad + i * step;
      const y = pad + innerH - ((s.total_value - min) / range) * innerH;
      return [x, y, s.total_value] as const;
    });
    const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
    const last = pts[pts.length - 1];
    const area = `${line} L${last[0].toFixed(2)},${(dims.h - pad).toFixed(2)} L${pad.toFixed(2)},${(
      dims.h - pad
    ).toFixed(2)} Z`;
    return { pts, line, area, min, max, last, pad };
  }, [snapshots, dims]);

  const net = snapshots.length >= 2 ? snapshots[snapshots.length - 1].total_value - snapshots[0].total_value : 0;
  const isUp = net >= 0;
  const stroke = isUp ? '#3ddc97' : '#ff5f6d';
  const fill = isUp ? 'rgba(61,220,151,0.10)' : 'rgba(255,95,109,0.10)';

  return (
    <div ref={ref} data-testid="pnl-chart" className="relative h-full w-full">
      {layout ? (
        <svg
          width={dims.w}
          height={dims.h}
          viewBox={`0 0 ${dims.w} ${dims.h}`}
          aria-label="Portfolio value over time"
          role="img"
        >
          <path d={layout.area} fill={fill} stroke="none" />
          <path
            d={layout.line}
            fill="none"
            stroke={stroke}
            strokeWidth="1.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {layout.pts.length > 0 ? (
            <circle cx={layout.last[0]} cy={layout.last[1]} r="3" fill={stroke} />
          ) : null}
          <text
            x={dims.w - 8}
            y={14}
            textAnchor="end"
            fill="#9aa4b2"
            className="text-[10px]"
            fontFamily="var(--font-mono), monospace"
          >
            {fmtUSD(layout.max)}
          </text>
          <text
            x={dims.w - 8}
            y={dims.h - 6}
            textAnchor="end"
            fill="#9aa4b2"
            className="text-[10px]"
            fontFamily="var(--font-mono), monospace"
          >
            {fmtUSD(layout.min)}
          </text>
        </svg>
      ) : (
        <div className="flex h-full items-center justify-center font-mono text-[11px] uppercase tracking-wider2 text-ink-mute">
          Accumulating snapshots…
        </div>
      )}
    </div>
  );
}
