import { useState, useEffect, useRef, useCallback } from 'react';
import { usePuzzle } from './hooks/usePuzzle';
import { GameSEO } from './components/GameSEO';
import { Header } from './components/Header';
import { GameBoard } from './components/GameBoard';
import { HelpModal } from './components/HelpModal';
import { GameModeTipModal } from './components/GameModeTipModal';
import type { GameMode } from './types';

const HELP_SEEN_KEY = 'ipl-cluster4-help-seen';
const GAME_MODE_KEY = 'ipl-cluster4-gamemode';
const MODE_TIP_COUNT_KEY = 'ipl-cluster4-mode-tip-count';
const MODE_TIP_MAX = 3;

function getModeTipCount(): number {
  try {
    return parseInt(localStorage.getItem(MODE_TIP_COUNT_KEY) ?? '0', 10) || 0;
  } catch { return MODE_TIP_MAX; } // fail-safe: don't spam if storage unavailable
}

function incrementModeTipCount(): void {
  try {
    localStorage.setItem(MODE_TIP_COUNT_KEY, String(getModeTipCount() + 1));
  } catch { /* ignore */ }
}

function App() {
  const { puzzle, loading, error } = usePuzzle();
  const [showHelp, setShowHelp] = useState(false);
  const [showModeTip, setShowModeTip] = useState(false);
  const modeTipShownThisSession = useRef(false);
  const [gameMode, setGameMode] = useState<GameMode>(() => {
    try {
      const stored = localStorage.getItem(GAME_MODE_KEY);
      return stored === 'easy' ? 'easy' : 'pro';
    } catch { return 'pro'; }
  });
  const [gameStarted, setGameStarted] = useState(false);

  // Reset gameStarted when puzzle changes
  useEffect(() => {
    setGameStarted(false);
  }, [puzzle?.id]);

  // Persist gameMode
  useEffect(() => {
    try { localStorage.setItem(GAME_MODE_KEY, gameMode); } catch { /* ignore */ }
  }, [gameMode]);

  // Auto-show help on first visit
  useEffect(() => {
    if (!loading && puzzle && !localStorage.getItem(HELP_SEEN_KEY)) {
      setShowHelp(true);
    }
  }, [loading, puzzle]);

  // Auto-show mode tip for existing users (immediately on load)
  useEffect(() => {
    if (!loading && puzzle && localStorage.getItem(HELP_SEEN_KEY)) {
      if (!modeTipShownThisSession.current && getModeTipCount() < MODE_TIP_MAX) {
        incrementModeTipCount();
        modeTipShownThisSession.current = true;
        setShowModeTip(true);
      }
    }
  }, [loading, puzzle]);

  function closeHelp() {
    localStorage.setItem(HELP_SEEN_KEY, '1');
    setShowHelp(false);
    // Show mode tip to new users right after they close help
    if (!modeTipShownThisSession.current && getModeTipCount() < MODE_TIP_MAX) {
      incrementModeTipCount();
      modeTipShownThisSession.current = true;
      setShowModeTip(true);
    }
  }

  function closeModeTip() {
    setShowModeTip(false);
  }

  const handleToggleGameMode = useCallback(() => {
    setGameMode(prev => prev === 'easy' ? 'pro' : 'easy');
  }, []);

  const handleFirstGuess = useCallback(() => {
    setGameStarted(true);
  }, []);

  return (
    <div className="min-h-screen stadium-bg flex flex-col">
      {puzzle && <GameSEO puzzle={puzzle} />}
      {puzzle && (
        <Header
          edition={puzzle.edition}
          date={puzzle.date}
          gameMode={gameMode}
          gameStarted={gameStarted}
          onToggleGameMode={handleToggleGameMode}
          onHelp={() => setShowHelp(true)}
        />
      )}

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
          <GameBoard puzzle={puzzle} gameMode={gameMode} onFirstGuess={handleFirstGuess} />
        )}
      </main>

      {showHelp && <HelpModal onClose={closeHelp} />}
      {showModeTip && <GameModeTipModal onClose={closeModeTip} />}
    </div>
  );
}

export default App;
