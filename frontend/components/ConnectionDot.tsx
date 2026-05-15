'use client';

import type { ConnectionState } from '@/lib/types';

const TONE: Record<ConnectionState, { color: string; label: string; pulse: boolean; state: string }> = {
  connecting: { color: '#ecad0a', label: 'CONNECTING', pulse: true, state: 'reconnecting' },
  connected: { color: '#3ddc97', label: 'LIVE', pulse: false, state: 'connected' },
  reconnecting: { color: '#ecad0a', label: 'RECONNECTING', pulse: true, state: 'reconnecting' },
  disconnected: { color: '#ff5f6d', label: 'OFFLINE', pulse: true, state: 'disconnected' },
};

export function ConnectionDot({ status }: { status: ConnectionState }) {
  const t = TONE[status];
  return (
    <div
      data-testid="connection-status"
      data-state={t.state}
      className="flex items-center gap-2 font-mono text-[10px] tracking-wider2 uppercase text-ink-dim"
    >
      <span
        className={`relative inline-block h-2 w-2 rounded-full ${t.pulse ? 'animate-pulse-dot' : ''}`}
        style={{ backgroundColor: t.color, boxShadow: `0 0 10px ${t.color}` }}
        aria-label={`Stream ${t.label.toLowerCase()}`}
      />
      <span>{t.label}</span>
    </div>
  );
}
