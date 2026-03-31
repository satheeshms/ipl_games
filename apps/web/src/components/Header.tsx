import { BiSolidCricketBall } from 'react-icons/bi';
import type { GameMode } from '../types';

interface HeaderProps {
  edition: number;
  date: string;
  gameMode: GameMode;
  gameStarted: boolean;
  onToggleGameMode: () => void;
  onHelp: () => void;
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function Header({ edition, date, gameMode, gameStarted, onToggleGameMode, onHelp }: HeaderProps) {
  return (
    <header className="w-full px-4 py-3 border-b border-game-accent/30">
      <div className="max-w-lg mx-auto flex items-center justify-between">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <BiSolidCricketBall size={26} className="shrink-0 text-red-600" />
          Cluster 4 - IPL Edition
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/50">
            #{edition} &middot; {formatDate(date)}
          </span>
          <div
            role="group"
            aria-label={gameStarted ? 'Game mode locked' : 'Game mode'}
            className={[
              'flex rounded-full border text-xs font-semibold overflow-hidden transition-opacity',
              gameStarted ? 'border-white/10 opacity-30 pointer-events-none' : 'border-white/25',
            ].join(' ')}
          >
            <button
              onClick={() => !gameStarted && gameMode !== 'pro' && onToggleGameMode()}
              aria-pressed={gameMode === 'pro'}
              disabled={gameStarted}
              className={[
                'px-3 py-1 transition-colors',
                gameMode === 'pro'
                  ? 'bg-sky-400/30 text-sky-300'
                  : 'text-white/40 hover:text-white/70',
              ].join(' ')}
            >
              Pro
            </button>
            <button
              onClick={() => !gameStarted && gameMode !== 'easy' && onToggleGameMode()}
              aria-pressed={gameMode === 'easy'}
              disabled={gameStarted}
              className={[
                'px-3 py-1 transition-colors',
                gameMode === 'easy'
                  ? 'bg-amber-400/30 text-amber-300'
                  : 'text-white/40 hover:text-white/70',
              ].join(' ')}
            >
              Easy
            </button>
          </div>
          <button
            onClick={onHelp}
            aria-label="How to play"
            className="w-7 h-7 rounded-full border border-white/30 text-white/60 hover:text-white hover:border-white/60 text-sm font-bold transition-colors flex items-center justify-center"
          >
            ?
          </button>
        </div>
      </div>
    </header>
  );
}
