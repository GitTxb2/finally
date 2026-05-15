import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TradeBar } from '../TradeBar';
import { api, ApiError } from '@/lib/api';
import type { Portfolio, PriceMap } from '@/lib/types';

vi.mock('@/lib/api', () => {
  class ApiErrorMock extends Error {
    status: number;
    body: unknown;
    constructor(status: number, msg: string, body: unknown) {
      super(msg);
      this.status = status;
      this.body = body;
    }
  }
  return {
    api: { trade: vi.fn() },
    ApiError: ApiErrorMock,
  };
});

const mockedApi = vi.mocked(api);
const prices: PriceMap = {
  AAPL: {
    ticker: 'AAPL',
    price: 200,
    previous_price: 200,
    timestamp: 0,
    change: 0,
    change_percent: 0,
    direction: 'flat',
  },
};
const portfolioStub: Portfolio = {
  cash_balance: 9000,
  positions: [],
  total_market_value: 1000,
  total_value: 10000,
  total_unrealized_pnl: 0,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('TradeBar', () => {
  it('submits a buy with normalized ticker + parsed qty and lifts the new portfolio', async () => {
    mockedApi.trade.mockResolvedValue({
      trade: {
        id: '1',
        user_id: 'default',
        ticker: 'AAPL',
        side: 'buy',
        quantity: 2,
        price: 200,
        executed_at: 'now',
      },
      portfolio: portfolioStub,
    });
    const onTraded = vi.fn();
    const onSuccess = vi.fn();
    const onError = vi.fn();
    render(
      <TradeBar
        selected="AAPL"
        prices={prices}
        onTraded={onTraded}
        onError={onError}
        onSuccess={onSuccess}
      />,
    );
    await userEvent.clear(screen.getByTestId('trade-ticker-input'));
    await userEvent.type(screen.getByTestId('trade-ticker-input'), 'aapl');
    await userEvent.type(screen.getByTestId('trade-quantity-input'), '2');
    await userEvent.click(screen.getByTestId('trade-buy-button'));

    await waitFor(() => {
      expect(mockedApi.trade).toHaveBeenCalledWith({ ticker: 'AAPL', quantity: 2, side: 'buy' });
    });
    expect(onTraded).toHaveBeenCalledWith(portfolioStub);
    expect(onSuccess).toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it('reports a backend error via onError without lifting any portfolio', async () => {
    mockedApi.trade.mockRejectedValue(new ApiError(400, 'insufficient cash', {}));
    const onError = vi.fn();
    const onTraded = vi.fn();
    render(
      <TradeBar
        selected="AAPL"
        prices={prices}
        onTraded={onTraded}
        onError={onError}
        onSuccess={() => {}}
      />,
    );
    await userEvent.type(screen.getByTestId('trade-quantity-input'), '1000');
    await userEvent.click(screen.getByTestId('trade-buy-button'));

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('insufficient cash');
    });
    expect(onTraded).not.toHaveBeenCalled();
  });

  it('rejects non-positive quantities client-side without hitting the API', async () => {
    const onError = vi.fn();
    render(
      <TradeBar
        selected="AAPL"
        prices={prices}
        onTraded={() => {}}
        onError={onError}
        onSuccess={() => {}}
      />,
    );
    await userEvent.type(screen.getByTestId('trade-quantity-input'), '0');
    await userEvent.click(screen.getByTestId('trade-sell-button'));
    expect(mockedApi.trade).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith('Quantity must be > 0');
  });
});
