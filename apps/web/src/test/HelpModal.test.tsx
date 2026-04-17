import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HelpModal } from '../components/HelpModal';

describe('HelpModal', () => {
  it('renders the GIF demo image', () => {
    render(<HelpModal onClose={() => {}} />);
    const img = screen.getByRole('img', { name: /how to play demo/i });
    expect(img).toHaveAttribute('src', '/help-demo.gif');
  });

  it('renders all four rules', () => {
    render(<HelpModal onClose={() => {}} />);
    expect(screen.getByText(/tap 4 players/i)).toBeInTheDocument();
    expect(screen.getByText(/submit/i)).toBeInTheDocument();
    expect(screen.getByText(/reveal a category title/i)).toBeInTheDocument();
    expect(screen.getByText(/find all 4 groups/i)).toBeInTheDocument();
  });

  it('shows correct Easy mode stats', () => {
    render(<HelpModal onClose={() => {}} />);
    expect(screen.getByText(/6 lives/i)).toBeInTheDocument();
    expect(screen.getByText(/3 hints/i)).toBeInTheDocument();
  });

  it('shows correct Pro mode stats', () => {
    render(<HelpModal onClose={() => {}} />);
    expect(screen.getByText(/4 lives/i)).toBeInTheDocument();
    expect(screen.getByText(/2 hints/i)).toBeInTheDocument();
  });

  it('calls onClose when Let\'s Play button is clicked', async () => {
    const onClose = vi.fn();
    render(<HelpModal onClose={onClose} />);
    await userEvent.click(screen.getByRole('button', { name: /let's play/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when Escape key is pressed', async () => {
    const onClose = vi.fn();
    render(<HelpModal onClose={onClose} />);
    await userEvent.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledOnce();
  });
});
