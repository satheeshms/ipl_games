interface HeaderProps {
  edition: number;
  date: string;
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function Header({ edition, date }: HeaderProps) {
  return (
    <header className="w-full px-4 py-3 border-b border-white/10">
      <div className="max-w-lg mx-auto flex items-center justify-between">
        <h1 className="text-xl font-bold text-white tracking-tight">IPL Connections</h1>
        <span className="text-sm text-white/50">
          #{edition} &middot; {formatDate(date)}
        </span>
      </div>
    </header>
  );
}
