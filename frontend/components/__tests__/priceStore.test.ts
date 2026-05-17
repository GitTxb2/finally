import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  __resetForTests,
  getPrice,
  setPrice,
  subscribe,
  type PriceUpdate,
} from '@/lib/priceStore';

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

describe('priceStore', () => {
  afterEach(() => {
    __resetForTests();
  });

  it('round-trips a single ticker via setPrice + getPrice', () => {
    const update = sample();
    setPrice(update);
    expect(getPrice('AAPL')).toEqual(update);
  });

  it('fires only the matching ticker subscribers on setPrice', () => {
    const aaplFn = vi.fn();
    const msftFn = vi.fn();
    subscribe('AAPL', aaplFn);
    subscribe('MSFT', msftFn);

    setPrice(sample({ ticker: 'AAPL' }));

    expect(aaplFn).toHaveBeenCalledTimes(1);
    expect(msftFn).not.toHaveBeenCalled();
  });

  it('unsubscribe stops further notifications', () => {
    const fn = vi.fn();
    const unsub = subscribe('AAPL', fn);
    setPrice(sample());
    expect(fn).toHaveBeenCalledTimes(1);
    unsub();
    setPrice(sample({ price: 192.0 }));
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('__resetForTests clears both prices and subscribers', () => {
    const fn = vi.fn();
    subscribe('AAPL', fn);
    setPrice(sample());
    expect(getPrice('AAPL')).toBeDefined();

    __resetForTests();

    expect(getPrice('AAPL')).toBeUndefined();
    setPrice(sample());
    expect(fn).toHaveBeenCalledTimes(1); // call before reset; never again
  });
});
