import type { GameConfig } from '../games';

interface HeaderProps {
  game: GameConfig;
  edition?: number;
  date?: string;
  onHelp: () => void;
  onMenuClick: () => void;
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function Header({ game, edition, date, onHelp, onMenuClick }: HeaderProps) {
  return (
    <header className="w-full px-4 py-3 border-b border-game-accent/30">
      <div className="max-w-lg mx-auto flex items-center justify-between">
        {/* Burger menu button */}
        <button
          onClick={onMenuClick}
          aria-label="Open navigation menu"
          className="w-8 h-8 flex flex-col items-center justify-center gap-1.5 text-white/60 hover:text-white transition-colors shrink-0"
        >
          <span className="block w-5 h-0.5 bg-current rounded-full" />
          <span className="block w-5 h-0.5 bg-current rounded-full" />
          <span className="block w-5 h-0.5 bg-current rounded-full" />
        </button>

        {/* Game title */}
        <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <span role="img" aria-hidden>{game.icon}</span>
          {game.label}
        </h1>

        {/* Edition, date, help */}
        <div className="flex items-center gap-3">
          {edition !== undefined && date !== undefined && (
            <span className="text-sm text-white/50">
              #{edition} &middot; {formatDate(date)}
            </span>
          )}
          <button
            onClick={onHelp}
            aria-label="How to play"
            className="w-7 h-7 rounded-full border border-white/30 text-white/60 hover:text-white hover:border-white/60 text-sm font-bold transition-colors flex items-center justify-center shrink-0"
          >
            ?
          </button>
        </div>
      </div>
    </header>
  );
}
