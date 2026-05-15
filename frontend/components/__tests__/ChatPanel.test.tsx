import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatPanel } from '../ChatPanel';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => {
  class ApiErrorMock extends Error {
    status = 0;
    body: unknown = null;
  }
  return {
    api: {
      sendChat: vi.fn(),
      getChatHistory: vi.fn().mockResolvedValue({ messages: [] }),
    },
    ApiError: ApiErrorMock,
  };
});

const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.clearAllMocks();
  mockedApi.getChatHistory.mockResolvedValue({ messages: [] });
});

describe('ChatPanel', () => {
  it('renders the toggle and reflects open/closed state via data-open', async () => {
    const { rerender } = render(
      <ChatPanel open={false} onToggle={() => {}} onActionsCommitted={() => {}} />,
    );
    // When closed: single chat-toggle, lives on the FAB, panel data-open="false".
    expect(screen.getAllByTestId('chat-toggle')).toHaveLength(1);
    expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-open', 'false');
    // Wait for the initial history fetch to settle before rerendering.
    await waitFor(() => expect(mockedApi.getChatHistory).toHaveBeenCalled());
    rerender(<ChatPanel open={true} onToggle={() => {}} onActionsCommitted={() => {}} />);
    // When open: single chat-toggle, lives in the panel header (FAB removed so
    // it cannot intercept clicks on chat-send). Panel data-open="true".
    expect(screen.getAllByTestId('chat-toggle')).toHaveLength(1);
    expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-open', 'true');
  });

  it('sends a message and renders the assistant reply with trade + watchlist chips', async () => {
    mockedApi.sendChat.mockResolvedValue({
      message: 'Bought 5 AAPL.',
      trades_executed: [
        {
          id: 't1',
          user_id: 'default',
          ticker: 'AAPL',
          side: 'buy',
          quantity: 5,
          price: 190.5,
          executed_at: 'now',
        },
      ],
      watchlist_changes: [{ ticker: 'PYPL', action: 'added' }],
      errors: [],
    });
    const onActionsCommitted = vi.fn();
    render(<ChatPanel open onToggle={() => {}} onActionsCommitted={onActionsCommitted} />);

    await userEvent.type(screen.getByTestId('chat-input'), 'buy 5 AAPL and watch PYPL');
    await userEvent.click(screen.getByTestId('chat-send'));

    await waitFor(() => {
      expect(mockedApi.sendChat).toHaveBeenCalledWith({ message: 'buy 5 AAPL and watch PYPL' });
    });
    const assistant = await screen.findByTestId('chat-message-assistant');
    expect(assistant).toHaveTextContent('Bought 5 AAPL.');
    // Chip textContent must include explicit spaces — flex `gap` is CSS-only.
    const tradeChip = screen.getByTestId('chat-action-trade');
    expect(tradeChip.textContent).toMatch(/BUY\s+5\s+AAPL\s+@\s+\$190\.50/);
    const wlChip = screen.getByTestId('chat-action-watchlist');
    expect(wlChip.textContent).toMatch(/WATCH \+\s+PYPL/);
    expect(onActionsCommitted).toHaveBeenCalledTimes(1);
    expect(onActionsCommitted).toHaveBeenCalledWith({ trades: true, watchlist: true });
  });

  it('signals only watchlist actions when the response contains only watchlist changes', async () => {
    mockedApi.sendChat.mockResolvedValue({
      message: 'Watching PYPL.',
      trades_executed: [],
      watchlist_changes: [{ ticker: 'PYPL', action: 'added' }],
      errors: [],
    });
    const onActionsCommitted = vi.fn();
    render(<ChatPanel open onToggle={() => {}} onActionsCommitted={onActionsCommitted} />);
    await userEvent.type(screen.getByTestId('chat-input'), 'add PYPL');
    await userEvent.click(screen.getByTestId('chat-send'));
    await screen.findByTestId('chat-message-assistant');
    expect(onActionsCommitted).toHaveBeenCalledWith({ trades: false, watchlist: true });
  });

  it('does not call onActionsCommitted when the response has no trades or watchlist changes', async () => {
    mockedApi.sendChat.mockResolvedValue({
      message: 'Your portfolio is fine.',
      trades_executed: [],
      watchlist_changes: [],
      errors: [],
    });
    const onActionsCommitted = vi.fn();
    render(<ChatPanel open onToggle={() => {}} onActionsCommitted={onActionsCommitted} />);

    await userEvent.type(screen.getByTestId('chat-input'), 'status');
    await userEvent.click(screen.getByTestId('chat-send'));

    await screen.findByTestId('chat-message-assistant');
    expect(onActionsCommitted).not.toHaveBeenCalled();
  });

  it('renders error banner and assistant error bubble when sendChat fails', async () => {
    mockedApi.sendChat.mockRejectedValue(new Error('boom'));
    render(<ChatPanel open onToggle={() => {}} onActionsCommitted={() => {}} />);
    await userEvent.type(screen.getByTestId('chat-input'), 'hi');
    await userEvent.click(screen.getByTestId('chat-send'));
    const assistant = await screen.findByTestId('chat-message-assistant');
    expect(assistant).toHaveTextContent(/error/i);
  });
});
