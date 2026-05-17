'use client';

import { useEffect, useRef, useState } from 'react';
import { getPrice, subscribe, type PriceUpdate } from '@/lib/priceStore';

type Flash = 'up' | 'down' | null;

type Props = { ticker: string };

export default function TickerTile({ ticker }: Props) {
  const [price, setPriceState] = useState<PriceUpdate | undefined>(() =>
    getPrice(ticker),
  );
  const [flash, setFlash] = useState<Flash>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const unsubscribe = subscribe(ticker, (update) => {
      setPriceState(update);
      if (update.direction === 'up' || update.direction === 'down') {
        setFlash(update.direction);
        if (timerRef.current !== null) {
          clearTimeout(timerRef.current);
        }
        timerRef.current = setTimeout(() => {
          setFlash(null);
          timerRef.current = null;
        }, 500);
      }
    });
    return () => {
      unsubscribe();
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [ticker]);

  const flashClass =
    flash === 'up'
      ? 'bg-flash-up'
      : flash === 'down'
        ? 'bg-flash-down'
        : 'bg-bg-elevated';

  const changeColor = price
    ? price.direction === 'up'
      ? 'text-green-400'
      : price.direction === 'down'
        ? 'text-red-400'
        : 'text-zinc-500'
    : 'text-zinc-500';

  const formattedTimestamp = price
    ? new Date(price.timestamp * 1000).toLocaleTimeString()
    : '—';

  return (
    <div
      data-testid="ticker-tile"
      className={`rounded-md border border-zinc-800 p-4 w-64 transition-colors duration-flash flex flex-col gap-1 ${flashClass}`}
    >
      <div className="flex items-baseline justify-between">
        <span className="text-accent text-lg font-bold">{ticker}</span>
        <span className="text-zinc-500 text-xs">{formattedTimestamp}</span>
      </div>
      <div className="text-3xl font-mono tabular-nums">
        {price ? `$${price.price.toFixed(2)}` : '—'}
      </div>
      <div className={`text-sm ${changeColor}`}>
        {price
          ? `${price.change >= 0 ? '+' : ''}${price.change.toFixed(2)} (${price.change_percent.toFixed(2)}%)`
          : 'connecting…'}
      </div>
    </div>
  );
}
