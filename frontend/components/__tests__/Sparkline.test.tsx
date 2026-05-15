import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Sparkline } from '../Sparkline';

describe('Sparkline', () => {
  it('renders a dashed placeholder line when there is no data', () => {
    const { container } = render(<Sparkline data={[]} />);
    const line = container.querySelector('line');
    expect(line).not.toBeNull();
    expect(line?.getAttribute('stroke-dasharray')).toBe('2 3');
  });

  it('renders area + line paths when data has at least two points', () => {
    const { container } = render(<Sparkline data={[1, 2, 3, 4]} />);
    const paths = container.querySelectorAll('path');
    expect(paths.length).toBe(2);
  });

  it('uses up-tone stroke when the series net direction is positive', () => {
    const { container } = render(<Sparkline data={[1, 2, 3]} />);
    const linePath = container.querySelectorAll('path')[1];
    expect(linePath.getAttribute('stroke')).toBe('#3ddc97');
  });

  it('uses down-tone stroke when the series net direction is negative', () => {
    const { container } = render(<Sparkline data={[3, 2, 1]} />);
    const linePath = container.querySelectorAll('path')[1];
    expect(linePath.getAttribute('stroke')).toBe('#ff5f6d');
  });
});
