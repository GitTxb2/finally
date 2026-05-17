'use client';

import { useEventStream } from '@/lib/useEventStream';
import TickerTile from './TickerTile';

export default function AppShell() {
  const { connected } = useEventStream();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-12 bg-bg-elevated border-b border-zinc-800 flex items-center px-4">
        <span className="text-accent font-bold tracking-wide">FinAlly</span>
        <span className="ml-auto text-xs text-zinc-500">
          {connected ? '● live' : '○ offline'}
        </span>
      </header>
      <main className="flex-1 p-6">
        <TickerTile ticker="AAPL" />
      </main>
    </div>
  );
}
