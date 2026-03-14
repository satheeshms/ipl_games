# IPL Connections — Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-03-14
**Status:** Draft
**References:** `specs/connections/requirements.md`

---

## 1. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend framework | React 18 + Vite | Fast dev/build, small bundle, static output |
| Language | TypeScript | Type safety for game state and puzzle schema |
| Styling | Tailwind CSS v3 | Responsive-first, no runtime overhead |
| Animation | Framer Motion | Tile fly-up and reveal animations |
| State management | `useReducer` + Context | Sufficient complexity — no external lib needed |
| PWA | `vite-plugin-pwa` | Service worker + manifest with zero config |
| Testing | Vitest + React Testing Library | Vite-native, fast |
| Data pipeline | Python 3.11+ | Scraping, data normalization |
| Puzzle curator | Python CLI (Click) | Interactive puzzle builder |
| Hashing (browser) | Web Crypto API (`SubtleCrypto`) | Native, no dependency |
| Hashing (curator) | Python `hashlib` | Standard lib, matches browser output |
| Deployment | GitHub Pages / Vercel | Static hosting, no server needed |

---

## 2. Repository Structure

```
ipl_games/
├── apps/
│   └── web/                          # React frontend
│       ├── public/
│       │   ├── puzzles/              # Static puzzle JSONs (YYYY-MM-DD.json)
│       │   └── icons/                # PWA icons
│       ├── src/
│       │   ├── components/           # UI components
│       │   ├── hooks/                # Game engine + utilities
│       │   ├── lib/                  # Pure utility functions
│       │   └── types/                # TypeScript types
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.ts
│       └── tsconfig.json
│
├── packages/
│   ├── data-pipeline/                # IPL data collection (Python)
│   │   ├── scrapers/                 # Source-specific scrapers
│   │   │   ├── espncricinfo.py
│   │   │   └── kaggle_loader.py
│   │   ├── normalizer.py             # Merge + deduplicate into data store
│   │   ├── data/                     # Output: ipl_data.json / ipl.db
│   │   └── requirements.txt
│   │
│   └── puzzle-curator/               # Puzzle builder CLI (Python)
│       ├── curator.py
│       ├── hash_util.py              # Must match browser hash implementation
│       └── requirements.txt
│
├── specs/
│   └── connections/
│       ├── requirements.md
│       └── implementation_plan.md    # (this file)
│
└── README.md
```

---

## 3. Puzzle JSON Format

The puzzle JSON stores items **flat** (shuffled). Category membership is hidden behind per-category SHA-256 hashes. Category **titles** are included — knowing a title ("CSK Players") does not spoil which items belong to it.

```jsonc
// public/puzzles/2026-03-15.json
{
  "id": "2026-03-15",
  "date": "2026-03-15",
  "edition": 1,
  "items": [
    // 16 items in shuffled order — no category grouping visible
    "Thala", "Rohit Sharma", "Dwayne Bravo", "MS Dhoni",
    "Shane Warne", "Hitman", "Yuzvendra Chahal", "King",
    "Ruturaj Gaikwad", "Harshal Patel", "Adam Gilchrist", "Universe Boss",
    "Bhuvneshwar Kumar", "Gautam Gambhir", "Deepak Chahar", "Ravindra Jadeja"
  ],
  "categories": [
    {
      "color": "yellow",
      "title": "CSK Players",
      "hash": "<sha256>"   // SHA-256 of sorted items of this category
    },
    {
      "color": "green",
      "title": "Purple Cap Winners",
      "hash": "<sha256>"
    },
    {
      "color": "blue",
      "title": "IPL Winning Captains (first time)",
      "hash": "<sha256>"
    },
    {
      "color": "purple",
      "title": "Player Nicknames",
      "hash": "<sha256>"
    }
  ]
}
```

### Hash Specification

```
input  = items.sort().join("|")   // e.g. "Deepak Chahar|MS Dhoni|Ravindra Jadeja|Ruturaj Gaikwad"
hash   = SHA-256(input)           // hex string, lowercase
```

- Items are sorted case-insensitively before joining.
- The same algorithm is implemented in both `lib/hash.ts` (browser) and `hash_util.py` (curator).
- Curator validates the round-trip before writing the puzzle file.

---

## 4. TypeScript Types

```typescript
// src/types/index.ts

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
```

---

## 5. Component Architecture

```
App
├── usePuzzle (fetch + parse puzzle JSON)
├── Header
│   └── HelpModal (shown on "?" click)
├── GameBoard (receives puzzle, owns game state via useGameEngine)
│   ├── CategoryBanner × n (revealed categories, stacked above grid)
│   ├── ItemGrid
│   │   └── ItemTile × 16 (selectable, shake animation on wrong guess)
│   ├── LivesIndicator (4 circles: filled = life remaining)
│   ├── ToastNotification ("One Away!", "Already guessed!")
│   └── ActionBar
│       ├── ShuffleButton
│       ├── DeselectAllButton
│       └── SubmitButton (disabled unless exactly 4 selected)
└── ResultsModal (shown on win/loss)
    ├── EmojiGrid (guess history as colored squares)
    └── ShareButton
```

---

## 6. Game Engine (`useGameEngine`)

Central `useReducer` hook. All game logic lives here — components are display-only.

### State

```typescript
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
```

### Actions

| Action | Payload | Description |
|---|---|---|
| `LOAD_PUZZLE` | `Puzzle, savedState?` | Initialize game; restore from localStorage if available |
| `SELECT_ITEM` | `item: string` | Add to selected (max 4) |
| `DESELECT_ITEM` | `item: string` | Remove from selected |
| `DESELECT_ALL` | — | Clear selection |
| `SHUFFLE` | — | Fisher-Yates shuffle of `gridItems` |
| `SUBMIT_GUESS` | `matchedColor?: Color` | Process the 4-item guess (async result fed back in) |
| `REVEAL_CATEGORY` | `color: Color` | Move matched items out of grid into revealed banners |
| `WRONG_GUESS` | `oneAway: boolean` | Deduct life, clear selection, set oneAway flag |
| `CLEAR_ONE_AWAY` | — | Clear toast after timeout |
| `GAME_OVER` | `status: 'won'\|'lost'` | Set terminal status, reveal all categories |

### Submit Flow (async, in `GameBoard`)

```
1. User clicks Submit
2. Hash selected items (Web Crypto — async)
3. Compare hash against each category.hash in puzzle
4. If match found → dispatch REVEAL_CATEGORY + check for win
5. If no match → check "one away" (try removing each item, recheck) → dispatch WRONG_GUESS
6. If lives === 0 → dispatch GAME_OVER('lost')
```

The submit is handled in `GameBoard` as an async callback, keeping the reducer synchronous and pure.

---

## 7. Key Utility Implementations

### `lib/hash.ts`

```typescript
export async function hashItems(items: string[]): Promise<string> {
  const sorted = [...items].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  const input = sorted.join('|');
  const encoded = new TextEncoder().encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
```

### `lib/shuffle.ts`

```typescript
export function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
```

### `lib/share.ts`

```typescript
const EMOJI: Record<Color, string> = {
  yellow: '🟨', green: '🟩', blue: '🟦', purple: '🟪',
};

export function buildShareText(puzzle: Puzzle, guessHistory: Guess[]): string {
  const header = `IPL Connections #${puzzle.edition} — ${formatDate(puzzle.date)}`;
  const grid = guessHistory
    .map(g => Array(4).fill(EMOJI[g.categoryColor ?? 'yellow']).join(''))
    // For wrong guesses, show each item's actual category color
    .join('\n');
  return `${header}\n${grid}`;
}
```

> Note: For incorrect guesses, each square in the row reflects the true category color of each item in the selection, preserving the NYT Connections format.

### `lib/storage.ts`

```typescript
const KEY = (id: string) => `ipl-connections-${id}`;

export function saveState(puzzleId: string, state: Partial<GameState>) { ... }
export function loadState(puzzleId: string): Partial<GameState> | null { ... }
export function clearStaleStates(currentId: string) { ... } // remove other puzzle keys
```

---

## 8. Session Persistence

On `LOAD_PUZZLE`:
1. Check `localStorage` for key `ipl-connections-{puzzleId}`.
2. If found and valid, restore: `gridItems`, `selected`, `revealedCategories`, `lives`, `guessHistory`, `status`.
3. If not found, start fresh.

After every state-changing action, the reducer's output is persisted to `localStorage` via a `useEffect` in `GameBoard`.

Fields persisted: `gridItems`, `selected`, `revealedCategories`, `lives`, `guessHistory`, `status`.

---

## 9. PWA Configuration

```typescript
// vite.config.ts (vite-plugin-pwa)
VitePWA({
  registerType: 'autoUpdate',
  manifest: {
    name: 'IPL Connections',
    short_name: 'IPL Connect',
    theme_color: '#1a1a2e',
    background_color: '#1a1a2e',
    display: 'standalone',
    icons: [{ src: 'icons/192.png', sizes: '192x192' }, { src: 'icons/512.png', sizes: '512x512' }],
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
    runtimeCaching: [{
      urlPattern: /\/puzzles\/.*\.json$/,
      handler: 'NetworkFirst',        // try network, fall back to cache
      options: { cacheName: 'puzzles', expiration: { maxAgeSeconds: 86400 } },
    }],
  },
})
```

---

## 10. Data Pipeline (`packages/data-pipeline`)

### Sources & Scripts

| Script | Source | Output |
|---|---|---|
| `kaggle_loader.py` | Kaggle IPL dataset CSV | Normalized player/team/award records |
| `espncricinfo.py` | Web scraping (respectful, rate-limited) | Recent season stats, squad lists |
| `normalizer.py` | All scrapers | `data/ipl_data.json` + `data/ipl.db` (SQLite) |

### Data Schema (SQLite)

```sql
-- Key tables (curator queries these)
players(id, name, nicknames, nationality, batting_hand, bowling_hand)
teams(id, name, short_name, city, home_venue, active_from, active_to)
player_teams(player_id, team_id, season)
awards(type, player_id, season)          -- type: orange_cap, purple_cap, mvp
ipl_wins(team_id, season, captain_id)
venues(id, name, city, aliases)
```

### Running the Pipeline

```bash
cd packages/data-pipeline
pip install -r requirements.txt
python normalizer.py            # fetches all sources, writes data/
```

---

## 11. Puzzle Curator CLI (`packages/puzzle-curator`)

### Usage

```bash
cd packages/puzzle-curator
pip install -r requirements.txt

# Create puzzle for a specific date (interactive)
python curator.py create --date 2026-03-20 --output ../apps/web/public/puzzles/

# Validate an existing puzzle file
python curator.py validate --file ../apps/web/public/puzzles/2026-03-20.json
```

### `create` Flow

```
1. Load ipl_data.db
2. Prompt: enter 4 category titles and colors (yellow/green/blue/purple)
3. For each category: search data store and select 4 items
4. Validate: no duplicate items across categories
5. Compute SHA-256 hash for each category (hash_util.py)
6. Shuffle all 16 items
7. Write puzzle JSON to output path
8. Print summary for manual review
```

### `hash_util.py` (must match browser implementation exactly)

```python
import hashlib

def hash_items(items: list[str]) -> str:
    sorted_items = sorted(items, key=str.casefold)
    input_str = "|".join(sorted_items)
    return hashlib.sha256(input_str.encode("utf-8")).hexdigest()
```

---

## 12. Implementation Phases

### Phase 1 — Project Scaffold (Week 1)
- [x] Init Vite + React + TypeScript project in `apps/web/`
- [x] Configure Tailwind CSS
- [x] Define all TypeScript types (`src/types/index.ts`)
- [x] Implement `lib/hash.ts` and `lib/shuffle.ts`
- [x] Create sample puzzle JSON for local dev (`public/puzzles/dev.json`)
- [x] `usePuzzle` hook: load puzzle by today's date, fall back to `dev.json`

### Phase 2 — Game Engine (Week 1)
- [x] Implement `useGameEngine` reducer with all actions
- [x] Submit flow: async hash check, one-away detection, life deduction
- [x] `lib/storage.ts`: localStorage save/load/clearStale helpers
- [x] Unit tests for reducer logic (Vitest) — 28 tests passing
- [x] Unit tests for `hash.ts` (verify matches `hash_util.py` output)

### Phase 3 — Core UI (Week 2)
- [x] `Header`, `ItemGrid`, `ItemTile` (select/deselect)
- [x] `CategoryBanner` (revealed group)
- [x] `LivesIndicator`
- [x] `ActionBar` (Shuffle, Deselect All, Submit)
- [x] Wire components to `useGameEngine`
- [x] Basic Tailwind styling, mobile layout

### Phase 4 — Animations (Week 2)
- [x] Tile shake animation on wrong guess (CSS keyframe)
- [x] Correct group reveal: tiles bounce then banner spring slides in (Framer Motion)
- [x] "One Away!" toast with auto-dismiss (AnimatePresence fade + slide)
- [x] Smooth tile deselection on wrong guess
- [x] Framer Motion installed; `useGameEngine` gained `revealCategory()` + `wrongGuess()` for animation-controlled dispatch timing; hash logic moved to `GameBoard.handleSubmit`

### Phase 5 — Session & Sharing (Week 3)
- [ ] `lib/storage.ts` + `useLocalStorage` hook
- [ ] Persist and restore game state per puzzle ID
- [ ] `ResultsModal`: emoji grid + share button
- [ ] `lib/share.ts`: build share text, clipboard copy, Web Share API

### Phase 6 — Help Modal & Polish (Week 3)
- [ ] `HelpModal` with rules, color key, animated example
- [ ] Accessibility: ARIA labels, keyboard nav (Tab + Enter)
- [ ] Contrast audit (≥ 4.5:1 on all tile text)
- [ ] Loading state while puzzle JSON fetches

### Phase 7 — PWA (Week 4)
- [ ] `vite-plugin-pwa` setup
- [ ] Offline: cache puzzle JSON + all assets
- [ ] App manifest: icons, theme, display mode
- [ ] Test offline mode in Chrome DevTools

### Phase 8 — Data Pipeline (Week 4)
- [x] `kaggle_loader.py`: load IPL CSVs into SQLite (`packages/data-pipeline/kaggle_loader.py` + `schema.py`)
- [x] `normalizer.py`: unified schema
- [ ] `espncricinfo.py`: basic squad/award scraper (rate-limited)
- [ ] Manual data entry: nicknames, slogans, wordplay items

### Phase 9 — Puzzle Curator (Week 5)
- [x] `curator.py create` interactive flow
- [x] `curator.py validate` for existing files
- [x] `hash_util.py` with cross-validation test vs browser hash
- [ ] Generate first 7 puzzles for IPL season launch

### Phase 10 — Deployment (Week 5)
- [x] GitHub Actions: build `apps/web/` → deploy to GitHub Pages
- [x] Puzzle JSON committed to repo (part of static assets)
- [x] Configure base URL for GitHub Pages sub-path
- [ ] Smoke test on real mobile devices (iOS Safari, Android Chrome)

---

## 13. Testing Strategy

| Layer | Tool | What's tested |
|---|---|---|
| Game engine | Vitest | Reducer actions, one-away detection, win/loss conditions |
| Hash utility | Vitest | Browser hash matches Python hash for same inputs |
| Components | React Testing Library | Tile select/deselect, submit enabled state, modal open/close |
| Storage | Vitest | Save/restore/clear localStorage state |
| E2E (optional) | Playwright | Full game play through: select groups, win, share |

---

## 14. Open Questions / Decisions Needed

| # | Question | Default Assumption |
|---|---|---|
| 1 | Will puzzles be committed to the repo or fetched from a CDN? | Committed to repo (static, simple) |
| 2 | Who curates puzzles — single person or team? | Single curator for v1 |
| 3 | Should category titles be hidden until revealed (to increase difficulty)? | Yes — titles shown only after correct guess |
| 4 | Does the share emoji grid show wrong-guess item colors or all-same color per row? | Per-item true category color (matches NYT behavior) |
| 5 | Off-season behavior: show archive or show nothing? | Show "IPL Classic" puzzles from historical data |
