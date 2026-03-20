"""
normalizer.py — Post-load normalisation pass over ipl.db.

Run this AFTER kaggle_loader.py. It:
  1. Applies team alias mappings (franchise renames / typos → canonical name)
  2. Exports data/ipl_data.json — flat structure for the curator CLI to query

Usage:
    python3 normalizer.py --db data/ipl.db
    python3 normalizer.py --db data/ipl.db --export-json data/ipl_data.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Team alias map  →  canonical name
# Covers franchise renames and known typos in the Kaggle dataset.
# ---------------------------------------------------------------------------

TEAM_ALIASES: dict[str, str] = {
    # Renamed franchises
    "Delhi Daredevils":         "Delhi Capitals",
    "Kings XI Punjab":          "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    # Typo in some Kaggle editions
    "Rising Pune Supergiant":   "Rising Pune Supergiants",
    # manual_coaches.json uses full name; Kaggle omits "India"
    "Pune Warriors India":      "Pune Warriors",
}


# ---------------------------------------------------------------------------
# Step 1 — Merge duplicate team records
# ---------------------------------------------------------------------------

def normalize_teams(conn) -> dict[int, int]:
    """
    For each alias → canonical pair:
      - Ensure the canonical team row exists (insert if needed).
      - Re-point all foreign keys (player_teams, ipl_wins) from alias → canonical.
      - Delete the alias row.

    Returns a mapping of old_team_id → canonical_team_id for every alias merged.
    """
    merged: dict[int, int] = {}

    for alias_name, canonical_name in TEAM_ALIASES.items():
        alias_row = conn.execute(
            "SELECT id FROM teams WHERE name = ?", (alias_name,)
        ).fetchone()
        if alias_row is None:
            continue  # alias not in DB — nothing to do

        alias_id = alias_row[0]

        # Ensure canonical exists
        conn.execute(
            "INSERT OR IGNORE INTO teams (name) VALUES (?)", (canonical_name,)
        )
        canonical_id = conn.execute(
            "SELECT id FROM teams WHERE name = ?", (canonical_name,)
        ).fetchone()[0]

        if alias_id == canonical_id:
            continue  # already the same row

        # Re-point player_teams
        conn.execute(
            "UPDATE OR IGNORE player_teams SET team_id = ? WHERE team_id = ?",
            (canonical_id, alias_id),
        )
        # Delete orphaned rows that couldn't be re-pointed (PK conflict)
        conn.execute(
            "DELETE FROM player_teams WHERE team_id = ?", (alias_id,)
        )

        # Re-point ipl_wins
        conn.execute(
            "UPDATE OR IGNORE ipl_wins SET team_id = ? WHERE team_id = ?",
            (canonical_id, alias_id),
        )
        conn.execute(
            "DELETE FROM ipl_wins WHERE team_id = ?", (alias_id,)
        )

        # Delete the alias team row
        conn.execute("DELETE FROM teams WHERE id = ?", (alias_id,))

        merged[alias_id] = canonical_id
        print(f"  Merged '{alias_name}' -> '{canonical_name}'")

    conn.commit()
    return merged


# ---------------------------------------------------------------------------
# Step 2 — Migrate coaches table and load from manual_coaches_all.ndjson
# ---------------------------------------------------------------------------

# Roles to extract from each team entry in manual_coaches_all.ndjson
COACH_ROLES = {
    "head_coach":     "head",
    "batting_coach":  "batting",
    "bowling_coach":  "bowling",
    "fielding_coach": "fielding",
}

# Placeholder values that mean "no coach appointed"
_NO_COACH = {"not appointed", "n/a", "tbd", ""}


def _clean_coach_name(raw: str) -> str | None:
    """Strip parenthetical role annotations and return None if not a real name."""
    if not raw:
        return None
    cleaned = re.sub(r"\s*\([^)]*\)", "", raw).strip()
    if cleaned.lower() in _NO_COACH:
        return None
    return cleaned if cleaned else None


def migrate_coaches_table(conn) -> None:
    """
    Recreate the coaches table with a role column.
    Safe to call on both old (no role column) and new schemas.
    """
    has_role = any(
        row[1] == "role"
        for row in conn.execute("PRAGMA table_info(coaches)")
    )
    if has_role:
        return  # already migrated

    print("  Migrating coaches table to add role column...")
    conn.executescript("""
        ALTER TABLE coaches RENAME TO coaches_old;
        CREATE TABLE coaches (
            id       INTEGER PRIMARY KEY,
            team_id  INTEGER REFERENCES teams(id),
            season   INTEGER,
            role     TEXT NOT NULL DEFAULT 'head',
            name     TEXT,
            UNIQUE (team_id, season, role)
        );
        INSERT INTO coaches (team_id, season, role, name)
            SELECT team_id, season, 'head', name FROM coaches_old;
        DROP TABLE coaches_old;
    """)
    conn.commit()
    print("  Migration done.")


def load_all_coaches(conn, data_dir: Path) -> tuple[int, list[str]]:
    """
    Read manual_coaches_all.ndjson and load all coach roles into the coaches table.

    The file is a sequence of top-level JSON objects (one per season), each with:
      { "ipl_season": YYYY, "teams": [ { "team_name": ..., "head_coach": ..., ... } ] }

    Only head / batting / bowling / fielding roles are loaded.
    Entries with "Not Appointed" or blank values are skipped.
    Parenthetical annotations like "(Lead)" are stripped from names.

    Returns (rows_inserted, skipped_entries).
    """
    ndjson_path = data_dir / "manual_coaches_all.ndjson"
    if not ndjson_path.exists():
        # Fallback to legacy file
        print(f"  [coaches] {ndjson_path} not found, trying manual_coaches.json...")
        return _load_coaches_legacy(conn, data_dir)

    content = ndjson_path.read_text(encoding="utf-8").strip()
    season_blocks = [
        json.loads(block.strip())
        for block in re.split(r"\n(?=\{)", content)
        if block.strip()
    ]

    team_map = {
        name: tid
        for tid, name in conn.execute("SELECT id, name FROM teams").fetchall()
    }

    rows = []
    skipped = []

    for block in season_blocks:
        season = block.get("ipl_season")
        if not season:
            continue
        for team_entry in block.get("teams", []):
            raw_team = team_entry.get("team_name", "")
            resolved = TEAM_ALIASES.get(raw_team, raw_team)
            team_id = team_map.get(resolved)
            if team_id is None:
                skipped.append(f"{season} {raw_team}: team not in DB")
                continue

            for field, role in COACH_ROLES.items():
                raw_name = team_entry.get(field, "")
                name = _clean_coach_name(raw_name)
                if name is None:
                    continue
                rows.append((team_id, season, role, name))

    if skipped:
        print(f"  [coaches] {len(skipped)} entries skipped:")
        for s in skipped[:10]:
            print(f"    {s}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped) - 10} more")

    conn.executemany(
        "INSERT OR REPLACE INTO coaches (team_id, season, role, name) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows), skipped


def _load_coaches_legacy(conn, data_dir: Path) -> tuple[int, list[str]]:
    """Fallback: load head coaches from manual_coaches.json (old format)."""
    coaches_path = data_dir / "manual_coaches.json"
    if not coaches_path.exists():
        print(f"  [coaches] {coaches_path} not found, skipping.")
        return 0, []

    with open(coaches_path, encoding="utf-8") as f:
        data = json.load(f)

    team_map = {
        name: tid
        for tid, name in conn.execute("SELECT id, name FROM teams").fetchall()
    }

    rows = []
    skipped = []

    for season_str, team_coaches in data.get("coaches", {}).items():
        if season_str.startswith("_"):
            continue
        try:
            season = int(season_str)
        except ValueError:
            skipped.append(f"Invalid season '{season_str}'")
            continue
        for team_name, coach_name in team_coaches.items():
            resolved = TEAM_ALIASES.get(team_name, team_name)
            team_id = team_map.get(resolved)
            if team_id is None:
                skipped.append(f"{season} {team_name}: team not in DB")
                continue
            rows.append((team_id, season, "head", coach_name))

    conn.executemany(
        "INSERT OR REPLACE INTO coaches (team_id, season, role, name) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows), skipped


# ---------------------------------------------------------------------------
# Step 3 — Export ipl_data.json
# ---------------------------------------------------------------------------

def load_records(data_dir: Path) -> dict:
    """
    Read manual_records.json and return its batting/bowling/season record lists.
    Returns an empty dict if the file doesn't exist.
    """
    records_path = data_dir / "manual_records.json"
    if not records_path.exists():
        print(f"  [records] {records_path} not found, skipping.")
        return {}
    with open(records_path, encoding="utf-8") as f:
        data = json.load(f)
    # Strip comment keys (starting with _)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def export_json(conn, out_path: Path, data_dir: Path | None = None) -> None:
    """
    Write a flat JSON file the curator CLI can query without SQLite.

    Structure:
    {
      "teams": [...],
      "players": [...],
      "player_teams": [...],
      "awards": [...],
      "ipl_wins": [...],
      "venues": [...],
      "coaches": [...],
      "records": {
        "batting_records": [...],
        "bowling_records": [...],
        "season_records": [...]
      }
    }
    """

    teams = [
        {
            "id": r[0],
            "name": r[1],
            "short_name": r[2],
            "city": r[3],
            "active_from": r[4],
            "active_to": r[5],
        }
        for r in conn.execute(
            "SELECT id, name, short_name, city, active_from, active_to FROM teams ORDER BY name"
        )
    ]

    players = [
        {
            "id": r[0],
            "name": r[1],
            "nicknames": r[2],
            "nationality": r[3],
        }
        for r in conn.execute(
            "SELECT id, name, nicknames, nationality FROM players ORDER BY name"
        )
    ]

    player_teams = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "team_id": r[2],
            "team_name": r[3],
            "season": r[4],
        }
        for r in conn.execute("""
            SELECT pt.player_id, p.name, pt.team_id, t.name, pt.season
            FROM player_teams pt
            JOIN players p ON p.id = pt.player_id
            JOIN teams   t ON t.id = pt.team_id
            ORDER BY pt.season, p.name
        """)
    ]

    awards = [
        {
            "type": r[0],
            "player_id": r[1],
            "player_name": r[2],
            "season": r[3],
        }
        for r in conn.execute("""
            SELECT a.type, a.player_id, p.name, a.season
            FROM awards a
            JOIN players p ON p.id = a.player_id
            ORDER BY a.season, a.type
        """)
    ]

    ipl_wins = [
        {
            "season": r[0],
            "team_id": r[1],
            "team_name": r[2],
        }
        for r in conn.execute("""
            SELECT w.season, w.team_id, t.name
            FROM ipl_wins w
            JOIN teams t ON t.id = w.team_id
            ORDER BY w.season
        """)
    ]

    venues = [
        {"id": r[0], "name": r[1], "city": r[2]}
        for r in conn.execute("SELECT id, name, city FROM venues ORDER BY name")
    ]

    coaches = [
        {
            "team_id": r[0],
            "team_name": r[1],
            "season": r[2],
            "role": r[3],
            "coach": r[4],
        }
        for r in conn.execute("""
            SELECT c.team_id, t.name, c.season, c.role, c.name
            FROM coaches c
            JOIN teams t ON t.id = c.team_id
            ORDER BY c.season, t.name, c.role
        """)
    ]

    records = load_records(data_dir) if data_dir else {}

    five_wicket_hauls = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "matches": r[2],
            "innings": r[3],
            "balls": r[4],
            "runs": r[5],
            "wickets": r[6],
            "bbi": r[7],
            "average": r[8],
            "economy": r[9],
            "strike_rate": r[10],
            "four_w": r[11],
            "five_w": r[12],
            "ten_w": r[13],
        }
        for r in conn.execute("""
            SELECT f.player_id, p.name,
                   f.matches, f.innings, f.balls, f.runs, f.wickets, f.bbi,
                   f.average, f.economy, f.strike_rate, f.four_w, f.five_w, f.ten_w
            FROM five_wicket_hauls f
            JOIN players p ON p.id = f.player_id
            ORDER BY f.wickets DESC
        """)
    ]

    batting_career_stats = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "matches": r[2],
            "innings": r[3],
            "not_out": r[4],
            "runs": r[5],
            "hs": r[6],
            "average": r[7],
            "balls_faced": r[8],
            "strike_rate": r[9],
            "hundreds": r[10],
            "fifties": r[11],
            "ducks": r[12],
            "fours": r[13],
            "sixes": r[14],
        }
        for r in conn.execute("""
            SELECT b.player_id, p.name,
                   b.matches, b.innings, b.not_out, b.runs, b.hs,
                   b.average, b.balls_faced, b.strike_rate,
                   b.hundreds, b.fifties, b.ducks, b.fours, b.sixes
            FROM batting_career_stats b
            JOIN players p ON p.id = b.player_id
            ORDER BY b.runs DESC
        """)
    ]

    bowling_career_stats = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "matches": r[2],
            "innings": r[3],
            "balls": r[4],
            "runs": r[5],
            "wickets": r[6],
            "bbi": r[7],
            "average": r[8],
            "economy": r[9],
            "strike_rate": r[10],
            "four_w": r[11],
            "five_w": r[12],
        }
        for r in conn.execute("""
            SELECT b.player_id, p.name,
                   b.matches, b.innings, b.balls, b.runs, b.wickets, b.bbi,
                   b.average, b.economy, b.strike_rate, b.four_w, b.five_w
            FROM bowling_career_stats b
            JOIN players p ON p.id = b.player_id
            ORDER BY b.wickets DESC
        """)
    ]

    multi_team_players = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "team_count": r[2],
            "teams": r[3],
        }
        for r in conn.execute("""
            SELECT m.player_id, p.name, m.team_count, m.teams
            FROM multi_team_players m
            JOIN players p ON p.id = m.player_id
            ORDER BY m.team_count DESC, p.name
        """)
    ]

    most_ducks = [
        {
            "player_id": r[0],
            "player_name": r[1],
            "matches": r[2],
            "innings": r[3],
            "not_out": r[4],
            "runs": r[5],
            "hs": r[6],
            "average": r[7],
            "balls_faced": r[8],
            "strike_rate": r[9],
            "hundreds": r[10],
            "fifties": r[11],
            "ducks": r[12],
            "fours": r[13],
            "sixes": r[14],
        }
        for r in conn.execute("""
            SELECT d.player_id, p.name,
                   d.matches, d.innings, d.not_out, d.runs, d.hs,
                   d.average, d.balls_faced, d.strike_rate,
                   d.hundreds, d.fifties, d.ducks, d.fours, d.sixes
            FROM most_ducks d
            JOIN players p ON p.id = d.player_id
            ORDER BY d.ducks DESC, p.name
        """)
    ]

    data = {
        "teams": teams,
        "players": players,
        "player_teams": player_teams,
        "awards": awards,
        "ipl_wins": ipl_wins,
        "venues": venues,
        "coaches": coaches,
        "records": records,
        "five_wicket_hauls": five_wicket_hauls,
        "batting_career_stats": batting_career_stats,
        "bowling_career_stats": bowling_career_stats,
        "multi_team_players": multi_team_players,
        "most_ducks": most_ducks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Exported {out_path}")
    print(f"    teams: {len(teams)}, players: {len(players)}, "
          f"player_teams: {len(player_teams)}, awards: {len(awards)}, "
          f"ipl_wins: {len(ipl_wins)}, venues: {len(venues)}, coaches: {len(coaches)}")
    print(f"    five_wicket_hauls: {len(five_wicket_hauls)}, "
          f"batting_career_stats: {len(batting_career_stats)}, "
          f"bowling_career_stats: {len(bowling_career_stats)}, "
          f"multi_team_players: {len(multi_team_players)}, "
          f"most_ducks: {len(most_ducks)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalise ipl.db and optionally export ipl_data.json"
    )
    parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="Path to ipl.db (produced by kaggle_loader.py)",
    )
    parser.add_argument(
        "--export-json",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write ipl_data.json to this path (default: <db-dir>/ipl_data.json)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip JSON export (DB normalisation only)",
    )
    args = parser.parse_args()

    db_path: Path = args.db
    if not db_path.exists():
        print(f"ERROR: DB not found: {db_path}")
        print("Run kaggle_loader.py first.")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    from schema import get_connection

    conn = get_connection(str(db_path))

    # Step 1 — team aliases
    print("Step 1: Normalising team names...")
    merged = normalize_teams(conn)
    if not merged:
        print("  No aliases to merge.")
    else:
        print(f"  {len(merged)} team(s) merged.")

    # Step 2 — squads
    print("Step 2: Loading squad files...")
    from squad_loader import load_squads
    load_squads(conn, db_path.parent)

    # Step 2b — re-run manual loaders now that squad players are in the DB
    # (entries skipped in kaggle_loader due to missing players are picked up here)
    print("Step 2b: Re-loading manual data (pick up squad-only players)...")
    from kaggle_loader import (
        load_manual_awards,
        load_manual_5wkt_hauls,
        load_manual_top_batsmen,
        load_manual_top_bowlers,
        load_manual_multi_team_players,
        load_manual_most_ducks,
    )
    player_id_map = {
        name: pid
        for pid, name in conn.execute("SELECT id, name FROM players").fetchall()
    }
    n = load_manual_awards(conn, db_path.parent, player_id_map)
    print(f"  {n} award entries processed (INSERT OR REPLACE)")
    n = load_manual_5wkt_hauls(conn, db_path.parent, player_id_map)
    print(f"  {n} five_wicket_hauls entries processed (INSERT OR REPLACE)")
    n = load_manual_top_batsmen(conn, db_path.parent, player_id_map)
    print(f"  {n} batting_career_stats entries processed (INSERT OR REPLACE)")
    n = load_manual_top_bowlers(conn, db_path.parent, player_id_map)
    print(f"  {n} bowling_career_stats entries processed (INSERT OR REPLACE)")
    n = load_manual_multi_team_players(conn, db_path.parent, player_id_map)
    print(f"  {n} multi_team_players entries processed (INSERT OR REPLACE)")
    n = load_manual_most_ducks(conn, db_path.parent, player_id_map)
    print(f"  {n} most_ducks entries processed (INSERT OR REPLACE)")

    # Step 3 — coaches
    print("Step 3: Migrating and loading coaches...")
    migrate_coaches_table(conn)
    n, skipped = load_all_coaches(conn, db_path.parent)
    print(f"  {n} coach records loaded, {len(skipped)} skipped.")

    # Step 4 — JSON export
    if not args.no_export:
        json_path = args.export_json or db_path.parent / "ipl_data.json"
        print(f"Step 4: Exporting {json_path}...")
        export_json(conn, json_path, data_dir=db_path.parent)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
