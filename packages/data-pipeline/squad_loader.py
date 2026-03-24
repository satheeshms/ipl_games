"""
squad_loader.py — Load ipl20??-squad CSV files into the SQLite database.

File format (two columns):
    Team,Complete Squad List
    CSK,"Ruturaj Gaikwad (C), MS Dhoni, Ravindra Jadeja, ..."

Season is inferred from the filename (e.g. ipl2025-squad → 2025).

Usage:
    python squad_loader.py --data-dir data/ --db data/ipl.db
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Short code → canonical team name (matches normalizer.py canonical names)
TEAM_CODES: dict[str, str] = {
    "CSK":  "Chennai Super Kings",
    "MI":   "Mumbai Indians",
    "RCB":  "Royal Challengers Bengaluru",
    "KKR":  "Kolkata Knight Riders",
    "DC":   "Delhi Capitals",
    "SRH":  "Sunrisers Hyderabad",
    "RR":   "Rajasthan Royals",
    "LSG":  "Lucknow Super Giants",
    "GT":   "Gujarat Titans",
    "PBKS": "Punjab Kings",
}

_SEASON_RE = re.compile(r"ipl(\d{4})-squad", re.IGNORECASE)


def _infer_season(path: Path) -> int | None:
    m = _SEASON_RE.search(path.name)
    return int(m.group(1)) if m else None


def _parse_players(raw: str) -> list[str]:
    """Split comma-separated player list, strip (C) and whitespace."""
    names = []
    for part in raw.split(","):
        name = part.strip().removesuffix("(C)").strip()
        if name:
            names.append(name)
    return names


def load_name_map(data_dir: Path) -> dict[str, str]:
    """Load player_name_map.json — maps expanded squad names to canonical DB names."""
    map_path = data_dir / "player_name_map.json"
    if not map_path.exists():
        return {}
    with open(map_path, encoding="utf-8") as f:
        data = json.load(f)
    # Strip the _comment key if present
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_squad_file(conn, path: Path, name_map: dict[str, str] | None = None) -> dict:
    """Load one squad CSV file. Returns counts dict."""
    season = _infer_season(path)
    if season is None:
        print(f"  [squad_loader] Cannot infer season from filename: {path.name}, skipping.")
        return {}

    print(f"  Season {season}: {path.name}")

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    teams_added = 0
    players_added = 0
    player_teams_added = 0
    skipped = []

    coaches_added = 0

    for row in rows:
        code = row.get("Team", "").strip()
        raw_squad = row.get("Complete Squad List", "").strip()
        coach_name = row.get("Head Coach", "").strip()

        team_name = TEAM_CODES.get(code)
        if team_name is None:
            skipped.append(f"Unknown team code '{code}'")
            continue

        # Ensure team exists
        conn.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (team_name,))
        team_id = conn.execute(
            "SELECT id FROM teams WHERE name = ?", (team_name,)
        ).fetchone()[0]
        teams_added += 1

        # Insert coach
        if coach_name:
            conn.execute(
                "INSERT OR REPLACE INTO coaches (team_id, season, name) VALUES (?, ?, ?)",
                (team_id, season, coach_name),
            )
            coaches_added += 1

        for player_name in _parse_players(raw_squad):
            # Resolve alias: map expanded name → canonical DB name if known
            canonical_name = (name_map or {}).get(player_name, player_name)

            # Insert player (INSERT OR IGNORE — no duplicate if already exists)
            conn.execute(
                "INSERT OR IGNORE INTO players (name) VALUES (?)", (canonical_name,)
            )
            player_id = conn.execute(
                "SELECT id FROM players WHERE name = ?", (canonical_name,)
            ).fetchone()[0]
            players_added += 1

            # Insert player_team link
            cursor = conn.execute(
                "INSERT OR IGNORE INTO player_teams (player_id, team_id, season) VALUES (?, ?, ?)",
                (player_id, team_id, season),
            )
            if cursor.rowcount:
                player_teams_added += 1

    conn.commit()

    if skipped:
        print(f"    Skipped: {skipped}")

    return {
        "season": season,
        "teams": teams_added,
        "coaches": coaches_added,
        "players": players_added,
        "player_teams": player_teams_added,
    }


def load_squads(conn, data_dir: Path) -> list[dict]:
    """
    Discover and load all ipl20??-squad files in data_dir.
    Returns list of per-file count dicts.
    """
    squad_files = sorted(data_dir.glob("ipl20??-squad"))
    if not squad_files:
        print("  [squad_loader] No ipl20??-squad files found.")
        return []

    name_map = load_name_map(data_dir)
    if name_map:
        print(f"  [squad_loader] Loaded {len(name_map)} name aliases from player_name_map.json")

    results = []
    for path in squad_files:
        result = load_squad_file(conn, path, name_map=name_map)
        if result:
            results.append(result)
            print(
                f"    -> {result['teams']} teams, {result.get('coaches', 0)} coaches, "
                f"{result['players']} players processed, {result['player_teams']} new player_team links"
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load ipl20??-squad CSV files into the IPL SQLite database."
    )
    parser.add_argument("--data-dir", required=True, type=Path,
                        help="Directory containing ipl20??-squad files")
    parser.add_argument("--db", required=True, type=Path,
                        help="Path to the SQLite database file")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"ERROR: DB not found: {args.db}")
        print("Run kaggle_loader.py first.")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    from schema import get_connection

    conn = get_connection(str(args.db))
    print("Loading squad files...")
    results = load_squads(conn, args.data_dir)
    conn.close()

    if results:
        total_pt = sum(r["player_teams"] for r in results)
        print(f"\nDone. {len(results)} file(s) loaded, {total_pt} total new player_team links.")
    else:
        print("\nDone. Nothing loaded.")


if __name__ == "__main__":
    main()
