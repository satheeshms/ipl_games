"""
category_generators.py — Auto-generate puzzle category items from ipl_data.json.

Each generator receives:
    ipl_data : dict   — full ipl_data.json loaded as a dict
    params   : list   — extra parameters parsed from the category spec (may be empty)
    exclude  : set    — item names to exclude (already used in this puzzle or prior puzzles)

Each generator returns:
    {"title": str, "items": [str]}   — exactly 4 unique items, none in exclude

Raise ValueError with a descriptive message if fewer than 4 candidates are available.
"""

import random


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _pick(candidates: list[str], exclude: set[str], label: str) -> list[str]:
    """Deduplicate candidates, remove excluded, pick 4 at random."""
    unique = list(dict.fromkeys(candidates))          # deduplicate, preserve order
    available = [c for c in unique if c not in exclude]
    if len(available) < 4:
        raise ValueError(
            f"{label}: only {len(available)} unique item(s) available after exclusions "
            f"(need 4). Consider fewer exclusions or a different season/team filter."
        )
    return random.sample(available, 4)


def _award(ipl_data: dict, award_type: str, title: str,
           exclude: set[str]) -> dict:
    """Pick 4 unique player names from a named award type."""
    names = [
        a["player_name"]
        for a in ipl_data.get("awards", [])
        if a["type"] == award_type
    ]
    items = _pick(names, exclude, award_type)
    return {"title": title, "items": items}


# ---------------------------------------------------------------------------
# Individual generators
# ---------------------------------------------------------------------------

def gen_orange_cap(ipl_data: dict, params: list, exclude: set) -> dict:
    return _award(ipl_data, "orange_cap", "Orange Cap Winners", exclude)


def gen_purple_cap(ipl_data: dict, params: list, exclude: set) -> dict:
    return _award(ipl_data, "purple_cap", "Purple Cap Winners", exclude)


def gen_player_of_tournament(ipl_data: dict, params: list, exclude: set) -> dict:
    return _award(ipl_data, "player_of_tournament", "Player of the Tournament", exclude)


def gen_costliest_player(ipl_data: dict, params: list, exclude: set) -> dict:
    return _award(ipl_data, "costliest_player", "Costliest Auction Picks", exclude)


def gen_winning_captain(ipl_data: dict, params: list, exclude: set) -> dict:
    return _award(ipl_data, "winning_captain", "IPL Winning Captains", exclude)


def gen_ipl_champions(ipl_data: dict, params: list, exclude: set) -> dict:
    """Pick 4 unique IPL-winning team names."""
    names = [w["team_name"] for w in ipl_data.get("ipl_wins", [])]
    items = _pick(names, exclude, "ipl_champions")
    return {"title": "IPL Champions", "items": items}


def gen_team_players(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players from a team's season squad.

    Params: [team_code_or_name, season]
        team_code_or_name — short code (CSK, MI …) or full name
        season            — 4-digit year string, e.g. "2025"

    Both params are required.
    """
    if len(params) < 2:
        raise ValueError(
            "team_players requires 2 params: team and season. "
            "Example: team_players:CSK:2025"
        )

    team_raw, season_raw = params[0], params[1]

    try:
        season = int(season_raw)
    except ValueError:
        raise ValueError(f"team_players: invalid season '{season_raw}' (must be a 4-digit year)")

    # Resolve short code → full name
    team_name = _resolve_team(ipl_data, team_raw)

    names = [
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name and pt["season"] == season
    ]

    if not names:
        raise ValueError(
            f"team_players: no players found for team '{team_name}' in season {season}. "
            "Check the team name/code and season."
        )

    items = _pick(names, exclude, f"team_players:{team_name}:{season}")
    return {"title": f"{team_name} {season} Squad", "items": items}


def gen_coaches(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 head coaches from a given season.

    Params: [season]   — 4-digit year string, e.g. "2025"
    """
    if len(params) < 1:
        raise ValueError(
            "coaches requires 1 param: season. Example: coaches:2025"
        )

    try:
        season = int(params[0])
    except ValueError:
        raise ValueError(f"coaches: invalid season '{params[0]}' (must be a 4-digit year)")

    names = [
        c["coach"]
        for c in ipl_data.get("coaches", [])
        if c["season"] == season
    ]

    if not names:
        raise ValueError(
            f"coaches: no coaches found for season {season}."
        )

    items = _pick(names, exclude, f"coaches:{season}")
    return {"title": f"{season} Head Coaches", "items": items}


# ---------------------------------------------------------------------------
# Team code resolver
# ---------------------------------------------------------------------------

_TEAM_CODES: dict[str, str] = {
    "CSK":  "Chennai Super Kings",
    "MI":   "Mumbai Indians",
    "RCB":  "Royal Challengers Bengaluru",
    "KKR":  "Kolkata Knight Riders",
    "DC":   "Delhi Capitals",
    "DD":   "Delhi Daredevils",
    "SRH":  "Sunrisers Hyderabad",
    "RR":   "Rajasthan Royals",
    "LSG":  "Lucknow Super Giants",
    "GT":   "Gujarat Titans",
    "PBKS": "Punjab Kings",
    "KXIP": "Kings XI Punjab",
    "PWI":  "Pune Warriors India",
    "RPS":  "Rising Pune Supergiants",
    "GL":   "Gujarat Lions",
}


def _resolve_team(ipl_data: dict, raw: str) -> str:
    """Return full team name given a short code or full name."""
    if raw in _TEAM_CODES:
        return _TEAM_CODES[raw]
    # Check if it's already a valid full name in the data
    known = {t["name"] for t in ipl_data.get("teams", [])}
    if raw in known:
        return raw
    raise ValueError(
        f"Unknown team '{raw}'. "
        f"Valid codes: {sorted(_TEAM_CODES.keys())}. "
        f"Or use the full team name."
    )


# ---------------------------------------------------------------------------
# Generator registry
# ---------------------------------------------------------------------------

GENERATORS: dict[str, callable] = {
    "orange_cap":           gen_orange_cap,
    "purple_cap":           gen_purple_cap,
    "player_of_tournament": gen_player_of_tournament,
    "costliest_player":     gen_costliest_player,
    "winning_captain":      gen_winning_captain,
    "ipl_champions":        gen_ipl_champions,
    "team_players":         gen_team_players,
    "coaches":              gen_coaches,
}


def generate_category(ipl_data: dict, spec: str, exclude: set[str]) -> dict:
    """
    Parse a category spec string and invoke the matching generator.

    Spec format:  type[:param1[:param2...]]
    Example:      team_players:CSK:2025

    Returns {"title": str, "items": [str]} or raises ValueError.
    """
    parts = spec.split(":")
    category_type = parts[0]
    params = parts[1:]

    gen_fn = GENERATORS.get(category_type)
    if gen_fn is None:
        raise ValueError(
            f"Unknown category type '{category_type}'. "
            f"Available types: {sorted(GENERATORS.keys())}"
        )

    return gen_fn(ipl_data, params, exclude)
