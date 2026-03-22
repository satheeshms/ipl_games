"""
generators/management.py — Team management category generators.

  winning_squad:SEASON     — players from the IPL championship-winning team that season
  coaches:TEAM:SEASON      — all 4 coaching staff (head/batting/bowling/fielding) for a team/season
"""

from category_generators import _pick, _resolve_team


def gen_winning_squad(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players from the IPL championship-winning squad of a given season.

    Params: [season]  — 4-digit year string, e.g. '2008'
    Example: winning_squad:2008

    Source:
      ipl_data['ipl_wins']    — {season, team_name} for each year's champion
      ipl_data['player_teams'] — cross-referenced by team_name + season

    Pool: 17 seasons, 15-23 players per season.
    """
    if len(params) < 1:
        raise ValueError(
            "winning_squad requires 1 param: season. Example: winning_squad:2008"
        )

    try:
        season = int(params[0])
    except ValueError:
        raise ValueError(
            f"winning_squad: invalid season '{params[0]}' (must be a 4-digit year)"
        )

    # Find the winning team for this season
    winner = next(
        (w for w in ipl_data.get("ipl_wins", []) if w["season"] == season),
        None,
    )
    if winner is None:
        available = sorted(w["season"] for w in ipl_data.get("ipl_wins", []))
        raise ValueError(
            f"winning_squad: no IPL winner found for season {season}. "
            f"Available seasons: {available}"
        )

    team_name = winner["team_name"]

    names = [
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name and pt["season"] == season
    ]

    if not names:
        raise ValueError(
            f"winning_squad: no players found for {team_name} in season {season}."
        )

    items = _pick(names, exclude, f"winning_squad:{season}")
    return {"title": f"{season} Champions — {team_name}", "items": items}


def gen_coaches_team_season(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick all 4 coaching staff (head, batting, bowling, fielding) for a team in a season.

    Params: [team_code_or_name, season]
    Example: coaches:CSK:2025

    Source: ipl_data['coaches'] — {team_name, season, role, coach}
    Roles expected: head, batting, bowling, fielding (exactly 4 per team/season in 2025/2026)

    Note: Spec 'coaches:TEAM:SEASON' — distinct from 'coaches:SEASON' (head coaches only).
    """
    if len(params) < 2:
        raise ValueError(
            "coaches (team+season) requires 2 params: team and season. "
            "Example: coaches:CSK:2025"
        )

    team_name = _resolve_team(ipl_data, params[0])

    try:
        season = int(params[1])
    except ValueError:
        raise ValueError(
            f"coaches: invalid season '{params[1]}' (must be a 4-digit year)"
        )

    ROLES = {"head", "batting", "bowling", "fielding"}

    coaches = [
        c["coach"]
        for c in ipl_data.get("coaches", [])
        if c["team_name"] == team_name
        and c["season"] == season
        and c.get("role") in ROLES
    ]

    if not coaches:
        raise ValueError(
            f"coaches: no coaching staff found for '{team_name}' in season {season}. "
            "Check team name/code and season."
        )

    if len(coaches) < 4:
        raise ValueError(
            f"coaches: only {len(coaches)} coach role(s) found for '{team_name}' "
            f"in {season} (need 4: head, batting, bowling, fielding). "
            f"Found: {coaches}"
        )

    # Return all found coaches (up to 4) — no random sampling, all roles are meaningful
    items = _pick(coaches, exclude, f"coaches:{team_name}:{season}")
    return {"title": f"{team_name} {season} Coaching Staff", "items": items}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GENERATORS = {
    "winning_squad": gen_winning_squad,
    # coaches:TEAM:SEASON is registered in __init__.py with special dispatch
    # (2-param form vs existing 1-param coaches:SEASON)
    "_coaches_team_season": gen_coaches_team_season,
}
