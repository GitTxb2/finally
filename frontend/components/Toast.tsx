'use client';

import { useEffect } from 'react';

export interface ToastMessage {
  id: number;
  kind: 'error' | 'success' | 'info';
  text: string;
}

interface ToastStackProps {
  toasts: ToastMessage[];
  dismiss: (id: number) => void;
}

const TONES: Record<ToastMessage['kind'], { border: string; bg: string; text: string }> = {
  error: { border: 'border-tape-down/50', bg: 'bg-tape-down/10', text: 'text-tape-down' },
  success: { border: 'border-tape-up/50', bg: 'bg-tape-up/10', text: 'text-tape-up' },
  info: { border: 'border-edge', bg: 'bg-bg-raised', text: 'text-ink-dim' },
};

export function ToastStack({ toasts, dismiss }: ToastStackProps) {
  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} dismiss={dismiss} />
      ))}
    </div>
  );
}

function Toast({ toast, dismiss }: { toast: ToastMessage; dismiss: (id: number) => void }) {
  const tone = TONES[toast.kind];

  useEffect(() => {
    const handle = setTimeout(() => dismiss(toast.id), 4500);
    return () => clearTimeout(handle);
  }, [toast.id, dismiss]);

  return (
    <div
      data-testid={toast.kind === 'error' ? 'trade-error-toast' : `toast-${toast.kind}`}
      className={`pointer-events-auto max-w-sm rounded-sm border ${tone.border} ${tone.bg} ${tone.text} px-3 py-2 font-mono text-[11px] uppercase tracking-wider2 shadow-panel`}
    >
      <div className="flex items-start gap-3">
        <span className="flex-1">{toast.text}</span>
        <button
          onClick={() => dismiss(toast.id)}
          className="text-ink-ghost hover:text-ink"
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}
