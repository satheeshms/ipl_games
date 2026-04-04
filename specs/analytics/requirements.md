# IPL Cluster 4 — Analytics Requirements

**Spec Version:** 1.0
**Date:** 2026-04-04
**Status:** Draft
**GitHub Issue:** #20

---

## 1. Overview

Track meaningful player engagement events for the IPL Cluster 4 game to understand how players interact with each daily puzzle. The system must be privacy-friendly (no PII, no user IDs), non-blocking (must not affect game performance), and self-contained within the existing Cloudflare Pages deployment.

---

## 2. Goals

- Know how many players actually started playing (vs. just loading the page).
- Understand guess-attempt behaviour per puzzle.
- Track how many players completed all four groups (won) vs. ran out of lives (lost).
- Track group-level completion to identify puzzle difficulty distribution.
- Zero additional infrastructure — run entirely within the Cloudflare Pages + Workers free tier.

---

## 3. Non-Goals

- No user identity or session tracking.
- No personally identifiable information (PII) of any kind.
- No A/B testing or feature flags.
- No real-time dashboards or alerting.
- No analytics for the data pipeline or curator tools.

---

## 4. Architecture

```
React app (static, Cloudflare Pages)
  └─ navigator.sendBeacon('/api/track', JSON.stringify(payload))
        └─ functions/api/track.ts  (Cloudflare Pages Function)
              └─ env.ANALYTICS.writeDataPoint(...)
                    └─ Cloudflare Analytics Engine dataset: "ipl_games"
                          └─ Queryable via Cloudflare dashboard SQL explorer
```

### Why this architecture

- **Pages Functions** are Cloudflare Workers co-located with the Pages project — no separate deployment or billing.
- **`navigator.sendBeacon`** is fire-and-forget: the browser sends the payload without blocking the UI or waiting for a response.
- **Analytics Engine** is purpose-built for time-series event data. Free tier: 100k writes/day, 1M reads/day — well above expected traffic (~1k visits/day).
- No third-party analytics vendor. Data stays within the project's existing Cloudflare account.

---

## 5. Events

### 5.1 Event Catalogue

| Event name | Fired when | Key fields |
|---|---|---|
| `game_started` | Puzzle loads fresh (no saved state) | `puzzle_id`, `game_mode` |
| `guess_submitted` | Player clicks Submit with 4 items selected | `puzzle_id`, `game_mode`, `attempt_number`, `result` |
| `group_completed` | A correct group is revealed | `puzzle_id`, `game_mode`, `color`, `attempt_number`, `groups_made_so_far` |
| `game_completed` | Game reaches won or lost state | `puzzle_id`, `game_mode`, `result`, `groups_made`, `total_attempts` |

### 5.2 Field Definitions

| Field | Type | Description |
|---|---|---|
| `event` | string | Event name from catalogue above |
| `puzzle_id` | string | Puzzle date string e.g. `2026-04-04` |
| `game_mode` | string | `easy` or `pro` |
| `attempt_number` | number | 1-based count of submit attempts this session |
| `result` | string | `correct`, `wrong`, `one_away`, `won`, or `lost` |
| `color` | string | Category color: `yellow`, `green`, `blue`, `purple` |
| `groups_made` / `groups_made_so_far` | number | Count of correct groups revealed (0–4) |
| `total_attempts` | number | Total submit attempts at game end |

### 5.3 What is NOT collected

- IP addresses (Cloudflare strips these before Analytics Engine writes by default)
- Browser fingerprints, user agents, or device IDs
- Any item text or puzzle content
- Session IDs or cookies

---

## 6. Analytics Engine Data Model

Each data point written to Analytics Engine maps fields as follows:

| AE field | Value |
|---|---|
| `indexes[0]` | `puzzle_id` — primary dimension for per-puzzle queries |
| `blobs[0]` | `event` name |
| `blobs[1]` | `game_mode` |
| `blobs[2]` | `result` (where applicable, else empty string) |
| `blobs[3]` | `color` (where applicable, else empty string) |
| `doubles[0]` | `attempt_number` (where applicable, else 0) |
| `doubles[1]` | `groups_made` / `groups_made_so_far` (where applicable, else 0) |
| `doubles[2]` | `total_attempts` (where applicable, else 0) |

---

## 7. Pages Function Behaviour

- Endpoint: `POST /api/track`
- Accepts: `Content-Type: application/json` body (sent by `sendBeacon`)
- Validates: required fields present, `event` is a known event name
- On invalid payload: responds `400` silently (client does not retry)
- On success: responds `204 No Content`
- The function must not throw — errors are caught and silently discarded so a broken analytics path never affects the game

---

## 8. Frontend Client Behaviour

- A thin `src/lib/analytics.ts` module exposes a single `track(event, props)` function
- Internally calls `navigator.sendBeacon('/api/track', JSON.stringify(payload))`
- Falls back silently if `sendBeacon` is unavailable (old browsers)
- Never `await`-ed — always fire-and-forget
- Import is tree-shaken: if `track` is never called, nothing is bundled

---

## 9. Wiring Points in Game Engine

| Event | Where to fire | Condition |
|---|---|---|
| `game_started` | `useGameEngine` → `loadPuzzle` | Only when `forceFresh` or no saved state (fresh game, not a restore) |
| `guess_submitted` | `useGameEngine` → `submitGuess` | After hash verification, before dispatch |
| `group_completed` | `useGameEngine` → `submitGuess` | When `matchedCategory` found |
| `game_completed` | `useGameEngine` → `submitGuess` | When `GAME_OVER` is dispatched |

---

## 10. Cloudflare Setup (Manual, One-Time)

1. In Cloudflare Pages project settings → **Functions** → **Analytics Engine bindings**
2. Add binding: Variable name `ANALYTICS`, Dataset name `ipl_games`
3. Dataset is created automatically on first write
4. Query data: Cloudflare dashboard → **Workers & Pages** → **Analytics Engine** → SQL explorer

---

## 11. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Latency impact | Zero — `sendBeacon` is non-blocking |
| Bundle size impact | < 500 bytes (utility is trivial) |
| Failure handling | Silent — analytics failure must never affect gameplay |
| Data retention | Cloudflare Analytics Engine default (3 months rolling) |
| Write volume | ≤ 5 events per game session × ~1k sessions/day = ~5k writes/day (well within 100k free limit) |
