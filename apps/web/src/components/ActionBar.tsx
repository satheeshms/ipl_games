interface ActionBarProps {
  onShuffle: () => void;
  onDeselectAll: () => void;
  onSubmit: () => void;
  canSubmit: boolean;
  canDeselectAll: boolean;
}

export function ActionBar({ onShuffle, onDeselectAll, onSubmit, canSubmit, canDeselectAll }: ActionBarProps) {
  return (
    <div className="flex items-center justify-center gap-3 flex-wrap">
      <button
        onClick={onShuffle}
        className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                   hover:border-white/70 hover:text-white transition-colors duration-150"
      >
        Shuffle
      </button>

      <button
        onClick={onDeselectAll}
        disabled={!canDeselectAll}
        className="rounded-full border border-white/40 px-6 py-2 text-sm font-medium text-white/80
                   hover:border-white/70 hover:text-white transition-colors duration-150
                   disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Deselect All
      </button>

      <button
        onClick={onSubmit}
        disabled={!canSubmit}
        className="rounded-full bg-white px-6 py-2 text-sm font-semibold text-[#1a1a2e]
                   hover:bg-white/90 transition-colors duration-150
                   disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Submit
      </button>
    </div>
  );
}
