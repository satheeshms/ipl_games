# Game History & Winning Streak — Requirements

**Feature:** Game History & Winning Streak
**Issue:** #18
**Spec Version:** 1.0
**Date:** 2026-04-01
**Status:** Draft

---

## 1. Overview

Provide daily motivation by showing players their winning streak across the puzzle games. Streaks are tracked per puzzle type (IPL today; EPL, World Cup in future) so the system scales to a multi-sport platform without re-architecting.

Full game history (archive view) is deferred to a later phase. Priority 1 is winning streak.

---

## 2. Goals

- Show players how many consecutive days they have won.
- Reset streak on a loss or a skipped day.
- Display streak in the Results Modal immediately after the game ends.
- Store everything in localStorage — no backend, no account required.
- Design the storage schema to support multiple puzzle types from day one.

---

## 3. Functional Requirements

### 3.1 Streak Tracking

| # | Requirement |
|---|---|
| FR-1 | One result entry is recorded per puzzle date per puzzle type. |
| FR-2 | Recording is idempotent — replaying or revisiting a finished puzzle must not create a duplicate entry. |
| FR-3 | Current streak = count of consecutive calendar days ending on the most recent entry where result is `won`. |
| FR-4 | Streak resets to 0 if any entry in the trailing run is `lost`. |
| FR-5 | Streak resets to 0 if the gap between any two consecutive entries in the trailing run exceeds 1 calendar day (skipped day). |
| FR-6 | Best streak = the longest `won`-only consecutive run recorded in the full history. |

### 3.2 Display

| # | Requirement |
|---|---|
| FR-7 | Current streak and best streak are shown in the Results Modal after game completion. |
| FR-8 | On a win, display current streak (includes today's win). |
| FR-9 | On a loss, display current streak as 0 (today broke the streak). |

### 3.3 Storage

| # | Requirement |
|---|---|
| FR-10 | History is stored in localStorage under the key `ipl-cluster4-history-{puzzleType}` (e.g. `ipl-cluster4-history-ipl`). |
| FR-11 | Puzzle type is an explicit field in the stored blob, not just inferred from the key. |
| FR-12 | History is never pruned by the existing `clearStaleStates` logic. |
| FR-13 | On any localStorage read/write error, the game continues normally — streaks show as 0. |

---

## 4. Data Schema

### 4.1 localStorage entry

**Key:** `ipl-cluster4-history-{puzzleType}`

**Value (JSON):**

```json
{
  "puzzleType": "ipl",
  "entries": [
    { "date": "2026-03-28", "result": "won",  "recordedAt": "2026-03-28T18:42:11.000Z" },
    { "date": "2026-03-29", "result": "lost", "recordedAt": "2026-03-29T09:15:03.000Z" },
    { "date": "2026-03-31", "result": "won",  "recordedAt": "2026-03-31T20:01:55.000Z" }
  ]
}
```

- `entries` is ordered oldest-first.
- One entry per `date`. Duplicate dates are rejected on write.
- `recordedAt` is an ISO-8601 UTC timestamp, stored for audit/debugging only.

### 4.2 Computed stats (never persisted)

```
currentStreak: number   — consecutive daily wins up to the last entry
bestStreak:    number   — longest ever winning run in history
```

Derived on read from `entries`; recomputed each time the modal opens.

---

## 5. Puzzle Type Support

The `puzzleType` identifier maps directly to the path segment in `puzzles/{puzzleType}/{date}.json`:

| Puzzle Type | Storage Key | Notes |
|---|---|---|
| `ipl` | `ipl-cluster4-history-ipl` | Current |
| `epl` | `ipl-cluster4-history-epl` | Future |
| `worldcup` | `ipl-cluster4-history-worldcup` | Future |

Each puzzle type has its own independent history and streak. There is no cross-type aggregation.

---

## 6. Out of Scope (v1 of this feature)

- Archive / history view UI (past results table) — deferred to later phase.
- Cross-device sync.
- Win-rate percentage or other aggregate stats.
- Streak notifications or push alerts.
- Sharing streak as part of share text.

---

## 7. Non-Functional Requirements

| Requirement | Target |
|---|---|
| No backend | All reads and writes are localStorage-only. |
| No crash on failure | localStorage unavailable or corrupted → silent fallback, streak shows as 0. |
| Idempotent writes | Re-recording the same date must be a no-op. |
| Backwards compatible | Existing game state keys and `clearStaleStates` must be unaffected. |
