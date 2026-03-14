import { usePuzzle } from './hooks/usePuzzle';
import { Header } from './components/Header';
import { GameBoard } from './components/GameBoard';

function App() {
  const { puzzle, loading, error } = usePuzzle();

  return (
    <div className="min-h-screen bg-[#1a1a2e] flex flex-col">
      {puzzle && <Header edition={puzzle.edition} date={puzzle.date} />}

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
          <GameBoard puzzle={puzzle} />
        )}
      </main>
    </div>
  );
}

export default App;
