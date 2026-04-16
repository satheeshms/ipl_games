import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface HelpModalProps {
  onClose: () => void;
}

const RULES = [
  {
    icon: '👆',
    label: 'Tap 4 players',
    detail: 'Select items from the grid that share a common IPL theme',
  },
  {
    icon: '✅',
    label: 'Submit',
    detail: 'Correct group is revealed with its title; wrong guess costs a life',
  },
  {
    icon: '💡',
    label: 'Hints',
    detail: 'Reveal a category title to help narrow it down',
  },
  {
    icon: '🏆',
    label: 'Find all 4 groups',
    detail: 'Puzzles span IPL 2008–present. Use Shuffle to spot connections',
  },
];

const EASY_FEATURES = [
  '❤️ 6 lives',
  '💡 3 hints',
  '🎯 Wrong tile highlighted on "one away"',
  '📊 Tells you if 2 picks match',
];

const PRO_FEATURES = [
  '❤️ 4 lives',
  '💡 2 hints',
  '🔕 No extra guidance',
  '💪 For the purists',
];

const DIFFICULTY_DOTS = [
  { color: '#F9DF6D', label: 'Yellow — Easiest' },
  { color: '#A0C35A', label: 'Green — Moderate' },
  { color: '#B0C4EF', label: 'Blue — Hard' },
  { color: '#BA81C5', label: 'Purple — Hardest' },
];

export function HelpModal({ onClose }: HelpModalProps) {
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
        key="backdrop"
        className="fixed inset-0 bg-black/70 z-40 overflow-y-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <div className="flex min-h-full items-center justify-center px-4 py-4">
          <motion.div
            key="panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-modal-title"
            className="relative bg-[#1a1a2e] border border-white/10 rounded-2xl w-full max-w-md p-6 z-50 text-white"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            onClick={e => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              ref={closeRef}
              onClick={onClose}
              aria-label="Close instructions"
              className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors text-xl leading-none focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50 rounded"
            >
              ✕
            </button>

            <h2
              id="help-modal-title"
              className="text-xl font-bold text-center mb-1"
            >
              How to Play
            </h2>
            <p className="text-white/40 text-xs text-center mb-4">
              Cluster 4 - IPL Edition
            </p>

            {/* GIF hero */}
            <img
              src="/help-demo.gif"
              alt="How to play demo"
              className="w-full rounded-xl mb-5 border border-white/10"
              style={{ maxHeight: '160px', objectFit: 'cover' }}
            />

            {/* Vertical rules */}
            <div className="space-y-2 mb-5">
              {RULES.map(({ icon, label, detail }) => (
                <div
                  key={label}
                  className="flex items-start gap-3 bg-white/5 rounded-lg px-3 py-2.5"
                >
                  <span className="text-lg leading-none mt-0.5 shrink-0">{icon}</span>
                  <span className="text-sm leading-snug">
                    <strong>{label}</strong>
                    <span className="text-white/55"> — {detail}</span>
                  </span>
                </div>
              ))}
            </div>

            {/* Game mode comparison */}
            <div className="border-t border-white/10 pt-4 mb-4">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-3">
                Choose your mode
              </p>
              <div className="grid grid-cols-2 gap-2">
                {/* Easy */}
                <div className="rounded-lg p-3 bg-amber-400/10 border border-amber-400/30">
                  <p className="text-xs font-bold text-amber-300 mb-2">⚡ Easy</p>
                  <ul className="space-y-1">
                    {EASY_FEATURES.map(f => (
                      <li key={f} className="text-xs text-white/70 leading-snug">{f}</li>
                    ))}
                  </ul>
                </div>
                {/* Pro */}
                <div className="rounded-lg p-3 bg-white/5 border border-white/10">
                  <p className="text-xs font-bold text-white/70 mb-2">🏏 Pro</p>
                  <ul className="space-y-1">
                    {PRO_FEATURES.map(f => (
                      <li key={f} className="text-xs text-white/70 leading-snug">{f}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="text-xs text-white/30 text-center mt-2">
                Toggle in header · locks after your first guess
              </p>
            </div>

            {/* Difficulty colour key */}
            <div className="border-t border-white/10 pt-4 mb-5">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-2">
                Difficulty
              </p>
              <div className="flex items-center gap-2 flex-wrap">
                {DIFFICULTY_DOTS.map(({ color, label }) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <span
                      className="w-3.5 h-3.5 rounded-sm shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs text-white/50">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-full bg-white text-[#1a1a2e] font-semibold rounded-full py-2.5 text-sm hover:bg-white/90 transition-colors"
            >
              Let's Play!
            </button>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
