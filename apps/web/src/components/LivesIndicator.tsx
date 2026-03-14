interface LivesIndicatorProps {
  lives: number;
}

export function LivesIndicator({ lives }: LivesIndicatorProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-white/60">Mistakes remaining</span>
      <div className="flex gap-1.5">
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
