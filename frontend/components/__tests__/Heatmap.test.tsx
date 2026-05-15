import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Heatmap } from '../Heatmap';
import type { Position } from '@/lib/types';

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeEach(() => {
  // jsdom doesn't ship ResizeObserver — stub it so Heatmap mounts.
  (globalThis as { ResizeObserver: unknown }).ResizeObserver = ResizeObserverStub;
});

afterEach(() => {
  vi.restoreAllMocks();
});

const positions: Position[] = [
  {
    ticker: 'AAPL',
    quantity: 3,
    avg_cost: 200,
    current_price: 205,
    market_value: 600,
    unrealized_pnl: 15,
    unrealized_pnl_pct: 2.5,
  },
  {
    ticker: 'NFLX',
    quantity: 1,
    avg_cost: 400,
    current_price: 380,
    market_value: 380,
    unrealized_pnl: -20,
    unrealized_pnl_pct: -5,
  },
];

describe('Heatmap', () => {
  it('renders a tile per position with positive market value', () => {
    render(
      <Heatmap
        positions={positions}
        totalMarketValue={980}
        selected={null}
        onSelect={() => {}}
      />,
    );
    expect(screen.getByTestId('heatmap-tile-AAPL')).toBeInTheDocument();
    expect(screen.getByTestId('heatmap-tile-NFLX')).toBeInTheDocument();
  });

  it('skips positions with null market value', () => {
    const partial: Position[] = [
      ...positions,
      {
        ticker: 'NEW',
        quantity: 0,
        avg_cost: 0,
        current_price: null,
        market_value: null,
        unrealized_pnl: null,
        unrealized_pnl_pct: null,
      },
    ];
    render(
      <Heatmap positions={partial} totalMarketValue={980} selected={null} onSelect={() => {}} />,
    );
    expect(screen.queryByTestId('heatmap-tile-NEW')).toBeNull();
  });

  it('renders the empty state when there are zero positions', () => {
    render(<Heatmap positions={[]} totalMarketValue={0} selected={null} onSelect={() => {}} />);
    expect(screen.getByText(/no positions to map/i)).toBeInTheDocument();
  });
});
