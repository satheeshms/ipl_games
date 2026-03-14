import type { GameStatus, Puzzle, Guess } from '../types';

interface ResultsModalProps {
  status: GameStatus;
  puzzle: Puzzle;
  guessHistory: Guess[];
  onClose: () => void;
}

export function ResultsModal({ status, onClose }: ResultsModalProps) {
  if (status !== 'won' && status !== 'lost') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#2d2d44] rounded-2xl p-8 max-w-sm w-full mx-4 text-center shadow-xl">
        <p className="text-2xl font-bold text-white mb-2">
          {status === 'won' ? 'You won! 🎉' : 'Better luck next time!'}
        </p>
        <p className="text-white/60 text-sm mb-6">
          {status === 'won'
            ? 'Great job solving the puzzle!'
            : 'The puzzle has been revealed above.'}
        </p>
        <button
          onClick={onClose}
          className="rounded-full bg-white px-8 py-2 text-sm font-semibold text-[#1a1a2e] hover:bg-white/90 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}
