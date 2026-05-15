import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ConnectionDot } from '../ConnectionDot';

describe('ConnectionDot', () => {
  it('renders LIVE label and exposes connected state', () => {
    render(<ConnectionDot status="connected" />);
    const node = screen.getByTestId('connection-status');
    expect(node).toHaveAttribute('data-state', 'connected');
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });

  it('shows RECONNECTING with pulse animation', () => {
    render(<ConnectionDot status="reconnecting" />);
    const node = screen.getByTestId('connection-status');
    expect(node).toHaveAttribute('data-state', 'reconnecting');
    expect(node.querySelector('span')?.className).toMatch(/animate-pulse-dot/);
    expect(screen.getByText('RECONNECTING')).toBeInTheDocument();
  });

  it('shows OFFLINE when disconnected', () => {
    render(<ConnectionDot status="disconnected" />);
    expect(screen.getByTestId('connection-status')).toHaveAttribute('data-state', 'disconnected');
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });
});
