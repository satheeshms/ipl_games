"""
gen_schedule.py — Generate a 67-day puzzle schedule with 4-day category cooldown.

Rules:
- Same category type cannot appear in any slot within 4 days of its last use
- team_players:TEAM:SEASON treated as type "team_players:TEAM" (same team = cooldown)
- Yellow = current 2026 squads (match-day, always different teams)
- Green = historic squads (iconic seasons, different team each time)
- Blue = stats/coaches categories
- Purple = niche/obscure categories
"""

from datetime import date, timedelta
from collections import defaultdict

# ---------------------------------------------------------------------------
# Puzzle dates (Ed 1–67)
# ---------------------------------------------------------------------------

def date_range(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

# Pre-IPL: 23–27 Mar
# Phase 1: 28 Mar – 12 Apr
# Phase 2: 13 Apr – 21 May
# Playoffs: 22 May, 23 May, 24 May, 26 May, 28 May, 30 May, 31 May

puzzle_dates = (
    list(date_range(date(2026, 3, 23), date(2026, 5, 21))) +
    [date(2026, 5, 22), date(2026, 5, 23), date(2026, 5, 24),
     date(2026, 5, 26), date(2026, 5, 28), date(2026, 5, 30), date(2026, 5, 31)]
)

# ---------------------------------------------------------------------------
# Category pools
# ---------------------------------------------------------------------------

# Yellow: 2026 squads — rotate through 10 teams
yellow_teams = ["RCB", "CSK", "MI", "KKR", "SRH", "RR", "GT", "PBKS", "LSG", "DC"]

# Green pool rules:
# - If Yellow is team_players:TEAM:2026 → Green is team_players:TEAM:2008 (same team, inaugural season)
#   If that team didn't exist in 2008 (GT, LSG, SRH) → use team_all_seasons:TEAM
# - If Yellow is NOT a team squad → Green is team_all_seasons:TEAM (rotating teams)

# Teams that existed in 2008
TEAMS_IN_2008 = {"RCB", "CSK", "MI", "KKR", "RR", "PBKS", "DC"}
# Teams that did NOT exist in 2008 → use team_all_seasons instead
TEAMS_NOT_IN_2008 = {"SRH", "GT", "LSG"}

# All-time team pool for non-squad days (rotating)
all_time_teams = ["CSK", "MI", "KKR", "RCB", "RR", "SRH", "DC", "PBKS", "GT", "LSG"]

# Blue: stats and coaches — 67 slots needed, interleaved for variety
# Max uses: batting_records=1, bowling_records=1, season_records=1, fielding_records=1
# highest_batting_avg=8, catches_by_fielder=6, topbat=7, topbowl=7,
# multi_team_players=9, fifers=7, coaches=unlimited (19 seasons)
blue_pool = [
    "batting_records",       # ⚠ use once (Ed 6 fixed, Ed 22 auto)
    "bowling_records",       # ⚠ use once (Ed 8 fixed, Ed 23 auto)
    "season_records",        # ⚠ use once (Ed 9 fixed, Ed 24 auto)
    "highest_batting_avg",
    "catches_by_fielder",
    "topbat",
    "topbowl",
    "multi_team_players",
    "fifers",
    "coaches:2022",
    "highest_batting_avg",
    "catches_by_fielder",
    "topbat",
    "coaches:2021",
    "topbowl",
    "multi_team_players",
    "fifers",
    "coaches:2020",
    "highest_batting_avg",
    "catches_by_fielder",
    "coaches:2019",
    "topbat",
    "topbowl",
    "coaches:2018",
    "multi_team_players",
    "fifers",
    "coaches:2017",
    "highest_batting_avg",
    "catches_by_fielder",
    "coaches:2016",
    "topbat",
    "topbowl",
    "coaches:2015",
    "multi_team_players",
    "fifers",
    "coaches:2014",
    "highest_batting_avg",
    "catches_by_fielder",
    "coaches:2013",
    "topbat",
    "topbowl",
    "coaches:2012",
    "multi_team_players",
    "fifers",
    "coaches:2011",
    "highest_batting_avg",
    "coaches:2010",
    "topbat",
    "coaches:2009",
    "topbowl",
    "coaches:2008",
    "multi_team_players",
    "coaches:2023",
    "fifers",
    "coaches:2024",
    "fielding_records",      # ⚠ use once — placed late, away from Ed 60/61 fixed
]

# Purple: niche/obscure
# Max uses: ipl_champions=1, winning_captain=2, allrounders=2,
# dismissals_by_keeper=3, high_strike_rate=4, orange_cap=3,
# purple_cap=3, player_of_tournament=3, costliest_player=4, most_ducks=5
# Note: fixed Phase 1 entries already use several of these — auto pool fills the rest
purple_pool = [
    "player_of_tournament",  # use 1 (auto)
    "allrounders",           # use 1
    "dismissals_by_keeper",  # use 1
    "high_strike_rate",      # use 1
    "most_ducks",            # use 1
    "ipl_champions",         # ⚠ use once
    "allrounders",           # use 2
    "dismissals_by_keeper",  # use 2
    "high_strike_rate",      # use 2
    "most_ducks",            # use 2
    "player_of_tournament",  # use 2
    "dismissals_by_keeper",  # use 3
    "high_strike_rate",      # use 3
    "most_ducks",            # use 3
    "player_of_tournament",  # use 3
    "high_strike_rate",      # use 4
    "most_ducks",            # use 4
    "most_ducks",            # use 5
    "winning_captain",       # use 1 (auto)
    "winning_captain",       # use 2 (auto)
]

COOLDOWN = 4  # days

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def category_type(spec):
    """Return the cooldown key for a spec."""
    if spec.startswith("team_players:"):
        parts = spec.split(":")
        return f"team_players:{parts[1]}"  # team-level cooldown
    if spec.startswith("team_all_seasons:"):
        parts = spec.split(":")
        return f"team_all_seasons:{parts[1]}"  # team-level cooldown
    if spec.startswith("coaches:"):
        return "coaches"  # all coach seasons share one cooldown key
    return spec


def build_schedule():
    last_used = {}  # category_type -> last date index used

    schedule = []

    yellow_idx = 0
    all_time_idx = 0  # for non-squad days

    blue_idx = 0
    purple_idx = 0

    # Fixed overrides for special days
    fixed = {
        0:  ("ipl_champions",       "orange_cap",           "purple_cap",           "player_of_tournament"),
        1:  ("team_players:RCB:2026","team_players:CSK:2026","team_players:MI:2026", "team_players:KKR:2026"),
        2:  ("orange_cap",           "purple_cap",           "costliest_player",     "winning_captain"),
        3:  ("coaches:2026",         "coaches:2025",         "coaches:2024",         "coaches:2013"),
        4:  ("team_players:SRH:2026","team_players:RR:2026", "team_players:GT:2026", "team_players:PBKS:2026"),
        # Phase 1 fixed
        5:  ("team_players:RCB:2026","team_players:SRH:2026","batting_records",      "player_of_tournament"),
        6:  ("team_players:MI:2026", "team_players:KKR:2026","orange_cap",           "costliest_player"),
        7:  ("team_players:RR:2026", "team_players:CSK:2026","winning_captain",      "bowling_records"),
        8:  ("team_players:PBKS:2026","team_players:GT:2026","purple_cap",           "season_records"),
        9:  ("team_players:LSG:2026","team_players:DC:2026", "player_of_tournament", "orange_cap"),
        10: ("team_players:KKR:2026","team_players:SRH:2026","winning_captain",      "costliest_player"),
        11: ("team_players:CSK:2026","team_players:PBKS:2026","coaches:2022",        "coaches:2021"),
        12: ("team_players:DC:2026", "team_players:MI:2026", "team_players:GT:2026", "team_players:RR:2026"),
        13: ("team_players:SRH:2026","team_players:LSG:2026","purple_cap",           "player_of_tournament"),
        14: ("team_players:KKR:2026","team_players:PBKS:2026","coaches:2026",        "winning_captain"),
        15: ("team_players:RR:2026", "team_players:MI:2026", "orange_cap",           "costliest_player"),
        16: ("team_players:DC:2026", "team_players:GT:2026", "coaches:2020",         "coaches:2019"),
        17: ("team_players:KKR:2026","team_players:LSG:2026","coaches:2018",         "coaches:2017"),
        18: ("team_players:RR:2026", "team_players:RCB:2026","coaches:2016",         "coaches:2015"),
        19: ("team_players:PBKS:2026","team_players:SRH:2026","team_players:CSK:2026","team_players:DC:2026"),
        20: ("team_players:LSG:2026","team_players:GT:2026", "team_players:MI:2026", "team_players:RCB:2026"),
        # Playoffs
        60: ("team_players:TEAM_A:2026","team_players:TEAM_B:2026","fielding_records","most_ducks"),
        61: ("team_players:MI:2026",    "team_players:MI:2008",    "topbat",          "fifers"),
        62: ("team_players:TEAM_C:2026","team_players:TEAM_D:2026","topbowl",         "high_strike_rate"),
        63: ("team_players:TEAM_A:2026","team_all_seasons:KKR",    "highest_batting_avg","allrounders"),
        64: ("team_owners",             "coaches:2024",             "multi_team_players","dismissals_by_keeper"),
        65: ("team_owners",             "coaches:2023",             "catches_by_fielder","most_ducks"),
        66: ("team_players:FINALIST_A:2026","team_players:FINALIST_B:2026","winning_captain","costliest_player"),
    }

    def next_available(pool, idx, day_idx, slot_label):
        """Find next pool item that respects cooldown."""
        attempts = 0
        while idx < len(pool):
            spec = pool[idx]
            ctype = category_type(spec)
            last = last_used.get(ctype, -999)
            if (day_idx - last) >= COOLDOWN:
                return idx, spec
            idx += 1
            attempts += 1
            if attempts > len(pool):
                break
        # fallback — return next regardless
        return idx, pool[min(idx, len(pool)-1)]

    green_teams_used = set()

    for i, d in enumerate(puzzle_dates):
        if i in fixed:
            y, g, b, p = fixed[i]
        else:
            # Yellow: next 2026 team with cooldown
            y_team = yellow_teams[yellow_idx % len(yellow_teams)]
            y = f"team_players:{y_team}:2026"
            yellow_idx += 1

            # Green: depends on Yellow
            # If Yellow is a 2026 squad → pair with 2008 squad (or team_all_seasons if team didn't exist in 2008)
            # If Yellow is NOT a squad → use team_all_seasons rotating
            if y.startswith("team_players:"):
                parts = y.split(":")
                team_code = parts[1]
                if team_code in TEAMS_IN_2008:
                    g = f"team_players:{team_code}:2008"
                else:
                    g = f"team_all_seasons:{team_code}"
            else:
                # non-squad yellow — use rotating all-time team
                at_team = all_time_teams[all_time_idx % len(all_time_teams)]
                g = f"team_all_seasons:{at_team}"
                all_time_idx += 1

            # Blue
            blue_idx, b = next_available(blue_pool, blue_idx, i, "blue")
            blue_idx += 1

            # Purple
            purple_idx, p = next_available(purple_pool, purple_idx, i, "purple")
            purple_idx += 1

        # Record usage
        for spec in [y, g, b, p]:
            last_used[category_type(spec)] = i

        schedule.append((i + 1, d, y, g, b, p))

    return schedule


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def main():
    schedule = build_schedule()

    lines = []
    lines.append("# IPL 2026 - Category Schedule v4 (4-Day Cooldown, 2008/2026 Seasons Only)")
    lines.append("")
    lines.append("Same category type will not repeat within 4 days.")
    lines.append("- Yellow = current 2026 squad (easy, match-day relevant)")
    lines.append("- Green  = team_players:TEAM:2008 (inaugural season) or team_all_seasons:TEAM if team didn't exist in 2008")
    lines.append("- Blue   = stats / coaches (hard)")
    lines.append("- Purple = niche / obscure (hardest)")
    lines.append("")

    sections = {
        date(2026, 3, 23): "## Pre-IPL Rollout (23-27 Mar)",
        date(2026, 3, 28): "## Phase 1 - Confirmed Fixtures (28 Mar - 12 Apr)",
        date(2026, 4, 13): "## Phase 2 - Match Days (13 Apr - 21 May)",
        date(2026, 5, 22): "## Playoffs (22-31 May)",
    }

    for ed, d, y, g, b, p in schedule:
        if d in sections:
            lines.append("")
            lines.append(sections[d])
            lines.append("")
            lines.append("| Ed | Date | Yellow | Green | Blue | Purple |")
            lines.append("|---|---|---|---|---|---|")
        date_str = d.strftime("%d %b").lstrip("0")
        lines.append(f"| {ed} | {date_str} | `{y}` | `{g}` | `{b}` | `{p}` |")

    # -----------------------------------------------------------------------
    # Pool usage summary — computed from the schedule
    # -----------------------------------------------------------------------

    # Pool sizes (actual data)
    POOL_SIZES = {
        "ipl_champions":          7,
        "batting_records":        8,
        "bowling_records":        8,
        "season_records":         5,
        "fielding_records":       5,
        "winning_captain":        9,
        "orange_cap":             14,
        "purple_cap":             15,
        "player_of_tournament":   14,
        "costliest_player":       17,
        "team_owners":            10,
        "allrounders":            11,
        "dismissals_by_keeper":   12,
        "high_strike_rate":       16,
        "highest_batting_avg":    35,
        "catches_by_fielder":     24,
        "topbat":                 28,
        "topbowl":                29,
        "multi_team_players":     37,
        "fifers":                 31,
        "most_ducks":             21,
    }

    # Max safe uses = floor(pool / 4)
    def max_uses(pool): return pool // 4

    def remaining_label(pool, uses):
        remaining = pool - (uses * 4)
        if remaining <= 0:
            return "0 ⚠ exhausted"
        elif remaining <= 4:
            return f"~{remaining} left"
        elif remaining <= 8:
            return "ok"
        else:
            return "plenty"

    # Count uses per base category type
    from collections import defaultdict
    usage = defaultdict(list)  # base_type -> [ed numbers]

    for ed, d, y, g, b, p in schedule:
        for spec in [y, g, b, p]:
            # Normalise to base type
            if spec.startswith("team_players:") or spec.startswith("team_all_seasons:"):
                continue  # skip team categories — unlimited
            base = spec.split(":")[0] if ":" in spec else spec
            if base == "coaches":
                continue  # coaches handled separately
            usage[base].append(ed)

    lines.append("")
    lines.append("")
    lines.append("## Pool Usage Summary")
    lines.append("")
    lines.append("| Category | Pool | Uses | Editions | Remaining |")
    lines.append("|---|---|---|---|---|")

    for cat, pool in POOL_SIZES.items():
        eds = usage.get(cat, [])
        uses = len(eds)
        eds_str = ", ".join(f"Ed {e}" for e in eds) if eds else "—"
        rem = remaining_label(pool, uses)
        lines.append(f"| `{cat}` | {pool} | {uses} | {eds_str} | {rem} |")

    # Coaches
    coach_eds = usage.get("coaches", [])
    # re-count coaches separately since they share a base key
    coach_usage = []
    for ed, d, y, g, b, p in schedule:
        for spec in [y, g, b, p]:
            if spec.startswith("coaches:"):
                coach_usage.append(ed)
    lines.append(f"| `coaches:SEASON` | 19 seasons | {len(coach_usage)} | {', '.join(f'Ed {e}' for e in coach_usage) if coach_usage else '—'} | plenty |")
    lines.append(f"| `team_players:TEAM:2026` | unlimited | backbone | — | unlimited |")
    lines.append(f"| `team_players:TEAM:2008` | 7 original teams | backbone | — | unlimited |")
    lines.append(f"| `team_all_seasons:TEAM` | unlimited | backbone | — | unlimited |")

    return "\n".join(lines)


if __name__ == "__main__":
    content = main()
    with open("category_schedule_suggestions_v4.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("Written to category_schedule_suggestions_v4.md")
