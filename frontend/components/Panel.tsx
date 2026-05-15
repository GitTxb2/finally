import type { ReactNode } from 'react';

interface PanelProps {
  title: string;
  badge?: string;
  actions?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export function Panel({ title, badge, actions, className = '', bodyClassName = '', children }: PanelProps) {
  return (
    <section className={`panel shadow-panel flex min-h-0 flex-col ${className}`}>
      <header className="panel-header">
        <div className="flex items-center gap-2">
          <span className="text-ink-dim">{title}</span>
          {badge ? (
            <span className="rounded-sm border border-edge px-1.5 py-px text-[9px] tracking-wider2 text-ink-mute">
              {badge}
            </span>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-2 text-ink-mute">{actions}</div> : null}
      </header>
      <div className={`min-h-0 flex-1 ${bodyClassName}`}>{children}</div>
    </section>
  );
}
