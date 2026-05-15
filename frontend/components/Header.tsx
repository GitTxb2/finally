'use client';

import { ConnectionDot } from './ConnectionDot';
import { fmtUSD } from '@/lib/format';
import type { ConnectionState } from '@/lib/types';

interface HeaderProps {
  totalValue: number | null;
  cashBalance: number | null;
  status: ConnectionState;
  asOf: number;
}

export function Header({ totalValue, cashBalance, status, asOf }: HeaderProps) {
  const time = asOf ? new Date(asOf) : new Date();
  const timeStr = time.toLocaleTimeString('en-US', { hour12: false });

  return (
    <header className="relative border-b border-edge bg-bg-base/80 backdrop-blur supports-[backdrop-filter]:bg-bg-base/60">
      <div className="accent-stripe" />
      <div className="flex items-center justify-between gap-6 px-5 py-3">
        <div className="flex items-center gap-5">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-lg font-semibold tracking-wider2 text-ink">
              FIN<span className="text-accent-yellow">/</span>ALLY
            </span>
            <span className="font-mono text-[10px] uppercase tracking-wider3 text-ink-mute">
              Trading Workstation
            </span>
          </div>
          <div className="hidden h-6 w-px bg-edge md:block" />
          <div className="hidden font-mono text-[10px] uppercase tracking-wider2 text-ink-mute md:block">
            <span className="text-ink-dim">{timeStr}</span>
            <span className="mx-2 text-ink-ghost">·</span>
            <span>SIM · US EQUITIES</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <Stat label="Portfolio" value={totalValue} accent testId="portfolio-total" />
          <Stat label="Cash" value={cashBalance} testId="cash-balance" />
          <ConnectionDot status={status} />
        </div>
      </div>
    </header>
  );
}

function Stat({
  label,
  value,
  accent = false,
  testId,
}: {
  label: string;
  value: number | null;
  accent?: boolean;
  testId?: string;
}) {
  return (
    <div className="flex flex-col items-end leading-tight">
      <span className="font-mono text-[9px] uppercase tracking-wider3 text-ink-mute">{label}</span>
      <span
        data-testid={testId}
        className={`tabular font-mono text-base font-semibold ${accent ? 'text-accent-yellow' : 'text-ink'}`}
      >
        {value == null ? '—' : fmtUSD(value)}
      </span>
    </div>
  );
}
