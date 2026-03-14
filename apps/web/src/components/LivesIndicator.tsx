interface LivesIndicatorProps {
  lives: number;
}

export function LivesIndicator({ lives }: LivesIndicatorProps) {
  return (
    <div className="flex items-center gap-3" role="status" aria-label={`${lives} mistake${lives === 1 ? '' : 's'} remaining`}>
      <span className="text-sm text-white/60" aria-hidden="true">Mistakes remaining</span>
      <div className="flex gap-1.5" aria-hidden="true">
        {Array.from({ length: 4 }, (_, i) => (
          <span
            key={i}
            className={`text-lg leading-none ${i < lives ? 'text-white' : 'text-white/20'}`}
          >
            {i < lives ? '●' : '○'}
          </span>
        ))}
      </div>
    </div>
  );
}
