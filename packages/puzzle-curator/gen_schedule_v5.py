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
import random
from datetime import date, timedelta
from collections import defaultdict
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

# Teams that existed in inaugural 2008 season
TEAMS_IN_2008 = {"RCB", "CSK", "MI", "KKR", "RR", "PBKS", "DC"}
# Teams that did NOT exist in 2008 → use team_all_seasons
TEAMS_NOT_IN_2008 = {"SRH", "GT", "LSG"}

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

# Yellow: 2026 squads — Mega tier (MI/CSK/RCB/KKR) weighted 50%
MEGA_TEAMS  = ["MI", "CSK", "RCB", "KKR"]
LARGE_TEAMS = ["RR", "SRH"]
SMALL_TEAMS = ["DC", "PBKS", "GT", "LSG"]
ALL_TEAMS   = MEGA_TEAMS + LARGE_TEAMS + SMALL_TEAMS  # 10 teams

# Blue pool: stats + geographic + management — complexity 3
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
    "legends:india", "legends:overseas",
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

# Green: alternate between 2008 squad (for teams in 2008), team_all_seasons,
# team_legends, winning_squad, legends  — see logic in build_schedule()

# ---------------------------------------------------------------------------
# Signature puzzles — fixed (Y, G, B, P)
# Index = edition number - 1 (0-based)
# ---------------------------------------------------------------------------

SIGNATURE = {
    # Ed 7 — CSK vs MI: El Clasico
    6:  ("team_players:CSK:2026", "team_players:MI:2026",
         "played_both:CSK:MI",    "winning_captain"),

    # Ed 14 — Dhoni vs Kohli: The Fanbases
    13: ("team_players:CSK:2026", "team_players:RCB:2026",
         "played_both:CSK:RCB",   "costliest_player"),

    # Ed 21 — Foreign Invasion
    20: ("country:Australia", "country:South Africa",
         "country:England",   "country:West Indies"),

    # Ed 28 — Golden Era (2008-2013)
    27: ("legends:india",       "legends:overseas",
         "winning_squad:2008",  "orange_cap"),

    # Ed 35 — Geography Quiz
    34: ("state:Maharashtra",  "state:Delhi",
         "ranji:Mumbai",       "ranji:Delhi"),

    # Ed 42 — Numbers Game
    41: ("top_run_scorers",    "top_wicket_takers",
         "highest_batting_avg","most_ducks"),

    # Ed 49 — Underdogs & Nomads
    48: ("team_all_seasons:GT", "team_all_seasons:LSG",
         "multi_team:5",        "longest_serving"),

    # Ed 56 — Record Breakers
    55: ("batting_records",    "bowling_records",
         "season_records",     "fielding_records"),

    # Playoffs Ed 61-65 — left with team placeholders; fill when teams known
}

# ---------------------------------------------------------------------------
# Pre-IPL fixed overrides (editions 1-3)
# ---------------------------------------------------------------------------

PRE_IPL_FIXED = {
    0: ("ipl_champions",       "orange_cap",           "purple_cap",     "player_of_tournament"),
    1: ("coaches:2026",        "coaches:2025",         "team_owners",    "winning_captain"),
    2: ("legends:india",       "legends:overseas",     "winning_squad:2008", "costliest_player"),
}

# ---------------------------------------------------------------------------
# Main scheduler
# ---------------------------------------------------------------------------

def _team_from_spec(spec: str) -> str | None:
    """Extract team code from a squad spec, or None."""
    if spec.startswith("team_players:"):
        return spec.split(":")[1]
    if spec.startswith("team_all_seasons:"):
        return spec.split(":")[1]
    return None


def _pick_yellow(day_str: str, cd: CooldownEngine, day_idx: int) -> str:
    """Pick Yellow category — match-day team if available, else fan-base weighted rotation."""
    fixture = FIXTURES_2026.get(day_str)
    if fixture:
        team1, team2 = fixture
        if cd.team_available(team1, day_idx):
            return f"team_players:{team1}:2026"
        if cd.team_available(team2, day_idx):
            return f"team_players:{team2}:2026"

    # Fallback: fan-base weighted rotation
    # Mega 50%, Large 25%, Small 25%
    weights = (
        [(t, 5) for t in MEGA_TEAMS] +
        [(t, 2) for t in LARGE_TEAMS] +
        [(t, 2) for t in SMALL_TEAMS]
    )
    pool = [(t, w) for t, w in weights if cd.team_available(t, day_idx)]
    if not pool:
        # all on cooldown — pick least-recently-used
        pool = [(t, w) for t, w in weights]

    teams, wts = zip(*pool)
    chosen = random.choices(teams, weights=wts, k=1)[0]
    return f"team_players:{chosen}:2026"


def _pick_green(yellow_spec: str, cd: CooldownEngine, day_idx: int,
                green_depth: dict) -> str:
    """Pick Green — paired historical/all-time squad, legends, or winning_squad."""
    team = _team_from_spec(yellow_spec)
    if team:
        if team in TEAMS_IN_2008:
            spec_2008 = f"team_players:{team}:2008"
            if cd.available(spec_2008, day_idx):
                return spec_2008
        # team_all_seasons
        spec_all = f"team_all_seasons:{team}"
        if cd.available(spec_all, day_idx):
            return spec_all
        # team_legends as fallback
        return f"team_legends:{team}"

    # Non-squad Yellow (signature day) — use rotating team or legends
    options = [
        "legends:india", "legends:overseas",
        "winning_squad:2011", "winning_squad:2013",
        "winning_squad:2019", "winning_squad:2022",
        "team_all_seasons:CSK", "team_all_seasons:MI",
    ]
    for opt in options:
        if cd.available(opt, day_idx):
            return opt
    return "team_all_seasons:MI"


def _pick_from_pool(pool: list[str], cd: CooldownEngine, day_idx: int,
                    used_groups: set[str], pointer: list[int]) -> str:
    """Advance through pool finding next available spec that respects cooldown + group constraint."""
    start = pointer[0]
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        grp  = get_group(spec)
        if cd.available(spec, day_idx) and grp not in used_groups:
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Relax group constraint — just find next cooldown-available
    for offset in range(len(pool)):
        idx = (start + offset) % len(pool)
        spec = pool[idx]
        if cd.available(spec, day_idx):
            pointer[0] = (idx + 1) % len(pool)
            return spec

    # Last resort — return current pointer regardless
    spec = pool[pointer[0] % len(pool)]
    pointer[0] = (pointer[0] + 1) % len(pool)
    return spec


def build_schedule() -> list[tuple]:
    """
    Returns list of (edition, date, yellow, green, blue, purple) tuples.
    """
    random.seed(42)  # reproducible output
    cd = CooldownEngine()
    blue_ptr  = [0]
    purple_ptr = [0]

    schedule = []

    for i, d in enumerate(PUZZLE_DATES):
        day_str = d.strftime("%Y-%m-%d")
        edition = i + 1

        # --- Signature puzzle override ---
        if i in SIGNATURE:
            y, g, b, p = SIGNATURE[i]
        elif i in PRE_IPL_FIXED:
            y, g, b, p = PRE_IPL_FIXED[i]
        else:
            # --- Dynamic selection ---
            y = _pick_yellow(day_str, cd, i)
            g = _pick_green(y, cd, i, {})

            used_groups = {get_group(y), get_group(g)}
            b = _pick_from_pool(BLUE_POOL,   cd, i, used_groups, blue_ptr)
            used_groups.add(get_group(b))
            p = _pick_from_pool(PURPLE_POOL, cd, i, used_groups, purple_ptr)

        # Record cooldowns for all 4 specs
        for spec in (y, g, b, p):
            cd.record(spec, i)
            team = _team_from_spec(spec)
            if team:
                cd.record(f"team_players:{team}:placeholder", i)

        schedule.append((edition, d, y, g, b, p))

    return schedule


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


def write_schedule(schedule: list[tuple], output_path: Path):
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
    from collections import Counter
    usage: Counter = Counter()
    for _, _, y, g, b, p in schedule:
        for spec in (y, g, b, p):
            usage[spec] += 1

    lines.append("## Pool Usage Summary")
    lines.append("")
    lines.append("| Spec | Uses |")
    lines.append("|------|------|")
    for spec, count in sorted(usage.items(), key=lambda x: -x[1]):
        lines.append(f"| `{spec}` | {count} |")
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
    args = parser.parse_args()

    schedule = build_schedule()

    if args.preview:
        for ed, d, y, g, b, p in schedule:
            print(f"Ed {ed:2d}  {d}  Y={y:<35} G={g:<35} B={b:<30} P={p}")
    else:
        output_path = Path(args.output)
        write_schedule(schedule, output_path)


if __name__ == "__main__":
    main()
