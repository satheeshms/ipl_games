# Implementation Plan: `team_legends` — Data Pipeline

## Context

`gen_team_legends` in `generators/stats.py` computed legend rankings at puzzle-generation
time using global `batting_career_stats` / `bowling_career_stats` tables, which are
hand-curated with high thresholds (3000+ runs, 100+ wickets). This produced only 8 teams
with shallow pools.

The fix moves ranking logic upstream into the data pipeline using 15 `team_*.json` files
that contain **per-team** stats for every significant player on each franchise. A new
`team_player_stats` DB table is introduced as the source of truth, and `normalizer.py`
pre-computes `team_legends` into `ipl_data.json` so the curator CLI needs no DB access.

**Puzzle-curator changes (`generators/stats.py`, `gen_schedule_v5.py`) are deferred
to the `puzzle-designer` branch.**

---

## Output Format in `ipl_data.json`

```json
{
  "team_legends": {
    "Chennai Super Kings": {
      "batting": ["MS Dhoni", "SK Raina", "RD Gaikwad", ...],
      "bowling": ["RA Jadeja", "DJ Bravo", "R Ashwin", ...]
    },
    "Mumbai Indians": {
      "batting": ["RG Sharma", "SA Yadav", "KA Pollard", ...],
      "bowling": ["JJ Bumrah", "SL Malinga", "Harbhajan Singh", ...]
    }
  }
}
```

- All 15 active/historical franchises included
- `batting`: top 12 by runs scored **for that team** (desc)
- `bowling`: top 12 by wickets taken **for that team** (desc)
- A player can appear in both lists (allrounders like Jadeja, Pollard)
- Teams with fewer than 4 eligible batters OR 4 eligible bowlers are excluded

---

## Files Modified

### 1. `packages/data-pipeline/schema.py`

**Added** `team_player_stats` table after `bowling_career_stats`, before `multi_team_players`:

```sql
CREATE TABLE IF NOT EXISTS team_player_stats (
    player_id   INTEGER REFERENCES players(id),
    team_id     INTEGER REFERENCES teams(id),
    span        TEXT,
    matches     INTEGER,
    runs        INTEGER,
    hs          TEXT,
    hundreds    INTEGER,
    wickets     INTEGER,
    bbi         TEXT,
    five_w      INTEGER,
    catches     INTEGER,
    stumpings   INTEGER,
    PRIMARY KEY (player_id, team_id)
);
```

**Added** `DROP TABLE IF EXISTS team_player_stats;` to `DROP_TABLES` (between
`multi_team_players` and `bowling_career_stats`) so `--reset` works cleanly.

---

### 2. `packages/data-pipeline/kaggle_loader.py`

**Added** `load_team_player_stats(conn, data_dir, player_id_map, team_id_map)` as
Step 11 (former Steps 11–16 renumbered to 12–17, `print_summary` moved to Step 18).

Key details:
- Globs all `data/team_*.json` files
- Resolves team via `doc["fullName"]` → `team_id_map` (built from `SELECT name, id FROM teams`)
- Resolves player via `entry["Player"]` → `player_id_map`
- `INSERT OR REPLACE` with composite PK — idempotent on re-runs
- Logs skipped teams and players

**Updated `print_summary`** to show per-team player counts under `team_player_stats`.

---

### 3. `packages/data-pipeline/normalizer.py`

**Added** `_top_n(name_value, n)` helper — returns top-n keys sorted by value desc.

**Added/updated** `build_team_legends(conn, top_n=12)` — queries `team_player_stats`
directly (single JOIN to `players` + `teams`), builds separate batting/bowling dicts,
excludes teams with <4 in either category, returns top-12 each.

**Updated `normalize_teams`** — added re-point + delete for `team_player_stats` when
merging alias teams (same pattern as `player_teams` and `ipl_wins`), preventing FK
constraint failures on `--reset`.

**Updated `export_json`**:
- Calls `build_team_legends(conn)` alongside `load_records`
- Adds `"team_legends": team_legends` to the `data` dict
- Adds `team_legends: N teams` to the print summary

---

### 4. `packages/data-pipeline/data/team_PWI.json`

Corrected `"fullName"` from `"Pune Warriors India"` → `"Pune Warriors"` to match
the team name in the DB.

---

## Data Flow

```
team_*.json  ──► kaggle_loader.py Step 11 ──► team_player_stats (DB)
                                                       │
                                          normalizer.py build_team_legends()
                                                       │
                                          ipl_data.json  "team_legends": { ... }
                                                       │
                                    puzzle-curator gen_team_legends()  [deferred]
```

---

## Verification

```bash
cd packages/data-pipeline

# Full reset + reload
python kaggle_loader.py --db data/ipl.db --data-dir data/ --reset

# Rebuild JSON
python normalizer.py --db data/ipl.db --export-json data/ipl_data.json

# Inspect output
python -c "
import json
d = json.load(open('data/ipl_data.json'))
tl = d['team_legends']
print(f'Teams: {len(tl)}')
for team, entry in sorted(tl.items()):
    print(f'  {team}: bat={len(entry[\"batting\"])} bowl={len(entry[\"bowling\"])}')
print()
print('CSK batting top 6:', tl['Chennai Super Kings']['batting'][:6])
print('CSK bowling top 6:', tl['Chennai Super Kings']['bowling'][:6])
"
```

**Expected:** 15 teams, batting and bowling pools of 12 each (except Kochi Tuskers
Kerala bowling = 9, small franchise).

---

## Pending (puzzle-designer branch)

- `packages/puzzle-curator/generators/stats.py` — replace `gen_team_legends` body
  to use `_pick()` from pre-computed `ipl_data["team_legends"]`, with optional
  `batting` / `bowling` / `any` second param
- `packages/puzzle-curator/gen_schedule_v5.py` — update `compute_pool_caps` to
  read pool size from `team_legends` union of batting+bowling lists
