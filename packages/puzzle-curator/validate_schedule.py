"""
validate_schedule.py — Validate a manually-edited curation_schedule.md.

Checks all rules from gen_schedule_v5.py:
  1. Cooldown windows (per-spec, shared-bucket, country category-wide)
  2. 4-Worlds group constraint (no two slots in same puzzle from same group)
  3. Same-type prefix constraint (no two slots with same spec prefix per puzzle)
  4. Team collision (no two slots referencing the same team per puzzle)
  5. team_legends blocking (batting ↔ top_run_scorers, bowling ↔ top_wicket_takers)
  6. Pool caps (spec does not appear more times than its pool allows)

Usage:
  python validate_schedule.py                          # validates curation_schedule.md
  python validate_schedule.py path/to/schedule.md
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Rules — mirrors gen_schedule_v5.py exactly
# ---------------------------------------------------------------------------

# Category groups
GROUP_A = "A"   # Team-based (squads, winning_squad)
GROUP_B = "B"   # Awards
GROUP_C = "C"   # Statistical
GROUP_D = "D"   # Geographic
GROUP_E = "E"   # Cross-team / relational
GROUP_F = "F"   # Management

GROUP_LABELS = {
    "A": "Squad/Team",
    "B": "Awards",
    "C": "Stats",
    "D": "Geographic",
    "E": "Cross-team/Legends",
    "F": "Management",
}


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
    if spec.startswith(("played_both:", "multi_team:", "longest_serving", "legends:")):
        return GROUP_E
    if spec.startswith(("coaches", "head_coaches", "batting_coaches",
                        "bowling_coaches", "fielding_coaches", "team_owners")):
        return GROUP_F
    return GROUP_C  # default


# Cooldown constants
COOLDOWN_CAT          = 4
COOLDOWN_TEAM         = 3
COOLDOWN_PLAYED_BOTH  = 2
COOLDOWN_TEAM_LEGENDS = 2
COOLDOWN_GEO_LOCAL    = 2
COOLDOWN_COUNTRY      = 5
COOLDOWN_COUNTRY_CAT  = 3
COOLDOWN_COACHES      = 3


def cooldown_key(spec: str) -> str:
    """Normalise spec to its shared cooldown bucket (mirrors gen_schedule_v5)."""
    if spec.startswith(("team_players:", "team_all_seasons:")):
        return f"team:{spec.split(':')[1]}"
    if spec.startswith("winning_squad:"):
        return "winning_squad"
    if spec.startswith(("coaches", "head_coaches", "batting_coaches",
                        "bowling_coaches", "fielding_coaches")):
        return "coaches"
    if spec.startswith("state:"):
        return "state"
    if spec.startswith("ranji:"):
        return "ranji"
    if spec.startswith("played_both:"):
        return "played_both"
    if spec.startswith("team_legends_batting:"):
        return "team_legends_batting"
    if spec.startswith("team_legends_bowling:"):
        return "team_legends_bowling"
    return spec  # country:X uses per-country key


def cooldown_for(spec: str) -> int:
    """Return the cooldown window (days) for a spec.

    team_players / team_all_seasons use the team-level cooldown (3 days),
    matching _pick_yellow's cd.team_available() call in gen_schedule_v5.
    All other specs use COOLDOWN_CAT (4) unless they have a shorter special window.
    """
    if spec.startswith(("team_players:", "team_all_seasons:")):
        return COOLDOWN_TEAM
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


def spec_prefix(spec: str) -> str:
    """Return blocking prefix (historical squads get distinct prefix)."""
    if spec.startswith("team_players:"):
        parts = spec.split(":")
        if len(parts) >= 3 and parts[2].isdigit() and int(parts[2]) <= 2024:
            return "historical_squad"
    return spec.split(":")[0]


def teams_from_spec(spec: str) -> set[str]:
    """Return team codes a spec 'owns' for collision checking."""
    if spec.startswith(("team_players:", "team_all_seasons:",
                        "team_legends_batting:", "team_legends_bowling:")):
        return {spec.split(":")[1]}
    if spec.startswith("played_both:"):
        parts = spec.split(":")
        return {parts[1], parts[2]}
    return set()


# ---------------------------------------------------------------------------
# Parse curation_schedule.md
# ---------------------------------------------------------------------------

# Matches table rows like: | 1 | 24 Mar | Tue | — | `spec` | `spec` | `spec` | `spec` | [ ] |
ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|"          # edition
    r"\s*([^|]+?)\s*\|"          # date
    r"\s*([^|]+?)\s*\|"          # day
    r"\s*([^|]+?)\s*\|"          # match
    r"\s*`([^`]+)`\s*\|"         # yellow
    r"\s*`([^`]+)`\s*\|"         # green
    r"\s*`([^`]+)`\s*\|"         # blue
    r"\s*`([^`]+)`\s*\|"         # purple
    r"\s*\[([^\]]*)\]\s*\|"      # status
)


def parse_schedule(path: Path) -> list[dict]:
    """Parse schedule markdown into list of edition dicts."""
    editions = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        ed, date_str, day, match, yellow, green, blue, purple, status = m.groups()
        editions.append({
            "edition": int(ed),
            "date": date_str.strip(),
            "day": day.strip(),
            "match": match.strip(),
            "yellow": yellow.strip(),
            "green": green.strip(),
            "blue": blue.strip(),
            "purple": purple.strip(),
            "status": status.strip(),
            "lineno": lineno,
        })
    return editions


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class Violation:
    def __init__(self, edition: int, date: str, rule: str, detail: str):
        self.edition = edition
        self.date = date
        self.rule = rule
        self.detail = detail

    def __str__(self):
        return f"  Ed {self.edition:2d} ({self.date})  [{self.rule}]  {self.detail}"


def validate(editions: list[dict], caps: dict[str, int] | None = None) -> list[Violation]:
    violations: list[Violation] = []
    # cooldown tracking: key → day_index last used
    last_used: dict[str, int] = {}
    last_country_cat: int = -999
    # cap tracking
    spec_use_count: Counter = Counter()

    for idx, ed in enumerate(editions):
        edition  = ed["edition"]
        date_str = ed["date"]
        slots    = [ed["yellow"], ed["green"], ed["blue"], ed["purple"]]
        slot_names = ["Yellow", "Green", "Blue", "Purple"]

        # ---- 1. Cooldown checks ----
        for slot, spec in zip(slot_names, slots):
            key = cooldown_key(spec)
            cd  = cooldown_for(spec)
            last = last_used.get(key, -999)
            gap  = idx - last
            if gap < cd:
                violations.append(Violation(
                    edition, date_str, "COOLDOWN",
                    f"{slot} `{spec}` reused after {gap} day(s) (cooldown={cd}, bucket='{key}')"
                ))

            # Country category-wide cooldown
            if spec.startswith("country:"):
                gap_cat = idx - last_country_cat
                if gap_cat < COOLDOWN_COUNTRY_CAT:
                    violations.append(Violation(
                        edition, date_str, "COOLDOWN_COUNTRY_CAT",
                        f"{slot} `{spec}` — any country appeared {gap_cat} day(s) ago "
                        f"(category-wide cooldown={COOLDOWN_COUNTRY_CAT})"
                    ))

        # ---- 2. 4-Worlds group constraint ----
        groups_seen: dict[str, list[str]] = defaultdict(list)
        for slot, spec in zip(slot_names, slots):
            g = get_group(spec)
            groups_seen[g].append(f"{slot}:`{spec}`")
        for g, specs_in_group in groups_seen.items():
            if len(specs_in_group) > 1:
                violations.append(Violation(
                    edition, date_str, "GROUP_CONFLICT",
                    f"Group {g} ({GROUP_LABELS[g]}) used by multiple slots: "
                    + ", ".join(specs_in_group)
                ))

        # ---- 3. Same-type prefix constraint ----
        prefixes_seen: dict[str, list[str]] = defaultdict(list)
        for slot, spec in zip(slot_names, slots):
            p = spec_prefix(spec)
            prefixes_seen[p].append(f"{slot}:`{spec}`")
        for p, specs_with_prefix in prefixes_seen.items():
            if len(specs_with_prefix) > 1:
                violations.append(Violation(
                    edition, date_str, "PREFIX_CONFLICT",
                    f"Prefix '{p}' shared by: " + ", ".join(specs_with_prefix)
                ))

        # ---- 4. Team collision ----
        teams_used: dict[str, str] = {}  # team_code → "Slot:`spec`"
        for slot, spec in zip(slot_names, slots):
            for team in teams_from_spec(spec):
                if team in teams_used:
                    violations.append(Violation(
                        edition, date_str, "TEAM_COLLISION",
                        f"Team '{team}' appears in both {teams_used[team]} and {slot}:`{spec}`"
                    ))
                else:
                    teams_used[team] = f"{slot}:`{spec}`"

        # ---- 5. team_legends blocking ----
        spec_set = set(slots)
        prefixes_in_puzzle = {spec_prefix(s) for s in slots}
        for slot, spec in zip(slot_names, slots):
            if spec.startswith("team_legends_batting:") and "top_run_scorers" in prefixes_in_puzzle:
                other = [f"{sn}:`{s}`" for sn, s in zip(slot_names, slots)
                         if s.startswith("top_run_scorers")]
                violations.append(Violation(
                    edition, date_str, "LEGENDS_BLOCK",
                    f"{slot}:`{spec}` conflicts with top_run_scorers: "
                    + ", ".join(other)
                ))
            if spec.startswith("team_legends_bowling:") and "top_wicket_takers" in prefixes_in_puzzle:
                other = [f"{sn}:`{s}`" for sn, s in zip(slot_names, slots)
                         if s.startswith("top_wicket_takers")]
                violations.append(Violation(
                    edition, date_str, "LEGENDS_BLOCK",
                    f"{slot}:`{spec}` conflicts with top_wicket_takers: "
                    + ", ".join(other)
                ))

        # ---- 6. Pool caps ----
        if caps:
            for slot, spec in zip(slot_names, slots):
                spec_use_count[spec] += 1
                cap = caps.get(spec)
                if cap is not None and spec_use_count[spec] > cap:
                    violations.append(Violation(
                        edition, date_str, "CAP_EXCEEDED",
                        f"{slot} `{spec}` used {spec_use_count[spec]}x (cap={cap})"
                    ))

        # ---- Record usage for next iterations ----
        for spec in slots:
            last_used[cooldown_key(spec)] = idx
            if spec.startswith("country:"):
                last_country_cat = idx

    return violations


# ---------------------------------------------------------------------------
# Cap loading (optional — reads ipl_data.json via gen_schedule_v5)
# ---------------------------------------------------------------------------

def load_caps() -> dict[str, int] | None:
    try:
        from gen_schedule_v5 import compute_pool_caps
        caps = compute_pool_caps()
        return caps
    except Exception as e:
        print(f"[WARN] Could not load caps from ipl_data.json: {e}")
        print("       Cap checks will be skipped.")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse as _ap

    parser = _ap.ArgumentParser(
        description="Validate a curation_schedule.md against all gen_schedule_v5 rules."
    )
    parser.add_argument(
        "file", nargs="?", default="curation_schedule.md",
        help="Path to the schedule file (default: curation_schedule.md)"
    )
    parser.add_argument(
        "--until", metavar="ED_OR_DATE", default=None,
        help=(
            "Validate only up to this point (inclusive). "
            "Accepts an edition number (e.g. 20) or a date string matching "
            "the schedule's date column (e.g. '15 Apr' or '15 Apr 2026'). "
            "Default: validate all editions."
        ),
    )
    args = parser.parse_args()
    path = Path(args.file)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    print(f"Validating: {path}")
    editions = parse_schedule(path)

    if not editions:
        print("ERROR: No editions parsed. Check the file format.")
        sys.exit(1)

    # Apply --until filter
    if args.until is not None:
        until_raw = args.until.strip()
        # Try edition number first
        if until_raw.isdigit():
            cutoff_ed = int(until_raw)
            editions = [e for e in editions if e["edition"] <= cutoff_ed]
            until_label = f"edition {cutoff_ed}"
        else:
            # Match against the date column (case-insensitive, partial match)
            until_lower = until_raw.lower()
            cutoff_idx = None
            for i, e in enumerate(editions):
                if until_lower in e["date"].lower():
                    cutoff_idx = i
            if cutoff_idx is None:
                print(f"ERROR: --until '{until_raw}' did not match any date in the schedule.")
                print(f"       Available dates: {', '.join(e['date'] for e in editions[:5])} ...")
                sys.exit(1)
            editions = editions[: cutoff_idx + 1]
            until_label = f"'{until_raw}' (Ed {editions[-1]['edition']})"
        print(f"Filtering to {until_label} -> {len(editions)} edition(s) to validate.")

    print(f"Parsed {len(editions)} edition(s).")

    caps = load_caps()
    if caps:
        print(f"Loaded {len(caps)} pool caps from ipl_data.json.")

    violations = validate(editions, caps)

    print()
    if not violations:
        print(f"OK  All {len(editions)} editions pass - no violations found.")
        sys.exit(0)

    # Group by rule type for a cleaner summary
    by_rule: dict[str, list[Violation]] = defaultdict(list)
    for v in violations:
        by_rule[v.rule].append(v)

    rule_order = ["COOLDOWN", "COOLDOWN_COUNTRY_CAT", "GROUP_CONFLICT",
                  "PREFIX_CONFLICT", "TEAM_COLLISION", "LEGENDS_BLOCK", "CAP_EXCEEDED"]

    total = 0
    for rule in rule_order:
        vs = by_rule.get(rule, [])
        if not vs:
            continue
        print(f"-- {rule} ({len(vs)} violation(s)) " + "-" * max(0, 50 - len(rule)))
        for v in vs:
            print(str(v))
        print()
        total += len(vs)

    # Any rule not in the ordered list
    for rule, vs in by_rule.items():
        if rule not in rule_order:
            print(f"-- {rule} ({len(vs)} violation(s))")
            for v in vs:
                print(str(v))
            print()
            total += len(vs)

    print(f"FAIL  {total} violation(s) found across {len(editions)} editions.")
    sys.exit(1)


if __name__ == "__main__":
    main()
