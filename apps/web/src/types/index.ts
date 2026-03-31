export type Color = 'yellow' | 'green' | 'blue' | 'purple';
export type GameMode = 'easy' | 'pro';

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
  /** Display-only map: canonical item name -> known popular name. Never used for hashing. */
  display_names?: Record<string, string>;
}

export type GameStatus = 'idle' | 'playing' | 'won' | 'lost';

export interface Guess {
  items: string[];          // 4 selected items
  correct: boolean;
  categoryColor?: Color;    // set if correct
  oneAwayColor?: Color;     // set if wrong but 3/4 items matched this category
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
  oneAwayWrongItem?: string; // set when one-away detected: the item that needs swapping
  hintedColors: Color[];    // colors whose titles have been revealed as hints (max 2)
}
