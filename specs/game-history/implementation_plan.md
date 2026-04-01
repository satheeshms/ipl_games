# Game History & Winning Streak — Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-04-01
**Status:** Draft
**References:** `specs/game-history/requirements.md`, Issue #18

---

## 1. New Types (`src/types/index.ts`)

Add four exports below the existing types. No existing types are modified.

```typescript
// Puzzle type identifier — matches the path segment in puzzles/{puzzleType}/{date}.json
export type PuzzleType = 'ipl' | 'epl' | 'worldcup';

// One completed puzzle result
export interface HistoryEntry {
  date: string;        // YYYY-MM-DD (puzzle date)
  result: 'won' | 'lost';
  recordedAt: string;  // ISO-8601 UTC timestamp
}

// Full persisted blob for one puzzle type
export interface PuzzleHistory {
  puzzleType: PuzzleType;
  entries: HistoryEntry[];  // ordered oldest-first, one entry per date
}

// Derived stats — computed on read, never stored
export interface StreakStats {
  currentStreak: number;
  bestStreak: number;
}
```

---

## 2. Storage Layer (`src/lib/history.ts`) — new file

localStorage key pattern: `ipl-cluster4-history-{puzzleType}`

### Functions

```typescript
export function historyKey(puzzleType: PuzzleType): string
// Returns the localStorage key string. Used by storage.ts to exclude it from clearStaleStates.

export function loadHistory(puzzleType: PuzzleType): PuzzleHistory
// Reads and parses from localStorage.
// On missing key, parse error, or invalid shape → returns { puzzleType, entries: [] }.

export function saveHistory(history: PuzzleHistory): void
// Serialises and writes to localStorage. Silently ignores all errors (QuotaExceededError etc.).

export function recordResult(puzzleType: PuzzleType, date: string, result: 'won' | 'lost'): void
// Idempotent: if an entry for `date` already exists, returns without writing.
// Otherwise appends { date, result, recordedAt: new Date().toISOString() } and saves.

export function computeStreaks(history: PuzzleHistory): StreakStats
// Pure function — no side effects.
// Sorts entries by date ascending.
// currentStreak: walks backwards from last entry; counts consecutive days where
//   result === 'won' and calendar gap to previous entry is exactly 1 day.
//   Resets to 0 on first 'lost' entry or any gap > 1 day.
// bestStreak: single forward pass tracking the longest won-only consecutive run.
```

### `computeStreaks` algorithm detail

```
Sort entries by date ascending.

--- currentStreak ---
i = last index
streak = 0
while i >= 0:
  if entries[i].result !== 'won': break
  if i > 0 and daysBetween(entries[i-1].date, entries[i].date) !== 1: break
  streak++
  i--
currentStreak = streak

--- bestStreak ---
best = 0, run = 0
for each entry (oldest → newest):
  if entry.result === 'won':
    if run > 0 and daysBetween(prev.date, entry.date) === 1:
      run++
    else:
      run = 1
  else:
    run = 0
  best = max(best, run)
bestStreak = best
```

---

## 3. Protect History Key (`src/lib/storage.ts`) — one change

`clearStaleStates` currently removes any `ipl-cluster4-*` key not in its `keep` set. Import `historyKey` and add it to the set.

```typescript
// Add import at top of storage.ts:
import { historyKey } from './history';

// Inside clearStaleStates, extend the keep set:
const keep = new Set([
  KEY(currentId),
  MODAL_CLOSED_KEY(currentId),
  historyKey('ipl'),
  // Add historyKey('epl'), historyKey('worldcup') when those puzzle types launch
]);
```

---

## 4. New Hook (`src/hooks/useGameHistory.ts`) — new file

Read-only. Does not write. Components use this to display streaks.

```typescript
export function useGameHistory(puzzleType: PuzzleType): {
  streaks: StreakStats;
  history: PuzzleHistory;
}
```

Implementation:
- On mount, calls `loadHistory(puzzleType)` and `computeStreaks(history)`.
- Listens for the native `window storage` event to refresh when another tab records a result.
- Returns memoised `{ streaks, history }`.

---

## 5. Engine Integration (`src/hooks/useGameEngine.ts`) — one addition

Add a single `useEffect` after the existing persist effect. The `recordResult` call is idempotent so it is safe if the effect fires on a restore of an already-terminal game.

```typescript
import { recordResult } from '../lib/history';

// After the persist useEffect in useGameEngine:
useEffect(() => {
  if (state.status !== 'won' && state.status !== 'lost') return;
  if (!state.puzzle) return;
  recordResult('ipl', state.puzzle.date, state.status);
}, [state.status, state.puzzle]);
```

`puzzleType` is hardcoded to `'ipl'`. When multi-league support is added, `puzzleType` should become a parameter of `useGameEngine` (or be added to the `Puzzle` type).

---

## 6. UI Changes

### `src/components/GameBoard.tsx`

Add the `useGameHistory` call and pass `streaks` to `ResultsModal`:

```typescript
const { streaks } = useGameHistory('ipl');

// In JSX:
<ResultsModal
  ...existing props...
  streaks={streaks}
/>
```

### `src/components/ResultsModal.tsx`

Add `streaks: StreakStats` to props. Insert a streak section in the modal body between the hints line and the share button:

```
// Won, streak >= 2:
🔥 {currentStreak}-day streak  |  Best: {bestStreak}

// Won, streak === 1:
1-day streak (new start!)  |  Best: {bestStreak}

// Lost:
Streak: 0  |  Best: {bestStreak}
```

Exact copy/styling is at the implementer's discretion. The data contract is `streaks.currentStreak` and `streaks.bestStreak`.

---

## 7. Implementation Phases

### Phase 1 — Types & Storage (no UI)
- [ ] Add `PuzzleType`, `HistoryEntry`, `PuzzleHistory`, `StreakStats` to `src/types/index.ts`
- [ ] Create `src/lib/history.ts` with all five functions
- [ ] Update `src/lib/storage.ts` `clearStaleStates` to preserve history key

### Phase 2 — Hook & Engine
- [ ] Create `src/hooks/useGameHistory.ts`
- [ ] Add `recordResult` effect to `src/hooks/useGameEngine.ts`

### Phase 3 — UI
- [ ] Update `src/components/GameBoard.tsx` to call `useGameHistory` and pass `streaks`
- [ ] Update `src/components/ResultsModal.tsx` to display streak

### Phase 4 — Tests
- [ ] Unit tests for `computeStreaks`:
  - Empty history → `{ currentStreak: 0, bestStreak: 0 }`
  - Single won entry → `{ 1, 1 }`
  - Consecutive wins → streak counts correctly
  - Loss resets current streak to 0
  - Day gap > 1 resets current streak to 0
  - Best streak preserved across reset
- [ ] Unit tests for `recordResult`:
  - Same date called twice → only one entry written
  - Different dates → two entries written

---

## 8. Dependency Order

```
Phase 1 (types + storage)
  └─► Phase 2 (hook + engine effect)   [can run in parallel within Phase 2]
        └─► Phase 3 (UI wiring)
              └─► Phase 4 (tests)
```

---

## 9. Edge Cases

| Scenario | Handling |
|---|---|
| Revisit after completion | `recordResult` date-deduplication — no second write |
| Restore of finished game | Effect fires, but `recordResult` is idempotent — no duplicate |
| Skipped day | `computeStreaks` detects gap > 1 day, resets `currentStreak` |
| Loss today | Entry written as `'lost'`; `currentStreak` = 0 |
| localStorage unavailable | `loadHistory` returns empty history; `saveHistory` silently fails; streak shows 0 |
| Corrupted JSON | `loadHistory` catches parse error; returns empty history |
| `clearStaleStates` | History key explicitly in `keep` set — never pruned |
| Multi-tab | `useGameHistory` refreshes on `storage` event |

---

## 10. Future Work (out of scope for this issue)

- History view UI (past results table) — see Issue #18 "Later phase" note.
- Add `puzzleType` to `Puzzle` type so engine derives it automatically.
- Add `historyKey('epl')` / `historyKey('worldcup')` to `clearStaleStates` keep set when those types launch.
- Sharing streak as part of the share text.
