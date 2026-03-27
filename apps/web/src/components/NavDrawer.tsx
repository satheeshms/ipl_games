import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { GAMES, getGamesByCategory } from '../games';

interface NavDrawerProps {
  open: boolean;
  activeSlug: string;
  onClose: () => void;
}

export function NavDrawer({ open, activeSlug, onClose }: NavDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const byCategory = getGamesByCategory();

  // Remember the element that opened the drawer so we can return focus on close
  useEffect(() => {
    if (open) {
      triggerRef.current = document.activeElement as HTMLElement;
      // Move focus into the drawer on next frame
      requestAnimationFrame(() => {
        drawerRef.current?.focus();
      });
    } else {
      triggerRef.current?.focus();
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        aria-hidden
        onClick={onClose}
      />

      {/* Drawer */}
      <nav
        ref={drawerRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label="Game navigation"
        className="fixed top-0 left-0 h-full w-64 bg-[#1a1a2e] border-r border-white/10 z-50 flex flex-col outline-none"
      >
        {/* Header */}
        <div className="px-4 py-4 border-b border-white/10 flex items-center justify-between">
          <span className="font-bold text-white text-base">🎮 Puzzle Games</span>
          <button
            onClick={onClose}
            aria-label="Close navigation menu"
            className="w-7 h-7 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors text-lg leading-none"
          >
            ✕
          </button>
        </div>

        {/* Game list */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          {Object.entries(byCategory).map(([category, games]) => (
            <div key={category} className="mb-5">
              <div className="text-xs font-semibold uppercase tracking-widest text-white/40 px-2 mb-2">
                {category}
              </div>
              {games.map(game => {
                const isActive = game.slug === activeSlug;
                const isComingSoon = game.status === 'coming-soon';

                if (isComingSoon) {
                  return (
                    <div
                      key={game.slug}
                      className="flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm text-white/30 mb-1"
                      aria-disabled="true"
                    >
                      <span role="img" aria-hidden>{game.icon}</span>
                      <span className="flex-1">{game.label}</span>
                      <span className="text-xs text-white/25">Soon</span>
                    </div>
                  );
                }

                return (
                  <Link
                    key={game.slug}
                    to={game.path}
                    onClick={onClose}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm mb-1 transition-colors ${
                      isActive
                        ? 'bg-white/15 text-white font-semibold'
                        : 'text-white/70 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    <span role="img" aria-hidden>{game.icon}</span>
                    <span>{game.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer: Home link */}
        <div className="px-3 py-4 border-t border-white/10">
          <Link
            to="/"
            onClick={onClose}
            className="flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/10 transition-colors"
          >
            🏠 <span>Home</span>
          </Link>
        </div>
      </nav>
    </>
  );
}

// Re-export so GamePage only needs to import from one place
export { GAMES };
