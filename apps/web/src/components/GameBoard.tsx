import { useEffect, useState, useCallback } from 'react';
import type { Color, Puzzle, PuzzleCategory } from '../types';
import { useGameEngine } from '../hooks/useGameEngine';
import { hashItems } from '../lib/hash';
import { CategoryBanner } from './CategoryBanner';
import { ItemGrid } from './ItemGrid';
import { LivesIndicator } from './LivesIndicator';
import { ToastNotification } from './ToastNotification';
import { ActionBar } from './ActionBar';
import { ResultsModal } from './ResultsModal';

const HINT_COLOR_ORDER: Color[] = ['yellow', 'green', 'blue', 'purple'];

const COLOR_LABEL: Record<Color, string> = {
  yellow: 'Yellow',
  green: 'Green',
  blue: 'Blue',
  purple: 'Purple',
};

interface GameBoardProps {
  puzzle: Puzzle;
}

async function checkOneAway(selected: string[], gridItems: string[], categories: PuzzleCategory[]): Promise<{ color: Color } | null> {
  const remainingItems = gridItems.filter(gi => !selected.includes(gi));
  for (const category of categories) {
    for (let removeIdx = 0; removeIdx < selected.length; removeIdx++) {
      const threesome = selected.filter((_, idx) => idx !== removeIdx);
      for (const candidate of remainingItems) {
        // eslint-disable-next-line no-await-in-loop
        const comboHash = await hashItems([...threesome, candidate]);
        if (comboHash === category.hash) return { color: category.color };
      }
    }
  }
  return null;
}

export function GameBoard({ puzzle }: GameBoardProps) {
  const engine = useGameEngine();
  const { state } = engine;

  // Toast message state (null = hidden)
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  // Whether the modal has been explicitly closed by the user (persisted per puzzle)
  const modalClosedKey = `ipl-cluster4-modal-closed-${puzzle.id}`;
  const [modalClosed, setModalClosed] = useState(() => {
    try { return localStorage.getItem(modalClosedKey) === '1'; } catch { return false; }
  });
  // Animation state
  const [shakingItems, setShakingItems] = useState<string[]>([]);
  const [bouncingItems, setBouncingItems] = useState<string[]>([]);

  // Load puzzle on mount / when puzzle id changes
  useEffect(() => {
    engine.loadPuzzle(puzzle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puzzle.id]);

  // Handle "One Away!" toast
  useEffect(() => {
    if (state.oneAway) {
      setToastMessage('One Away!');
      const timer = setTimeout(() => {
        engine.clearOneAway();
        setToastMessage(null);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state.oneAway]);

  // Handle submit with inline hash logic and animations
  const handleSubmit = useCallback(async () => {
    if (state.status !== 'playing' || state.selected.length !== 4 || !state.puzzle) return;

    // Capture before any state change
    const selectedItems = [...state.selected];

    // Duplicate check
    const sortedSelected = [...selectedItems].sort();
    const isDuplicate = state.guessHistory.some(g => {
      const s = [...g.items].sort();
      return s.length === 4 && s.every((item, i) => item === sortedSelected[i]);
    });

    if (isDuplicate) {
      setToastMessage('Already guessed!');
      setTimeout(() => setToastMessage(null), 2000);
      return;
    }

    // Hash check
    const guessHash = await hashItems(selectedItems);
    const matched = state.puzzle.categories.find(c => c.hash === guessHash);

    if (matched) {
      // Bounce animation then reveal
      setBouncingItems(selectedItems);
      setTimeout(() => {
        setBouncingItems([]);
        engine.revealCategory(matched.color);
      }, 500);
    } else {
      // Shake animation
      setShakingItems(selectedItems);
      setTimeout(() => setShakingItems([]), 650);

      // One-away check
      const match = await checkOneAway(selectedItems, state.gridItems, state.puzzle.categories);
      engine.wrongGuess(match !== null, match?.color);
    }
  }, [state, engine]);

  // Keyboard: Enter to submit when 4 items selected
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Enter' && state.selected.length === 4 && state.status === 'playing') {
        handleSubmit();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [state.selected.length, state.status, handleSubmit]);

  // When the puzzle resets (new puzzle.id), re-read the persisted closed state
  useEffect(() => {
    try {
      setModalClosed(localStorage.getItem(modalClosedKey) === '1');
    } catch {
      setModalClosed(false);
    }
  }, [puzzle.id]);

  // Hint: reveal the title of the next hintable category (skipping already-found ones)
  const handleHint = useCallback(() => {
    if (state.hintedColors.length >= 2 || state.status !== 'playing') return;
    const targetColor = HINT_COLOR_ORDER.find(
      c => !state.hintedColors.includes(c) && !state.revealedCategories.includes(c)
    );
    if (!targetColor) return;
    engine.useHint(targetColor);
  }, [state.hintedColors, state.revealedCategories, state.status, engine]);

  // Derive which hint titles are currently visible (hinted but not yet correctly guessed)
  const visibleHints = state.hintedColors
    .filter(c => !state.revealedCategories.includes(c))
    .map(c => {
      const category = puzzle.categories.find(cat => cat.color === c);
      return category ? { color: c, title: category.title } : null;
    })
    .filter((h): h is { color: Color; title: string } => h !== null);

  const hintsRemaining = 2 - state.hintedColors.length;
  const canHint =
    state.status === 'playing' &&
    state.hintedColors.length < 2 &&
    HINT_COLOR_ORDER.some(c => !state.hintedColors.includes(c) && !state.revealedCategories.includes(c));

  const isGameOver = state.status === 'won' || state.status === 'lost';
  const gridDisabled = state.status !== 'playing';

  // Find revealed categories (in reveal order) from puzzle definition
  const revealedPuzzleCategories = state.revealedCategories
    .map(color => puzzle.categories.find(c => c.color === color))
    .filter((c): c is NonNullable<typeof c> => c !== undefined);

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-lg mx-auto px-4 py-6" role="main" aria-label="Cluster 4 - IPL Edition puzzle">
      {/* Revealed category banners */}
      {revealedPuzzleCategories.map(category => (
        <CategoryBanner
          key={category.color}
          category={category}
          guessHistory={state.guessHistory}
        />
      ))}

      {/* Remaining item grid */}
      {state.gridItems.length > 0 && (
        <ItemGrid
          items={state.gridItems}
          selected={state.selected}
          onSelect={engine.selectItem}
          onDeselect={engine.deselectItem}
          disabled={gridDisabled}
          shakingItems={shakingItems}
          bouncingItems={bouncingItems}
        />
      )}

      {/* Hint panel */}
      {visibleHints.length > 0 && (
        <div className="w-full flex flex-col gap-2">
          {visibleHints.map(hint => (
            <div
              key={hint.color}
              className="w-full rounded-lg px-4 py-2 text-sm font-medium text-white/90 bg-white/10 border border-white/20 flex items-center gap-2"
            >
              <span className="text-base">💡</span>
              <span>
                <span className="font-semibold capitalize">{COLOR_LABEL[hint.color]}:</span>{' '}
                {hint.title}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Lives indicator */}
      <LivesIndicator lives={state.lives} />

      {/* Toast notification */}
      <ToastNotification message={toastMessage} />

      {/* Action bar */}
      <ActionBar
        onShuffle={engine.shuffle}
        onDeselectAll={engine.deselectAll}
        onSubmit={handleSubmit}
        onHint={handleHint}
        canSubmit={state.selected.length === 4 && state.status === 'playing'}
        canDeselectAll={state.selected.length > 0}
        hintsRemaining={hintsRemaining}
        canHint={canHint}
      />

      {/* Results modal */}
      {isGameOver && !modalClosed && (
        <ResultsModal
          status={state.status}
          puzzle={puzzle}
          guessHistory={state.guessHistory}
          hintsUsed={state.hintedColors.length}
          onClose={() => {
            try { localStorage.setItem(modalClosedKey, '1'); } catch { /* ignore */ }
            setModalClosed(true);
          }}
        />
      )}
    </div>
  );
}
