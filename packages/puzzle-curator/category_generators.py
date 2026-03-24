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


def gen_team_all_seasons(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players who have ever played for a team (any season).

    Params: [team_code_or_name]
    Example: team_all_seasons:CSK

    Used when the puzzle has no season context — pairs well with non-squad
    categories like coaches, awards, records.
    """
    if len(params) < 1:
        raise ValueError(
            "team_all_seasons requires 1 param: team. "
            "Example: team_all_seasons:CSK"
        )

    team_name = _resolve_team(ipl_data, params[0])

    names = [
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name
    ]

    if not names:
        raise ValueError(
            f"team_all_seasons: no players found for team '{team_name}'."
        )

    items = _pick(names, exclude, f"team_all_seasons:{team_name}")
    return {"title": f"{team_name} Players (All Time)", "items": items}


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
        if c["season"] == season and c.get("role", "head") == "head"
    ]

    if not names:
        raise ValueError(
            f"coaches: no head coaches found for season {season}."
        )

    items = _pick(names, exclude, f"coaches:{season}")
    return {"title": f"{season} Head Coaches", "items": items}


def gen_head_coaches(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 IPL head coaches across all seasons.
    Spec: head_coaches  (no season param)
    """
    names = list({
        c["coach"]
        for c in ipl_data.get("coaches", [])
        if c.get("role", "head") == "head"
    })
    if not names:
        raise ValueError("head_coaches: no head coach data found in ipl_data['coaches']")
    items = _pick(names, exclude, "head_coaches")
    return {"title": "IPL Head Coaches", "items": items}


def _gen_specialist_coaches(ipl_data: dict, params: list, exclude: set,
                             role: str, label: str) -> dict:
    """
    Shared logic for batting / bowling / fielding coach generators.
    Without a season param — picks from all seasons (all-time pool).
    With a season param   — picks only from that season.
    """
    if params:
        try:
            season = int(params[0])
        except ValueError:
            raise ValueError(f"{role}_coaches: invalid season '{params[0]}' (must be a 4-digit year)")
        names = [
            c["coach"]
            for c in ipl_data.get("coaches", [])
            if c["season"] == season and c.get("role") == role
        ]
        if not names:
            raise ValueError(f"{role}_coaches: no {label} coaches found for season {season}.")
        label_str = f"{season} {label} Coaches"
        key = f"{role}_coaches:{season}"
    else:
        names = list({
            c["coach"]
            for c in ipl_data.get("coaches", [])
            if c.get("role") == role
        })
        if not names:
            raise ValueError(f"{role}_coaches: no {label} coach data found in ipl_data['coaches']")
        label_str = f"IPL {label} Coaches"
        key = f"{role}_coaches"

    items = _pick(names, exclude, key)
    return {"title": label_str, "items": items}


def gen_batting_coaches(ipl_data: dict, params: list, exclude: set) -> dict:
    """Pick 4 batting coaches. Params: [] all-seasons or [season]"""
    return _gen_specialist_coaches(ipl_data, params, exclude, "batting", "Batting")


def gen_bowling_coaches(ipl_data: dict, params: list, exclude: set) -> dict:
    """Pick 4 bowling coaches. Params: [] all-seasons or [season]"""
    return _gen_specialist_coaches(ipl_data, params, exclude, "bowling", "Bowling")


def gen_fielding_coaches(ipl_data: dict, params: list, exclude: set) -> dict:
    """Pick 4 fielding coaches. Params: [] all-seasons or [season]"""
    return _gen_specialist_coaches(ipl_data, params, exclude, "fielding", "Fielding")


def gen_fielding_records(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players who each hold a unique IPL fielding record:
      Most WK Catches, Most Stumpings, Most Catches (non-keeper), Most Run-Outs (non-keeper).

    Pool: exactly 4 unique players — use once.
    """
    entries = ipl_data.get("records", {}).get("fielding_records", [])
    if not entries:
        raise ValueError("fielding_records: no data in ipl_data['records']['fielding_records']")
    names = [e["player"] for e in entries]
    items = _pick(names, exclude, "fielding_records")
    return {"title": "IPL Fielding Record Holders", "items": items}


def gen_batting_records(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 unique players who hold an IPL career batting record.

    Source: ipl_data['records']['batting_records']
    """
    entries = ipl_data.get("records", {}).get("batting_records", [])
    if not entries:
        raise ValueError("batting_records: no data found in ipl_data['records']['batting_records']")
    names = [e["player"] for e in entries]
    items = _pick(names, exclude, "batting_records")
    return {"title": "IPL Batting Record Holders", "items": items}


def gen_bowling_records(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 unique players who hold an IPL career bowling record.

    Source: ipl_data['records']['bowling_records']
    """
    entries = ipl_data.get("records", {}).get("bowling_records", [])
    if not entries:
        raise ValueError("bowling_records: no data found in ipl_data['records']['bowling_records']")
    names = [e["player"] for e in entries]
    items = _pick(names, exclude, "bowling_records")
    return {"title": "IPL Bowling Record Holders", "items": items}


def gen_team_owners(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 unique IPL franchise owners.

    Source: ipl_data['records']['team_owners']
    Pool: 10 teams — supports up to 2 uses.
    """
    entries = ipl_data.get("records", {}).get("team_owners", [])
    if not entries:
        raise ValueError("team_owners: no data found in ipl_data['records']['team_owners']")
    names = [e["owner"] for e in entries]
    items = _pick(names, exclude, "team_owners")
    return {"title": "IPL Franchise Owners", "items": items}


def gen_season_records(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 unique players who hold an IPL single-season record.

    Source: ipl_data['records']['season_records']
    """
    entries = ipl_data.get("records", {}).get("season_records", [])
    if not entries:
        raise ValueError("season_records: no data found in ipl_data['records']['season_records']")
    names = [e["player"] for e in entries]
    items = _pick(names, exclude, "season_records")
    return {"title": "IPL Single Season Record Holders", "items": items}


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
# Generator registry — core generators defined in this file
# ---------------------------------------------------------------------------

from generators import GENERATORS as _NEW_GENERATORS
from generators.management import gen_coaches_team_season

_CORE_GENERATORS: dict[str, callable] = {
    "orange_cap":             gen_orange_cap,
    "purple_cap":             gen_purple_cap,
    "player_of_tournament":   gen_player_of_tournament,
    "costliest_player":       gen_costliest_player,
    "winning_captain":        gen_winning_captain,
    "ipl_champions":          gen_ipl_champions,
    "team_players":           gen_team_players,
    "team_all_seasons":       gen_team_all_seasons,
    "head_coaches":           gen_head_coaches,
    "batting_coaches":        gen_batting_coaches,
    "bowling_coaches":        gen_bowling_coaches,
    "fielding_coaches":       gen_fielding_coaches,
    "fielding_records":       gen_fielding_records,
    "batting_records":        gen_batting_records,
    "bowling_records":        gen_bowling_records,
    "season_records":         gen_season_records,
    "team_owners":            gen_team_owners,
}

# Merge: new generators extend core; core takes precedence on name conflicts
GENERATORS: dict[str, callable] = {**_NEW_GENERATORS, **_CORE_GENERATORS}


def generate_category(ipl_data: dict, spec: str, exclude: set[str]) -> dict:
    """
    Parse a category spec string and invoke the matching generator.

    Spec format:  type[:param1[:param2...]]
    Examples:
      team_players:CSK:2025
      coaches:2025              — head coaches for a season  (1 param → gen_coaches)
      coaches:CSK:2025          — all staff for a team/season (2 params → gen_coaches_team_season)
      legends:india
      country:Australia
      winning_squad:2008

    Returns {"title": str, "items": [str]} or raises ValueError.
    """
    parts = spec.split(":")
    category_type = parts[0]
    params = parts[1:]

    # Special dispatch: coaches:SEASON (1 param) vs coaches:TEAM:SEASON (2 params)
    if category_type == "coaches":
        if len(params) == 1:
            result = gen_coaches(ipl_data, params, exclude)
        elif len(params) == 2:
            result = gen_coaches_team_season(ipl_data, params, exclude)
        else:
            raise ValueError(
                "coaches spec format: 'coaches:SEASON' or 'coaches:TEAM:SEASON'. "
                f"Got {len(params)} param(s)."
            )
        result["spec"] = spec
        return result

    gen_fn = GENERATORS.get(category_type)
    if gen_fn is None:
        raise ValueError(
            f"Unknown category type '{category_type}'. "
            f"Available types: {sorted(GENERATORS.keys())}"
        )

    result = gen_fn(ipl_data, params, exclude)
    result["spec"] = spec
    return result
