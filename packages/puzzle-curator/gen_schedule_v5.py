"""
gen_schedule_v5.py — Generate IPL 2026 puzzle curation_schedule.md (65 editions).

Improvements over v4:
  - 65 editions (pre-IPL reduced to 3: 25-27 Mar)
  - All new Phase-1 generators: geographic, cross-team, legends,
    winning_squad, coaches:TEAM:SEASON, top_run_scorers, top_wicket_takers
  - 4 Worlds constraint: Yellow/Green/Blue/Purple from different category groups
  - Signature puzzles every ~7 editions with special themes
  - Fan-base weighted Yellow team rotation (Mega tier 50%)
  - Cooldown engine: 4-day category, 3-day team

Usage:
  python gen_schedule_v5.py              # writes curation_schedule.md
  python gen_schedule_v5.py --preview    # prints to stdout only
"""

import argparse
import json
import random
from datetime import date, timedelta
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Puzzle dates: 65 editions
# ---------------------------------------------------------------------------

def _date_range(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

# Pre-IPL: 25-27 Mar (3 days)
# Phase 1:  28 Mar - 12 Apr (16 days)
# Phase 2:  13 Apr - 21 May (39 days)
# Playoffs: 22, 23, 24, 26, 28, 30, 31 May (7 days)
PUZZLE_DATES = (
    list(_date_range(date(2026, 3, 25), date(2026, 5, 21))) +
    [date(2026, 5, 22), date(2026, 5, 23), date(2026, 5, 24),
     date(2026, 5, 26), date(2026, 5, 28), date(2026, 5, 30), date(2026, 5, 31)]
)

assert len(PUZZLE_DATES) == 65, f"Expected 65 dates, got {len(PUZZLE_DATES)}"

# ---------------------------------------------------------------------------
# IPL 2026 fixtures (match-day team anchoring for Yellow)
# Hardcoded — update once official schedule is confirmed.
# Format: "YYYY-MM-DD": (team1, team2)
# Yellow picks team1 (home/first-listed team)
# ---------------------------------------------------------------------------

FIXTURES_2026 = {
    # Phase 1 (28 Mar - 12 Apr)
    "2026-03-28": ("RCB", "SRH"),
    "2026-03-29": ("MI",  "KKR"),
    "2026-03-30": ("RR",  "CSK"),
    "2026-03-31": ("PBKS","GT"),
    "2026-04-01": ("LSG", "DC"),
    "2026-04-02": ("KKR", "SRH"),
    "2026-04-03": ("CSK", "PBKS"),
    "2026-04-04": ("DC",  "MI"),
    "2026-04-05": ("SRH", "LSG"),
    "2026-04-06": ("KKR", "PBKS"),
    "2026-04-07": ("RR",  "MI"),
    "2026-04-08": ("DC",  "GT"),
    "2026-04-09": ("KKR", "LSG"),
    "2026-04-10": ("RR",  "RCB"),
    "2026-04-11": ("PBKS","SRH"),
    "2026-04-12": ("LSG", "GT"),
    # Phase 2 (13 Apr - 21 May) — rotating all 10 teams
    "2026-04-13": ("RCB", "CSK"),
    "2026-04-14": ("MI",  "RR"),
    "2026-04-15": ("KKR", "DC"),
    "2026-04-16": ("GT",  "SRH"),
    "2026-04-17": ("CSK", "LSG"),
    "2026-04-18": ("RCB", "MI"),
    "2026-04-19": ("PBKS","KKR"),
    "2026-04-20": ("RR",  "GT"),
    "2026-04-21": ("DC",  "SRH"),
    "2026-04-22": ("CSK", "RCB"),
    "2026-04-23": ("MI",  "PBKS"),
    "2026-04-24": ("LSG", "RR"),
    "2026-04-25": ("KKR", "GT"),
    "2026-04-26": ("SRH", "DC"),
    "2026-04-27": ("RCB", "LSG"),
    "2026-04-28": ("CSK", "MI"),
    "2026-04-29": ("GT",  "PBKS"),
    "2026-04-30": ("RR",  "KKR"),
    "2026-05-01": ("DC",  "RCB"),
    "2026-05-02": ("MI",  "SRH"),
    "2026-05-03": ("LSG", "CSK"),
    "2026-05-04": ("PBKS","RR"),
    "2026-05-05": ("GT",  "KKR"),
    "2026-05-06": ("SRH", "RCB"),
    "2026-05-07": ("DC",  "LSG"),
    "2026-05-08": ("MI",  "CSK"),
    "2026-05-09": ("RR",  "SRH"),
    "2026-05-10": ("KKR", "PBKS"),
    "2026-05-11": ("GT",  "RCB"),
    "2026-05-12": ("DC",  "CSK"),
    "2026-05-13": ("MI",  "GT"),
    "2026-05-14": ("LSG", "KKR"),
    "2026-05-15": ("SRH", "PBKS"),
    "2026-05-16": ("RCB", "RR"),
    "2026-05-17": ("CSK", "DC"),
    "2026-05-18": ("KKR", "MI"),
    "2026-05-19": ("GT",  "LSG"),
    "2026-05-20": ("PBKS","RR"),
    "2026-05-21": ("SRH", "DC"),
}

# ---------------------------------------------------------------------------
# Category groups (for 4-Worlds constraint)
# ---------------------------------------------------------------------------

GROUP_A = "A"  # Team-based (squads, winning_squad)
GROUP_B = "B"  # Awards (orange_cap, purple_cap, etc.)
GROUP_C = "C"  # Statistical
GROUP_D = "D"  # Geographic
GROUP_E = "E"  # Cross-team / relational
GROUP_F = "F"  # Management (coaches, team_owners)

def get_group(spec: str) -> str:
    if spec.startswith(("team_players:", "team_all_seasons:", "winning_squad:")):
        return GROUP_A
    if spec in ("orange_cap", "purple_cap", "winning_captain",
                "costliest_player", "player_of_tournament", "ipl_champions"):
        return GROUP_B
    if spec.startswith(("batting_records", "bowling_records", "season_records",
                        "fielding_records", "highest_batting_avg", "high_strike_rate",
                        "catches_by_fielder", "dismissals_by_keeper", "allrounders",
                        "top_run_scorers", "top_wicket_takers", "most_fifties",
                        "most_matches", "team_legends:", "most_ducks", "fifers")):
        return GROUP_C
    if spec.startswith(("country:", "state:", "ranji:")):
        return GROUP_D
    if spec.startswith(("played_both:", "multi_team:", "longest_serving",
                        "legends:")):
        return GROUP_E
    if spec.startswith(("coaches:", "team_owners", "batting_coaches:",
                        "bowling_coaches:", "fielding_coaches:")):
        return GROUP_F
    return GROUP_C  # default

# ---------------------------------------------------------------------------
# Cooldown engine
# ---------------------------------------------------------------------------

COOLDOWN_CAT  = 4   # days before same category type can repeat
COOLDOWN_TEAM = 3   # days before same team can appear in Yellow/Green

def cooldown_key(spec: str) -> str:
    """Normalise spec to its cooldown bucket key."""
    if spec.startswith("team_players:"):
        parts = spec.split(":")
        return f"team:{parts[1]}"           # team-level (ignore season)
    if spec.startswith("team_all_seasons:"):
        parts = spec.split(":")
        return f"team:{parts[1]}"
    if spec.startswith("winning_squad:"):
        return "winning_squad"              # all seasons share one bucket
    if spec.startswith("coaches:") and spec.count(":") == 1:
        return "coaches_season"            # coaches:SEASON
    if spec.startswith("coaches:") and spec.count(":") == 2:
        return "coaches_team_season"       # coaches:TEAM:SEASON
    if spec.startswith("country:"):
        return spec                        # each country separate
    if spec.startswith("state:"):
        return spec
    if spec.startswith("ranji:"):
        return spec
    if spec.startswith("played_both:"):
        parts = spec.split(":")
        key = ":".join(sorted([parts[1], parts[2]]))
        return f"played_both:{key}"
    if spec.startswith("team_legends:"):
        return spec
    return spec


class CooldownEngine:
    def __init__(self):
        self._last: dict[str, int] = {}   # cooldown_key → day index last used

    def available(self, spec: str, day_idx: int, cooldown: int = COOLDOWN_CAT) -> bool:
        key = cooldown_key(spec)
        last = self._last.get(key, -999)
        return (day_idx - last) >= cooldown

    def record(self, spec: str, day_idx: int):
        self._last[cooldown_key(spec)] = day_idx

    def team_available(self, team_code: str, day_idx: int) -> bool:
        key = f"team:{team_code}"
        last = self._last.get(key, -999)
        return (day_idx - last) >= COOLDOWN_TEAM


# ---------------------------------------------------------------------------
# Category pools per slot
# ---------------------------------------------------------------------------

MEGA_TEAMS  = ["MI", "CSK", "RCB", "KKR"]
LARGE_TEAMS = ["RR", "SRH"]
SMALL_TEAMS = ["DC", "PBKS", "GT", "LSG"]
ALL_TEAMS   = MEGA_TEAMS + LARGE_TEAMS + SMALL_TEAMS  # 10 teams

# Teams that existed in inaugural 2008 season
TEAMS_IN_2008     = {"RCB", "CSK", "MI", "KKR", "RR", "PBKS", "DC"}
TEAMS_NOT_IN_2008 = {"SRH", "GT", "LSG"}

# ---------------------------------------------------------------------------
# Yellow pool — Easy slot
#
# Squad specs are repeated proportionally to fan-base size so the rotation
# naturally weights Mega teams more heavily.  Caps (computed from squad sizes
# at runtime) enforce the hard per-spec limit.
#
# Non-squad openers (awards, records, legends) appear once or twice so they
# surface naturally across the 65-edition run without any hardcoded placement.
# To add a new spec, just append it here.
# ---------------------------------------------------------------------------
YELLOW_POOL: list[str] = (
    [f"team_players:{t}:2026" for t in MEGA_TEAMS]  * 7 +   # MI/CSK/RCB/KKR × 7
    [f"team_players:{t}:2026" for t in LARGE_TEAMS] * 5 +   # RR/SRH × 5
    [f"team_players:{t}:2026" for t in SMALL_TEAMS] * 4 +   # DC/PBKS/GT/LSG × 4
    # Non-squad variety — once each; update this list freely as data changes
    ["ipl_champions", "orange_cap", "legends:india",
     "team_owners",   "top_run_scorers", "batting_records"]
)

# ---------------------------------------------------------------------------
# Green pool — Medium slot (standalone / non-team-paired)
#
# Used when Yellow is non-squad, or when all same-team Green options are
# exhausted.  Team-paired options (TEAM:2008, team_all_seasons, team_legends)
# are tried first in _pick_green before falling back to this pool.
# To surface a spec earlier, add more copies; to restrict, remove copies.
# ---------------------------------------------------------------------------
GREEN_POOL: list[str] = (
    # Legends & history
    ["legends:india", "legends:india",
     "legends:overseas", "legends:overseas",
     "winning_squad:2008", "winning_squad:2011", "winning_squad:2013",
     "winning_squad:2016", "winning_squad:2019", "winning_squad:2022",
     "winning_squad:2024"] +
    # Awards / management (medium difficulty)
    ["orange_cap", "purple_cap", "costliest_player", "winning_captain",
     "player_of_tournament",
     "coaches:2026", "coaches:2025", "coaches:2024", "coaches:2023",
     "coaches:2022", "coaches:2021", "coaches:2020", "coaches:2019"] +
    # Geographic
    ["country:Australia", "country:South Africa", "country:England",
     "country:New Zealand", "country:Sri Lanka", "country:West Indies",
     "state:Maharashtra", "state:Delhi", "state:Karnataka",
     "state:Tamil Nadu", "state:Uttar Pradesh", "state:Punjab",
     "ranji:Mumbai", "ranji:Delhi", "ranji:Karnataka"] +
    # Historical squad fallbacks (when team-pairing unavailable)
    [f"team_players:{t}:2008" for t in sorted(TEAMS_IN_2008)] +
    [f"team_all_seasons:{t}" for t in ALL_TEAMS] +
    [f"team_legends:{t}"     for t in ALL_TEAMS]
)

# ---------------------------------------------------------------------------
# Blue pool: stats + geographic + management — complexity 3
# ---------------------------------------------------------------------------
BLUE_POOL = [
    # Stats
    "top_run_scorers", "top_wicket_takers", "highest_batting_avg",
    "catches_by_fielder", "most_fifties", "most_matches",
    "top_run_scorers", "top_wicket_takers", "highest_batting_avg",
    "catches_by_fielder", "most_fifties",
    "top_run_scorers", "top_wicket_takers", "highest_batting_avg",
    "catches_by_fielder",
    # Geographic
    "country:Australia", "country:South Africa", "country:England",
    "country:New Zealand", "country:Sri Lanka", "country:West Indies",
    "state:Maharashtra", "state:Delhi", "state:Karnataka",
    "state:Tamil Nadu", "state:Uttar Pradesh", "state:Punjab",
    "ranji:Mumbai", "ranji:Delhi", "ranji:Karnataka",
    # Management
    "coaches:2026", "coaches:2025", "coaches:2024", "coaches:2023",
    "coaches:2022", "coaches:2021", "coaches:2020", "coaches:2019",
    "coaches:2018", "coaches:2017", "coaches:2016", "coaches:2015",
    "coaches:2014", "coaches:2013", "coaches:2012", "coaches:2011",
    "coaches:2010", "coaches:2009", "coaches:2008",
    # Records (use once each)
    "batting_records", "bowling_records", "season_records", "fielding_records",
]

# Purple pool: niche + cross-team + expert stats — complexity 4
PURPLE_POOL = [
    # Cross-team
    "played_both:CSK:MI", "played_both:CSK:RCB", "played_both:RCB:MI",
    "played_both:KKR:MI", "played_both:CSK:KKR", "played_both:RR:CSK",
    "multi_team:5", "multi_team:7", "longest_serving",
    # Niche stats
    "most_ducks", "most_ducks", "most_ducks",
    "dismissals_by_keeper", "dismissals_by_keeper",
    "allrounders", "allrounders",
    "fifers", "fifers", "fifers",
    "high_strike_rate", "high_strike_rate",
    # Awards (used as purple when tricky)
    "orange_cap", "purple_cap", "winning_captain",
    "costliest_player", "player_of_tournament", "ipl_champions",
    "team_owners", "team_owners",
    # Winning squads (historical)
    "winning_squad:2008", "winning_squad:2011", "winning_squad:2013",
    "winning_squad:2016", "winning_squad:2019", "winning_squad:2022",
    "winning_squad:2024",
]

# ---------------------------------------------------------------------------
# Main scheduler
# ---------------------------------------------------------------------------

def spec_prefix(spec: str) -> str:
    """Return the type prefix of a spec, e.g. 'country' for 'country:Australia'."""
    return spec.split(":")[0]


# Reverse mapping: short code → full team name (mirrors category_generators._TEAM_CODES)
_TEAM_FULL_NAMES: dict[str, str] = {
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
_FULL_NAME_TO_CODE: dict[str, str] = {v: k for k, v in _TEAM_FULL_NAMES.items()}


def compute_pool_caps(data_file: Path | None = None) -> dict[str, int]:
    """
    Compute max uses per spec from ipl_data.json pool sizes.

    For a pool of N distinct items, cap = max(1, N // 4) so schedule_runner
    never exhausts the pool.  Returns {} gracefully if data unavailable.

    Covers:
      team_players:TEAM:SEASON  — squad size for that season
      team_all_seasons:TEAM     — distinct players across all seasons
      team_legends:TEAM         — players with batting career stats for that team
    """
    if data_file is None:
        default = Path(__file__).parent.parent / "data-pipeline" / "data" / "ipl_data.json"
        if not default.exists():
            return {}
        data_file = default

    try:
        with open(data_file, encoding="utf-8") as f:
            ipl_data = json.load(f)
    except Exception:
        return {}

    pt = ipl_data.get("player_teams", [])
    caps: dict[str, int] = {}

    # team_players:TEAM:SEASON — count per (team, season)
    season_teams: Counter = Counter(
        (p["team_name"], str(p["season"])) for p in pt
    )
    for (team_name, season), count in season_teams.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            caps[f"team_players:{code}:{season}"] = max(1, count // 4)

    # team_all_seasons:TEAM — distinct players ever for each team
    from collections import defaultdict
    team_player_set: dict[str, set] = defaultdict(set)
    for p in pt:
        team_player_set[p["team_name"]].add(p["player_name"])
    for team_name, players in team_player_set.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            caps[f"team_all_seasons:{code}"] = max(1, len(players) // 4)

    # team_legends:TEAM — distinct players with batting OR bowling career stats
    stat_names = (
        {e["player_name"] for e in ipl_data.get("batting_career_stats", [])} |
        {e["player_name"] for e in ipl_data.get("bowling_career_stats", [])}
    )
    for team_name, players in team_player_set.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            legend_count = len(players & stat_names)
            if legend_count >= 4:
                caps[f"team_legends:{code}"] = max(1, legend_count // 4)

    return caps


def _team_from_spec(spec: str) -> str | None:
    """Extract team code from a squad spec, or None."""
    if spec.startswith("team_players:"):
        return spec.split(":")[1]
    if spec.startswith("team_all_seasons:"):
        return spec.split(":")[1]
    return None


def _under_cap(spec: str, spec_use_count: Counter, caps: dict[str, int]) -> bool:
    """Return True if spec has not yet reached its use cap."""
    return spec_use_count[spec] < caps.get(spec, 99)


def _best_squad_spec(team: str, spec_use_count: Counter,
                     caps: dict[str, int]) -> str:
    """Return the best squad spec for a team: 2026 if under cap, else team_all_seasons."""
    spec_2026 = f"team_players:{team}:2026"
    if _under_cap(spec_2026, spec_use_count, caps):
        return spec_2026
    return f"team_all_seasons:{team}"


def _pick_yellow(day_str: str, cd: CooldownEngine, day_idx: int,
                 spec_use_count: Counter, caps: dict[str, int],
                 yellow_ptr: list[int]) -> str:
    """Pick Yellow — fixture-team priority, then YELLOW_POOL rotation.

    On match days the fixture team gets first pick (respecting cooldown).
    Otherwise falls through to the pool which naturally weights Mega teams
    more heavily via repetition.  Caps degrade 2026 → team_all_seasons.
    """
    fixture = FIXTURES_2026.get(day_str)
    if fixture:
        for team in fixture:
            if cd.team_available(team, day_idx):
                spec = _best_squad_spec(team, spec_use_count, caps)
                if _under_cap(spec, spec_use_count, caps):
                    return spec

    # Pool rotation — respects caps and cooldowns
    return _pick_from_pool(
        YELLOW_POOL, cd, day_idx,
        used_groups=set(), pointer=yellow_ptr,
        spec_use_count=spec_use_count, caps=caps,
    )


def _pick_green(yellow_spec: str, cd: CooldownEngine, day_idx: int,
                used_groups: set[str], used_prefixes: set[str],
                spec_use_count: Counter, caps: dict[str, int],
                green_ptr: list[int]) -> str:
    """Pick Green — same-team historical preference, then GREEN_POOL fallback.

    Priority for squad-based Yellow:
      1. team_players:TEAM:2008  (if team existed in 2008)
      2. team_all_seasons:TEAM   (skip if Yellow already claimed it)
      3. team_legends:TEAM

    Falls back to GREEN_POOL for non-squad Yellow or when all team
    options are exhausted/on-cooldown.
    """
    team = _team_from_spec(yellow_spec)
    if team:
        candidates = []
        if team in TEAMS_IN_2008:
            candidates.append(f"team_players:{team}:2008")
        spec_all = f"team_all_seasons:{team}"
        if spec_all != yellow_spec:
            candidates.append(spec_all)
        candidates.append(f"team_legends:{team}")

        for spec in candidates:
            # Team-pairing (Y=2026 squad, G=2008/all-time) intentionally shares
            # the same group AND same prefix — both constraints are relaxed here.
            # Only cooldown and cap are enforced.
            if (cd.available(spec, day_idx)
                    and _under_cap(spec, spec_use_count, caps)):
                return spec

    # Fallback: general Green pool
    return _pick_from_pool(
        GREEN_POOL, cd, day_idx,
        used_groups=used_groups, pointer=green_ptr,
        used_prefixes=used_prefixes,
        spec_use_count=spec_use_count, caps=caps,
    )


def _pick_from_pool(pool: list[str], cd: CooldownEngine, day_idx: int,
                    used_groups: set[str], pointer: list[int],
                    used_prefixes: set[str] | None = None,
                    spec_use_count: Counter | None = None,
                    caps: dict[str, int] | None = None) -> str:
    """Advance through pool finding next available spec that respects:
    - cooldown engine
    - 4-Worlds group constraint (used_groups)
    - same-type-prefix constraint (used_prefixes) — prevents e.g. 2× country:* in one puzzle
    - pool exhaustion cap (spec_use_count vs caps)
    """
    if used_prefixes is None:
        used_prefixes = set()
    if spec_use_count is None:
        spec_use_count = Counter()
    if caps is None:
        caps = {}

    def _allowed(spec: str, check_group: bool) -> bool:
        if not cd.available(spec, day_idx):
            return False
        if spec_use_count[spec] >= caps.get(spec, 99):
            return False
        if spec_prefix(spec) in used_prefixes:
            return False
        if check_group and get_group(spec) in used_groups:
            return False
        return True

    start = pointer[0]
    # Pass 1: full constraints (group + prefix)
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if _allowed(spec, check_group=True):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Pass 2: relax group constraint — keep prefix constraint
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if _allowed(spec, check_group=False):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Pass 3: relax prefix constraint too — just need cooldown + cap
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if cd.available(spec, day_idx) and spec_use_count[spec] < caps.get(spec, 99):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Last resort — return current pointer regardless
    spec = pool[pointer[0] % len(pool)]
    pointer[0] = (pointer[0] + 1) % len(pool)
    return spec


def build_schedule(data_file: Path | None = None) -> tuple[list[tuple], dict]:
    """
    Returns (schedule, caps) where schedule is a list of
    (edition, date, yellow, green, blue, purple) tuples.

    All four slots are picked purely from their pools — no per-edition
    overrides.  To change what appears in the schedule, edit the pool
    lists (YELLOW_POOL, GREEN_POOL, BLUE_POOL, PURPLE_POOL).
    """
    random.seed(42)  # reproducible output
    cd = CooldownEngine()
    yellow_ptr = [0]
    green_ptr  = [0]
    blue_ptr   = [0]
    purple_ptr = [0]
    spec_use_count: Counter = Counter()
    caps = compute_pool_caps(data_file)

    schedule = []

    for i, d in enumerate(PUZZLE_DATES):
        day_str = d.strftime("%Y-%m-%d")
        edition = i + 1

        y = _pick_yellow(day_str, cd, i, spec_use_count, caps, yellow_ptr)

        used_groups   = {get_group(y)}
        used_prefixes = {spec_prefix(y)}

        g = _pick_green(y, cd, i, used_groups, used_prefixes,
                        spec_use_count, caps, green_ptr)

        used_groups.add(get_group(g))
        used_prefixes.add(spec_prefix(g))
        # team_legends is a combined run+wicket leaderboard — block stat leaders
        # in the same puzzle even if the group constraint is later relaxed
        if g.startswith("team_legends:"):
            used_prefixes.update({"top_run_scorers", "top_wicket_takers"})

        b = _pick_from_pool(BLUE_POOL, cd, i, used_groups, blue_ptr,
                            used_prefixes=used_prefixes,
                            spec_use_count=spec_use_count, caps=caps)
        used_groups.add(get_group(b))
        used_prefixes.add(spec_prefix(b))

        p = _pick_from_pool(PURPLE_POOL, cd, i, used_groups, purple_ptr,
                            used_prefixes=used_prefixes,
                            spec_use_count=spec_use_count, caps=caps)

        for spec in (y, g, b, p):
            cd.record(spec, i)
            spec_use_count[spec] += 1
            team = _team_from_spec(spec)
            if team:
                cd.record(f"team_players:{team}:placeholder", i)

        schedule.append((edition, d, y, g, b, p))

    return schedule, caps


# ---------------------------------------------------------------------------
# Output: curation_schedule.md
# ---------------------------------------------------------------------------

MONTH_ABBR = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec",
}

DAY_ABBR = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

SECTION_DATES = {
    date(2026, 3, 25): "## Pre-IPL (25-27 Mar)",
    date(2026, 3, 28): "## Phase 1 — Match Days (28 Mar - 12 Apr)",
    date(2026, 4, 13): "## Phase 2 — Match Days (13 Apr - 21 May)",
    date(2026, 5, 22): "## Playoffs (22-31 May)",
}

def _fmt_date(d: date) -> str:
    return f"{d.day} {MONTH_ABBR[d.month]}"

def _fmt_spec(spec: str) -> str:
    return f"`{spec}`"

def _match_context(d: date) -> str:
    ds = d.strftime("%Y-%m-%d")
    fix = FIXTURES_2026.get(ds)
    if fix:
        return f"{fix[0]} vs {fix[1]}"
    return "—"


def write_schedule(schedule: list[tuple], output_path: Path,
                   caps: dict[str, int] | None = None):
    lines = [
        "# IPL 2026 — Curation Schedule v5",
        "",
        "Generated by `gen_schedule_v5.py`.",
        "- Yellow (1-Easy)  : Current squad / fan-base anchored",
        "- Green  (2-Medium): Historical squad / legends / geographic",
        "- Blue   (3-Hard)  : Stats / coaches / geographic deep-dive",
        "- Purple (4-Expert): Cross-team / niche records / nomads",
        "",
        "Status: `[ ]` pending · `[g]` generated · `[r]` reviewed · `[x]` published · `[!]` needs attention",
        "",
    ]

    for edition, d, y, g, b, p in schedule:
        if d in SECTION_DATES:
            lines += ["", SECTION_DATES[d], ""]
            lines.append("| Ed | Date | Day | Match | Yellow | Green | Blue | Purple | Status |")
            lines.append("|---|---|---|---|---|---|---|---|---|")

        day_name = DAY_ABBR[d.weekday()]
        match = _match_context(d)
        row = (
            f"| {edition} | {_fmt_date(d)} | {day_name} | {match} "
            f"| {_fmt_spec(y)} | {_fmt_spec(g)} | {_fmt_spec(b)} | {_fmt_spec(p)} | [ ] |"
        )
        lines.append(row)

    lines += ["", "---", ""]

    # Pool usage summary
    usage: Counter = Counter()
    for _, _, y, g, b, p in schedule:
        for spec in (y, g, b, p):
            usage[spec] += 1

    _caps = caps or {}

    lines.append("## Pool Usage Summary")
    lines.append("")
    lines.append("| Spec | Uses | Cap | Remaining |")
    lines.append("|------|------|-----|-----------|")
    for spec, count in sorted(usage.items(), key=lambda x: -x[1]):
        cap = _caps.get(spec)
        cap_str  = str(cap) if cap is not None else "∞"
        rem_str  = str(cap - count) if cap is not None else "∞"
        lines.append(f"| `{spec}` | {count} | {cap_str} | {rem_str} |")
    lines.append("")

    text = "\n".join(lines)
    output_path.write_text(text, encoding="utf-8")
    print(f"Written: {output_path}  ({len(schedule)} editions)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate IPL 2026 curation schedule v5")
    parser.add_argument("--preview", action="store_true",
                        help="Print to stdout instead of writing file")
    parser.add_argument("--output", default="curation_schedule.md",
                        help="Output path (default: ./curation_schedule.md)")
    parser.add_argument("--data-file", default=None,
                        help="Path to ipl_data.json for pool-cap computation")
    args = parser.parse_args()

    data_file = Path(args.data_file) if args.data_file else None
    schedule, caps = build_schedule(data_file=data_file)

    if args.preview:
        for ed, d, y, g, b, p in schedule:
            print(f"Ed {ed:2d}  {d}  Y={y:<35} G={g:<35} B={b:<30} P={p}")
    else:
        output_path = Path(args.output)
        write_schedule(schedule, output_path, caps=caps)


if __name__ == "__main__":
    main()
