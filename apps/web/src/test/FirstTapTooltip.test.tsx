import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FirstTapTooltip } from '../components/FirstTapTooltip';

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('FirstTapTooltip', () => {
  it('renders tooltip text when visible', () => {
    render(<FirstTapTooltip visible onDismiss={() => {}} />);
    expect(screen.getByText(/tap 3 more/i)).toBeInTheDocument();
  });

  it('renders nothing when not visible', () => {
    const { container } = render(<FirstTapTooltip visible={false} onDismiss={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it('calls onDismiss after 4 seconds', () => {
    const onDismiss = vi.fn();
    render(<FirstTapTooltip visible onDismiss={onDismiss} />);
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(4000); });
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('calls onDismiss when clicked', async () => {
    vi.useRealTimers(); // Need real timers for userEvent
    const onDismiss = vi.fn();
    render(<FirstTapTooltip visible onDismiss={onDismiss} />);
    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));
    expect(onDismiss).toHaveBeenCalledOnce();
    vi.useFakeTimers(); // Reset to fake timers
  });
});
