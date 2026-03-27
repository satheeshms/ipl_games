import { useState, useEffect } from 'react';
import { usePuzzle } from '../hooks/usePuzzle';
import { Header } from '../components/Header';
import { GameBoard } from '../components/GameBoard';
import { HelpModal } from '../components/HelpModal';
import { NavDrawer } from '../components/NavDrawer';
import { getGameBySlug } from '../games';

interface GamePageProps {
  slug: string;
}

export function GamePage({ slug }: GamePageProps) {
  const game = getGameBySlug(slug)!;
  const { puzzle, loading, error } = usePuzzle(game.puzzleDir);
  const helpSeenKey = `${game.storagePrefix}-help-seen`;
  const [showHelp, setShowHelp] = useState(false);
  const [showDrawer, setShowDrawer] = useState(false);

  useEffect(() => {
    if (!loading && puzzle && !localStorage.getItem(helpSeenKey)) {
      setShowHelp(true);
    }
  }, [loading, puzzle, helpSeenKey]);

  function closeHelp() {
    localStorage.setItem(helpSeenKey, '1');
    setShowHelp(false);
  }

  return (
    <div className="min-h-screen stadium-bg flex flex-col">
      <Header
        game={game}
        edition={puzzle?.edition}
        date={puzzle?.date}
        onHelp={() => setShowHelp(true)}
        onMenuClick={() => setShowDrawer(true)}
      />

      <main className="flex-1 flex flex-col items-center justify-start pt-4">
        {loading && (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="mt-16 text-center px-4">
            <p className="text-red-400 font-medium text-lg">Failed to load puzzle</p>
            <p className="text-white/50 text-sm mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && puzzle && (
          <GameBoard game={game} puzzle={puzzle} storagePrefix={game.storagePrefix} />
        )}
      </main>

      {showHelp && <HelpModal game={game} onClose={closeHelp} />}
      <NavDrawer open={showDrawer} activeSlug={slug} onClose={() => setShowDrawer(false)} />
    </div>
  );
}
