'use client';

import { useEffect, useRef, useState, useCallback, type FormEvent } from 'react';
import { api, ApiError } from '@/lib/api';
import { fmtPrice } from '@/lib/format';
import type { ChatMessage, ChatResponse, ChatWatchlistAction, TradeRecord } from '@/lib/types';

export interface ChatActionKinds {
  trades: boolean;
  watchlist: boolean;
}

interface ChatPanelProps {
  open: boolean;
  onToggle: () => void;
  /**
   * Called after a chat turn that included any trades or watchlist
   * mutations. `kinds` indicates which categories of action fired so
   * the caller can refresh only the affected data sources.
   */
  onActionsCommitted: (kinds: ChatActionKinds) => void;
}

/**
 * Collapsible AI chat docked on the right edge. Maintains its own
 * message log (loaded from /api/chat/history if the backend exposes it,
 * otherwise starts empty). Trades and watchlist changes returned by
 * the LLM are rendered inline as confirmation chips under the
 * assistant message.
 */
export function ChatPanel({ open, onToggle, onActionsCommitted }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Best-effort history load; ignore if the endpoint isn't available.
    api
      .getChatHistory()
      .then((res) => setMessages(res.messages ?? []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, busy]);

  const send = useCallback(
    async (e?: FormEvent) => {
      e?.preventDefault();
      const text = draft.trim();
      if (!text || busy) return;
      setError(null);
      setDraft('');
      setMessages((m) => [...m, { role: 'user', content: text }]);
      setBusy(true);
      try {
        const res: ChatResponse = await api.sendChat({ message: text });
        setMessages((m) => [
          ...m,
          {
            role: 'assistant',
            content: res.message,
            trades: res.trades_executed,
            watchlist_changes: res.watchlist_changes,
            errors: res.errors,
          },
        ]);
        const trades = (res.trades_executed?.length ?? 0) > 0;
        const watchlist = (res.watchlist_changes?.length ?? 0) > 0;
        if (trades || watchlist) {
          onActionsCommitted({ trades, watchlist });
        }
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Chat unavailable';
        setError(msg);
        setMessages((m) => [
          ...m,
          { role: 'assistant', content: `Error: ${msg}`, errors: [msg] },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [draft, busy, onActionsCommitted],
  );

  return (
    <>
      {open ? null : (
        <button
          data-testid="chat-toggle"
          onClick={onToggle}
          aria-expanded={false}
          aria-label="Open AI chat"
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full border border-accent-purple/70 bg-accent-purple/90 px-4 py-2 font-display text-[11px] uppercase tracking-wider3 text-white shadow-panel transition hover:bg-accent-purple"
        >
          <span className="relative inline-block h-2 w-2 rounded-full bg-accent-yellow shadow-[0_0_8px_#ecad0a]" />
          Ask FinAlly
        </button>
      )}

      <aside
        data-testid="chat-panel"
        data-open={open}
        aria-hidden={!open}
        className={`fixed right-0 top-0 z-30 flex h-screen w-[380px] flex-col border-l border-edge bg-bg-panel/95 shadow-panel backdrop-blur transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <header className="flex items-center justify-between border-b border-edge px-4 py-3">
          <div>
            <div className="font-display text-sm font-semibold tracking-wider2 text-ink">FinAlly Copilot</div>
            <div className="font-mono text-[9px] uppercase tracking-wider3 text-ink-mute">
              gpt-oss-120b · cerebras
            </div>
          </div>
          <button
            data-testid={open ? 'chat-toggle' : undefined}
            onClick={onToggle}
            aria-expanded={open}
            aria-label="Close chat"
            className="rounded-sm border border-edge px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider2 text-ink-dim hover:border-accent-yellow hover:text-accent-yellow"
          >
            ×
          </button>
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
          {messages.length === 0 && !busy ? (
            <Welcome />
          ) : (
            <ul className="flex flex-col gap-3">
              {messages.map((msg, i) => (
                <Bubble key={i} msg={msg} />
              ))}
              {busy ? <Typing /> : null}
            </ul>
          )}
        </div>

        {error ? (
          <div className="border-t border-tape-down/30 bg-tape-down/10 px-3 py-2 font-mono text-[10px] tracking-wider2 text-tape-down">
            {error}
          </div>
        ) : null}

        <form onSubmit={send} className="flex items-center gap-2 border-t border-edge px-3 py-3">
          <input
            data-testid="chat-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask FinAlly… (e.g. 'buy 5 AAPL')"
            aria-label="Chat input"
            className="flex-1 rounded-sm border border-edge bg-bg-raised px-3 py-2 font-mono text-[12px] text-ink placeholder:text-ink-ghost focus:border-accent-yellow focus:outline-none"
            disabled={busy}
          />
          <button
            data-testid="chat-send"
            type="submit"
            disabled={busy || !draft.trim()}
            className="rounded-sm border border-accent-purple/60 bg-accent-purple/90 px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider2 text-white hover:bg-accent-purple disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </aside>
    </>
  );
}

function Welcome() {
  return (
    <div className="space-y-2 px-2 py-3 font-mono text-[11px] uppercase tracking-wider2 text-ink-mute">
      <p className="text-ink-dim">Try one of these</p>
      <ul className="space-y-1 text-ink-mute">
        <li>buy 5 aapl</li>
        <li>watch pypl</li>
        <li>how&apos;s my portfolio</li>
      </ul>
    </div>
  );
}

function Bubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user';
  return (
    <li
      className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}
      data-testid={isUser ? 'chat-message-user' : 'chat-message-assistant'}
    >
      <div
        className={`max-w-[88%] rounded-sm px-3 py-2 font-mono text-[12px] leading-snug ${
          isUser
            ? 'border border-accent-yellow/40 bg-accent-yellow/10 text-ink'
            : 'border border-edge bg-bg-raised text-ink'
        }`}
      >
        {msg.content}
      </div>
      {(msg.trades?.length ?? 0) > 0 ? (
        <div className="flex flex-wrap gap-1">
          {msg.trades!.map((t) => (
            <TradeChip key={t.id} trade={t} />
          ))}
        </div>
      ) : null}
      {(msg.watchlist_changes?.length ?? 0) > 0 ? (
        <div className="flex flex-wrap gap-1">
          {msg.watchlist_changes!.map((wl, i) => (
            <WatchlistChip key={i} change={wl} />
          ))}
        </div>
      ) : null}
      {(msg.errors?.length ?? 0) > 0 ? (
        <ul className="flex flex-col gap-0.5">
          {msg.errors!.map((e, i) => (
            <li
              key={i}
              className="rounded-sm border border-tape-down/40 bg-tape-down/10 px-2 py-1 font-mono text-[10px] tracking-wider2 text-tape-down"
            >
              {e}
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

function TradeChip({ trade }: { trade: TradeRecord }) {
  const isBuy = trade.side === 'buy';
  // Explicit whitespace between children so the chip's textContent reads
  // "BUY 2 AAPL @ $189.93" rather than "BUY2 AAPL@ $189.93" — flex `gap`
  // is CSS-only, it doesn't add space text nodes that querying / regex
  // / screen readers depend on.
  return (
    <span
      data-testid="chat-action-trade"
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 font-mono text-[10px] uppercase tracking-wider2 ${
        isBuy
          ? 'border-tape-up/50 bg-tape-up/10 text-tape-up'
          : 'border-tape-down/50 bg-tape-down/10 text-tape-down'
      }`}
    >
      <span className="font-semibold">{isBuy ? 'BUY' : 'SELL'}</span>
      {' '}
      <span className="text-ink">
        {trade.quantity} {trade.ticker}
      </span>
      {' '}
      <span className="text-ink-dim">@ ${fmtPrice(trade.price)}</span>
    </span>
  );
}

function WatchlistChip({ change }: { change: ChatWatchlistAction }) {
  const verb = {
    added: 'WATCH +',
    already_present: 'ALREADY WATCHED',
    removed: 'WATCH −',
    not_present: 'NOT WATCHED',
  }[change.action];
  const tone =
    change.action === 'added' || change.action === 'already_present'
      ? 'border-accent-blue/50 bg-accent-blue/10 text-accent-blue'
      : 'border-edge bg-bg-raised text-ink-dim';
  return (
    <span
      data-testid="chat-action-watchlist"
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 font-mono text-[10px] uppercase tracking-wider2 ${tone}`}
    >
      <span className="font-semibold">{verb}</span>
      {' '}
      <span className="text-ink">{change.ticker}</span>
    </span>
  );
}

function Typing() {
  return (
    <li
      data-testid="chat-typing"
      className="flex items-center gap-1 self-start px-3 py-2 font-mono text-[11px] text-ink-mute"
    >
      <Dot />
      <Dot delay={150} />
      <Dot delay={300} />
    </li>
  );
}

function Dot({ delay = 0 }: { delay?: number }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 rounded-full bg-accent-yellow"
      style={{ animation: 'pulseDot 1.4s ease-in-out infinite', animationDelay: `${delay}ms` }}
    />
  );
}
