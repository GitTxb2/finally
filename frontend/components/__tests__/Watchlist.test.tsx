import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Watchlist } from '../Watchlist';
import { api } from '@/lib/api';
import type { PriceMap } from '@/lib/types';

vi.mock('@/lib/api', () => ({
  api: {
    getWatchlist: vi.fn(),
    addWatchlist: vi.fn(),
    removeWatchlist: vi.fn(),
  },
  ApiError: class extends Error {
    status = 0;
    body: unknown = null;
  },
}));

const mockedApi = vi.mocked(api);

function makePrices(rows: { ticker: string; price: number; change_percent: number }[]): PriceMap {
  return Object.fromEntries(
    rows.map((r) => [
      r.ticker,
      {
        ticker: r.ticker,
        price: r.price,
        previous_price: r.price,
        timestamp: 0,
        change: 0,
        change_percent: r.change_percent,
        direction: 'flat' as const,
      },
    ]),
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Watchlist', () => {
  it('renders rows returned from /api/watchlist with live prices and remove buttons', async () => {
    mockedApi.getWatchlist.mockResolvedValue([
      { ticker: 'AAPL', price: 190.5 },
      { ticker: 'GOOGL', price: 175.0 },
    ]);
    render(
      <Watchlist
        prices={makePrices([
          { ticker: 'AAPL', price: 190.5, change_percent: 0.4 },
          { ticker: 'GOOGL', price: 175.0, change_percent: -1.2 },
        ])}
        history={{}}
        selected={null}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByTestId('watchlist-row-AAPL')).toBeInTheDocument();
      expect(screen.getByTestId('watchlist-row-GOOGL')).toBeInTheDocument();
    });
    expect(screen.getByTestId('watchlist-price-AAPL')).toHaveTextContent('190.50');
    expect(screen.getByTestId('watchlist-remove-AAPL')).toBeInTheDocument();
  });

  it('selects a ticker when its row is clicked', async () => {
    mockedApi.getWatchlist.mockResolvedValue([{ ticker: 'AAPL', price: 190.5 }]);
    const onSelect = vi.fn();
    render(
      <Watchlist
        prices={makePrices([{ ticker: 'AAPL', price: 190.5, change_percent: 0 }])}
        history={{}}
        selected={null}
        onSelect={onSelect}
      />,
    );
    const row = await screen.findByTestId('watchlist-row-AAPL');
    await userEvent.click(row);
    expect(onSelect).toHaveBeenCalledWith('AAPL');
  });

  it('adds a new ticker via the add form', async () => {
    mockedApi.getWatchlist.mockResolvedValue([{ ticker: 'AAPL', price: 190.5 }]);
    mockedApi.addWatchlist.mockResolvedValue({ ticker: 'PYPL', status: 'added' });
    render(
      <Watchlist
        prices={makePrices([{ ticker: 'AAPL', price: 190.5, change_percent: 0 }])}
        history={{}}
        selected={null}
        onSelect={() => {}}
      />,
    );
    await screen.findByTestId('watchlist-row-AAPL');

    const input = screen.getByTestId('watchlist-add-input');
    await userEvent.type(input, 'pypl');
    await userEvent.click(screen.getByTestId('watchlist-add-button'));

    await waitFor(() => {
      expect(mockedApi.addWatchlist).toHaveBeenCalledWith('PYPL');
      expect(screen.getByTestId('watchlist-row-PYPL')).toBeInTheDocument();
    });
  });

  it('refetches the watchlist when refreshSignal changes', async () => {
    mockedApi.getWatchlist
      .mockResolvedValueOnce([{ ticker: 'AAPL', price: 190.5 }])
      .mockResolvedValueOnce([
        { ticker: 'AAPL', price: 190.5 },
        { ticker: 'PYPL', price: 65 },
      ]);

    const { rerender } = render(
      <Watchlist
        prices={makePrices([{ ticker: 'AAPL', price: 190.5, change_percent: 0 }])}
        history={{}}
        selected={null}
        onSelect={() => {}}
        refreshSignal={0}
      />,
    );
    await screen.findByTestId('watchlist-row-AAPL');
    expect(screen.queryByTestId('watchlist-row-PYPL')).toBeNull();

    rerender(
      <Watchlist
        prices={makePrices([
          { ticker: 'AAPL', price: 190.5, change_percent: 0 },
          { ticker: 'PYPL', price: 65, change_percent: 0 },
        ])}
        history={{}}
        selected={null}
        onSelect={() => {}}
        refreshSignal={1}
      />,
    );
    await waitFor(() => {
      expect(mockedApi.getWatchlist).toHaveBeenCalledTimes(2);
      expect(screen.getByTestId('watchlist-row-PYPL')).toBeInTheDocument();
    });
  });

  it('removes a ticker when its remove button is clicked', async () => {
    mockedApi.getWatchlist.mockResolvedValue([
      { ticker: 'AAPL', price: 190.5 },
      { ticker: 'GOOGL', price: 175.0 },
    ]);
    mockedApi.removeWatchlist.mockResolvedValue({ ticker: 'GOOGL', status: 'removed' });
    render(
      <Watchlist
        prices={makePrices([
          { ticker: 'AAPL', price: 190.5, change_percent: 0 },
          { ticker: 'GOOGL', price: 175.0, change_percent: 0 },
        ])}
        history={{}}
        selected={null}
        onSelect={() => {}}
      />,
    );
    await screen.findByTestId('watchlist-row-GOOGL');

    await userEvent.click(screen.getByTestId('watchlist-remove-GOOGL'));

    await waitFor(() => {
      expect(mockedApi.removeWatchlist).toHaveBeenCalledWith('GOOGL');
      expect(screen.queryByTestId('watchlist-row-GOOGL')).toBeNull();
    });
    expect(screen.getByTestId('watchlist-row-AAPL')).toBeInTheDocument();
  });
});
