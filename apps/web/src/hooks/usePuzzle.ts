import { useState, useEffect } from 'react';
import type { Puzzle } from '../types';

interface UsePuzzleResult {
  puzzle: Puzzle | null;
  loading: boolean;
  error: string | null;
}

function getTodayDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function usePuzzle(): UsePuzzleResult {
  const [puzzle, setPuzzle] = useState<Puzzle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchPuzzle() {
      setLoading(true);
      setError(null);

      const today = getTodayDateString();

      // Try fetching today's puzzle first
      try {
        const res = await fetch(`${import.meta.env.BASE_URL}puzzles/${today}.json`);
        if (res.ok) {
          const data: Puzzle = await res.json();
          if (!cancelled) {
            setPuzzle(data);
            setLoading(false);
          }
          return;
        }
      } catch {
        // Fall through to dev.json fallback
      }

      // Fall back to dev.json
      try {
        const res = await fetch(`${import.meta.env.BASE_URL}puzzles/dev.json`);
        if (!res.ok) {
          throw new Error(`Failed to load dev puzzle: ${res.status} ${res.statusText}`);
        }
        const data: Puzzle = await res.json();
        if (!cancelled) {
          setPuzzle(data);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load puzzle');
          setLoading(false);
        }
      }
    }

    fetchPuzzle();

    return () => {
      cancelled = true;
    };
  }, []);

  return { puzzle, loading, error };
}
