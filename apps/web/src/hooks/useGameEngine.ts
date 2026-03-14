import { useReducer, useEffect, useCallback } from 'react';
import type { GameState, Color, Puzzle } from '../types';
import { shuffle } from '../lib/shuffle';
import { hashItems } from '../lib/hash';
import { saveState, loadState } from '../lib/storage';

// ---------------------------------------------------------------------------
// Action definitions
// ---------------------------------------------------------------------------

type GameAction =
  | { type: 'LOAD_PUZZLE'; payload: { puzzle: Puzzle; savedState?: Partial<GameState> } }
  | { type: 'SELECT_ITEM'; payload: { item: string } }
  | { type: 'DESELECT_ITEM'; payload: { item: string } }
  | { type: 'DESELECT_ALL' }
  | { type: 'SHUFFLE' }
  | { type: 'REVEAL_CATEGORY'; payload: { color: Color } }
  | { type: 'WRONG_GUESS'; payload: { oneAway: boolean } }
  | { type: 'CLEAR_ONE_AWAY' }
  | { type: 'GAME_OVER'; payload: { status: 'won' | 'lost' } };

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const initialState: GameState = {
  puzzle: null,
  gridItems: [],
  selected: [],
  revealedCategories: [],
  lives: 4,
  guessHistory: [],
  status: 'idle',
  oneAway: false,
};

// ---------------------------------------------------------------------------
// Reducer (pure / synchronous) — exported for unit testing
// ---------------------------------------------------------------------------

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'LOAD_PUZZLE': {
      const { puzzle, savedState } = action.payload;

      // If we have a valid saved state, restore it
      if (
        savedState &&
        savedState.gridItems &&
        savedState.gridItems.length > 0 &&
        savedState.status &&
        savedState.status !== 'idle'
      ) {
        return {
          ...initialState,
          ...savedState,
          puzzle,
        };
      }

      // Fresh start
      return {
        ...initialState,
        puzzle,
        gridItems: shuffle(puzzle.items),
        status: 'playing',
      };
    }

    case 'SELECT_ITEM': {
      const { item } = action.payload;
      if (state.selected.length >= 4 || state.selected.includes(item)) {
        return state;
      }
      return { ...state, selected: [...state.selected, item] };
    }

    case 'DESELECT_ITEM': {
      return {
        ...state,
        selected: state.selected.filter(i => i !== action.payload.item),
      };
    }

    case 'DESELECT_ALL': {
      return { ...state, selected: [] };
    }

    case 'SHUFFLE': {
      return { ...state, gridItems: shuffle(state.gridItems) };
    }

    case 'REVEAL_CATEGORY': {
      const { color } = action.payload;
      // Remove selected items from gridItems
      const newGridItems = state.gridItems.filter(i => !state.selected.includes(i));
      return {
        ...state,
        gridItems: newGridItems,
        revealedCategories: [...state.revealedCategories, color],
        guessHistory: [
          ...state.guessHistory,
          { items: [...state.selected], correct: true, categoryColor: color },
        ],
        selected: [],
      };
    }

    case 'WRONG_GUESS': {
      return {
        ...state,
        lives: state.lives - 1,
        selected: [],
        oneAway: action.payload.oneAway,
        guessHistory: [
          ...state.guessHistory,
          { items: [...state.selected], correct: false },
        ],
      };
    }

    case 'CLEAR_ONE_AWAY': {
      return { ...state, oneAway: false };
    }

    case 'GAME_OVER': {
      return { ...state, status: action.payload.status };
    }

    default: {
      return state;
    }
  }
}

// ---------------------------------------------------------------------------
// Hook return type
// ---------------------------------------------------------------------------

interface UseGameEngineResult {
  state: GameState;
  selectItem: (item: string) => void;
  deselectItem: (item: string) => void;
  deselectAll: () => void;
  shuffle: () => void;
  submitGuess: () => Promise<void>;
  loadPuzzle: (puzzle: Puzzle) => void;
  clearOneAway: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useGameEngine(): UseGameEngineResult {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // Persist state to localStorage after every meaningful change
  useEffect(() => {
    if (!state.puzzle || state.status === 'idle') return;
    saveState(state.puzzle.id, {
      gridItems: state.gridItems,
      selected: state.selected,
      revealedCategories: state.revealedCategories,
      lives: state.lives,
      guessHistory: state.guessHistory,
      status: state.status,
    });
  }, [state]);

  // ------------------------------------------------------------------
  // loadPuzzle — loads saved state then dispatches LOAD_PUZZLE
  // ------------------------------------------------------------------
  const loadPuzzle = useCallback((puzzle: Puzzle) => {
    const savedState = loadState(puzzle.id);
    dispatch({
      type: 'LOAD_PUZZLE',
      payload: { puzzle, savedState: savedState ?? undefined },
    });
  }, []);

  // ------------------------------------------------------------------
  // Simple sync dispatchers
  // ------------------------------------------------------------------
  const selectItem = useCallback((item: string) => {
    dispatch({ type: 'SELECT_ITEM', payload: { item } });
  }, []);

  const deselectItem = useCallback((item: string) => {
    dispatch({ type: 'DESELECT_ITEM', payload: { item } });
  }, []);

  const deselectAll = useCallback(() => {
    dispatch({ type: 'DESELECT_ALL' });
  }, []);

  const shuffleItems = useCallback(() => {
    dispatch({ type: 'SHUFFLE' });
  }, []);

  const clearOneAway = useCallback(() => {
    dispatch({ type: 'CLEAR_ONE_AWAY' });
  }, []);

  // ------------------------------------------------------------------
  // submitGuess — async; does hash verification then dispatches
  // ------------------------------------------------------------------
  const submitGuess = useCallback(async () => {
    // Capture a snapshot from the ref to avoid stale closure issues.
    // We need the current state, so we use a functional approach with
    // a separate state ref — but since this is a simple hook, we read
    // state directly (it's the latest render's state when called).
    if (state.selected.length !== 4 || state.status !== 'playing') return;
    if (!state.puzzle) return;

    const { selected, puzzle, gridItems, revealedCategories } = state;

    // Hash the selected items
    const guessHash = await hashItems(selected);

    // Check against every category hash
    const matchedCategory = puzzle.categories.find(cat => cat.hash === guessHash);

    if (matchedCategory) {
      dispatch({ type: 'REVEAL_CATEGORY', payload: { color: matchedCategory.color } });

      // Check for win: all 4 categories revealed after this one
      if (revealedCategories.length + 1 === puzzle.categories.length) {
        dispatch({ type: 'GAME_OVER', payload: { status: 'won' } });
      }
      return;
    }

    // --- One-away detection ---
    // For each category hash, try all C(4,3)=4 combos of 3 from selected
    // plus each remaining grid item not in selected. If any 4-combo hashes match → oneAway.
    const remainingItems = gridItems.filter(gi => !selected.includes(gi));

    let oneAway = false;

    outer: for (const category of puzzle.categories) {
      // Try removing each of the 4 selected items to get a 3-combo
      for (let removeIdx = 0; removeIdx < selected.length; removeIdx++) {
        const threesome = selected.filter((_, idx) => idx !== removeIdx);
        // Try adding each remaining grid item
        for (const candidate of remainingItems) {
          const fourCombo = [...threesome, candidate];
          // eslint-disable-next-line no-await-in-loop
          const comboHash = await hashItems(fourCombo);
          if (comboHash === category.hash) {
            oneAway = true;
            break outer;
          }
        }
      }
    }

    dispatch({ type: 'WRONG_GUESS', payload: { oneAway } });

    // lives - 1 because the reducer hasn't run yet at this point
    if (state.lives - 1 === 0) {
      dispatch({ type: 'GAME_OVER', payload: { status: 'lost' } });
    }
  }, [state]);

  return {
    state,
    selectItem,
    deselectItem,
    deselectAll,
    shuffle: shuffleItems,
    submitGuess,
    loadPuzzle,
    clearOneAway,
  };
}
