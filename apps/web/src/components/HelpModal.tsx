import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface HelpModalProps {
  onClose: () => void;
}

const DIFFICULTY_LEVELS = [
  {
    color: '#F9DF6D',
    label: 'Yellow — Easiest',
    description: 'Straightforward IPL groupings (e.g. "CSK Players")',
  },
  {
    color: '#A0C35A',
    label: 'Green — Moderate',
    description: 'Requires IPL knowledge (e.g. "Purple Cap Winners")',
  },
  {
    color: '#B0C4EF',
    label: 'Blue — Hard',
    description: 'Nuanced facts or lesser-known trivia',
  },
  {
    color: '#BA81C5',
    label: 'Purple — Hardest',
    description: 'Wordplay, puns, or obscure connections',
  },
];

export function HelpModal({ onClose }: HelpModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  // Focus the close button when modal opens
  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        key="backdrop"
        className="fixed inset-0 bg-black/70 z-40 flex items-center justify-center px-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        {/* Panel */}
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

          <h2 id="help-modal-title" className="text-xl font-bold text-center mb-1">How to Play</h2>
          <p className="text-white/60 text-sm text-center mb-1">Cluster 4 - IPL Edition</p>
          <p className="text-white/40 text-xs text-center mb-5">Puzzles span the entire IPL history — from 2008 to present</p>

          {/* Rules */}
          <ol className="space-y-3 text-sm mb-6">
            <li className="flex gap-3">
              <span className="text-white/50 font-bold shrink-0">1.</span>
              <span>Find <strong>4 groups of 4 items</strong> that share a common IPL theme.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-white/50 font-bold shrink-0">2.</span>
              <span>Tap items to <strong>select</strong> them. Tap again to deselect. Select exactly 4, then hit <strong>Submit</strong>.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-white/50 font-bold shrink-0">3.</span>
              <span>A correct group is revealed with its category title. An incorrect guess costs you a <strong>life</strong>.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-white/50 font-bold shrink-0">4.</span>
              <span>You have <strong>4 lives</strong>. Lose all 4 and the puzzle ends. Reveal all 4 groups to win!</span>
            </li>
            <li className="flex gap-3">
              <span className="text-white/50 font-bold shrink-0">5.</span>
              <span>Watch for the <strong>"One Away!"</strong> hint — it means 3 of your 4 picks are correct.</span>
            </li>
          </ol>

          {/* Difficulty key */}
          <div className="border-t border-white/10 pt-4">
            <p className="text-xs text-white/50 uppercase tracking-widest mb-3">Difficulty</p>
            <div className="space-y-2">
              {DIFFICULTY_LEVELS.map(({ color, label, description }) => (
                <div key={label} className="flex items-start gap-3">
                  <span
                    className="w-4 h-4 rounded-sm shrink-0 mt-0.5"
                    style={{ backgroundColor: color }}
                  />
                  <div className="text-sm">
                    <span className="font-semibold">{label}</span>
                    <span className="text-white/50"> — {description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tip */}
          <p className="mt-5 text-xs text-white/50 text-center">
            Tip: use <strong className="text-white/50">Shuffle</strong> to spot hidden connections
          </p>

          <button
            onClick={onClose}
            className="mt-5 w-full bg-white text-[#1a1a2e] font-semibold rounded-full py-2.5 text-sm hover:bg-white/90 transition-colors"
          >
            Let's Play!
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
