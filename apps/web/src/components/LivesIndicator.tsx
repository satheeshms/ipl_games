import { CricketWicketIcon } from './icons/CricketWicket';

interface LivesIndicatorProps {
  lives: number;
  maxLives: number;
}

export function LivesIndicator({ lives, maxLives }: LivesIndicatorProps) {
  return (
    <div className="flex items-center gap-3" role="status" aria-label={`${lives} wicket${lives === 1 ? '' : 's'} remaining`}>
      <span className="text-sm text-white/60" aria-hidden="true">Wickets remaining</span>
      <div className="flex gap-1.5" aria-hidden="true">
        {Array.from({ length: maxLives }, (_, i) => (
          <CricketWicketIcon
            key={i}
            size={20}
            fallen={i >= lives}
            className={i < lives ? 'text-game-accent' : 'text-white/25'}
          />
        ))}
      </div>
    </div>
  );
}
