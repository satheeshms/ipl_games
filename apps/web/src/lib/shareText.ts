import type { GameMode, Puzzle, Guess } from '../types';

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
    const pos = index % 4;
    [cells[3], cells[pos]] = [cells[pos], cells[3]];
    return cells.join('');
  }
  return '⬛'.repeat(4);
}

export function buildEmojiRows(guessHistory: Guess[]): string[] {
  return guessHistory.map((guess, i) => buildRow(guess, i));
}

export function buildShareText(puzzle: Puzzle, guessHistory: Guess[], hintsUsed: number, gameMode: GameMode = 'pro'): string {
  const formattedDate = new Date(puzzle.date + 'T00:00:00').toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
  const emojiRows = guessHistory.map((guess, i) => buildRow(guess, i));
  const hintsLine = hintsUsed > 0 ? `💡 Hints used: ${hintsUsed}/2` : 'No hints used';
  const modeLabel = gameMode === 'easy' ? ' · Easy Mode' : '';
  const gameUrl = window.location.origin + window.location.pathname;

  return [
    `Cluster 4 – IPL #${puzzle.edition}${modeLabel}`,
    formattedDate,
    '',
    ...emojiRows,
    '',
    hintsLine,
    '',
    gameUrl,
  ].join('\n');
}
