import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import TickerTile from '@/components/TickerTile';
import { __resetForTests, setPrice, type PriceUpdate } from '@/lib/priceStore';

const sample = (overrides: Partial<PriceUpdate> = {}): PriceUpdate => ({
  ticker: 'AAPL',
  price: 191.23,
  previous_price: 190.1,
  timestamp: 1778994753.63,
  change: 1.13,
  change_percent: 0.5944,
  direction: 'up',
  ...overrides,
});

describe('TickerTile', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    __resetForTests();
  });

  afterEach(() => {
    vi.useRealTimers();
    __resetForTests();
  });

  it('renders ticker symbol and connecting state when no price is set', () => {
    render(<TickerTile ticker="AAPL" />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('connecting…')).toBeInTheDocument();
  });

  it('renders the formatted price after setPrice', () => {
    render(<TickerTile ticker="AAPL" />);
    act(() => {
      setPrice(sample());
    });
    expect(screen.getByText('$191.23')).toBeInTheDocument();
    expect(screen.getByText(/\+1\.13 \(0\.59%\)/)).toBeInTheDocument();
  });

  it('applies bg-flash-up when direction is up and removes it after 500ms', () => {
    render(<TickerTile ticker="AAPL" />);
    act(() => {
      setPrice(sample({ direction: 'up' }));
    });
    const tile = screen.getByTestId('ticker-tile');
    expect(tile.className).toContain('bg-flash-up');

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(tile.className).not.toContain('bg-flash-up');
  });

  it('applies bg-flash-down when direction is down and removes it after 500ms', () => {
    render(<TickerTile ticker="AAPL" />);
    act(() => {
      setPrice(sample({ direction: 'down', price: 189.0, change: -1.1 }));
    });
    const tile = screen.getByTestId('ticker-tile');
    expect(tile.className).toContain('bg-flash-down');

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(tile.className).not.toContain('bg-flash-down');
  });
});
