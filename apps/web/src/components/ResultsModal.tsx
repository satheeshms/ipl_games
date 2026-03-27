import { useState } from 'react';
import type { GameStatus, Puzzle, Guess } from '../types';
import type { GameConfig } from '../games';

const COLOR_EMOJI: Record<string, string> = {
  yellow: '🟨',
  green:  '🟩',
  blue:   '🟦',
  purple: '🟪',
};

function buildRow(guess: Guess, index: number): string {
  if (guess.correct && guess.categoryColor) return COLOR_EMOJI[guess.categoryColor].repeat(4);
  if (guess.oneAwayColor) {
    const cells = [COLOR_EMOJI[guess.oneAwayColor], COLOR_EMOJI[guess.oneAwayColor], COLOR_EMOJI[guess.oneAwayColor], '⬛'];
    // rotate ⬛ to a different position per row index
    const pos = index % 4;
    [cells[3], cells[pos]] = [cells[pos], cells[3]];
    return cells.join('');
  }
  return '⬛'.repeat(4);
}

interface ResultsModalProps {
  game: GameConfig;
  status: GameStatus;
  puzzle: Puzzle;
  guessHistory: Guess[];
  hintsUsed: number;
  onClose: () => void;
}

export function ResultsModal({ game, status, puzzle, guessHistory, hintsUsed, onClose }: ResultsModalProps) {
  const [copied, setCopied] = useState(false);

  if (status !== 'won' && status !== 'lost') return null;

  const formattedDate = new Date(puzzle.date + 'T00:00:00').toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  });

  // Build one emoji row per guess
  const emojiRows = guessHistory.map((guess, i) => buildRow(guess, i));

  const hintsLine = hintsUsed > 0 ? `💡 Hints used: ${hintsUsed}/2` : 'No hints used';

  const gameUrl = window.location.origin + window.location.pathname;

  const shareText = [
    `Cluster 4 – ${game.label} #${puzzle.edition}`,
    formattedDate,
    '',
    ...emojiRows,
    '',
    hintsLine,
    '',
    gameUrl,
  ].join('\n');

  async function handleShare() {
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable — no-op
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-[#2d2d44] rounded-2xl p-6 max-w-sm w-full mx-4 text-center shadow-xl">
        {/* Heading */}
        <p className="text-2xl font-bold text-white mb-1">
          {status === 'won' ? 'You won! 🎉' : 'Better luck next time!'}
        </p>
        <p className="text-white/50 text-xs mb-4">
          {game.label} #{puzzle.edition} · {formattedDate}
        </p>

        {/* Emoji grid */}
        <div className="bg-[#1a1a2e] rounded-xl px-6 py-4 mb-3 inline-block text-2xl leading-snug">
          {emojiRows.map((row, i) => (
            <div key={i}>{row}</div>
          ))}
        </div>

        {/* Hints line */}
        <p className="text-white/50 text-xs mb-3">{hintsLine}</p>

        {/* Game link */}
        <a
          href={gameUrl}
          className="block text-game-accent text-xs mb-5 hover:underline break-all"
        >
          {gameUrl}
        </a>

        {/* Action buttons */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={handleShare}
            className="rounded-full bg-game-accent px-6 py-2 text-sm font-semibold text-[#1a1a2e]
                       hover:opacity-90 transition-opacity"
          >
            {copied ? 'Copied!' : 'Share'}
          </button>
          <button
            onClick={onClose}
            className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                       hover:border-white/70 hover:text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
