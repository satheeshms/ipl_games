import type { GameState } from '../types';

const KEY = (prefix: string, id: string) => `${prefix}-${id}`;

// Fields to persist
type PersistedState = Pick<
  GameState,
  'gridItems' | 'selected' | 'revealedCategories' | 'lives' | 'guessHistory' | 'status' | 'hintedColors'
>;

export function saveState(prefix: string, puzzleId: string, state: PersistedState): void {
  try {
    localStorage.setItem(KEY(prefix, puzzleId), JSON.stringify(state));
  } catch {
    // localStorage unavailable — ignore
  }
}

export function loadState(prefix: string, puzzleId: string): PersistedState | null {
  try {
    const raw = localStorage.getItem(KEY(prefix, puzzleId));
    if (!raw) return null;
    return JSON.parse(raw) as PersistedState;
  } catch {
    return null;
  }
}

export function clearStaleStates(prefix: string, currentId: string): void {
  try {
    const keyPrefix = `${prefix}-`;
    const keep = new Set([KEY(prefix, currentId)]);
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith(keyPrefix) && !keep.has(key)) {
        localStorage.removeItem(key);
      }
    }
  } catch {
    // ignore
  }
}
