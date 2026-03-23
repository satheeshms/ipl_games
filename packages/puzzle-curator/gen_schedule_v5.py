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

# Pre-IPL: 24-27 Mar (4 days)
# Phase 1:  28 Mar - 12 Apr (16 days)
# Phase 2:  13 Apr - 21 May (39 days)
# Playoffs: 22, 23, 24, 26, 28, 30, 31 May (7 days)
PUZZLE_DATES = (
    list(_date_range(date(2026, 3, 24), date(2026, 5, 21))) +
    [date(2026, 5, 22), date(2026, 5, 23), date(2026, 5, 24),
     date(2026, 5, 26), date(2026, 5, 28), date(2026, 5, 30), date(2026, 5, 31)]
)

assert len(PUZZLE_DATES) == 66, f"Expected 66 dates, got {len(PUZZLE_DATES)}"

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
                        "most_matches", "team_legends_batting:", "team_legends_bowling:",
                        "most_ducks", "fifers")):
        return GROUP_C
    if spec.startswith(("country:", "state:", "ranji:")):
        return GROUP_D
    if spec.startswith(("played_both:", "multi_team:", "longest_serving",
                        "legends:")):
        return GROUP_E
    if spec.startswith(("coaches", "head_coaches", "batting_coaches",
                        "bowling_coaches", "fielding_coaches", "team_owners")):
        return GROUP_F
    return GROUP_C  # default

# ---------------------------------------------------------------------------
# Cooldown engine
# ---------------------------------------------------------------------------

COOLDOWN_CAT          = 4   # days before same category type can repeat
COOLDOWN_TEAM         = 3   # days before same team can appear in Yellow/Green
COOLDOWN_PLAYED_BOTH  = 2   # days before any played_both combo can repeat
COOLDOWN_TEAM_LEGENDS = 2   # days before any team_legends_batting/bowling can repeat
COOLDOWN_GEO_LOCAL    = 2   # days before any state:* or ranji:* can repeat
COOLDOWN_COUNTRY      = 5   # days before same country repeats
COOLDOWN_COUNTRY_CAT  = 3   # days before ANY country repeats (category-wide)
COOLDOWN_COACHES      = 3   # days before any coach sub-category repeats

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
    if spec.startswith(("coaches", "head_coaches", "batting_coaches",
                        "bowling_coaches", "fielding_coaches")):
        return "coaches"                   # all sub-types share one bucket → 3-day cooldown
    if spec.startswith("country:"):
        return spec                        # each country separate
    if spec.startswith("state:"):
        return "state"                     # all states share one bucket → 2-day cooldown
    if spec.startswith("ranji:"):
        return "ranji"                     # all ranji teams share one bucket → 2-day cooldown
    if spec.startswith("played_both:"):
        return "played_both"        # all combos share one bucket → 2-day cooldown
    if spec.startswith("team_legends_batting:"):
        return "team_legends_batting"   # all teams share one bucket → 2-day cooldown
    if spec.startswith("team_legends_bowling:"):
        return "team_legends_bowling"   # all teams share one bucket → 2-day cooldown
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

    def available_key(self, key: str, day_idx: int, cooldown: int) -> bool:
        last = self._last.get(key, -999)
        return (day_idx - last) >= cooldown

    def record_key(self, key: str, day_idx: int):
        self._last[key] = day_idx

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
    # 2008 inaugural squads — historical trivia, once per team
    [f"team_players:{t}:2008" for t in sorted(TEAMS_IN_2008)] +
    # Non-squad variety — once each
    ["ipl_champions", "legends:india", "team_owners",
     "top_run_scorers", "batting_records"]
)

# ---------------------------------------------------------------------------
# Green pool — Medium slot
#
# Interleaved in 4 rounds so team-based specs (2025/2008 squads, legends)
# surface alongside geographic specs rather than being buried at the end.
# team_all_seasons is intentionally excluded — 2025/2008 are preferred.
# ---------------------------------------------------------------------------
GREEN_POOL: list[str] = (
    # Round A: 2025 squads + countries
    [f"team_players:{t}:2025" for t in ALL_TEAMS] +
    ["country:Australia", "country:South Africa", "country:England",
     "country:New Zealand", "country:Sri Lanka", "country:West Indies"] +
    # Round B: states
    ["state:Maharashtra", "state:Delhi", "state:Karnataka",
     "state:Tamil Nadu", "state:Uttar Pradesh", "state:Punjab"] +
    # Round C: batting legends + ranji + India/overseas legends
    # GT and LSG excluded — insufficient career batting stats (post-2022 teams)
    [f"team_legends_batting:{t}" for t in ALL_TEAMS if t not in ("GT", "LSG")] +
    ["ranji:Mumbai", "ranji:Delhi", "ranji:Karnataka"] +
    ["legends:india", "legends:india", "legends:overseas", "legends:overseas"] +
    # Round D: bowling legends + winning squads
    # LSG excluded — insufficient career bowling stats
    [f"team_legends_bowling:{t}" for t in ALL_TEAMS if t != "LSG"] +
    ["winning_squad:2008", "winning_squad:2011", "winning_squad:2013",
     "winning_squad:2016", "winning_squad:2019", "winning_squad:2022",
     "winning_squad:2024"] +
    # Tail: awards / coaches (all-seasons, no suffix)
    ["orange_cap", "purple_cap", "costliest_player", "winning_captain",
     "player_of_tournament",
     "head_coaches", "batting_coaches", "bowling_coaches", "fielding_coaches"]
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
    # Management — coach sub-categories (all-seasons, no season suffix)
    "head_coaches", "head_coaches",
    "batting_coaches", "batting_coaches",
    "bowling_coaches", "bowling_coaches",
    "fielding_coaches", "fielding_coaches",
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
    "costliest_player", "player_of_tournament",
    # Winning squads (historical)
    "winning_squad:2008", "winning_squad:2011", "winning_squad:2013",
    "winning_squad:2016", "winning_squad:2019", "winning_squad:2022",
    "winning_squad:2024",
]

# ---------------------------------------------------------------------------
# Main scheduler
# ---------------------------------------------------------------------------

def spec_prefix(spec: str) -> str:
    """Return the prefix used for same-type blocking within a puzzle.

    Historical squads (2024 and earlier) get a distinct prefix so they are not
    blocked by the current-era Yellow squad's 'team_players' prefix.  They are
    still GROUP_A, so Pass 1 skips them; Pass 2 (relax group) picks them when
    other options are on cooldown or capped.
    """
    if spec.startswith("team_players:"):
        parts = spec.split(":")
        if len(parts) >= 3 and parts[2].isdigit() and int(parts[2]) <= 2024:
            return "historical_squad"
    return spec.split(":")[0]


def _teams_from_spec(spec: str) -> set[str]:
    """Return team codes that a spec 'owns' for collision checking.

    team_players:TEAM:SEASON, team_all_seasons:TEAM → {TEAM}
    team_legends_batting:TEAM, team_legends_bowling:TEAM → {TEAM}
    played_both:T1:T2                               → {T1, T2}
    Everything else (country, stats…)               → empty set
    """
    if spec.startswith(("team_players:", "team_all_seasons:",
                         "team_legends_batting:", "team_legends_bowling:")):
        return {spec.split(":")[1]}
    if spec.startswith("played_both:"):
        parts = spec.split(":")
        return {parts[1], parts[2]}
    return set()


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

# Safety-net caps used only when ipl_data.json is unavailable at runtime.
_FALLBACK_CAPS: dict[str, int] = {
    "orange_cap": 3, "purple_cap": 3, "player_of_tournament": 4,
    "costliest_player": 4, "winning_captain": 2,
    "ipl_champions": 1, "team_owners": 2,
    "top_run_scorers": 5, "top_wicket_takers": 5,
    "most_fifties": 5, "most_matches": 5, "most_ducks": 5,
    "highest_batting_avg": 6, "high_strike_rate": 3,
    "catches_by_fielder": 4, "dismissals_by_keeper": 2,
    "allrounders": 2, "fifers": 4,
    "batting_records": 2, "bowling_records": 2,
    "season_records": 2, "fielding_records": 2,
    "legends:india": 3, "legends:overseas": 3,
    "head_coaches": 2, "batting_coaches": 2,
    "bowling_coaches": 2, "fielding_coaches": 2,
    **{f"country:{c}": 3 for c in [
        "Australia", "South Africa", "England",
        "New Zealand", "Sri Lanka", "West Indies"]},
}


def compute_pool_caps(data_file: Path | None = None) -> dict[str, int]:
    """
    Compute max uses per spec entirely from ipl_data.json at runtime.

    Formula: cap = max(1, pool_size // 4) so the schedule never exhausts
    a category's unique-item pool.  Falls back to _FALLBACK_CAPS when the
    data file cannot be loaded.
    """
    if data_file is None:
        default = Path(__file__).parent.parent / "data-pipeline" / "data" / "ipl_data.json"
        if not default.exists():
            return _FALLBACK_CAPS.copy()
        data_file = default

    try:
        with open(data_file, encoding="utf-8") as f:
            ipl_data = json.load(f)
    except Exception:
        return _FALLBACK_CAPS.copy()

    caps: dict[str, int] = {}
    pt = ipl_data.get("player_teams", [])

    # ---- team_players:TEAM:SEASON ----
    season_teams: Counter = Counter(
        (p["team_name"], str(p["season"])) for p in pt
    )
    for (team_name, season), count in season_teams.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            caps[f"team_players:{code}:{season}"] = max(1, count // 4)

    # ---- team_all_seasons:TEAM ----
    team_player_set: dict[str, set] = defaultdict(set)
    for p in pt:
        team_player_set[p["team_name"]].add(p["player_name"])
    for team_name, players in team_player_set.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            caps[f"team_all_seasons:{code}"] = max(1, len(players) // 4)

    # ---- team_legends_batting / _bowling:TEAM (cap=1 per team) ----
    bat_names  = {e["player_name"] for e in ipl_data.get("batting_career_stats", [])}
    bowl_names = {e["player_name"] for e in ipl_data.get("bowling_career_stats", [])}
    for team_name, players in team_player_set.items():
        code = _FULL_NAME_TO_CODE.get(team_name)
        if code:
            if len(players & bat_names) >= 4:
                caps[f"team_legends_batting:{code}"] = 1
            if len(players & bowl_names) >= 4:
                caps[f"team_legends_bowling:{code}"] = 1

    # ---- Awards: unique player names per award type ----
    awards_by_type: dict[str, set] = {}
    for a in ipl_data.get("awards", []):
        awards_by_type.setdefault(a["type"], set()).add(a["player_name"])
    for award_type in ("orange_cap", "purple_cap", "player_of_tournament",
                       "costliest_player", "winning_captain"):
        n = len(awards_by_type.get(award_type, set()))
        caps[award_type] = max(1, n // 4) if n >= 4 else 1

    # ---- IPL champions: unique winning team names ----
    ipl_wins = ipl_data.get("ipl_wins", [])
    n = len({w["team_name"] for w in ipl_wins})
    caps["ipl_champions"] = max(1, n // 4) if n >= 4 else 1

    # ---- Team owners ----
    owners = ipl_data.get("records", {}).get("team_owners", [])
    caps["team_owners"] = max(1, len(owners) // 4) if len(owners) >= 4 else 1

    # ---- Stat specs: unique player names ----
    for spec, data_key, name_field in [
        ("top_run_scorers",      "batting_career_stats",     "player_name"),
        ("most_fifties",         "batting_career_stats",     "player_name"),
        ("most_matches",         "batting_career_stats",     "player_name"),
        ("most_ducks",           "most_ducks",               "player_name"),
        ("top_wicket_takers",    "bowling_career_stats",     "player_name"),
        ("allrounders",          "allrounders",              "name"),
        ("high_strike_rate",     "high_strike_rate_batsmen", "player_name"),
        ("highest_batting_avg",  "highest_batting_avg",      "player_name"),
        ("catches_by_fielder",   "catches_by_fielder",       "player_name"),
        ("dismissals_by_keeper", "dismissals_by_keeper",     "player_name"),
    ]:
        entries = ipl_data.get(data_key, [])
        n = len({e[name_field] for e in entries if name_field in e})
        caps[spec] = max(1, n // 4) if n >= 4 else 1

    # ---- fifers: unique player names from five_wicket_hauls ----
    fifer_names = {
        e.get("player_name") or e.get("name", "")
        for e in ipl_data.get("five_wicket_hauls", [])
    } - {""}
    caps["fifers"] = max(1, len(fifer_names) // 4) if len(fifer_names) >= 4 else 1

    # ---- Records: unique player names per record category ----
    records = ipl_data.get("records", {})
    for spec, rec_key in [
        ("batting_records",  "batting_records"),
        ("bowling_records",  "bowling_records"),
        ("season_records",   "season_records"),
        ("fielding_records", "fielding_records"),
    ]:
        entries = records.get(rec_key, [])
        n = len({e.get("player") for e in entries} - {None})
        caps[spec] = max(1, n // 4) if n >= 4 else 1

    # ---- Legends: curated lists verified against player_teams ----
    try:
        from generators.cross_team import _LEGENDS_INDIA, _LEGENDS_OVERSEAS
        known_players = {p["player_name"] for p in pt}
        n_india    = len([name for name in _LEGENDS_INDIA    if name in known_players])
        n_overseas = len([name for name in _LEGENDS_OVERSEAS if name in known_players])
        caps["legends:india"]    = max(1, n_india    // 4) if n_india    >= 4 else 1
        caps["legends:overseas"] = max(1, n_overseas // 4) if n_overseas >= 4 else 1
    except ImportError:
        caps["legends:india"]    = _FALLBACK_CAPS["legends:india"]
        caps["legends:overseas"] = _FALLBACK_CAPS["legends:overseas"]

    # ---- Coach sub-categories: unique coach names per role ----
    coaches_data = ipl_data.get("coaches", [])
    for role, spec in [
        ("head",     "head_coaches"),
        ("batting",  "batting_coaches"),
        ("bowling",  "bowling_coaches"),
        ("fielding", "fielding_coaches"),
    ]:
        n = len({c["coach"] for c in coaches_data if c.get("role") == role})
        caps[spec] = max(1, n // 4) if n >= 4 else 1

    # ---- Country specs: unique player names, capped at 3 per spec ----
    # (raw pool can be 60+ for Australia; cap of 3 matches editorial intent)
    foreign_players = ipl_data.get("foreign_players", [])
    for country in ("Australia", "South Africa", "England",
                    "New Zealand", "Sri Lanka", "West Indies"):
        n = len({e["name"] for e in foreign_players if e.get("country") == country})
        caps[f"country:{country}"] = min(3, max(1, n // 4)) if n >= 4 else 1

    # ---- State specs ----
    for state, entries in ipl_data.get("india_state_wise", {}).items():
        n = len(entries)
        if n >= 4:
            caps[f"state:{state}"] = max(1, n // 4)

    # ---- Ranji team specs ----
    for ranji_team, entries in ipl_data.get("ranji_team_wise", {}).items():
        n = len(entries)
        if n >= 4:
            caps[f"ranji:{ranji_team}"] = max(1, n // 4)

    # ---- winning_squad:SEASON ----
    win_teams = {w["season"]: w["team_name"] for w in ipl_wins}
    for season, team_name in win_teams.items():
        n = sum(1 for p in pt if p["team_name"] == team_name and p["season"] == season)
        if n >= 4:
            caps[f"winning_squad:{season}"] = max(1, n // 4)

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
    """Return best squad spec: 2026 → 2025 → 2008. No team_all_seasons."""
    spec_2026 = f"team_players:{team}:2026"
    if _under_cap(spec_2026, spec_use_count, caps):
        return spec_2026
    spec_2025 = f"team_players:{team}:2025"
    if _under_cap(spec_2025, spec_use_count, caps):
        return spec_2025
    if team in TEAMS_IN_2008:
        return f"team_players:{team}:2008"
    return spec_2025  # last resort for newer teams (GT, LSG, SRH)


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
                used_teams: set[str],
                spec_use_count: Counter, caps: dict[str, int],
                green_ptr: list[int]) -> str:
    """Pick Green from GREEN_POOL, enforcing team collision, group, and prefix constraints.

    All team-based specs (team_players, team_all_seasons, team_legends_batting,
    team_legends_bowling, played_both) must reference a team not already used
    in the puzzle to avoid player pool overlap.
    """
    return _pick_from_pool(
        GREEN_POOL, cd, day_idx,
        used_groups=used_groups, pointer=green_ptr,
        used_prefixes=used_prefixes,
        used_teams=used_teams,
        spec_use_count=spec_use_count, caps=caps,
    )


def _pick_from_pool(pool: list[str], cd: CooldownEngine, day_idx: int,
                    used_groups: set[str], pointer: list[int],
                    used_prefixes: set[str] | None = None,
                    used_teams: set[str] | None = None,
                    spec_use_count: Counter | None = None,
                    caps: dict[str, int] | None = None) -> str:
    """Advance through pool finding next available spec that respects:
    - cooldown engine
    - 4-Worlds group constraint (used_groups)
    - same-type-prefix constraint (used_prefixes) — prevents e.g. 2× country:* in one puzzle
    - team collision constraint (used_teams) — prevents same team in squad/played_both specs
    - pool exhaustion cap (spec_use_count vs caps)
    """
    if used_prefixes is None:
        used_prefixes = set()
    if used_teams is None:
        used_teams = set()
    if spec_use_count is None:
        spec_use_count = Counter()
    if caps is None:
        caps = {}

    def _cooldown_for(spec: str) -> int:
        if spec.startswith("played_both:"):
            return COOLDOWN_PLAYED_BOTH
        if spec.startswith(("team_legends_batting:", "team_legends_bowling:")):
            return COOLDOWN_TEAM_LEGENDS
        if spec.startswith(("state:", "ranji:")):
            return COOLDOWN_GEO_LOCAL
        if spec.startswith("country:"):
            return COOLDOWN_COUNTRY
        if spec.startswith(("coaches", "head_coaches", "batting_coaches",
                             "bowling_coaches", "fielding_coaches")):
            return COOLDOWN_COACHES
        return COOLDOWN_CAT

    def _allowed(spec: str, check_group: bool, check_teams: bool) -> bool:
        if not cd.available(spec, day_idx, _cooldown_for(spec)):
            return False
        # country: additionally enforce category-wide 3-day cooldown
        if spec.startswith("country:") and not cd.available_key("country", day_idx, COOLDOWN_COUNTRY_CAT):
            return False
        if spec_use_count[spec] >= caps.get(spec, 99):
            return False
        if spec_prefix(spec) in used_prefixes:
            return False
        if check_group and get_group(spec) in used_groups:
            return False
        if check_teams and _teams_from_spec(spec) & used_teams:
            return False
        return True

    start = pointer[0]
    # Pass 1: full constraints (group + prefix + teams)
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if _allowed(spec, check_group=True, check_teams=True):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Pass 2: relax group constraint — keep prefix + team constraints
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if _allowed(spec, check_group=False, check_teams=True):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Pass 3: relax prefix constraint too — keep team constraint
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if (cd.available(spec, day_idx, _cooldown_for(spec))
                and spec_use_count[spec] < caps.get(spec, 99)
                and not (_teams_from_spec(spec) & used_teams)):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Pass 4: relax all constraints — just need cooldown + cap
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if cd.available(spec, day_idx, _cooldown_for(spec)) and spec_use_count[spec] < caps.get(spec, 99):
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
        used_teams    = _teams_from_spec(y)

        def _apply(spec: str):
            used_groups.add(get_group(spec))
            used_prefixes.add(spec_prefix(spec))
            used_teams.update(_teams_from_spec(spec))
            # legends overlap with global leaderboards — block in same puzzle
            if spec.startswith("team_legends_batting:"):
                used_prefixes.add("top_run_scorers")
            if spec.startswith("team_legends_bowling:"):
                used_prefixes.add("top_wicket_takers")

        g = _pick_green(y, cd, i, used_groups, used_prefixes, used_teams,
                        spec_use_count, caps, green_ptr)
        _apply(g)

        b = _pick_from_pool(BLUE_POOL, cd, i, used_groups, blue_ptr,
                            used_prefixes=used_prefixes,
                            used_teams=used_teams,
                            spec_use_count=spec_use_count, caps=caps)
        _apply(b)

        p = _pick_from_pool(PURPLE_POOL, cd, i, used_groups, purple_ptr,
                            used_prefixes=used_prefixes,
                            used_teams=used_teams,
                            spec_use_count=spec_use_count, caps=caps)

        for spec in (y, g, b, p):
            cd.record(spec, i)
            spec_use_count[spec] += 1
            team = _team_from_spec(spec)
            if team:
                cd.record(f"team_players:{team}:placeholder", i)
            if spec.startswith("country:"):
                cd.record_key("country", i)   # category-wide 3-day cooldown

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
    date(2026, 3, 24): "## Pre-IPL (24-27 Mar)",
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
