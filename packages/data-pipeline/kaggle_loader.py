"""
kaggle_loader.py — Load the standard Kaggle IPL dataset (matches.csv + deliveries.csv)
into a SQLite database using the schema defined in schema.py.

Usage:
    python kaggle_loader.py --data-dir data/ --db data/ipl.db
    python kaggle_loader.py --data-dir data/ --db data/ipl.db --reset
"""

import argparse
import sys
from pathlib import Path

KAGGLE_URL = "https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020"


def _print_startup(data_dir: Path) -> None:
    print("IPL Kaggle Loader")
    print(f"Dataset: {KAGGLE_URL}")
    print(f"Download matches.csv and deliveries.csv into: {data_dir}")
    print()


# ---------------------------------------------------------------------------
# Step 1 — Load CSVs
# ---------------------------------------------------------------------------

def load_csvs(data_dir: Path):
    """Load matches.csv and deliveries.csv from data_dir. Exit on missing files."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    matches_path = data_dir / "matches.csv"
    deliveries_path = data_dir / "deliveries.csv"

    missing = [str(p) for p in (matches_path, deliveries_path) if not p.exists()]
    if missing:
        print("ERROR: Required CSV files not found:")
        for m in missing:
            print(f"  {m}")
        print(f"\nDownload the dataset from:\n  {KAGGLE_URL}")
        print(f"and place matches.csv + deliveries.csv into: {data_dir}")
        sys.exit(1)

    matches_df = pd.read_csv(matches_path)
    deliveries_df = pd.read_csv(deliveries_path)

    print(f"Loaded matches.csv:    {len(matches_df):>6} rows")
    print(f"Loaded deliveries.csv: {len(deliveries_df):>6} rows")
    return matches_df, deliveries_df


# ---------------------------------------------------------------------------
# Step 2 — Venues
# ---------------------------------------------------------------------------

def load_venues(conn, matches_df) -> dict:
    """Insert unique venues and return a venue_name -> venue_id mapping."""
    venue_rows = (
        matches_df[["venue", "city"]]
        .drop_duplicates(subset=["venue"])
        .itertuples(index=False)
    )

    rows = []
    for row in venue_rows:
        name = row.venue
        city = None if (isinstance(row.city, float) or row.city != row.city) else row.city
        rows.append((name, city))

    conn.executemany(
        "INSERT OR IGNORE INTO venues (name, city) VALUES (?, ?)",
        rows,
    )
    conn.commit()

    cursor = conn.execute("SELECT id, name FROM venues")
    return {name: vid for vid, name in cursor.fetchall()}


# ---------------------------------------------------------------------------
# Step 3 — Teams
# ---------------------------------------------------------------------------

def load_teams(conn, matches_df) -> dict:
    """Insert unique team names and return a team_name -> team_id mapping."""
    team_names = set(matches_df["team1"].dropna()) | set(matches_df["team2"].dropna())
    rows = [(name,) for name in sorted(team_names)]

    conn.executemany(
        "INSERT OR IGNORE INTO teams (name) VALUES (?)",
        rows,
    )
    conn.commit()

    cursor = conn.execute("SELECT id, name FROM teams")
    return {name: tid for tid, name in cursor.fetchall()}


# ---------------------------------------------------------------------------
# Step 4 — IPL season winners
# ---------------------------------------------------------------------------

def load_ipl_wins(conn, matches_df, team_id_map: dict) -> None:
    """Insert ipl_wins (one per season = winner of the final match by highest id)."""
    # Normalise season to int where possible
    df = matches_df.copy()
    df["season"] = df["season"].apply(_coerce_season)

    rows = []
    for season, group in df.groupby("season"):
        final = group.loc[group["id"].idxmax()]
        result = str(final.get("result", "")).strip().lower()
        winner = final.get("winner", None)
        if result == "no result":
            continue
        if not isinstance(winner, str) or winner != winner:
            continue
        if season is None:
            continue
        team_id = team_id_map.get(winner)
        if team_id is None:
            continue
        rows.append((team_id, int(season), None))

    conn.executemany(
        "INSERT OR IGNORE INTO ipl_wins (team_id, season, captain_id) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


def _coerce_season(val):
    """Return season as a canonical int year, or None if unparseable.

    Kaggle uses "2007/08" for IPL 1 (played in 2008) and "2009/10" for
    IPL 3 (played in 2010). For those, we take the second part.
    "2020/21" is IPL 13 played in 2020 — take the first part.
    Explicit overrides handle the ambiguous cases.
    """
    _SLASH_OVERRIDES = {
        "2007/08": 2008,
        "2009/10": 2010,
    }
    try:
        return int(val)
    except (ValueError, TypeError):
        s = str(val).strip()
        if s in _SLASH_OVERRIDES:
            return _SLASH_OVERRIDES[s]
        if "/" in s:
            try:
                return int(s.split("/")[0])
            except (ValueError, TypeError):
                pass
        return None


# ---------------------------------------------------------------------------
# Step 5 — Players
# ---------------------------------------------------------------------------

def load_players(conn, matches_df, deliveries_df) -> dict:
    """
    Collect all unique player names from deliveries and matches, insert into
    the players table, and return a player_name -> player_id mapping.
    """
    import pandas as pd

    names: set = set()

    # From deliveries — support both old ("batsman") and new ("batter") column names
    for col in ("batsman", "batter", "non_striker", "bowler", "player_dismissed"):
        if col in deliveries_df.columns:
            names.update(deliveries_df[col].dropna().unique())

    # fielder column may contain "A & B" — split on " & "
    if "fielder" in deliveries_df.columns:
        for val in deliveries_df["fielder"].dropna().unique():
            for part in str(val).split(" & "):
                part = part.strip()
                if part:
                    names.add(part)

    # From matches
    if "player_of_match" in matches_df.columns:
        names.update(matches_df["player_of_match"].dropna().unique())

    # Remove any blank / nan-like strings
    names = {n for n in names if isinstance(n, str) and n.strip()}

    rows = [(name,) for name in sorted(names)]
    conn.executemany(
        "INSERT OR IGNORE INTO players (name) VALUES (?)",
        rows,
    )
    conn.commit()

    cursor = conn.execute("SELECT id, name FROM players")
    return {name: pid for pid, name in cursor.fetchall()}


# ---------------------------------------------------------------------------
# Step 6 — player_teams
# ---------------------------------------------------------------------------

def load_player_teams(conn, matches_df, deliveries_df, player_id_map: dict,
                      team_id_map: dict) -> None:
    """
    Derive (player, team, season) triples from deliveries joined with matches,
    then insert into player_teams.
    """
    import pandas as pd

    # Normalise match seasons
    match_season = matches_df[["id", "season"]].copy()
    match_season["season"] = match_season["season"].apply(_coerce_season)
    match_season = match_season.rename(columns={"id": "match_id"})

    # Join deliveries with match seasons
    merged = deliveries_df.merge(match_season, on="match_id", how="left")

    triples: set = set()

    # batsman/batter -> batting_team
    batter_col = "batsman" if "batsman" in merged.columns else "batter" if "batter" in merged.columns else None
    if batter_col and "batting_team" in merged.columns:
        sub = merged[[batter_col, "batting_team", "season"]].dropna()
        for row in sub.itertuples(index=False):
            triples.add((getattr(row, batter_col), row.batting_team, row.season))

    # bowler -> bowling_team
    if "bowler" in merged.columns and "bowling_team" in merged.columns:
        sub = merged[["bowler", "bowling_team", "season"]].dropna()
        for row in sub.itertuples(index=False):
            triples.add((row.bowler, row.bowling_team, row.season))

    rows = []
    for player_name, team_name, season in triples:
        pid = player_id_map.get(player_name)
        tid = team_id_map.get(team_name)
        if pid is None or tid is None:
            continue
        rows.append((pid, tid, season))

    conn.executemany(
        "INSERT OR IGNORE INTO player_teams (player_id, team_id, season) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Step 7 — Orange Cap
# ---------------------------------------------------------------------------

def load_orange_cap(conn, matches_df, deliveries_df, player_id_map: dict) -> None:
    """Insert orange_cap awards (top run scorer per season)."""
    import pandas as pd

    df = deliveries_df.copy()

    # Handle is_super_over column
    if "is_super_over" in df.columns:
        df["is_super_over"] = pd.to_numeric(df["is_super_over"], errors="coerce").fillna(0).astype(int)
        df = df[df["is_super_over"] == 0]

    # Join seasons
    match_season = matches_df[["id", "season"]].copy()
    match_season["season"] = match_season["season"].apply(_coerce_season)
    match_season = match_season.rename(columns={"id": "match_id"})
    df = df.merge(match_season, on="match_id", how="left")

    # Support both old ("batsman") and new ("batter") column names
    batter_col = "batsman" if "batsman" in df.columns else "batter" if "batter" in df.columns else None
    if "batsman_runs" not in df.columns or batter_col is None:
        print("  [orange_cap] Required columns missing, skipping.")
        return

    runs = (
        df.groupby(["season", batter_col])["batsman_runs"]
        .sum()
        .reset_index()
        .rename(columns={batter_col: "batsman"})
    )

    rows = []
    for season, group in runs.groupby("season"):
        top = group.loc[group["batsman_runs"].idxmax()]
        pid = player_id_map.get(top["batsman"])
        if pid is None:
            continue
        rows.append(("orange_cap", pid, season))

    conn.executemany(
        "INSERT OR REPLACE INTO awards (type, player_id, season) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Step 8 — Purple Cap
# ---------------------------------------------------------------------------

_NON_BOWLER_DISMISSALS = {"run out", "retired hurt", "obstructing the field"}


def load_purple_cap(conn, matches_df, deliveries_df, player_id_map: dict) -> None:
    """Insert purple_cap awards (top wicket taker per season)."""
    import pandas as pd

    df = deliveries_df.copy()

    if "player_dismissed" not in df.columns or "dismissal_kind" not in df.columns:
        print("  [purple_cap] Required columns missing, skipping.")
        return

    # Keep only rows that are genuine bowler wickets
    df = df[
        df["player_dismissed"].notna()
        & ~df["dismissal_kind"].isin(_NON_BOWLER_DISMISSALS)
    ]

    # Join seasons
    match_season = matches_df[["id", "season"]].copy()
    match_season["season"] = match_season["season"].apply(_coerce_season)
    match_season = match_season.rename(columns={"id": "match_id"})
    df = df.merge(match_season, on="match_id", how="left")

    if "bowler" not in df.columns:
        print("  [purple_cap] bowler column missing, skipping.")
        return

    wickets = (
        df.groupby(["season", "bowler"])["player_dismissed"]
        .count()
        .reset_index()
        .rename(columns={"player_dismissed": "wickets"})
    )

    rows = []
    for season, group in wickets.groupby("season"):
        top = group.loc[group["wickets"].idxmax()]
        pid = player_id_map.get(top["bowler"])
        if pid is None:
            continue
        rows.append(("purple_cap", pid, season))

    conn.executemany(
        "INSERT OR REPLACE INTO awards (type, player_id, season) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Step 9 — Manual awards (player_of_tournament etc.)
# ---------------------------------------------------------------------------

def load_manual_awards(conn, data_dir: Path, player_id_map: dict) -> int:
    """Load manual_awards.json and insert into the awards table.

    Returns the number of rows inserted.
    """
    import json

    manual_path = data_dir / "manual_awards.json"
    if not manual_path.exists():
        print(f"  [manual_awards] {manual_path} not found, skipping.")
        return 0

    with open(manual_path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    skipped = []
    for award_type, season_map in data.items():
        if award_type.startswith("_"):  # skip comment keys
            continue
        for season_str, player_name in season_map.items():
            season = _coerce_season(season_str)
            if season is None:
                skipped.append((award_type, season_str, player_name))
                continue
            pid = player_id_map.get(player_name)
            if pid is None:
                skipped.append((award_type, season_str, player_name))
                continue
            rows.append((award_type, pid, int(season)))

    if skipped:
        print(f"  [manual_awards] {len(skipped)} entries skipped (player not in DB):")
        for award_type, season_str, name in skipped:
            print(f"    {award_type} {season_str}: '{name}'")

    conn.executemany(
        "INSERT OR REPLACE INTO awards (type, player_id, season) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# Step 11 — Summary
# ---------------------------------------------------------------------------

def print_summary(conn) -> None:
    def count(table, where=""):
        q = f"SELECT COUNT(*) FROM {table}"
        if where:
            q += f" WHERE {where}"
        return conn.execute(q).fetchone()[0]

    venues_n = count("venues")
    teams_n = count("teams")
    players_n = count("players")
    player_teams_n = count("player_teams")
    orange_n = count("awards", "type='orange_cap'")
    purple_n = count("awards", "type='purple_cap'")
    pot_n = count("awards", "type='player_of_tournament'")
    awards_n = orange_n + purple_n + pot_n
    ipl_wins_n = count("ipl_wins")

    print("\nLoaded:")
    print(f"  venues:       {venues_n}")
    print(f"  teams:        {teams_n}")
    print(f"  players:      {players_n}")
    print(f"  player_teams: {player_teams_n}")
    print(
        f"  awards:       {awards_n} "
        f"({orange_n} orange_cap + {purple_n} purple_cap + {pot_n} player_of_tournament)"
    )
    print(f"  ipl_wins:     {ipl_wins_n}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Kaggle IPL dataset CSVs into a SQLite database."
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        type=Path,
        help="Directory containing matches.csv and deliveries.csv",
    )
    parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="Path to the SQLite database file (will be created if absent)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before loading",
    )
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    db_path: Path = args.db

    _print_startup(data_dir)

    # Ensure parent directory of the DB exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Import schema helpers
    from schema import get_connection, create_schema, drop_schema

    conn = get_connection(str(db_path))

    if args.reset:
        print("--reset: dropping existing tables...")
        drop_schema(conn)

    create_schema(conn)

    # Step 1
    try:
        print("Step 1: Loading CSVs...")
        matches_df, deliveries_df = load_csvs(data_dir)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Step 1 FAILED: {exc}")
        sys.exit(1)

    # Step 2
    try:
        print("Step 2: Loading venues...")
        venue_id_map = load_venues(conn, matches_df)
        print(f"  {len(venue_id_map)} venues")
    except Exception as exc:
        print(f"Step 2 (venues) FAILED: {exc}")
        sys.exit(1)

    # Step 3
    try:
        print("Step 3: Loading teams...")
        team_id_map = load_teams(conn, matches_df)
        print(f"  {len(team_id_map)} teams")
    except Exception as exc:
        print(f"Step 3 (teams) FAILED: {exc}")
        sys.exit(1)

    # Step 4
    try:
        print("Step 4: Loading IPL season winners...")
        load_ipl_wins(conn, matches_df, team_id_map)
    except Exception as exc:
        print(f"Step 4 (ipl_wins) FAILED: {exc}")
        sys.exit(1)

    # Step 5
    try:
        print("Step 5: Loading players...")
        player_id_map = load_players(conn, matches_df, deliveries_df)
        print(f"  {len(player_id_map)} players")
    except Exception as exc:
        print(f"Step 5 (players) FAILED: {exc}")
        sys.exit(1)

    # Step 6
    try:
        print("Step 6: Loading player_teams...")
        load_player_teams(conn, matches_df, deliveries_df, player_id_map, team_id_map)
    except Exception as exc:
        print(f"Step 6 (player_teams) FAILED: {exc}")
        sys.exit(1)

    # Step 7
    try:
        print("Step 7: Loading Orange Cap awards...")
        load_orange_cap(conn, matches_df, deliveries_df, player_id_map)
    except Exception as exc:
        print(f"Step 7 (orange_cap) FAILED: {exc}")
        sys.exit(1)

    # Step 8
    try:
        print("Step 8: Loading Purple Cap awards...")
        load_purple_cap(conn, matches_df, deliveries_df, player_id_map)
    except Exception as exc:
        print(f"Step 8 (purple_cap) FAILED: {exc}")
        sys.exit(1)

    # Step 9
    try:
        print("Step 9: Loading manual awards (player_of_tournament)...")
        n = load_manual_awards(conn, data_dir, player_id_map)
        print(f"  {n} manual award entries loaded")
    except Exception as exc:
        print(f"Step 9 (manual_awards) FAILED: {exc}")
        sys.exit(1)

    # Step 10
    print_summary(conn)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
