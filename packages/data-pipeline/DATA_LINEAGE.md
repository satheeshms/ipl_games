# Data Pipeline Lineage

Documents the full data flow from raw sources to `ipl_data.json`.

---

## Source Overview

| Source | Coverage | Format |
|--------|----------|--------|
| Kaggle IPL dataset | IPL 2008–2020 | `matches.csv`, `deliveries.csv` |
| Squad CSV files | IPL 2021–2025 | `ipl20??-squad.csv` |
| ESPNcricinfo scraper | Recent seasons | Web scrape via `espncricinfo.py` |
| Manual JSON files | IPL 2008–2025 | Curated `manual_*.json` files |

> **Note:** The player registry is a hybrid of Kaggle (pre-2021) and squad files (post-2020). Players who never appeared in a Kaggle delivery (e.g., squad-only players who didn't bat or bowl) are only known via squad files.

---

## CSV Columns Used

### matches.csv
| Column | Used by | Produces |
|--------|---------|---------|
| `venue`, `city` | `load_venues()` | `venues` table |
| `team1`, `team2` | `load_teams()` | `teams` table |
| `season`, `winner`, `result`, `id` | `load_ipl_wins()` | `ipl_wins` table |
| `player_of_match` | `load_players()` | `players` table (partial) |

### deliveries.csv
| Column | Used by | Produces |
|--------|---------|---------|
| `batsman` / `batter`, `non_striker`, `bowler`, `player_dismissed` | `load_players()` | `players` table (main source) |
| `fielder` | `load_players()` | `players` table (split on ` & `) |
| `batting_team`, `bowling_team` + match `season` | `load_player_teams()` | `player_teams` table |

---

## DB Tables and Their Sources

| Table | Seeded by | Source |
|-------|-----------|--------|
| `venues` | `kaggle_loader.py` Step 2 | matches.csv |
| `teams` | `kaggle_loader.py` Step 3 | matches.csv |
| `ipl_wins` | `kaggle_loader.py` Step 4 | matches.csv |
| `players` | `kaggle_loader.py` Step 5 | deliveries.csv + matches.csv + squad CSVs |
| `player_teams` | `kaggle_loader.py` Step 6 | deliveries.csv × matches.csv |
| `awards` | `kaggle_loader.py` Step 7 | `manual_awards.json` |
| `five_wicket_hauls` | `kaggle_loader.py` Step 8 | `manual_5_plus_wickets.json` |
| `batting_career_stats` | `kaggle_loader.py` Step 9 | `manual_top_run_batsmen.json` (3000+ runs) |
| `bowling_career_stats` | `kaggle_loader.py` Step 10 | `manual_top_bowlers.json` (100+ wickets) |
| `multi_team_players` | `kaggle_loader.py` Step 11 | `manual_players_multi_team.json` (5+ teams) |
| `most_ducks` | `kaggle_loader.py` Step 12 | `manual_most_ducks.json` (10+ ducks) |
| `coaches` | `normalizer.py` Step 3 | `manual_coaches_all.ndjson` / `manual_coaches.json` |

> **Re-run in normalizer Step 2b:** After `squad_loader` adds post-2020 players, all manual loaders (Steps 7–12) are re-run with `INSERT OR REPLACE` to pick up players who were missing from the Kaggle CSV data.

---

## ipl_data.json Keys and Their Origins

| Key | DB Table | Original Source | Notes |
|-----|----------|-----------------|-------|
| `teams` | `teams` | matches.csv | `short_name`, `city`, `active_from`, `active_to` always NULL |
| `players` | `players` | deliveries.csv + matches.csv | `nicknames`, `nationality`, `batting_hand`, `bowling_hand` always NULL |
| `player_teams` | `player_teams` | deliveries.csv × matches.csv | Flat rows: one per player×team×season. Pre-2021 only from Kaggle. |
| `awards` | `awards` | `manual_awards.json` | Orange Cap, Purple Cap, Player of Tournament, costliest auction buys |
| `ipl_wins` | `ipl_wins` | matches.csv | Season champions only (no runners-up) |
| `venues` | `venues` | matches.csv | No known consumer in curator or game UI |
| `coaches` | `coaches` | `manual_coaches_all.ndjson` | Head, batting, bowling, fielding roles per team per season |
| `records` | *(none)* | `manual_records.json` | **Bypasses DB** — read directly in `export_json()` |
| `five_wicket_hauls` | `five_wicket_hauls` | `manual_5_plus_wickets.json` | Career bowling stats for players with 5w hauls |
| `batting_career_stats` | `batting_career_stats` | `manual_top_run_batsmen.json` | Career batting stats, filtered to 3000+ runs |
| `bowling_career_stats` | `bowling_career_stats` | `manual_top_bowlers.json` | Career bowling stats, filtered to 100+ wickets |
| `multi_team_players` | `multi_team_players` | `manual_players_multi_team.json` | Players who played for 5+ franchises |
| `most_ducks` | `most_ducks` | `manual_most_ducks.json` | Batting stats for players with 10+ ducks |
| `foreign_players` | *(none)* | `players_master_enriched.json` | **Bypasses DB** — non-Indian players with country, teams, matches |
| `india_state_wise` | *(none)* | `players_master_enriched.json` | **Bypasses DB** — Indian players grouped by home state |
| `ranji_team_wise` | *(none)* | `players_master_enriched.json` | **Bypasses DB** — Indian players grouped by Ranji Trophy team; players with multiple teams appear in each group |

---

## Player Data Shape

The `players` table stores **identity only** — no team or season info:

```
players: id, name, nicknames*, nationality*, batting_hand*, bowling_hand*
(* always NULL — never populated by any current loader)
```

Team and season associations are in `player_teams` (flat join table):
```
player_teams: player_id, team_id, season
→ exported with player_name and team_name resolved via JOIN
```

For a consolidated player→teams→seasons view, `multi_team_players` provides this but only for players with 5+ teams. All other players require grouping `player_teams` rows at query time.

---

## Known Issues and Gaps

| Issue | Impact |
|-------|--------|
| `records` bypasses the DB | Inconsistent — only manual dataset not loaded into a table |
| `player_teams` is large | Thousands of flat rows in ipl_data.json; curator never queries it |
| `venues` has no consumer | Exported but unused in game or curator logic |
| Ghost DB columns | Several columns always NULL, bloating player/team JSON objects |
| No team code lookup | Manual JSONs use short codes (RCB, CSK); no code→full name map in export |
| Kaggle cutoff 2020 | player_teams is incomplete for 2021–2025 seasons |
| Enriched player coverage | 375 of 592 players still missing country/state/ranji — populated incrementally via `batches/*enriched*.json` |

---

## Pipeline Execution Order

```
1. kaggle_loader.py --data-dir data/ --db data/ipl.db
   └── Loads CSV data + all manual JSON files into ipl.db

2. normalizer.py --db data/ipl.db --export-json data/ipl_data.json
   ├── Step 1: Normalise team name aliases
   ├── Step 2: Load squad CSV files (squad_loader)
   ├── Step 2b: Re-run manual loaders (picks up squad-only players)
   ├── Step 3: Load coaches
   └── Step 4: Export ipl_data.json
```

---

*Last updated: IPL 2025 season — added foreign_players, india_state_wise, ranji_team_wise*
