import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { FlashCell } from '../FlashCell';

const fmt = (n: number) => n.toFixed(2);

describe('FlashCell', () => {
  it('renders the formatted value with no flash on initial mount', () => {
    render(<FlashCell value={190.5} format={fmt} testId="px" />);
    const node = screen.getByTestId('px');
    expect(node).toHaveTextContent('190.50');
    expect(node.className).not.toMatch(/animate-flash-/);
    expect(node).toHaveAttribute('data-direction', 'flat');
  });

  it('applies flash-up when the value rises', () => {
    const { rerender } = render(<FlashCell value={190.5} format={fmt} testId="px" />);
    rerender(<FlashCell value={191.25} format={fmt} testId="px" />);
    const node = screen.getByTestId('px');
    expect(node.className).toMatch(/animate-flash-up/);
    expect(node).toHaveAttribute('data-direction', 'up');
    expect(node).toHaveTextContent('191.25');
  });

  it('applies flash-down when the value falls', () => {
    const { rerender } = render(<FlashCell value={190.5} format={fmt} testId="px" />);
    rerender(<FlashCell value={188.0} format={fmt} testId="px" />);
    const node = screen.getByTestId('px');
    expect(node.className).toMatch(/animate-flash-down/);
    expect(node).toHaveAttribute('data-direction', 'down');
  });

  it('renders an em dash for null/non-finite values', () => {
    render(<FlashCell value={null} format={fmt} testId="px" />);
    expect(screen.getByTestId('px')).toHaveTextContent('—');
  });
});
