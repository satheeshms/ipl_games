"""
generators/geographic.py — Geographic category generators.

Uses enriched player data exported to ipl_data.json:
  country:COUNTRY   — ipl_data['foreign_players'][].country
  state:STATE       — ipl_data['india_state_wise'][STATE]
  ranji:TEAM        — ipl_data['ranji_team_wise'][TEAM]
"""

from category_generators import _pick


def gen_country(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 IPL players from a given country.

    Params: [country_name]  — e.g. 'Australia', 'South Africa', 'England'
    Example: country:Australia

    Source: ipl_data['foreign_players'] — each entry has 'country' and 'name' fields.

    Available pools: Australia(69), South Africa(46), Sri Lanka(31),
                     England(30), New Zealand(29), West Indies(19), Afghanistan(9)
    """
    if len(params) < 1:
        raise ValueError("country requires 1 param: country name. Example: country:Australia")

    country = params[0].replace("_", " ")  # allow country:South_Africa

    entries = ipl_data.get("foreign_players", [])
    names = [e["name"] for e in entries if e.get("country") == country]

    if not names:
        raise ValueError(
            f"country: no players found for country '{country}'. "
            "Check spelling. Example values: Australia, South Africa, England, New Zealand, "
            "Sri Lanka, West Indies, Afghanistan."
        )

    items = _pick(names, exclude, f"country:{country}")
    return {"title": f"Players from {country}", "items": items}


def gen_state(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 IPL players from a given Indian state.

    Params: [state_name]  — e.g. 'Delhi', 'Maharashtra', 'Karnataka'
    Example: state:Delhi

    Source: ipl_data['india_state_wise'][STATE] — pre-grouped dict.
    Each entry has 'name' field (IPL display name).

    Available pools: Delhi(22), Maharashtra(~30), Karnataka(~20), UP(~25),
                     Tamil Nadu(~19), Punjab(~22) and more.
    """
    if len(params) < 1:
        raise ValueError("state requires 1 param: state name. Example: state:Delhi")

    state = params[0].replace("_", " ")

    state_map = ipl_data.get("india_state_wise", {})
    entries = state_map.get(state, [])

    if not entries:
        available = sorted(state_map.keys())
        raise ValueError(
            f"state: no players found for state '{state}'. "
            f"Available states: {available}"
        )

    names = [e["name"] for e in entries]
    items = _pick(names, exclude, f"state:{state}")
    return {"title": f"Players from {state}", "items": items}


def gen_ranji(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 IPL players who played Ranji Trophy for a given team.

    Params: [ranji_team]  — e.g. 'Mumbai', 'Delhi', 'Karnataka'
    Example: ranji:Mumbai

    Source: ipl_data['ranji_team_wise'][TEAM] — pre-grouped dict.
    Each entry has 'name' field (IPL display name).

    Available pools: Mumbai(33), Delhi(32), Karnataka(25) and more.
    """
    if len(params) < 1:
        raise ValueError("ranji requires 1 param: Ranji team name. Example: ranji:Mumbai")

    ranji_team = params[0].replace("_", " ")

    ranji_map = ipl_data.get("ranji_team_wise", {})
    entries = ranji_map.get(ranji_team, [])

    if not entries:
        available = sorted(ranji_map.keys())
        raise ValueError(
            f"ranji: no players found for Ranji team '{ranji_team}'. "
            f"Available teams: {available}"
        )

    names = [e["name"] for e in entries]
    items = _pick(names, exclude, f"ranji:{ranji_team}")
    return {"title": f"Ranji Trophy: {ranji_team}", "items": items}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GENERATORS = {
    "country": gen_country,
    "state":   gen_state,
    "ranji":   gen_ranji,
}
