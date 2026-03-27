interface LivesIndicatorProps {
  lives: number;
}

export function LivesIndicator({ lives }: LivesIndicatorProps) {
  return (
    <div className="flex items-center gap-3" role="status" aria-label={`${lives} ${lives === 1 ? 'life' : 'lives'} remaining`}>
      <span className="text-sm text-white/60" aria-hidden="true">Lives remaining</span>
      <div className="flex gap-1.5" aria-hidden="true">
        {Array.from({ length: 4 }, (_, i) => (
          <span
            key={i}
            className={`w-4 h-4 rounded-full border-2 ${
              i < lives
                ? 'bg-game-accent border-game-accent'
                : 'bg-transparent border-white/25'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
