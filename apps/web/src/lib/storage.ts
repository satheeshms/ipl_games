import type { GameState } from '../types';

const KEY = (id: string) => `ipl-cluster4-${id}`;

// Fields to persist
type PersistedState = Pick<
  GameState,
  'gridItems' | 'selected' | 'revealedCategories' | 'lives' | 'guessHistory' | 'status' | 'hintedColors'
>;

export function saveState(puzzleId: string, state: PersistedState): void {
  try {
    localStorage.setItem(KEY(puzzleId), JSON.stringify(state));
  } catch {
    // localStorage unavailable — ignore
  }
}

export function loadState(puzzleId: string): PersistedState | null {
  try {
    const raw = localStorage.getItem(KEY(puzzleId));
    if (!raw) return null;
    return JSON.parse(raw) as PersistedState;
  } catch {
    return null;
  }
}

const MODAL_CLOSED_KEY = (id: string) => `ipl-cluster4-modal-closed-${id}`;

export function clearStaleStates(currentId: string): void {
  try {
    const prefix = 'ipl-cluster4-';
    const keep = new Set([KEY(currentId), MODAL_CLOSED_KEY(currentId)]);
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith(prefix) && !keep.has(key)) {
        localStorage.removeItem(key);
      }
    }
  } catch {
    // ignore
  }
}
