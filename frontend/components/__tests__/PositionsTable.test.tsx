import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { PositionsTable } from '../PositionsTable';
import type { Position } from '@/lib/types';

const positions: Position[] = [
  {
    ticker: 'AAPL',
    quantity: 3,
    avg_cost: 200,
    current_price: 205,
    market_value: 615,
    unrealized_pnl: 15,
    unrealized_pnl_pct: 2.5,
  },
  {
    ticker: 'NFLX',
    quantity: 1.5,
    avg_cost: 400,
    current_price: 380,
    market_value: 570,
    unrealized_pnl: -30,
    unrealized_pnl_pct: -5,
  },
];

describe('PositionsTable', () => {
  it('renders an empty state when there are no positions', () => {
    render(<PositionsTable positions={[]} prices={{}} selected={null} onSelect={() => {}} />);
    expect(screen.getByText(/no positions yet/i)).toBeInTheDocument();
  });

  it('renders each position row with formatted values', () => {
    render(<PositionsTable positions={positions} prices={{}} selected={null} onSelect={() => {}} />);
    const row = screen.getByTestId('position-row-AAPL');
    expect(row).toHaveTextContent('AAPL');
    // qty column: 3 (whole), then avg cost $200.00, then last $205.00
    expect(row.textContent).toMatch(/AAPL3\$200/);
    expect(row).toHaveTextContent('+$15.00');
    expect(row).toHaveTextContent('+2.50%');
    const nflxRow = screen.getByTestId('position-row-NFLX');
    expect(nflxRow.textContent).toMatch(/NFLX1\.5\$400/); // fractional qty
    expect(nflxRow).toHaveTextContent('−$30.00');
    expect(nflxRow).toHaveTextContent('-5.00%');
  });

  it('invokes onSelect when a row is clicked', async () => {
    const onSelect = vi.fn();
    render(<PositionsTable positions={positions} prices={{}} selected={null} onSelect={onSelect} />);
    await userEvent.click(screen.getByTestId('position-row-NFLX'));
    expect(onSelect).toHaveBeenCalledWith('NFLX');
  });
});
