export type Color = 'yellow' | 'green' | 'blue' | 'purple';

export interface PuzzleCategory {
  color: Color;
  title: string;
  hash: string;
}

export interface Puzzle {
  id: string;
  date: string;
  edition: number;
  items: string[];
  categories: PuzzleCategory[];
}

export type GameStatus = 'idle' | 'playing' | 'won' | 'lost';

export interface Guess {
  items: string[];          // 4 selected items
  correct: boolean;
  categoryColor?: Color;    // set if correct
}

export interface GameState {
  puzzle: Puzzle | null;
  gridItems: string[];      // items remaining in grid (shuffled)
  selected: string[];       // currently selected items (max 4)
  revealedCategories: Color[];
  lives: number;            // starts at 4
  guessHistory: Guess[];
  status: GameStatus;
  oneAway: boolean;         // transient flag for "One Away!" toast
}
