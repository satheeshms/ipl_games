import { BiSolidCricketBall } from 'react-icons/bi';

interface HeaderProps {
  edition: number;
  date: string;
  onHelp: () => void;
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function Header({ edition, date, onHelp }: HeaderProps) {
  return (
    <header className="w-full px-4 py-3 border-b border-game-accent/30">
      <div className="max-w-lg mx-auto flex items-center justify-between">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <BiSolidCricketBall size={26} className="shrink-0 text-red-600" />
          IPL Connections
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/50">
            #{edition} &middot; {formatDate(date)}
          </span>
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
