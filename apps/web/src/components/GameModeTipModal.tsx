import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface GameModeTipModalProps {
  onClose: () => void;
}

const BULLETS = [
  { icon: '🏏', text: <><strong>6 lives</strong> instead of 4 — more room for mistakes.</> },
  { icon: '🎯', text: <>When you're one away, the <strong>wrong tile is highlighted</strong> to guide you.</> },
  { icon: '🔒', text: <>Mode <strong>locks after your first guess</strong> — choose before you start.</> },
];

export function GameModeTipModal({ onClose }: GameModeTipModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <AnimatePresence>
      <motion.div
        key="tip-backdrop"
        className="fixed inset-0 bg-black/60 z-40 overflow-y-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <div className="flex min-h-full items-center justify-center px-4 py-4">
          <motion.div
            key="tip-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mode-tip-title"
            className="relative bg-[#1a1a2e] border border-white/10 rounded-2xl w-full max-w-sm p-6 z-50 text-white"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            onClick={e => e.stopPropagation()}
          >
            <button
              ref={closeRef}
              onClick={onClose}
              aria-label="Close tip"
              className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors text-xl leading-none focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50 rounded"
            >
              ✕
            </button>

            <div className="flex items-center gap-2 mb-1">
              <span className="bg-amber-400/20 text-amber-300 text-xs font-semibold px-2 py-0.5 rounded-full">
                NEW
              </span>
              <h2 id="mode-tip-title" className="text-lg font-bold">Easy Mode</h2>
            </div>
            <p className="text-white/50 text-sm mb-5">A new game mode is now available — toggle it in the header before you start.</p>

            <ul className="space-y-3 mb-6">
              {BULLETS.map(({ icon, text }, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="shrink-0 text-base leading-snug">{icon}</span>
                  <span className="text-white/80">{text}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={onClose}
              className="w-full bg-white text-[#1a1a2e] font-semibold rounded-full py-2.5 text-sm hover:bg-white/90 transition-colors"
            >
              Got it!
            </button>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
