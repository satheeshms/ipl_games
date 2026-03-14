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
        print(f"  Merged '{alias_name}' → '{canonical_name}'")

    conn.commit()
    return merged


# ---------------------------------------------------------------------------
# Step 2 — Load coaches from manual_coaches.json
# ---------------------------------------------------------------------------

def load_coaches(conn, data_dir: Path) -> tuple[int, list[str]]:
    """
    Read manual_coaches.json and insert into the coaches table.
    Must run AFTER normalize_teams() so canonical team names exist.

    Returns (rows_inserted, skipped_entries).
    """
    coaches_path = data_dir / "manual_coaches.json"
    if not coaches_path.exists():
        print(f"  [coaches] {coaches_path} not found, skipping.")
        return 0, []

    with open(coaches_path, encoding="utf-8") as f:
        data = json.load(f)

    # Build team_name -> team_id map
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
            team_id = team_map.get(team_name)
            if team_id is None:
                skipped.append(f"{season} {team_name}: team not in DB")
                continue
            rows.append((team_id, season, coach_name))

    if skipped:
        print(f"  [coaches] {len(skipped)} entries skipped:")
        for s in skipped:
            print(f"    {s}")

    conn.executemany(
        "INSERT OR REPLACE INTO coaches (team_id, season, name) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows), skipped


# ---------------------------------------------------------------------------
# Step 3 — Export ipl_data.json
# ---------------------------------------------------------------------------

def export_json(conn, out_path: Path) -> None:
    """
    Write a flat JSON file the curator CLI can query without SQLite.

    Structure:
    {
      "teams": [{"id", "name", "short_name", "city", "active_from", "active_to"}],
      "players": [{"id", "name", "nicknames", "nationality"}],
      "player_teams": [{"player_id", "player_name", "team_id", "team_name", "season"}],
      "awards": [{"type", "player_id", "player_name", "season"}],
      "ipl_wins": [{"season", "team_id", "team_name"}],
      "venues": [{"id", "name", "city"}]
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
            "coach": r[3],
        }
        for r in conn.execute("""
            SELECT c.team_id, t.name, c.season, c.name
            FROM coaches c
            JOIN teams t ON t.id = c.team_id
            ORDER BY c.season, t.name
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
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Exported {out_path}")
    print(f"    teams: {len(teams)}, players: {len(players)}, "
          f"player_teams: {len(player_teams)}, awards: {len(awards)}, "
          f"ipl_wins: {len(ipl_wins)}, venues: {len(venues)}, coaches: {len(coaches)}")


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

    # Step 3 — coaches
    print("Step 3: Loading coaches...")
    n, skipped = load_coaches(conn, db_path.parent)
    print(f"  {n} coach records loaded, {len(skipped)} skipped.")

    # Step 4 — JSON export
    if not args.no_export:
        json_path = args.export_json or db_path.parent / "ipl_data.json"
        print(f"Step 4: Exporting {json_path}...")
        export_json(conn, json_path)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
