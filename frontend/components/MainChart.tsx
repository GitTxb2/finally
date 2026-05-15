'use client';

import { useMemo } from 'react';
import { fmtPrice, fmtPct } from '@/lib/format';
import type { PriceUpdate } from '@/lib/types';

interface MainChartProps {
  ticker: string | null;
  series: number[];
  latest: PriceUpdate | null;
}

const DIMS = { w: 720, h: 240, pad: 24 };

/**
 * Larger price chart for the focused ticker. Renders an inline SVG
 * area+line over the in-memory price history accumulated by
 * usePriceStream. No external charting library — keeps the bundle
 * small and the look pixel-accurate to the terminal aesthetic.
 */
export function MainChart({ ticker, series, latest }: MainChartProps) {
  const dims = DIMS;

  const path = useMemo(() => {
    if (!series || series.length < 2) return null;
    const min = Math.min(...series);
    const max = Math.max(...series);
    const range = max - min || 1;
    const innerW = DIMS.w - DIMS.pad * 2;
    const innerH = DIMS.h - DIMS.pad * 2;
    const step = innerW / (series.length - 1);

    const pts = series.map((v, i) => {
      const x = DIMS.pad + i * step;
      const y = DIMS.pad + innerH - ((v - min) / range) * innerH;
      return [x, y] as const;
    });
    const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
    const last = pts[pts.length - 1];
    const area = `${line} L${last[0].toFixed(2)},${(DIMS.h - DIMS.pad).toFixed(2)} L${DIMS.pad},${(
      DIMS.h - DIMS.pad
    ).toFixed(2)} Z`;
    return { line, area, min, max, lastX: last[0], lastY: last[1] };
  }, [series]);

  const netUp = (latest?.change ?? 0) >= 0;
  const stroke = !latest ? '#9aa4b2' : netUp ? '#3ddc97' : '#ff5f6d';
  const fill = !latest
    ? 'rgba(154,164,178,0.06)'
    : netUp
      ? 'rgba(61,220,151,0.10)'
      : 'rgba(255,95,109,0.10)';

  return (
    <div
      data-testid="main-chart"
      data-ticker={ticker ?? 'none'}
      className="flex h-full min-h-0 flex-col"
    >
      <div className="flex items-center justify-between border-b border-edge px-3 py-2">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-base font-semibold tracking-wider2 text-ink">
            {ticker ?? '— SELECT A TICKER —'}
          </span>
          {latest ? (
            <span className="tabular font-mono text-[12px] text-ink-dim">
              ${fmtPrice(latest.price)}
            </span>
          ) : null}
        </div>
        {latest ? (
          <div
            className={`tabular font-mono text-[12px] ${
              netUp ? 'text-tape-up' : 'text-tape-down'
            }`}
          >
            {fmtPct(latest.change_percent)}
          </div>
        ) : null}
      </div>

      <div className="relative min-h-0 flex-1 p-3">
        <svg
          viewBox={`0 0 ${dims.w} ${dims.h}`}
          preserveAspectRatio="none"
          className="h-full w-full"
          aria-label={ticker ? `${ticker} price chart` : 'Price chart placeholder'}
          role="img"
        >
          <defs>
            <pattern id="mainGrid" width="60" height="40" patternUnits="userSpaceOnUse">
              <path d="M60 0 L0 0 0 40" fill="none" stroke="#1f2630" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect x="0" y="0" width={dims.w} height={dims.h} fill="url(#mainGrid)" />

          {path ? (
            <>
              <path d={path.area} fill={fill} stroke="none" />
              <path
                d={path.line}
                fill="none"
                stroke={stroke}
                strokeWidth="1.5"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              <line
                x1={path.lastX}
                y1={dims.pad}
                x2={path.lastX}
                y2={dims.h - dims.pad}
                stroke={stroke}
                strokeOpacity="0.25"
                strokeDasharray="2 4"
              />
              <circle cx={path.lastX} cy={path.lastY} r="3" fill={stroke} />
              <text
                x={dims.w - dims.pad}
                y={dims.pad - 6}
                textAnchor="end"
                fill="#6b7585"
                className="text-[10px]"
                fontFamily="var(--font-mono), monospace"
              >
                MAX {fmtPrice(path.max)}
              </text>
              <text
                x={dims.w - dims.pad}
                y={dims.h - dims.pad + 14}
                textAnchor="end"
                fill="#6b7585"
                className="text-[10px]"
                fontFamily="var(--font-mono), monospace"
              >
                MIN {fmtPrice(path.min)}
              </text>
            </>
          ) : (
            <text
              x={dims.w / 2}
              y={dims.h / 2}
              textAnchor="middle"
              fill="#4b5563"
              className="text-[12px]"
              fontFamily="var(--font-mono), monospace"
            >
              {ticker ? 'AWAITING TAPE…' : 'CLICK A TICKER IN THE WATCHLIST'}
            </text>
          )}
        </svg>
      </div>
    </div>
  );
}
