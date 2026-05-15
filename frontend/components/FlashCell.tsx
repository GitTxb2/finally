'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import type { Direction } from '@/lib/types';

interface FlashCellProps {
  value: number | null | undefined;
  format: (n: number) => string;
  className?: string;
  testId?: string;
  /** When provided, overrides direction inference from value diffs. */
  direction?: Direction;
  children?: ReactNode;
}

/**
 * Wraps a numeric value and briefly applies a green/red flash animation
 * when the value changes. Uses `key`-based re-mounting on each tick so
 * the CSS animation always replays cleanly without manual cleanup.
 */
export function FlashCell({ value, format, className = '', testId, direction, children }: FlashCellProps) {
  const previousRef = useRef<number | null>(null);
  const [flashKey, setFlashKey] = useState(0);
  const [tone, setTone] = useState<Direction | null>(null);

  useEffect(() => {
    if (value == null || !Number.isFinite(value)) return;
    const prev = previousRef.current;
    if (prev == null) {
      previousRef.current = value;
      return;
    }
    if (value === prev) return;
    const inferred: Direction = direction ?? (value > prev ? 'up' : 'down');
    setTone(inferred);
    setFlashKey((k) => k + 1);
    previousRef.current = value;
  }, [value, direction]);

  const flashClass =
    tone === 'up' ? 'animate-flash-up' : tone === 'down' ? 'animate-flash-down' : '';

  return (
    <span
      key={flashKey}
      data-testid={testId}
      data-direction={tone ?? 'flat'}
      className={`inline-block rounded-sm px-1 ${flashClass} ${className}`}
    >
      {children ?? (value == null || !Number.isFinite(value) ? '—' : format(value))}
    </span>
  );
}
