import { getGamesByCategory } from '../games';
import { GameCard } from '../components/GameCard';

export function HomePage() {
  const byCategory = getGamesByCategory();

  return (
    <div className="min-h-screen stadium-bg text-white">
      <div className="max-w-lg mx-auto px-4 py-8">
        <header className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight">Puzzle Games</h1>
          <p className="text-white/50 mt-2 text-sm">Daily puzzles across sports, politics &amp; more</p>
        </header>

        {Object.entries(byCategory).map(([category, games]) => (
          <section key={category} className="mb-8">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-white/40 mb-3">
              {category}
            </h2>
            <div className="flex flex-col gap-3">
              {games.map(game => (
                <GameCard key={game.slug} game={game} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
