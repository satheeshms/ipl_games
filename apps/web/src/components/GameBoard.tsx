import { useEffect, useState, useCallback } from 'react';
import type { Puzzle } from '../types';
import { useGameEngine } from '../hooks/useGameEngine';
import { CategoryBanner } from './CategoryBanner';
import { ItemGrid } from './ItemGrid';
import { LivesIndicator } from './LivesIndicator';
import { ToastNotification } from './ToastNotification';
import { ActionBar } from './ActionBar';
import { ResultsModal } from './ResultsModal';

interface GameBoardProps {
  puzzle: Puzzle;
}

export function GameBoard({ puzzle }: GameBoardProps) {
  const engine = useGameEngine();
  const { state } = engine;

  // Toast message state (null = hidden)
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  // Whether the modal has been explicitly closed by the user
  const [modalClosed, setModalClosed] = useState(false);

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

  // Handle submit with duplicate-guess detection
  const handleSubmit = useCallback(async () => {
    if (state.status !== 'playing') return;
    if (state.selected.length !== 4) return;

    // Check for duplicate guess: compare sorted selected against all previous guesses
    const sortedSelected = [...state.selected].sort();
    const isDuplicate = state.guessHistory.some(g => {
      const sortedGuess = [...g.items].sort();
      return (
        sortedGuess.length === sortedSelected.length &&
        sortedGuess.every((item, i) => item === sortedSelected[i])
      );
    });

    if (isDuplicate) {
      setToastMessage('Already guessed!');
      const timer = setTimeout(() => setToastMessage(null), 2000);
      // Return cleanup — we can't return from an async callback in useCallback easily,
      // so we just schedule the clear.
      void timer;
      return;
    }

    await engine.submitGuess();
  }, [state.status, state.selected, state.guessHistory, engine]);

  // When the puzzle resets (new puzzle.id), reset modal closed state
  useEffect(() => {
    setModalClosed(false);
  }, [puzzle.id]);

  const isGameOver = state.status === 'won' || state.status === 'lost';
  const gridDisabled = state.status !== 'playing';

  // Find revealed categories (in reveal order) from puzzle definition
  const revealedPuzzleCategories = state.revealedCategories
    .map(color => puzzle.categories.find(c => c.color === color))
    .filter((c): c is NonNullable<typeof c> => c !== undefined);

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-lg mx-auto px-4 py-6">
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
        />
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
        canSubmit={state.selected.length === 4 && state.status === 'playing'}
        canDeselectAll={state.selected.length > 0}
      />

      {/* Results modal (placeholder) */}
      {isGameOver && !modalClosed && (
        <ResultsModal
          status={state.status}
          puzzle={puzzle}
          guessHistory={state.guessHistory}
          onClose={() => setModalClosed(true)}
        />
      )}
    </div>
  );
}
