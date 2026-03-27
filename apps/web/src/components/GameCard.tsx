import { Link } from 'react-router-dom';
import type { GameConfig } from '../games';

interface GameCardProps {
  game: GameConfig;
}

export function GameCard({ game }: GameCardProps) {
  const isActive = game.status === 'active';

  const cardContent = (
    <div
      className={`rounded-xl border p-4 flex items-center gap-4 transition-colors ${
        isActive
          ? 'border-white/20 bg-white/5 hover:bg-white/10 cursor-pointer'
          : 'border-white/10 bg-white/[0.02] opacity-60'
      }`}
    >
      <span className="text-3xl shrink-0" role="img" aria-hidden>
        {game.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-white">{game.label}</div>
        <div className="text-sm text-white/50 mt-0.5">{game.description}</div>
      </div>
      {isActive ? (
        <span className="text-sm font-medium px-3 py-1 rounded-full bg-white/10 text-white shrink-0">
          Play →
        </span>
      ) : (
        <span className="text-xs px-2 py-1 rounded-full bg-white/5 text-white/40 shrink-0">
          Coming Soon
        </span>
      )}
    </div>
  );

  if (!isActive) {
    return (
      <div aria-disabled="true" aria-label={`${game.label} — coming soon`}>
        {cardContent}
      </div>
    );
  }

  return (
    <Link to={game.path} aria-label={`Play ${game.label}`} className="block no-underline">
      {cardContent}
    </Link>
  );
}
