'use client';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  className?: string;
}

/**
 * Lightweight inline SVG sparkline. Accumulates from the SSE history
 * buffer in `usePriceStream`. Color is derived from net direction of
 * the window (first → last), not the last tick — keeps it stable.
 */
export function Sparkline({ data, width = 88, height = 24, className = '' }: SparklineProps) {
  if (!data || data.length < 2) {
    return (
      <svg width={width} height={height} className={className} aria-hidden="true">
        <line
          x1="0"
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="#2a323e"
          strokeWidth="1"
          strokeDasharray="2 3"
        />
      </svg>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = data.length > 1 ? width / (data.length - 1) : 0;

  const pts = data.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * (height - 2) - 1;
    return [x, y] as const;
  });

  const d = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
  const areaD = `${d} L${pts[pts.length - 1][0].toFixed(2)},${height} L0,${height} Z`;

  const net = data[data.length - 1] - data[0];
  const stroke = net > 0 ? '#3ddc97' : net < 0 ? '#ff5f6d' : '#9aa4b2';
  const fill = net > 0 ? 'rgba(61,220,151,0.10)' : net < 0 ? 'rgba(255,95,109,0.10)' : 'rgba(154,164,178,0.08)';

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      aria-hidden="true"
    >
      <path d={areaD} fill={fill} stroke="none" />
      <path d={d} fill="none" stroke={stroke} strokeWidth="1.25" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
