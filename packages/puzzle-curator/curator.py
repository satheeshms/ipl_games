"""
curator.py — Puzzle Curator CLI for IPL Connections.

Usage:
  python3 curator.py create --date 2026-03-20 --output ../../apps/web/public/puzzles/
  python3 curator.py validate --file ../../apps/web/public/puzzles/2026-03-20.json
"""

import argparse
import itertools
import json
import random
import sys
from datetime import date as dt_date
from pathlib import Path

from hash_util import hash_items, verify_known_hashes, find_category_items, load_known_names, build_display_names

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLORS = ["yellow", "green", "blue", "purple"]

COLOR_DESCRIPTIONS = {
    "yellow": "YELLOW — Easiest (obvious IPL groupings)",
    "green":  "GREEN  — Moderate (requires IPL knowledge)",
    "blue":   "BLUE   — Hard (nuanced facts / less-known trivia)",
    "purple": "PURPLE — Hardest (wordplay, puns, obscure connections)",
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def shuffle(items: list) -> list:
    """Fisher-Yates shuffle — returns a new list."""
    a = list(items)
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


def search_data(query: str, ipl_data: dict) -> list[str]:
    """Return up to 10 player/team names matching query (case-insensitive substring).

    Also searches:
      foreign_players  — by player name or country
      india_state_wise — by player name or state (matching state returns all players in it)
      ranji_team_wise  — by player name or team name (matching team returns all players in it)
    """
    q = query.lower()
    results: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            results.append(name)

    for player in ipl_data.get("players", []):
        if q in player["name"].lower():
            add(player["name"])

    for team in ipl_data.get("teams", []):
        if q in team["name"].lower():
            add(team["name"])

    for p in ipl_data.get("foreign_players", []):
        if q in (p.get("name") or "").lower() or q in (p.get("country") or "").lower():
            add(p["name"])

    for state, players in ipl_data.get("india_state_wise", {}).items():
        if q in state.lower():
            for p in players:
                add(p["name"])
        else:
            for p in players:
                if q in (p.get("name") or "").lower():
                    add(p["name"])

    for ranji_team, players in ipl_data.get("ranji_team_wise", {}).items():
        if q in ranji_team.lower():
            for p in players:
                add(p["name"])
        else:
            for p in players:
                if q in (p.get("name") or "").lower():
                    add(p["name"])

    for row in ipl_data.get("player_teams", []):
        if q in (row.get("team_name") or "").lower() or q in str(row.get("season") or ""):
            add(row.get("player_name") or "")

    return results[:10]


BROWSE_SHORTCUTS = (
    "?team[:CODE[:SEASON]]  ?team_all:CODE  "
    "?coaches[:SEASON]  ?batting_coaches[:SEASON]  ?bowling_coaches[:SEASON]  ?fielding_coaches[:SEASON]  "
    "?orange_cap  ?purple_cap  ?pot  ?costliest  ?winning_captain  ?ipl_champions  "
    "?batting_records  ?bowling_records  ?season_records  ?fielding_records  ?team_owners  "
    "?countries  ?states  ?ranji  ?fifers  ?topbat  ?topbowl  ?multiteam  ?ducks  "
    "?strikers  ?batting_avg  ?fielders  ?keepers  ?allrounders"
)


def browse_groups(category: str, ipl_data: dict) -> None:
    """Print available groups / ranked lists for a browse shortcut.

    Shortcuts:
      ?countries  — foreign players grouped by country
      ?states     — Indian players grouped by home state
      ?ranji      — Indian players grouped by Ranji team
      ?fifers     — players with IPL 5-wicket hauls (wickets desc)
      ?topbat     — top run-scorers (runs desc)
      ?topbowl    — top wicket-takers (wickets desc)
      ?multiteam  — players who played for the most franchises
      ?ducks      — players with most ducks
    """
    if category == "countries":
        counts: dict[str, int] = {}
        for p in ipl_data.get("foreign_players", []):
            country = p.get("country") or "Unknown"
            counts[country] = counts.get(country, 0) + 1
        if not counts:
            print("  No foreign player data loaded.")
            return
        print("  Foreign player countries:")
        for country, n in sorted(counts.items()):
            print(f"    {country} ({n})")

    elif category == "states":
        groups = ipl_data.get("india_state_wise", {})
        if not groups:
            print("  No state data loaded.")
            return
        print("  Indian states:")
        for state, players in sorted(groups.items()):
            print(f"    {state} ({len(players)})")

    elif category == "ranji":
        groups = ipl_data.get("ranji_team_wise", {})
        if not groups:
            print("  No Ranji team data loaded.")
            return
        print("  Ranji Trophy teams:")
        for team, players in sorted(groups.items()):
            print(f"    {team} ({len(players)})")

    elif category == "fifers":
        players = ipl_data.get("five_wicket_hauls", [])
        if not players:
            print("  No five_wicket_hauls data loaded.")
            return
        print("  Players with IPL 5-wicket hauls (wickets desc):")
        for p in players:
            print(f"    {p['player_name']}  {p['wickets']}w  BBI {p['bbi']}")

    elif category == "topbat":
        players = ipl_data.get("batting_career_stats", [])
        if not players:
            print("  No batting_career_stats data loaded.")
            return
        print("  Top run-scorers:")
        for p in players:
            print(f"    {p['player_name']}  {p['runs']} runs  avg {p['average']}  100s {p['hundreds']}")

    elif category == "topbowl":
        players = ipl_data.get("bowling_career_stats", [])
        if not players:
            print("  No bowling_career_stats data loaded.")
            return
        print("  Top wicket-takers:")
        for p in players:
            print(f"    {p['player_name']}  {p['wickets']}w  econ {p['economy']}  BBI {p['bbi']}")

    elif category == "multiteam":
        players = ipl_data.get("multi_team_players", [])
        if not players:
            print("  No multi_team_players data loaded.")
            return
        print("  Players with most franchises:")
        for p in players:
            print(f"    {p['player_name']}  {p['team_count']} teams  ({p['teams']})")

    elif category == "ducks":
        players = ipl_data.get("most_ducks", [])
        if not players:
            print("  No most_ducks data loaded.")
            return
        print("  Players with most ducks:")
        for p in players:
            print(f"    {p['player_name']}  {p['ducks']} ducks  {p['innings']} innings")

    elif category == "strikers":
        players = ipl_data.get("high_strike_rate_batsmen", [])
        if not players:
            print("  No high_strike_rate_batsmen data loaded.")
            return
        print("  High strike rate batsmen (150+ SR):")
        for p in players:
            print(f"    {p['player_name']}  SR {p.get('strike_rate', '?')}  {p.get('matches', '?')} matches")

    elif category == "batting_avg":
        players = ipl_data.get("highest_batting_avg", [])
        if not players:
            print("  No highest_batting_avg data loaded.")
            return
        print("  Highest batting average (30+ avg, 50+ matches, 1000+ runs):")
        for p in players:
            print(f"    {p['player_name']}  avg {p.get('average', '?')}  {p.get('runs', '?')} runs  {p.get('matches', '?')} matches")

    elif category == "fielders":
        players = ipl_data.get("catches_by_fielder", [])
        if not players:
            print("  No catches_by_fielder data loaded.")
            return
        print("  Most catches by fielder (50+ matches, 50+ catches):")
        for p in players:
            print(f"    {p['player_name']}  {p.get('catches', '?')} catches  {p.get('matches', '?')} matches")

    elif category == "keepers":
        players = ipl_data.get("dismissals_by_keeper", [])
        if not players:
            print("  No dismissals_by_keeper data loaded.")
            return
        print("  Most dismissals by keeper (50+ matches, 50+ dismissals):")
        for p in players:
            print(f"    {p['player_name']}  {p.get('dismissals', '?')} dismissals  {p.get('matches', '?')} matches")

    elif category == "allrounders":
        players = ipl_data.get("allrounders", [])
        if not players:
            print("  No allrounders data loaded.")
            return
        print("  IPL Allrounders (1000+ runs & 50+ wickets):")
        for p in players:
            print(f"    {p['name']}  {p.get('runs', '?')} runs  {p.get('wickets', '?')} wickets")

    elif category.startswith("team_all"):
        parts = category.split(":", 1)
        pt = ipl_data.get("player_teams", [])
        if not pt:
            print("  No player_teams data loaded.")
            return
        if len(parts) == 1:
            print("  Usage: ?team_all:CODE  (e.g. ?team_all:CSK)")
            return
        q = parts[1].upper()
        from category_generators import _TEAM_CODES, _resolve_team
        try:
            team_name = _resolve_team(ipl_data, q)
        except ValueError as e:
            print(f"  {e}")
            return
        players = sorted({row["player_name"] for row in pt if row["team_name"] == team_name})
        print(f"  {team_name} — all-time players ({len(players)}):")
        for p in players:
            print(f"    {p}")

    elif category.startswith("team"):
        parts = category.split(":", 2)
        pt = ipl_data.get("player_teams", [])
        if not pt:
            print("  No player_teams data loaded.")
            return
        if len(parts) == 1:
            team_seasons: dict[str, set] = {}
            for row in pt:
                team_seasons.setdefault(row["team_name"], set()).add(row["season"])
            print("  Teams (use ?team:CODE for seasons, ?team:CODE:SEASON for squad):")
            for tn, seasons in sorted(team_seasons.items()):
                print(f"    {tn}  ({len(seasons)} seasons: {min(seasons)}-{max(seasons)})")
        elif len(parts) == 2:
            q = parts[1].lower()
            season_players: dict = {}
            for row in pt:
                if q in row["team_name"].lower():
                    season_players.setdefault(row["season"], []).append(row["player_name"])
            if not season_players:
                print(f"  No team matching '{parts[1]}'.")
                return
            print(f"  Seasons for '{parts[1]}' (use ?team:{parts[1]}:SEASON for squad):")
            for s in sorted(season_players):
                print(f"    {s}  ({len(season_players[s])} players)")
        elif len(parts) == 3:
            q, season_q = parts[1].lower(), parts[2]
            players = sorted({
                row["player_name"] for row in pt
                if q in row["team_name"].lower() and str(row["season"]) == season_q
            })
            if not players:
                print(f"  No players found for '{parts[1]}' {season_q}.")
                return
            print(f"  {parts[1]} {season_q} squad ({len(players)} players):")
            for p in players:
                print(f"    {p}")

    elif any(category.startswith(r) for r in
             ("coaches", "batting_coaches", "bowling_coaches", "fielding_coaches")):
        parts = category.split(":", 1)
        role_key = parts[0]
        role_map = {"coaches": "head", "batting_coaches": "batting",
                    "bowling_coaches": "bowling", "fielding_coaches": "fielding"}
        role = role_map.get(role_key, "head")
        all_coaches = ipl_data.get("coaches", [])
        if not all_coaches:
            print("  No coaches data loaded.")
            return
        if len(parts) == 1:
            seasons = sorted({c["season"] for c in all_coaches if c.get("role") == role})
            print(f"  Seasons with {role_key} data (use ?{role_key}:SEASON):")
            for s in seasons:
                n = sum(1 for c in all_coaches if c["season"] == s and c.get("role") == role)
                print(f"    {s}  ({n} coaches)")
        else:
            try:
                season = int(parts[1])
            except ValueError:
                print(f"  Invalid season '{parts[1]}'.")
                return
            names = sorted({c["coach"] for c in all_coaches
                            if c["season"] == season and c.get("role") == role})
            if not names:
                print(f"  No {role} coaches found for {season}.")
                return
            print(f"  {season} {role} coaches:")
            for n in names:
                print(f"    {n}")

    elif category in ("orange_cap", "purple_cap", "player_of_tournament",
                      "pot", "costliest", "costliest_player", "winning_captain"):
        award_map = {"pot": "player_of_tournament", "costliest": "costliest_player"}
        award_type = award_map.get(category, category)
        entries = [a for a in ipl_data.get("awards", []) if a["type"] == award_type]
        if not entries:
            print(f"  No {award_type} data loaded.")
            return
        print(f"  {award_type} winners ({len(entries)}):")
        for a in sorted(entries, key=lambda x: x["season"]):
            print(f"    {a['season']}  {a['player_name']}")

    elif category == "ipl_champions":
        wins = ipl_data.get("ipl_wins", [])
        if not wins:
            print("  No ipl_wins data loaded.")
            return
        print(f"  IPL Champions ({len(wins)}):")
        for w in sorted(wins, key=lambda x: x["season"]):
            print(f"    {w['season']}  {w['team_name']}")

    elif category in ("batting_records", "bowling_records", "season_records", "fielding_records"):
        entries = ipl_data.get("records", {}).get(category, [])
        if not entries:
            print(f"  No {category} data loaded.")
            return
        print(f"  {category} ({len(entries)}):")
        for e in entries:
            print(f"    {e.get('player')}  --  {e.get('record', '')}")

    elif category == "team_owners":
        entries = ipl_data.get("records", {}).get("team_owners", [])
        if not entries:
            print("  No team_owners data loaded.")
            return
        print(f"  Franchise owners ({len(entries)}):")
        for e in entries:
            print(f"    {e.get('owner')}  ({e.get('team', '')})")

    else:
        print(f"  Unknown browse shortcut. Available: {BROWSE_SHORTCUTS}")


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

# Cooldown windows (days). Adjust here to tune the rule engine.
ITEM_COOLDOWN_DAYS    = 2   # same item in any group within N days
GROUP_COOLDOWN_DAYS   = 4   # same group tag within N days
TYPE_COOLDOWN_DAYS    = 3   # same category-type prefix within N days
TEAM_COOLDOWN_DAYS    = 2   # same franchise team within N days


class RuleViolation:
    """A single rule violation with a severity level."""
    def __init__(self, rule: str, message: str, severity: str = "warn"):
        self.rule     = rule
        self.message  = message
        self.severity = severity   # "warn" (ask to override) | "block" (hard stop)

    def __repr__(self) -> str:
        return f"RuleViolation({self.rule!r}, severity={self.severity!r})"


class DedupeIndex:
    """Pre-computed lookup tables built from all past puzzle files."""
    def __init__(self):
        self.used_items:  dict[tuple[str, str], str] = {}  # (group, item) -> first_date
        self.group_dates: dict[str, str]              = {}  # group -> latest_date
        self.item_dates:  dict[str, str]              = {}  # item  -> latest_date (any group)
        self.type_dates:  dict[str, str]              = {}  # type_prefix -> latest_date
        self.team_dates:  dict[str, str]              = {}  # team_code -> latest_date

    @property
    def group_count(self) -> int:
        return len(self.group_dates)

    @property
    def pair_count(self) -> int:
        return len(self.used_items)


def _group_type(group: str) -> str:
    """'team_players:CSK:2026' -> 'team_players',  'orange_cap' -> 'orange_cap'"""
    return group.split(":")[0] if group else ""


def _team_code(group: str) -> str | None:
    """'team_players:CSK:2026' -> 'CSK',  anything else -> None"""
    parts = group.split(":")
    if parts[0] == "team_players" and len(parts) >= 2:
        return parts[1]
    return None


def _days_between(from_date: str, to_date: str) -> int | None:
    """Return (to_date - from_date).days, or None if either date is unparseable."""
    try:
        return (dt_date.fromisoformat(to_date) - dt_date.fromisoformat(from_date)).days
    except ValueError:
        return None


def check_group_rules(group: str, puzzle_date: str, idx: "DedupeIndex") -> list[RuleViolation]:
    """Run all group-tag-level rules. Returns list of violations (may be empty)."""
    if not group:
        return []
    violations: list[RuleViolation] = []

    # Rule 1: group cooldown
    if group in idx.group_dates:
        n = _days_between(idx.group_dates[group], puzzle_date)
        if n is not None and 0 < n < GROUP_COOLDOWN_DAYS:
            violations.append(RuleViolation(
                rule="group_cooldown",
                message=(f"Group '{group}' was last used on {idx.group_dates[group]} "
                         f"({n} day(s) ago — min gap is {GROUP_COOLDOWN_DAYS} days)."),
            ))

    # Rule 2: category-type cooldown
    gtype = _group_type(group)
    if gtype and gtype in idx.type_dates:
        n = _days_between(idx.type_dates[gtype], puzzle_date)
        if n is not None and 0 < n < TYPE_COOLDOWN_DAYS:
            violations.append(RuleViolation(
                rule="type_cooldown",
                message=(f"Category type '{gtype}' was last used on {idx.type_dates[gtype]} "
                         f"({n} day(s) ago — min gap is {TYPE_COOLDOWN_DAYS} days)."),
            ))

    # Rule 3: team cooldown
    team = _team_code(group)
    if team and team in idx.team_dates:
        n = _days_between(idx.team_dates[team], puzzle_date)
        if n is not None and 0 < n < TEAM_COOLDOWN_DAYS:
            violations.append(RuleViolation(
                rule="team_cooldown",
                message=(f"Team '{team}' appeared in a puzzle on {idx.team_dates[team]} "
                         f"({n} day(s) ago — min gap is {TEAM_COOLDOWN_DAYS} days)."),
            ))

    return violations


def check_item_rules(group: str, item: str, puzzle_date: str,
                     idx: "DedupeIndex") -> list[RuleViolation]:
    """Run all item-level rules. Returns list of violations (may be empty)."""
    violations: list[RuleViolation] = []

    # Rule 4: (group, item) pair already used — permanent block
    if group:
        prev = idx.used_items.get((group, item))
        if prev:
            violations.append(RuleViolation(
                rule="group_item_used",
                message=f"'{item}' was already used in group '{group}' on {prev}.",
                severity="block",
            ))

    # Rule 5: item appeared in any puzzle within the cooldown window
    if item in idx.item_dates:
        n = _days_between(idx.item_dates[item], puzzle_date)
        if n is not None and 0 < n < ITEM_COOLDOWN_DAYS:
            violations.append(RuleViolation(
                rule="item_cooldown",
                message=(f"'{item}' appeared in a puzzle {n} day(s) ago "
                         f"(min gap is {ITEM_COOLDOWN_DAYS} days)."),
            ))

    return violations


def prompt_violations(violations: list[RuleViolation]) -> bool:
    """Print violations and ask for confirmation if any are warnings.

    Returns True if the curator wants to proceed, False to reject.
    Blocks (severity='block') always return False.
    """
    if not violations:
        return True

    blocks = [v for v in violations if v.severity == "block"]
    warns  = [v for v in violations if v.severity == "warn"]

    for v in violations:
        tag = "[BLOCK]" if v.severity == "block" else "[WARN] "
        print(f"  {tag} {v.message}")

    if blocks:
        print("  This item cannot be added (hard block). Choose a different item.")
        return False

    override = input(f"  Add anyway? [y/N]: ").strip().lower()
    return override == "y"


# ---------------------------------------------------------------------------
# Deduplication helpers
# ---------------------------------------------------------------------------


def load_used_items(output_dir: Path) -> DedupeIndex:
    """Scan all existing YYYY-MM-DD.json puzzle files in output_dir.

    Builds and returns a DedupeIndex with five lookup tables:
      used_items  : {(group, item): first_date_used}     — permanent pair tracking
      group_dates : {group: latest_date_used}             — group cooldown
      item_dates  : {item: latest_date_used (any group)}  — item cooldown
      type_dates  : {type_prefix: latest_date_used}       — category-type cooldown
      team_dates  : {team_code: latest_date_used}         — team cooldown

    Only categories with both a 'group' field and an 'items' list are indexed.
    Legacy puzzle files without these fields are silently skipped.
    """
    idx = DedupeIndex()
    if not output_dir.exists():
        return idx

    def _update_latest(d: dict, key: str, date: str) -> None:
        if key and (key not in d or date > d[key]):
            d[key] = date

    for puzzle_file in sorted(output_dir.glob("????-??-??.json")):
        try:
            with puzzle_file.open(encoding="utf-8") as fh:
                puzzle = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue

        date = puzzle.get("date", puzzle_file.stem)
        for cat in puzzle.get("categories", []):
            group = (cat.get("group") or "").strip()
            if not group:
                continue

            _update_latest(idx.group_dates, group, date)
            _update_latest(idx.type_dates,  _group_type(group), date)
            team = _team_code(group)
            if team:
                _update_latest(idx.team_dates, team, date)

            cat_items = cat.get("items") or find_category_items(
                puzzle.get("items", []), cat.get("hash", "")
            )
            for item in cat_items:
                key = (group, item)
                if key not in idx.used_items:
                    idx.used_items[key] = date
                _update_latest(idx.item_dates, item, date)

    return idx


# ---------------------------------------------------------------------------
# `create` subcommand
# ---------------------------------------------------------------------------


def cmd_create(args: argparse.Namespace) -> int:
    print("=" * 60)
    print("  IPL Connections — Puzzle Creator")
    print("=" * 60)

    output_dir = Path(args.output)

    # 1. Verify hash_util is working correctly
    print("\n[1/8] Verifying hash_util …")
    if not verify_known_hashes():
        print("ERROR: hash_util verification failed. Aborting.")
        return 1
    print("  Hash verification: PASS")

    # 2. Load optional data file + past-puzzle dedup index
    print("\n[2/8] Loading data …")
    ipl_data: dict = {}
    if args.data_file:
        data_path = Path(args.data_file)
        if not data_path.exists():
            print(f"WARNING: data file not found: {data_path}. Search helper disabled.")
        else:
            with data_path.open(encoding="utf-8") as fh:
                ipl_data = json.load(fh)
            player_count      = len(ipl_data.get("players", []))
            team_count        = len(ipl_data.get("teams", []))
            pt_count          = len(ipl_data.get("player_teams", []))
            awards_count      = len(ipl_data.get("awards", []))
            coaches_count     = len(ipl_data.get("coaches", []))
            foreign_count     = len(ipl_data.get("foreign_players", []))
            state_count       = len(ipl_data.get("india_state_wise", {}))
            ranji_count       = len(ipl_data.get("ranji_team_wise", {}))
            fifers_count      = len(ipl_data.get("five_wicket_hauls", []))
            topbat_count      = len(ipl_data.get("batting_career_stats", []))
            topbowl_count     = len(ipl_data.get("bowling_career_stats", []))
            multiteam_count   = len(ipl_data.get("multi_team_players", []))
            ducks_count       = len(ipl_data.get("most_ducks", []))
            strikers_count    = len(ipl_data.get("high_strike_rate_batsmen", []))
            batting_avg_count = len(ipl_data.get("highest_batting_avg", []))
            fielders_count    = len(ipl_data.get("catches_by_fielder", []))
            keepers_count     = len(ipl_data.get("dismissals_by_keeper", []))
            allrounders_count = len(ipl_data.get("allrounders", []))
            print(f"  Loaded: {player_count} players, {team_count} teams, "
                  f"{pt_count} player-team-season rows, {awards_count} awards, "
                  f"{coaches_count} coach records, {foreign_count} foreign players, "
                  f"{state_count} states, {ranji_count} ranji teams, "
                  f"{fifers_count} fifers, {topbat_count} top batsmen, {topbowl_count} top bowlers, "
                  f"{multiteam_count} multi-team, {ducks_count} ducks, "
                  f"{strikers_count} strikers, {batting_avg_count} batting avg, "
                  f"{fielders_count} fielders, {keepers_count} keepers, {allrounders_count} allrounders")
            print(f"  Browse: {BROWSE_SHORTCUTS}")

    idx = load_used_items(output_dir)
    if idx.pair_count:
        print(f"  Dedup index: {idx.pair_count} (group, item) pairs across "
              f"{idx.group_count} groups from past puzzles")
        print(f"  Rules: item cooldown {ITEM_COOLDOWN_DAYS}d  |  "
              f"group cooldown {GROUP_COOLDOWN_DAYS}d  |  "
              f"type cooldown {TYPE_COOLDOWN_DAYS}d  |  "
              f"team cooldown {TEAM_COOLDOWN_DAYS}d")
    else:
        print("  Dedup index: no past puzzles found — starting fresh")

    # 3. Collect categories interactively
    print("\n[3/8] Enter puzzle categories\n")
    categories_data: list[dict] = []  # [{color, title, items:[str]}]

    for color in COLORS:
        desc = COLOR_DESCRIPTIONS[color]
        print(f"  ── {desc} ──")

        # Title
        while True:
            title = input(f"  Category title for {color.upper()}: ").strip()
            if title:
                break
            print("  Title cannot be empty. Try again.")

        # Group tag — used for cross-puzzle deduplication
        print(f"  Group tag identifies the data source for dedup (e.g. topbat / state:Karnataka / ranji:Mumbai).")
        if idx.group_dates:
            print(f"  Groups used so far: {', '.join(sorted(idx.group_dates))}")
        while True:
            group = input(f"  Group tag for {color.upper()} (Enter to skip): ").strip()
            violations = check_group_rules(group, args.date, idx)
            if not prompt_violations(violations):
                print("  Enter a different group tag.")
                continue
            break

        # Items — prompt until exactly 4 unique items collected
        items: list[str] = []
        print(f"  Enter 4 items for {color.upper()}:")
        while len(items) < 4:
            remaining = 4 - len(items)
            prompt_label = f"  Item {len(items) + 1}/4"

            # Optional search helper
            if ipl_data:
                search_query = input(f"{prompt_label} — Search / browse (? for shortcuts, Enter to skip): ").strip()
                if search_query == "?":
                    print(f"  Browse shortcuts: {BROWSE_SHORTCUTS}")
                elif search_query.startswith("?"):
                    browse_groups(search_query[1:].lower(), ipl_data)
                elif search_query:
                    matches = search_data(search_query, ipl_data)
                    if matches:
                        print("  Matches:")
                        for idx, m in enumerate(matches, 1):
                            print(f"    {idx}. {m}")
                    else:
                        print("  No matches found.")

            item = input(f"{prompt_label} — Item name: ").strip()
            if not item:
                print(f"  Need {remaining} more item(s). Please enter an item name.")
                continue
            if item in items:
                print(f"  '{item}' already added to this category. Enter a different item.")
                continue

            # Cross-puzzle rule checks
            violations = check_item_rules(group, item, args.date, idx)
            if not prompt_violations(violations):
                print("  Skipped. Please enter a different item.")
                continue

            items.append(item)
            print(f"  Added: {item}  ({len(items)}/4)")

        categories_data.append({"color": color, "title": title, "group": group, "items": items})
        print()

    # 4. Validate: no duplicate items across all 4 categories
    print("[4/8] Checking for duplicate items …")
    all_items: list[str] = []
    duplicates: list[str] = []
    for cat in categories_data:
        for item in cat["items"]:
            if item in all_items:
                duplicates.append(item)
            else:
                all_items.append(item)

    if duplicates:
        print(f"ERROR: Duplicate items found across categories: {duplicates}")
        print("Please re-run and enter unique items in each category.")
        return 1
    print("  No duplicates found: OK")

    # 5. Compute SHA-256 hash for each category
    print("\n[5/8] Computing category hashes …")
    categories_out: list[dict] = []
    for cat in categories_data:
        h = hash_items(cat["items"])
        entry = {
            "color": cat["color"],
            "title": cat["title"],
            "hash":  h,
        }
        if cat["group"]:
            entry["group"] = cat["group"]
        categories_out.append(entry)
        group_label = f"  [{cat['group']}]" if cat["group"] else ""
        print(f"  {cat['color'].upper():8s} '{cat['title']}'{group_label} → {h[:16]}…")

    # 6. Shuffle all 16 items
    print("\n[6/8] Shuffling items …")
    shuffled_items = shuffle(all_items)
    print(f"  Items shuffled: {shuffled_items}")

    # 7. Determine edition number
    print("\n[7/8] Determining edition number …")
    if args.edition is not None:
        edition = args.edition
        print(f"  Edition (from --edition flag): {edition}")
    else:
        # Count existing YYYY-MM-DD.json puzzle files (exclude dev.json etc.)
        existing = [
            f for f in output_dir.glob("????-??-??.json")
            if f.is_file()
        ]
        edition = len(existing) + 1
        print(f"  Auto-detected edition: {edition} ({len(existing)} existing puzzle(s) found)")

    # 8. Write puzzle JSON
    print(f"\n[8/8] Writing puzzle file …")
    known_names = load_known_names()
    display_names = build_display_names(shuffled_items, known_names)
    puzzle: dict = {
        "id": args.date,
        "date": args.date,
        "edition": edition,
        "items": shuffled_items,
        "categories": categories_out,
    }
    if display_names:
        puzzle["display_names"] = display_names

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{args.date}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, indent=2, ensure_ascii=False)
    print(f"  Written: {out_path.resolve()}")

    # 9. Print summary for review
    print("\n" + "=" * 60)
    print("  PUZZLE SUMMARY")
    print("=" * 60)
    print(json.dumps(puzzle, indent=2, ensure_ascii=False))
    print("=" * 60)
    print(f"\nPuzzle #{edition} for {args.date} saved successfully.")
    return 0


# ---------------------------------------------------------------------------
# `validate` subcommand
# ---------------------------------------------------------------------------


def cmd_validate(args: argparse.Namespace) -> int:
    file_path = Path(args.file)
    print("=" * 60)
    print(f"  IPL Connections — Puzzle Validator")
    print(f"  File: {file_path}")
    print("=" * 60)

    errors: list[str] = []

    # 1. JSON parses correctly
    print("\n[1] Parsing JSON …")
    try:
        with file_path.open(encoding="utf-8") as fh:
            puzzle = json.load(fh)
        print("  JSON parse: OK")
    except FileNotFoundError:
        print(f"  ERROR: File not found: {file_path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"  ERROR: Invalid JSON: {exc}")
        return 1

    # 2. Required fields present
    print("\n[2] Checking required fields …")
    required_fields = ["id", "date", "edition", "items", "categories"]
    for field in required_fields:
        if field not in puzzle:
            errors.append(f"Missing required field: '{field}'")
        else:
            print(f"  '{field}': OK")

    if errors:
        _print_errors(errors)
        return 1

    # 3. Exactly 16 items
    print("\n[3] Checking item count …")
    item_count = len(puzzle["items"])
    if item_count != 16:
        errors.append(f"Expected 16 items, found {item_count}")
    else:
        print(f"  Item count: {item_count} — OK")

    # 4. Exactly 4 categories with correct colors (one each)
    print("\n[4] Checking categories …")
    categories = puzzle.get("categories", [])
    cat_count = len(categories)
    if cat_count != 4:
        errors.append(f"Expected 4 categories, found {cat_count}")
    else:
        print(f"  Category count: {cat_count} — OK")

    found_colors = [c.get("color") for c in categories]
    for required_color in COLORS:
        if found_colors.count(required_color) != 1:
            errors.append(f"Expected exactly one '{required_color}' category; found {found_colors.count(required_color)}")
        else:
            print(f"  Color '{required_color}': OK")

    # 5. No duplicate items
    print("\n[5] Checking for duplicate items …")
    items: list[str] = puzzle.get("items", [])
    seen: set[str] = set()
    dupes: list[str] = []
    for item in items:
        if item in seen:
            dupes.append(item)
        seen.add(item)
    if dupes:
        errors.append(f"Duplicate items: {dupes}")
    else:
        print(f"  No duplicates: OK")

    # 6. Each category hash is a valid 64-char hex string
    print("\n[6] Checking hash format …")
    for cat in categories:
        color = cat.get("color", "?")
        h = cat.get("hash", "")
        if not (isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)):
            errors.append(f"Category '{color}' has invalid hash: '{h}'")
        else:
            print(f"  '{color}' hash format: OK")

    if errors:
        _print_errors(errors)
        return 1

    # 7. Hash round-trip: find which 4 items produce each category hash
    print("\n[7] Verifying category hashes (round-trip, C(16,4)=1820 combinations) …")
    hash_errors: list[str] = []
    for cat in categories:
        color = cat["color"]
        stored_hash = cat["hash"]
        matched = False
        for combo in itertools.combinations(puzzle["items"], 4):
            if hash_items(list(combo)) == stored_hash:
                matched = True
                print(f"  '{color}' hash verified: {list(combo)}")
                break
        if not matched:
            hash_errors.append(
                f"Category '{color}' (title: '{cat.get('title', '?')}') hash does not match any combination of 4 items"
            )

    if hash_errors:
        errors.extend(hash_errors)

    # Final result
    print("\n" + "=" * 60)
    if errors:
        _print_errors(errors)
        print("  Result: FAIL")
        print("=" * 60)
        return 1
    else:
        print("  Result: PASS — puzzle is valid")
        print("=" * 60)
        return 0


def _print_errors(errors: list[str]) -> None:
    print("\n  ERRORS:")
    for err in errors:
        print(f"    - {err}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="curator",
        description="IPL Connections — Puzzle Curator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- create ---------------------------------------------------------------
    create_p = subparsers.add_parser(
        "create",
        help="Interactively create a new puzzle JSON file",
    )
    create_p.add_argument(
        "--date",
        required=True,
        metavar="YYYY-MM-DD",
        help="Puzzle date (used as file name and puzzle id)",
    )
    create_p.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Output directory for the puzzle JSON file",
    )
    create_p.add_argument(
        "--edition",
        type=int,
        default=None,
        metavar="N",
        help="Edition number (auto-detected from existing files if omitted)",
    )
    create_p.add_argument(
        "--data-file",
        default=None,
        metavar="PATH",
        help="Optional path to ipl_data.json for the search helper",
    )

    # -- validate -------------------------------------------------------------
    validate_p = subparsers.add_parser(
        "validate",
        help="Validate an existing puzzle JSON file",
    )
    validate_p.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to the puzzle JSON file to validate",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAborted by user (Ctrl+C). No file was written.")
        sys.exit(1)
