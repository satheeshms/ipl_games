# IPL Cluster 4 — Analytics Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-04-04
**Status:** Draft
**References:** `specs/analytics/requirements.md`

---

## 1. Overview

Three deliverables:

1. **`functions/api/track.ts`** — Cloudflare Pages Function (ingestion endpoint)
2. **`src/lib/analytics.ts`** — frontend fire-and-forget client utility
3. **`useGameEngine.ts` wiring** — call `track()` at the four event points

No new dependencies. No schema changes. No test infrastructure changes needed.

---

## 2. Repository Changes

```
ipl_games/
├── apps/
│   └── web/
│       ├── functions/
│       │   └── api/
│       │       └── track.ts          ← NEW: Pages Function
│       └── src/
│           └── lib/
│               └── analytics.ts      ← NEW: client utility
│               (hooks/useGameEngine.ts modified)
└── specs/
    └── analytics/
        ├── requirements.md
        └── implementation_plan.md    ← (this file)
```

> **Note:** Cloudflare Pages Functions must live in a `functions/` directory at the same level as `package.json` (i.e., `apps/web/functions/`). They are picked up automatically on deploy.

---

## 3. Step 1 — Pages Function (`functions/api/track.ts`)

```typescript
// apps/web/functions/api/track.ts

interface Env {
  ANALYTICS: AnalyticsEngineDataset;
}

interface TrackPayload {
  event: string;
  puzzle_id?: string;
  game_mode?: string;
  result?: string;
  color?: string;
  attempt_number?: number;
  groups_made?: number;
  total_attempts?: number;
}

const KNOWN_EVENTS = new Set([
  'game_started',
  'guess_submitted',
  'group_completed',
  'game_completed',
]);

export async function onRequestPost(
  context: EventContext<Env, string, unknown>
): Promise<Response> {
  try {
    const body = await context.request.json<TrackPayload>();

    if (!body.event || !KNOWN_EVENTS.has(body.event)) {
      return new Response(null, { status: 400 });
    }

    context.env.ANALYTICS.writeDataPoint({
      indexes: [body.puzzle_id ?? ''],
      blobs: [
        body.event,
        body.game_mode ?? '',
        body.result ?? '',
        body.color ?? '',
      ],
      doubles: [
        body.attempt_number ?? 0,
        body.groups_made ?? 0,
        body.total_attempts ?? 0,
      ],
    });

    return new Response(null, { status: 204 });
  } catch {
    // Never let analytics errors surface to the client
    return new Response(null, { status: 204 });
  }
}
```

### Wrangler / Pages binding

The `ANALYTICS` binding is configured in the Cloudflare Pages dashboard (not in code):

```
Pages project → Settings → Functions → Analytics Engine bindings
  Variable name : ANALYTICS
  Dataset name  : ipl_games
```

For local development with `wrangler pages dev`, add to `wrangler.toml` (or `.dev.vars`) if needed — but since the function is fire-and-forget, it can be left unbound locally (the endpoint will return 204 regardless).

---

## 4. Step 2 — Frontend Client (`src/lib/analytics.ts`)

```typescript
// apps/web/src/lib/analytics.ts

interface TrackProps {
  puzzle_id?: string;
  game_mode?: string;
  result?: string;
  color?: string;
  attempt_number?: number;
  groups_made?: number;
  total_attempts?: number;
}

export function track(event: string, props: TrackProps = {}): void {
  if (typeof navigator === 'undefined' || !navigator.sendBeacon) return;
  navigator.sendBeacon('/api/track', JSON.stringify({ event, ...props }));
}
```

- Single exported function, no class, no state.
- `sendBeacon` check guards against SSR or very old browsers.
- The function is synchronous from the caller's perspective — it enqueues the payload and returns immediately.

---

## 5. Step 3 — Wire Events into `useGameEngine.ts`

Four call sites. All are additions only — no existing logic changes.

### 5.1 `game_started` — in `loadPuzzle`

```typescript
// In the loadPuzzle callback, after dispatch:
const loadPuzzle = useCallback((puzzle: Puzzle, gameMode: GameMode, forceFresh?: boolean) => {
  const savedState = forceFresh ? undefined : loadState(puzzle.id);
  dispatch({
    type: 'LOAD_PUZZLE',
    payload: { puzzle, savedState: savedState ?? undefined, gameMode },
  });

  // Track only fresh game starts, not state restores
  if (!savedState || savedState.status === 'idle') {
    track('game_started', { puzzle_id: puzzle.id, game_mode: gameMode });
  }
}, []);
```

### 5.2 `guess_submitted` + `group_completed` + `game_completed` — in `submitGuess`

```typescript
// In submitGuess, after the hash check resolves:

const attemptNumber = state.guessHistory.length + 1;

if (matchedCategory) {
  dispatch({ type: 'REVEAL_CATEGORY', payload: { color: matchedCategory.color } });

  const groupsMadeSoFar = state.revealedCategories.length + 1;

  track('guess_submitted', {
    puzzle_id: state.puzzle.id,
    game_mode: /* pass down from state or context */,
    attempt_number: attemptNumber,
    result: 'correct',
  });

  track('group_completed', {
    puzzle_id: state.puzzle.id,
    game_mode: /* ... */,
    color: matchedCategory.color,
    attempt_number: attemptNumber,
    groups_made: groupsMadeSoFar,
  });

  if (revealedCategories.length + 1 === puzzle.categories.length) {
    dispatch({ type: 'GAME_OVER', payload: { status: 'won' } });
    track('game_completed', {
      puzzle_id: state.puzzle.id,
      game_mode: /* ... */,
      result: 'won',
      groups_made: 4,
      total_attempts: attemptNumber,
    });
  }
  return;
}

// Wrong guess path
const result = oneAway ? 'one_away' : 'wrong';
track('guess_submitted', {
  puzzle_id: state.puzzle.id,
  game_mode: /* ... */,
  attempt_number: attemptNumber,
  result,
});

dispatch({ type: 'WRONG_GUESS', payload: { oneAway } });

if (state.lives - 1 === 0) {
  dispatch({ type: 'GAME_OVER', payload: { status: 'lost' } });
  track('game_completed', {
    puzzle_id: state.puzzle.id,
    game_mode: /* ... */,
    result: 'lost',
    groups_made: state.revealedCategories.length,
    total_attempts: attemptNumber,
  });
}
```

> **Note on `game_mode` in `submitGuess`:** The current `GameState` type does not store `gameMode`. The simplest fix is to add `gameMode: GameMode` to `GameState` and populate it in the `LOAD_PUZZLE` reducer case. This is a one-line change to the type, one-line change to the reducer, and one-line change to `initialState`.

---

## 6. GameState Type Change

```typescript
// src/types/index.ts — add one field to GameState
export interface GameState {
  // ... existing fields ...
  gameMode: GameMode;   // ← ADD: needed to include in analytics events
}
```

```typescript
// useGameEngine.ts initialState
const initialState: GameState = {
  // ... existing fields ...
  gameMode: 'pro',   // ← ADD: default; overwritten on LOAD_PUZZLE
};
```

```typescript
// LOAD_PUZZLE reducer case — set gameMode from payload
return {
  ...initialState,
  puzzle,
  gridItems: shuffle(puzzle.items),
  status: 'playing',
  lives: action.payload.gameMode === 'easy' ? 6 : 4,
  gameMode: action.payload.gameMode,   // ← ADD
};
```

---

## 7. Implementation Phases

### Phase 1 — Pages Function
- [ ] Create `apps/web/functions/api/track.ts` as specified in §3
- [ ] Verify Cloudflare Pages picks it up on next deploy (check Functions tab in Pages dashboard)
- [ ] Add `ANALYTICS` binding in Pages project → Settings → Functions → Analytics Engine bindings, dataset `ipl_games`

### Phase 2 — Frontend Client
- [ ] Create `apps/web/src/lib/analytics.ts` as specified in §4

### Phase 3 — GameState Type Change
- [ ] Add `gameMode: GameMode` to `GameState` in `src/types/index.ts`
- [ ] Add `gameMode: 'pro'` to `initialState` in `useGameEngine.ts`
- [ ] Set `gameMode: action.payload.gameMode` in `LOAD_PUZZLE` reducer case

### Phase 4 — Wire Events
- [ ] Add `game_started` track call in `loadPuzzle` (§5.1)
- [ ] Add `guess_submitted`, `group_completed`, `game_completed` track calls in `submitGuess` (§5.2)

### Phase 5 — Verification
- [ ] Deploy to Cloudflare Pages
- [ ] Play through a puzzle once; open Cloudflare dashboard → Workers & Pages → Analytics Engine → `ipl_games` dataset
- [ ] Run sample SQL to confirm events are arriving:
  ```sql
  SELECT blob1 AS event, COUNT() AS count
  FROM ipl_games
  WHERE timestamp > NOW() - INTERVAL '1' HOUR
  GROUP BY event
  ORDER BY count DESC
  ```

---

## 8. Useful Analytics Engine Queries

Once data is flowing, these queries answer the questions from issue #20:

```sql
-- How many players actually started the game (fresh start) today
SELECT COUNT() AS players_started
FROM ipl_games
WHERE blob1 = 'game_started'
  AND index1 = '2026-04-04';

-- Completion funnel: started → completed
SELECT blob1 AS event, COUNT() AS count
FROM ipl_games
WHERE index1 = '2026-04-04'
  AND blob1 IN ('game_started', 'game_completed')
GROUP BY event;

-- Win vs loss breakdown
SELECT blob3 AS result, COUNT() AS count
FROM ipl_games
WHERE blob1 = 'game_completed'
  AND index1 = '2026-04-04'
GROUP BY result;

-- How many groups did losing players manage to complete?
SELECT double2 AS groups_made, COUNT() AS count
FROM ipl_games
WHERE blob1 = 'game_completed'
  AND blob3 = 'lost'
  AND index1 = '2026-04-04'
GROUP BY groups_made
ORDER BY groups_made;

-- Guess result distribution (correct vs wrong vs one_away)
SELECT blob3 AS result, COUNT() AS count
FROM ipl_games
WHERE blob1 = 'guess_submitted'
  AND index1 = '2026-04-04'
GROUP BY result;

-- Easy vs Pro mode split
SELECT blob2 AS game_mode, COUNT() AS count
FROM ipl_games
WHERE blob1 = 'game_started'
  AND index1 = '2026-04-04'
GROUP BY game_mode;
```

---

## 9. Testing

| Scenario | How to verify |
|---|---|
| Fresh game start fires `game_started` | Open devtools Network tab, filter for `/api/track`, start a fresh game |
| Restoring a saved game does NOT fire `game_started` | Reload page mid-game, confirm no `game_started` beacon |
| Correct guess fires `guess_submitted` (result=correct) + `group_completed` | Submit a correct group, check two beacons sent |
| Wrong guess fires `guess_submitted` (result=wrong or one_away) | Submit wrong guess, check one beacon sent |
| Win fires `game_completed` (result=won) | Complete all 4 groups, check beacon |
| Loss fires `game_completed` (result=lost) | Exhaust all lives, check beacon |
| Function unavailable → game unaffected | Temporarily remove binding, play game — no errors in console |

---

## 10. Open Questions

| # | Question | Default Assumption |
|---|---|---|
| 1 | Should hint usage (`hint_used`) be tracked? | Not in v1 — can add later |
| 2 | Should shuffle usage be tracked? | No — not meaningful for engagement |
| 3 | Should the Analytics Engine dataset be named differently per environment (prod vs preview)? | Single dataset `ipl_games` for now |
