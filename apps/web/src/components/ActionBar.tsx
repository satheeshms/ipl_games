interface ActionBarProps {
  onShuffle: () => void;
  onDeselectAll: () => void;
  onSubmit: () => void;
  onHint: () => void;
  onShare?: () => void;
  canSubmit: boolean;
  canDeselectAll: boolean;
  hintsRemaining: number;
  canHint: boolean;
  isGameOver?: boolean;
}

export function ActionBar({ onShuffle, onDeselectAll, onSubmit, onHint, onShare, canSubmit, canDeselectAll, hintsRemaining, canHint, isGameOver = false }: ActionBarProps) {
  return (
    <div className="flex items-center justify-center gap-3 flex-wrap" role="group" aria-label="Game actions">
      {!isGameOver && (
        <>
          <button
            onClick={onShuffle}
            aria-label="Shuffle tiles"
            className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                       hover:border-white/70 hover:text-white transition-colors duration-150"
          >
            Shuffle
          </button>

          <button
            onClick={onDeselectAll}
            disabled={!canDeselectAll}
            aria-disabled={!canDeselectAll}
            aria-label="Deselect all tiles"
            className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                       hover:border-white/70 hover:text-white transition-colors duration-150
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Deselect All
          </button>

          <button
            onClick={onHint}
            disabled={!canHint}
            aria-disabled={!canHint}
            aria-label={`Use hint, ${hintsRemaining} remaining`}
            className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                       hover:border-white/70 hover:text-white transition-colors duration-150
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Hint ({hintsRemaining})
          </button>

          <button
            onClick={onSubmit}
            disabled={!canSubmit}
            aria-disabled={!canSubmit}
            aria-label="Submit selected tiles"
            className="rounded-full bg-white px-6 py-2 text-sm font-semibold text-[#1a1a2e]
                       hover:bg-white/90 transition-colors duration-150
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Submit
          </button>
        </>
      )}

      {isGameOver && onShare && (
        <button
          onClick={onShare}
          aria-label="Share your result"
          className="rounded-full bg-game-accent px-8 py-2 text-sm font-semibold text-[#1a1a2e]
                     hover:opacity-90 transition-opacity"
        >
          Share Result
        </button>
      )}
    </div>
  );
}
