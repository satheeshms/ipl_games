import { describe, it, expect } from 'vitest';
import { gameReducer } from './useGameEngine';
import type { GameState, Puzzle } from '../types';

// ---------------------------------------------------------------------------
// Test fixture — mirrors dev.json structure
// ---------------------------------------------------------------------------

const DEV_PUZZLE: Puzzle = {
  id: 'dev',
  date: '2026-03-14',
  edition: 1,
  items: [
    'Thala', 'Rohit Sharma', 'Dwayne Bravo', 'MS Dhoni',
    'Shane Warne', 'Hitman', 'Yuzvendra Chahal', 'King',
    'Ruturaj Gaikwad', 'Harshal Patel', 'Adam Gilchrist', 'Universe Boss',
    'Bhuvneshwar Kumar', 'Gautam Gambhir', 'Deepak Chahar', 'Ravindra Jadeja',
  ],
  categories: [
    {
      color: 'yellow',
      title: 'CSK Players',
      hash: '753706144fc233169880b91c9005090779ac9a468be8f76632d9499979e891b3',
    },
    {
      color: 'green',
      title: 'Purple Cap Winners',
      hash: '6437fb428c7b3343eadf2e14b4304447f0a04c5ca68181dfc3af5e6cbc6ebc04',
    },
    {
      color: 'blue',
      title: 'IPL Winning Captains (first time)',
      hash: '1c220d9dce0fed47b30cac25aba057809f10713da8fc7b4c54dadd89f6129e9e',
    },
    {
      color: 'purple',
      title: 'Player Nicknames',
      hash: '58d9d8330433ba08338a9f9834d8ff62cbdc165806cbddf6b7edbffea508d23a',
    },
  ],
};

// ---------------------------------------------------------------------------
// Helper — build a base state for test scenarios
// ---------------------------------------------------------------------------

const basePlayingState: GameState = {
  puzzle: DEV_PUZZLE,
  gridItems: [...DEV_PUZZLE.items],
  selected: [],
  revealedCategories: [],
  lives: 4,
  guessHistory: [],
  status: 'playing',
  oneAway: false,
  hintedColors: [],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('gameReducer', () => {
  // -------------------------------------------------------------------------
  // LOAD_PUZZLE
  // -------------------------------------------------------------------------
  describe('LOAD_PUZZLE', () => {
    it('fresh start: gridItems contains all 16 items, lives=4, status=playing', () => {
      const initialState: GameState = {
        puzzle: null,
        gridItems: [],
        selected: [],
        revealedCategories: [],
        lives: 4,
        guessHistory: [],
        status: 'idle',
        oneAway: false,
        hintedColors: [],
      };

      const next = gameReducer(initialState, {
        type: 'LOAD_PUZZLE', payload: { gameMode: 'pro', puzzle: DEV_PUZZLE },
      });

      expect(next.puzzle).toBe(DEV_PUZZLE);
      expect(next.gridItems).toHaveLength(16);
      // All original items should be present (just shuffled)
      expect([...next.gridItems].sort()).toEqual([...DEV_PUZZLE.items].sort());
      expect(next.lives).toBe(4);
      expect(next.status).toBe('playing');
      expect(next.selected).toEqual([]);
      expect(next.revealedCategories).toEqual([]);
      expect(next.guessHistory).toEqual([]);
    });

    it('with savedState: restores revealedCategories, lives, guessHistory and status', () => {
      const initialState: GameState = {
        puzzle: null,
        gridItems: [],
        selected: [],
        revealedCategories: [],
        lives: 4,
        guessHistory: [],
        status: 'idle',
        oneAway: false,
        hintedColors: [],
      };

      const savedState: Partial<GameState> = {
        gridItems: ['Thala', 'Rohit Sharma', 'Dwayne Bravo', 'MS Dhoni'],
        selected: [],
        revealedCategories: ['yellow', 'green'],
        lives: 2,
        guessHistory: [
          { items: ['a', 'b', 'c', 'd'], correct: false },
          { items: ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Ravindra Jadeja'], correct: true, categoryColor: 'yellow' },
        ],
        status: 'playing',
      };

      const next = gameReducer(initialState, {
        type: 'LOAD_PUZZLE', payload: { gameMode: 'pro', puzzle: DEV_PUZZLE, savedState },
      });

      expect(next.puzzle).toBe(DEV_PUZZLE);
      expect(next.revealedCategories).toEqual(['yellow', 'green']);
      expect(next.lives).toBe(2);
      expect(next.guessHistory).toHaveLength(2);
      expect(next.status).toBe('playing');
      expect(next.gridItems).toEqual(['Thala', 'Rohit Sharma', 'Dwayne Bravo', 'MS Dhoni']);
    });

    it('ignores savedState with empty gridItems and starts fresh', () => {
      const initialState: GameState = {
        puzzle: null,
        gridItems: [],
        selected: [],
        revealedCategories: [],
        lives: 4,
        guessHistory: [],
        status: 'idle',
        oneAway: false,
        hintedColors: [],
      };

      // savedState has empty gridItems — treated as invalid
      const next = gameReducer(initialState, {
        type: 'LOAD_PUZZLE',
        payload: {
          gameMode: 'pro',
          puzzle: DEV_PUZZLE,
          savedState: { gridItems: [], status: 'playing', revealedCategories: [], lives: 3, guessHistory: [], selected: [] },
        },
      });

      expect(next.gridItems).toHaveLength(16);
      expect(next.lives).toBe(4);
    });
  });

  // -------------------------------------------------------------------------
  // SELECT_ITEM
  // -------------------------------------------------------------------------
  describe('SELECT_ITEM', () => {
    it('adds an item to selected', () => {
      const next = gameReducer(basePlayingState, {
        type: 'SELECT_ITEM',
        payload: { item: 'MS Dhoni' },
      });
      expect(next.selected).toContain('MS Dhoni');
      expect(next.selected).toHaveLength(1);
    });

    it('is a no-op when item is already selected', () => {
      const stateWithOne: GameState = { ...basePlayingState, selected: ['MS Dhoni'] };
      const next = gameReducer(stateWithOne, {
        type: 'SELECT_ITEM',
        payload: { item: 'MS Dhoni' },
      });
      expect(next.selected).toHaveLength(1);
    });

    it('is a no-op when selected.length === 4', () => {
      const fullSelected: GameState = {
        ...basePlayingState,
        selected: ['MS Dhoni', 'Rohit Sharma', 'Thala', 'Hitman'],
      };
      const next = gameReducer(fullSelected, {
        type: 'SELECT_ITEM',
        payload: { item: 'King' },
      });
      expect(next.selected).toHaveLength(4);
      expect(next.selected).not.toContain('King');
    });

    it('allows selecting up to 4 items', () => {
      let state = basePlayingState;
      state = gameReducer(state, { type: 'SELECT_ITEM', payload: { item: 'MS Dhoni' } });
      state = gameReducer(state, { type: 'SELECT_ITEM', payload: { item: 'Rohit Sharma' } });
      state = gameReducer(state, { type: 'SELECT_ITEM', payload: { item: 'Thala' } });
      state = gameReducer(state, { type: 'SELECT_ITEM', payload: { item: 'Hitman' } });
      expect(state.selected).toHaveLength(4);
    });
  });

  // -------------------------------------------------------------------------
  // DESELECT_ITEM
  // -------------------------------------------------------------------------
  describe('DESELECT_ITEM', () => {
    it('removes an item from selected', () => {
      const stateWithItems: GameState = {
        ...basePlayingState,
        selected: ['MS Dhoni', 'Rohit Sharma'],
      };
      const next = gameReducer(stateWithItems, {
        type: 'DESELECT_ITEM',
        payload: { item: 'MS Dhoni' },
      });
      expect(next.selected).not.toContain('MS Dhoni');
      expect(next.selected).toContain('Rohit Sharma');
    });

    it('is a no-op if item is not in selected', () => {
      const stateWithItems: GameState = {
        ...basePlayingState,
        selected: ['Rohit Sharma'],
      };
      const next = gameReducer(stateWithItems, {
        type: 'DESELECT_ITEM',
        payload: { item: 'MS Dhoni' },
      });
      expect(next.selected).toEqual(['Rohit Sharma']);
    });
  });

  // -------------------------------------------------------------------------
  // DESELECT_ALL
  // -------------------------------------------------------------------------
  describe('DESELECT_ALL', () => {
    it('clears all selected items', () => {
      const stateWithItems: GameState = {
        ...basePlayingState,
        selected: ['MS Dhoni', 'Rohit Sharma', 'Thala', 'Hitman'],
      };
      const next = gameReducer(stateWithItems, { type: 'DESELECT_ALL' });
      expect(next.selected).toEqual([]);
    });
  });

  // -------------------------------------------------------------------------
  // SHUFFLE
  // -------------------------------------------------------------------------
  describe('SHUFFLE', () => {
    it('keeps the same set of items after shuffle', () => {
      const next = gameReducer(basePlayingState, { type: 'SHUFFLE' });
      expect(next.gridItems).toHaveLength(basePlayingState.gridItems.length);
      expect([...next.gridItems].sort()).toEqual([...basePlayingState.gridItems].sort());
    });

    it('does not mutate selected, lives, or status', () => {
      const stateWithSome: GameState = {
        ...basePlayingState,
        selected: ['MS Dhoni'],
        lives: 3,
      };
      const next = gameReducer(stateWithSome, { type: 'SHUFFLE' });
      expect(next.selected).toEqual(['MS Dhoni']);
      expect(next.lives).toBe(3);
      expect(next.status).toBe('playing');
    });
  });

  // -------------------------------------------------------------------------
  // REVEAL_CATEGORY
  // -------------------------------------------------------------------------
  describe('REVEAL_CATEGORY', () => {
    it('removes selected items from gridItems and adds color to revealedCategories', () => {
      const cskItems = ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Ravindra Jadeja'];
      const stateBeforeReveal: GameState = {
        ...basePlayingState,
        selected: cskItems,
      };

      const next = gameReducer(stateBeforeReveal, {
        type: 'REVEAL_CATEGORY',
        payload: { color: 'yellow' },
      });

      // All selected items removed from gridItems
      for (const item of cskItems) {
        expect(next.gridItems).not.toContain(item);
      }
      expect(next.gridItems).toHaveLength(12); // 16 - 4 = 12
      expect(next.revealedCategories).toContain('yellow');
      expect(next.selected).toEqual([]);
    });

    it('records a correct guess in guessHistory', () => {
      const cskItems = ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Ravindra Jadeja'];
      const stateBeforeReveal: GameState = {
        ...basePlayingState,
        selected: cskItems,
      };

      const next = gameReducer(stateBeforeReveal, {
        type: 'REVEAL_CATEGORY',
        payload: { color: 'yellow' },
      });

      expect(next.guessHistory).toHaveLength(1);
      expect(next.guessHistory[0].correct).toBe(true);
      expect(next.guessHistory[0].categoryColor).toBe('yellow');
      expect(next.guessHistory[0].items).toEqual(cskItems);
    });
  });

  // -------------------------------------------------------------------------
  // WRONG_GUESS
  // -------------------------------------------------------------------------
  describe('WRONG_GUESS', () => {
    it('decrements lives, clears selected, and records incorrect guess', () => {
      const stateWithSome: GameState = {
        ...basePlayingState,
        selected: ['Thala', 'Rohit Sharma', 'Hitman', 'King'],
      };
      const next = gameReducer(stateWithSome, {
        type: 'WRONG_GUESS',
        payload: { oneAway: false },
      });

      expect(next.lives).toBe(3);
      expect(next.selected).toEqual([]);
      expect(next.oneAway).toBe(false);
      expect(next.guessHistory).toHaveLength(1);
      expect(next.guessHistory[0].correct).toBe(false);
      expect(next.guessHistory[0].items).toEqual(['Thala', 'Rohit Sharma', 'Hitman', 'King']);
    });

    it('sets oneAway = true when oneAway payload is true', () => {
      const stateWithSome: GameState = {
        ...basePlayingState,
        selected: ['Thala', 'Rohit Sharma', 'Hitman', 'King'],
      };
      const next = gameReducer(stateWithSome, {
        type: 'WRONG_GUESS',
        payload: { oneAway: true },
      });

      expect(next.oneAway).toBe(true);
      expect(next.lives).toBe(3);
    });
  });

  // -------------------------------------------------------------------------
  // CLEAR_ONE_AWAY
  // -------------------------------------------------------------------------
  describe('CLEAR_ONE_AWAY', () => {
    it('sets oneAway to false', () => {
      const stateWithOneAway: GameState = { ...basePlayingState, oneAway: true };
      const next = gameReducer(stateWithOneAway, { type: 'CLEAR_ONE_AWAY' });
      expect(next.oneAway).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // GAME_OVER
  // -------------------------------------------------------------------------
  describe('GAME_OVER', () => {
    it('sets status to won', () => {
      const next = gameReducer(basePlayingState, {
        type: 'GAME_OVER',
        payload: { status: 'won' },
      });
      expect(next.status).toBe('won');
    });

    it('sets status to lost', () => {
      const next = gameReducer(basePlayingState, {
        type: 'GAME_OVER',
        payload: { status: 'lost' },
      });
      expect(next.status).toBe('lost');
    });

    it('does not change other state fields', () => {
      const next = gameReducer(basePlayingState, {
        type: 'GAME_OVER',
        payload: { status: 'won' },
      });
      expect(next.lives).toBe(basePlayingState.lives);
      expect(next.gridItems).toEqual(basePlayingState.gridItems);
    });
  });

  // -------------------------------------------------------------------------
  // Multi-action sequences
  // -------------------------------------------------------------------------
  describe('multi-action sequences', () => {
    it('select 4 items then reveal a category leaves 12 grid items', () => {
      const cskItems = ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Ravindra Jadeja'];
      let state = basePlayingState;

      for (const item of cskItems) {
        state = gameReducer(state, { type: 'SELECT_ITEM', payload: { item } });
      }
      expect(state.selected).toHaveLength(4);

      state = gameReducer(state, { type: 'REVEAL_CATEGORY', payload: { color: 'yellow' } });
      expect(state.gridItems).toHaveLength(12);
      expect(state.revealedCategories).toEqual(['yellow']);
      expect(state.guessHistory).toHaveLength(1);
    });

    it('wrong guess decrements lives and losing all lives does not auto set status (GAME_OVER is separate dispatch)', () => {
      let state: GameState = { ...basePlayingState, lives: 1, selected: ['a', 'b', 'c', 'd'] };
      state = gameReducer(state, { type: 'WRONG_GUESS', payload: { oneAway: false } });
      // lives should be 0 but status is still 'playing' — GAME_OVER is a separate dispatch
      expect(state.lives).toBe(0);
      expect(state.status).toBe('playing');

      // The hook dispatches GAME_OVER separately
      state = gameReducer(state, { type: 'GAME_OVER', payload: { status: 'lost' } });
      expect(state.status).toBe('lost');
    });
  });
});
