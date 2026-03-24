"""
generators/stats.py — Statistical category generators.

Covers:
  - 5 quick wins (data already in ipl_data.json, functions were missing):
      high_strike_rate, highest_batting_avg, catches_by_fielder,
      dismissals_by_keeper, allrounders
  - New stat generators:
      top_run_scorers, top_wicket_takers, most_fifties, most_matches,
      team_legends_batting, team_legends_bowling
"""

from category_generators import _pick, _resolve_team


# ---------------------------------------------------------------------------
# Quick wins — data already exported, just needed function bodies
# ---------------------------------------------------------------------------

def gen_high_strike_rate(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 batsmen with the highest IPL career strike rate (min matches filter applied upstream).
    Source: ipl_data['high_strike_rate_batsmen']  (16 entries)
    """
    entries = ipl_data.get("high_strike_rate_batsmen", [])
    if not entries:
        raise ValueError("high_strike_rate: no data in ipl_data['high_strike_rate_batsmen']")
    names = [e["player_name"] for e in entries]
    items = _pick(names, exclude, "high_strike_rate")
    return {"title": "IPL High Strike Rate Batsmen (150+ SR)", "items": items}


def gen_highest_batting_avg(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 batsmen with the highest IPL career batting average (min matches filter applied upstream).
    Source: ipl_data['highest_batting_avg']  (35 entries)
    """
    entries = ipl_data.get("highest_batting_avg", [])
    if not entries:
        raise ValueError("highest_batting_avg: no data in ipl_data['highest_batting_avg']")
    names = [e["player_name"] for e in entries]
    items = _pick(names, exclude, "highest_batting_avg")
    return {"title": "IPL Career Batting Average Leaders (30+ avg)", "items": items}


def gen_catches_by_fielder(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 non-keeper fielders with the most IPL catches.
    Source: ipl_data['catches_by_fielder']  (24 entries)
    """
    entries = ipl_data.get("catches_by_fielder", [])
    if not entries:
        raise ValueError("catches_by_fielder: no data in ipl_data['catches_by_fielder']")
    names = [e["player_name"] for e in entries]
    items = _pick(names, exclude, "catches_by_fielder")
    return {"title": "Most IPL Catches by a Fielder (50+ matches)", "items": items}


def gen_dismissals_by_keeper(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 wicket-keepers with the most IPL dismissals.
    Source: ipl_data['dismissals_by_keeper']  (12 entries)
    """
    entries = ipl_data.get("dismissals_by_keeper", [])
    if not entries:
        raise ValueError("dismissals_by_keeper: no data in ipl_data['dismissals_by_keeper']")
    names = [e["player_name"] for e in entries]
    items = _pick(names, exclude, "dismissals_by_keeper")
    return {"title": "Most IPL Dismissals by a Keeper (50+ matches)", "items": items}


def gen_allrounders(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 IPL all-rounders (players with notable runs AND wickets).
    Source: ipl_data['allrounders']  (11 entries, field: 'name')
    """
    entries = ipl_data.get("allrounders", [])
    if not entries:
        raise ValueError("allrounders: no data in ipl_data['allrounders']")
    names = [e["name"] for e in entries]
    items = _pick(names, exclude, "allrounders")
    return {"title": "IPL All-Rounders (1000+ Runs & 50+ Wickets)", "items": items}


# ---------------------------------------------------------------------------
# New stat generators
# ---------------------------------------------------------------------------

def gen_top_run_scorers(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 from the all-time top run scorers in IPL (3000+ runs filter applied upstream).
    Source: ipl_data['batting_career_stats']  (28 entries, field: 'player_name')
    """
    entries = ipl_data.get("batting_career_stats", [])
    if not entries:
        raise ValueError("top_run_scorers: no data in ipl_data['batting_career_stats']")
    # Sort by runs descending (data may already be sorted, but enforce it)
    sorted_entries = sorted(entries, key=lambda e: e.get("runs", 0), reverse=True)
    names = [e["player_name"] for e in sorted_entries]
    items = _pick(names, exclude, "top_run_scorers")
    return {"title": "IPL Career Run Scorers (3000+ Runs)", "items": items}


def gen_top_wicket_takers(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 from the all-time top wicket takers in IPL (100+ wickets filter applied upstream).
    Source: ipl_data['bowling_career_stats']  (29 entries, field: 'player_name')
    """
    entries = ipl_data.get("bowling_career_stats", [])
    if not entries:
        raise ValueError("top_wicket_takers: no data in ipl_data['bowling_career_stats']")
    sorted_entries = sorted(entries, key=lambda e: e.get("wickets", 0), reverse=True)
    names = [e["player_name"] for e in sorted_entries]
    items = _pick(names, exclude, "top_wicket_takers")
    return {"title": "IPL Career Wicket Takers (100+ Wickets)", "items": items}


def gen_most_fifties(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 batsmen with the most IPL fifties.
    Source: ipl_data['batting_career_stats'] sorted by 'fifties'  (28 entries)
    """
    entries = ipl_data.get("batting_career_stats", [])
    if not entries:
        raise ValueError("most_fifties: no data in ipl_data['batting_career_stats']")
    sorted_entries = sorted(entries, key=lambda e: e.get("fifties", 0), reverse=True)
    names = [e["player_name"] for e in sorted_entries]
    items = _pick(names, exclude, "most_fifties")
    return {"title": "Most IPL Fifties", "items": items}


def gen_most_matches(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players with the most IPL matches.
    Source: ipl_data['batting_career_stats'] sorted by 'matches'  (28 entries)
    """
    entries = ipl_data.get("batting_career_stats", [])
    if not entries:
        raise ValueError("most_matches: no data in ipl_data['batting_career_stats']")
    sorted_entries = sorted(entries, key=lambda e: e.get("matches", 0), reverse=True)
    names = [e["player_name"] for e in sorted_entries]
    items = _pick(names, exclude, "most_matches")
    return {"title": "Most IPL Matches", "items": items}


def gen_team_legends_batting(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 all-time batting legends for a specific team (top 12 by runs).

    Params: [team_code_or_name]
    Example: team_legends_batting:CSK
    """
    if len(params) < 1:
        raise ValueError("team_legends_batting requires 1 param: team. Example: team_legends_batting:CSK")

    team_name = _resolve_team(ipl_data, params[0])

    team_player_names = {
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name
    }

    bat_map = {
        e["player_name"]: e.get("runs", 0)
        for e in ipl_data.get("batting_career_stats", [])
        if e["player_name"] in team_player_names
    }

    if not bat_map:
        raise ValueError(
            f"team_legends_batting: no batting stats found for players who played for '{team_name}'."
        )

    top12 = sorted(bat_map, key=lambda n: bat_map[n], reverse=True)[:12]
    items = _pick(top12, exclude, f"team_legends_batting:{team_name}")
    return {"title": f"{team_name} Batting Legends", "items": items}


def gen_team_legends_bowling(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 all-time bowling legends for a specific team (top 12 by wickets).

    Params: [team_code_or_name]
    Example: team_legends_bowling:CSK
    """
    if len(params) < 1:
        raise ValueError("team_legends_bowling requires 1 param: team. Example: team_legends_bowling:CSK")

    team_name = _resolve_team(ipl_data, params[0])

    team_player_names = {
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name
    }

    bowl_map = {
        e["player_name"]: e.get("wickets", 0)
        for e in ipl_data.get("bowling_career_stats", [])
        if e["player_name"] in team_player_names
    }

    if not bowl_map:
        raise ValueError(
            f"team_legends_bowling: no bowling stats found for players who played for '{team_name}'."
        )

    top12 = sorted(bowl_map, key=lambda n: bowl_map[n], reverse=True)[:12]
    items = _pick(top12, exclude, f"team_legends_bowling:{team_name}")
    return {"title": f"{team_name} Bowling Legends", "items": items}


def gen_most_ducks(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players with the most IPL ducks (golden ducks / zero scores).
    Source: ipl_data['most_ducks']  (field: 'player_name')
    """
    entries = ipl_data.get("most_ducks", [])
    if not entries:
        raise ValueError("most_ducks: no data in ipl_data['most_ducks']")
    names = [e["player_name"] for e in entries if "player_name" in e]
    items = _pick(names, exclude, "most_ducks")
    return {"title": "Most IPL Ducks (10+ Ducks)", "items": items}


def gen_fifers(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players who have taken an IPL 5-wicket haul (fifer).
    Source: ipl_data['five_wicket_hauls']  (field: 'player_name' or 'name')
    """
    entries = ipl_data.get("five_wicket_hauls", [])
    if not entries:
        raise ValueError("fifers: no data in ipl_data['five_wicket_hauls']")
    # Support both field name variants
    names = [e.get("player_name") or e.get("name") for e in entries]
    names = [n for n in names if n]
    items = _pick(names, exclude, "fifers")
    return {"title": "IPL Five-Wicket Hauls", "items": items}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GENERATORS = {
    "high_strike_rate":       gen_high_strike_rate,
    "highest_batting_avg":    gen_highest_batting_avg,
    "catches_by_fielder":     gen_catches_by_fielder,
    "dismissals_by_keeper":   gen_dismissals_by_keeper,
    "allrounders":            gen_allrounders,
    "top_run_scorers":        gen_top_run_scorers,
    "top_wicket_takers":      gen_top_wicket_takers,
    "most_fifties":           gen_most_fifties,
    "most_matches":           gen_most_matches,
    "most_ducks":             gen_most_ducks,
    "fifers":                 gen_fifers,
    "team_legends_batting":   gen_team_legends_batting,
    "team_legends_bowling":   gen_team_legends_bowling,
}
