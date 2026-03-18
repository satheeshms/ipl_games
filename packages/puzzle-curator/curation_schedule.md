# IPL 2026 — Puzzle Curation Schedule

**Season:** TATA IPL 2026
**Puzzle window:** 23 Mar – 31 May 2026
**Phase 1 schedule:** Confirmed (matches 1–20, Mar 28 – Apr 12)
**Phase 2 schedule:** TBD — fill specs once BCCI announces fixtures

**Status:** `[ ]` pending · `[~]` draft ready · `[x]` published

**Difficulty:** 🟨 Yellow = easiest · 🟩 Green · 🟦 Blue · 🟪 Purple = hardest

---

## Available Generator Types

| Spec | What it picks |
|---|---|
| `team_players:TEAM:SEASON` | 4 players from a team's season squad (e.g. `team_players:RCB:2026`) |
| `orange_cap` | 4 Orange Cap winners (pool: 17) |
| `purple_cap` | 4 Purple Cap winners (pool: 17) |
| `player_of_tournament` | 4 Player of Tournament winners (pool: 17) |
| `costliest_player` | 4 most expensive auction buys (pool: 18) |
| `winning_captain` | 4 IPL title-winning captains (pool: 17) |
| `ipl_champions` | 4 IPL championship-winning team names (pool: 7) |
| `coaches:SEASON` | 4 head coaches from a given season (pool: ~10 per season) |
| `batting_coaches:SEASON` | 4 batting coaches from a given season (pool: ~8–10 per season) |
| `bowling_coaches:SEASON` | 4 bowling coaches from a given season (pool: ~8–10 per season) |
| `fielding_coaches:SEASON` | 4 fielding coaches from a given season (pool: ~6–9 per season) |
| `batting_records` | 4 players who hold a career batting record (pool: 8 unique) — **use once** |
| `bowling_records` | 4 players who hold a career bowling record (pool: 8 unique) — **use once** |
| `season_records` | 4 players who hold a single-season record (pool: 5 unique) — **use once** |
| `fielding_records` | 4 fielding record holders: most WK catches (Dhoni), most stumpings (Dhoni), most overseas fielder catches (AB de Villiers), most catches non-keeper (Kohli), most run-outs non-keeper (Jadeja) — pool 4 unique — **use once** |
| `team_owners` | 4 IPL franchise owners (pool: 10) — best as 🟨 Yellow (easy) |

**⚠ Pool depletion note:** All record generators have small fixed pools — use each only once. `fielding_records` always returns the same 4 players. `team_owners` supports up to 2 uses. Award generators (`orange_cap` etc.) support up to 4 uses each.

---

## How to generate

```bash
cd packages/puzzle-curator

# Dry run — preview all pending puzzles
python schedule_runner.py --dry-run

# Generate all pending puzzles
python schedule_runner.py

# Generate just one date
python schedule_runner.py --date 2026-03-28

# Generate pre-IPL rollout only
python schedule_runner.py --from 2026-03-23 --to 2026-03-27
```

---

## Pre-IPL Rollout (23–27 Mar 2026)

| Ed | Date | Day | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟪 Purple | Status |
|---|---|---|---|---|---|---|---|
| 1 | 23 Mar | Mon | `ipl_champions` | `orange_cap` | `purple_cap` | `player_of_tournament` | [ ] |
| 2 | 24 Mar | Tue | `team_players:RCB:2026` | `team_players:CSK:2026` | `team_players:MI:2026` | `team_players:KKR:2026` | [ ] |
| 3 | 25 Mar | Wed | `orange_cap` | `purple_cap` | `costliest_player` | `winning_captain` | [ ] |
| 4 | 26 Mar | Thu | `coaches:2026` | `coaches:2025` | `coaches:2024` | `coaches:2013` | [ ] |
| 5 | 27 Mar | Fri | `team_players:SRH:2026` | `team_players:RR:2026` | `team_players:GT:2026` | `team_players:PBKS:2026` | [ ] |

---

## Phase 1 — Confirmed Fixtures (28 Mar – 12 Apr 2026)

| Ed | Date | Day | Match(es) | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟪 Purple | Status |
|---|---|---|---|---|---|---|---|---|
| 6  | 28 Mar | Sat | M1: RCB vs SRH | `team_players:RCB:2026` | `team_players:SRH:2026` | `batting_records` | `player_of_tournament` | [ ] |
| 7  | 29 Mar | Sun | M2: MI vs KKR | `team_players:MI:2026` | `team_players:KKR:2026` | `orange_cap` | `costliest_player` | [ ] |
| 8  | 30 Mar | Mon | M3: RR vs CSK | `team_players:RR:2026` | `team_players:CSK:2026` | `winning_captain` | `bowling_records` | [ ] |
| 9  | 31 Mar | Tue | M4: PBKS vs GT | `team_players:PBKS:2026` | `team_players:GT:2026` | `purple_cap` | `season_records` | [ ] |
| 10 | 01 Apr | Wed | M5: LSG vs DC | `team_players:LSG:2026` | `team_players:DC:2026` | `player_of_tournament` | `orange_cap` | [ ] |
| 11 | 02 Apr | Thu | M6: KKR vs SRH | `team_players:KKR:2026` | `team_players:SRH:2026` | `winning_captain` | `costliest_player` | [ ] |
| 12 | 03 Apr | Fri | M7: CSK vs PBKS | `team_players:CSK:2026` | `team_players:PBKS:2026` | `coaches:2022` | `coaches:2021` | [ ] |
| 13 | 04 Apr | Sat | M8: DC vs MI · M9: GT vs RR | `team_players:DC:2026` | `team_players:MI:2026` | `team_players:GT:2026` | `team_players:RR:2026` | [ ] |
| 14 | 05 Apr | Sun | M10: SRH vs LSG · M11: RCB vs CSK | `team_players:SRH:2026` | `team_players:LSG:2026` | `purple_cap` | `player_of_tournament` | [ ] |
| 15 | 06 Apr | Mon | M12: KKR vs PBKS | `team_players:KKR:2026` | `team_players:PBKS:2026` | `coaches:2026` | `winning_captain` | [ ] |
| 16 | 07 Apr | Tue | M13: RR vs MI | `team_players:RR:2026` | `team_players:MI:2026` | `orange_cap` | `costliest_player` | [ ] |
| 17 | 08 Apr | Wed | M14: DC vs GT | `team_players:DC:2026` | `team_players:GT:2026` | `coaches:2020` | `coaches:2019` | [ ] |
| 18 | 09 Apr | Thu | M15: KKR vs LSG | `team_players:KKR:2026` | `team_players:LSG:2026` | `coaches:2018` | `coaches:2017` | [ ] |
| 19 | 10 Apr | Fri | M16: RR vs RCB | `team_players:RR:2026` | `team_players:RCB:2026` | `coaches:2016` | `coaches:2015` | [ ] |
| 20 | 11 Apr | Sat | M17: PBKS vs SRH · M18: CSK vs DC | `team_players:PBKS:2026` | `team_players:SRH:2026` | `team_players:CSK:2026` | `team_players:DC:2026` | [ ] |
| 21 | 12 Apr | Sun | M19: LSG vs GT · M20: MI vs RCB | `team_players:LSG:2026` | `team_players:GT:2026` | `team_players:MI:2026` | `team_players:RCB:2026` | [ ] |

---

## Phase 2 — Estimated Match Days (13 Apr – 21 May 2026)

> Fill specs once BCCI announces Phase 2 fixtures. Match pairings are TBD.

| Ed | Date | Day | Match(es) | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟪 Purple | Status |
|---|---|---|---|---|---|---|---|---|
| 22 | 13 Apr | Mon | M21 (TBD) | — | — | — | — | [ ] |
| 23 | 14 Apr | Tue | M22 (TBD) | — | — | — | — | [ ] |
| 24 | 15 Apr | Wed | M23 (TBD) | — | — | — | — | [ ] |
| 25 | 16 Apr | Thu | M24 (TBD) | — | — | — | — | [ ] |
| 26 | 17 Apr | Fri | M25 (TBD) | — | — | — | — | [ ] |
| 27 | 18 Apr | Sat | M26–27 (TBD) | — | — | — | — | [ ] |
| 28 | 19 Apr | Sun | M28–29 (TBD) | — | — | — | — | [ ] |
| 29 | 20 Apr | Mon | M30 (TBD) | — | — | — | — | [ ] |
| 30 | 21 Apr | Tue | M31 (TBD) | — | — | — | — | [ ] |
| 31 | 22 Apr | Wed | M32 (TBD) | — | — | — | — | [ ] |
| 32 | 23 Apr | Thu | M33 (TBD) | — | — | — | — | [ ] |
| 33 | 24 Apr | Fri | M34 (TBD) | — | — | — | — | [ ] |
| 34 | 25 Apr | Sat | M35–36 (TBD) | — | — | — | — | [ ] |
| 35 | 26 Apr | Sun | M37–38 (TBD) | — | — | — | — | [ ] |
| 36 | 27 Apr | Mon | M39 (TBD) | — | — | — | — | [ ] |
| 37 | 28 Apr | Tue | M40 (TBD) | — | — | — | — | [ ] |
| 38 | 29 Apr | Wed | M41 (TBD) | — | — | — | — | [ ] |
| 39 | 30 Apr | Thu | M42 (TBD) | — | — | — | — | [ ] |
| 40 | 01 May | Fri | M43 (TBD) | — | — | — | — | [ ] |
| 41 | 02 May | Sat | M44–45 (TBD) | — | — | — | — | [ ] |
| 42 | 03 May | Sun | M46–47 (TBD) | — | — | — | — | [ ] |
| 43 | 04 May | Mon | M48 (TBD) | — | — | — | — | [ ] |
| 44 | 05 May | Tue | M49 (TBD) | — | — | — | — | [ ] |
| 45 | 06 May | Wed | M50 (TBD) | — | — | — | — | [ ] |
| 46 | 07 May | Thu | M51 (TBD) | — | — | — | — | [ ] |
| 47 | 08 May | Fri | M52 (TBD) | — | — | — | — | [ ] |
| 48 | 09 May | Sat | M53–54 (TBD) | — | — | — | — | [ ] |
| 49 | 10 May | Sun | M55–56 (TBD) | — | — | — | — | [ ] |
| 50 | 11 May | Mon | M57 (TBD) | — | — | — | — | [ ] |
| 51 | 12 May | Tue | M58 (TBD) | — | — | — | — | [ ] |
| 52 | 13 May | Wed | M59 (TBD) | — | — | — | — | [ ] |
| 53 | 14 May | Thu | M60 (TBD) | — | — | — | — | [ ] |
| 54 | 15 May | Fri | M61 (TBD) | — | — | — | — | [ ] |
| 55 | 16 May | Sat | M62–63 (TBD) | — | — | — | — | [ ] |
| 56 | 17 May | Sun | M64–65 (TBD) | — | — | — | — | [ ] |
| 57 | 18 May | Mon | M66 (TBD) | — | — | — | — | [ ] |
| 58 | 19 May | Tue | M67 (TBD) | — | — | — | — | [ ] |
| 59 | 20 May | Wed | M68 (TBD) | — | — | — | — | [ ] |
| 60 | 21 May | Thu | M69–70 (TBD) | — | — | — | — | [ ] |

---

## Playoffs (estimated 22–31 May 2026)

> Teams TBD. Fill `team_players` specs once finalists are known.

| Ed | Date | Day | Match | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟪 Purple | Status |
|---|---|---|---|---|---|---|---|---|
| 61 | 22 May | Fri | Qualifier 1 | — | — | — | — | [ ] |
| 62 | 23 May | Sat | Rest day | — | — | — | — | [ ] |
| 63 | 24 May | Sun | Eliminator | — | — | — | — | [ ] |
| 64 | 26 May | Tue | Qualifier 2 | — | — | — | — | [ ] |
| 65 | 28 May | Thu | Rest day | — | — | — | — | [ ] |
| 66 | 30 May | Fri | Rest day | — | — | — | — | [ ] |
| 67 | 31 May | Sun | Final | — | — | — | — | [ ] |
