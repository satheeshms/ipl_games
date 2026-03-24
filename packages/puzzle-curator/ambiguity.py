"""
ambiguity.py — Detect cross-category player ambiguity in generated puzzles.

A puzzle has ambiguity when a player placed in category A is also a valid
candidate for category B — making it impossible for solvers to determine
the correct grouping.

Public API:
  get_candidate_pool(ipl_data, spec) -> set[str]
      Return the full set of valid player names for a spec (no sampling, no
      exclusions). Returns set() for non-player categories (coaches,
      ipl_champions, team_owners).

  check_ambiguity(ipl_data, categories) -> list[tuple[str, str, str]]
      For each placed item, check if it's also valid in another category.
      Returns list of (item_name, placed_in_color, also_qualifies_for_color).
"""

from collections import defaultdict

from category_generators import _resolve_team
from generators.cross_team import LEGENDS_INDIA, LEGENDS_OVERSEAS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_candidate_pool(ipl_data: dict, spec: str) -> set[str]:
    """
    Return the full set of valid player names for a spec string.
    No sampling, no exclusions applied. Returns set() for non-player
    categories or on any error.
    """
    parts = spec.split(":")
    category_type = parts[0]
    params = parts[1:]

    fn = _POOL_DISPATCH.get(category_type)
    if fn is None:
        return set()
    try:
        return fn(ipl_data, params)
    except Exception:
        return set()


def check_ambiguity(ipl_data: dict,
                    categories: list[dict]) -> list[tuple[str, str, str]]:
    """
    Check for item-level ambiguity across categories.

    Input:
        categories — list of {"color", "title", "items": [...], "spec"}

    Output:
        list of (item_name, placed_in_color, also_qualifies_for_color)
        Empty list means no ambiguity detected.
    """
    pools = {
        cat["color"]: get_candidate_pool(ipl_data, cat.get("spec", ""))
        for cat in categories
    }

    conflicts: list[tuple[str, str, str]] = []
    for cat in categories:
        color_i = cat["color"]
        for item in cat.get("items", []):
            for other_cat in categories:
                color_j = other_cat["color"]
                if color_i == color_j:
                    continue
                if item in pools[color_j]:
                    conflicts.append((item, color_i, color_j))

    return conflicts


# ---------------------------------------------------------------------------
# Per-spec pool functions (mirror generator logic, return full candidate set)
# ---------------------------------------------------------------------------

def _pool_award(ipl_data: dict, params: list, award_type: str) -> set[str]:
    return {
        a["player_name"]
        for a in ipl_data.get("awards", [])
        if a["type"] == award_type
    }


def _pool_orange_cap(ipl_data, params):
    return _pool_award(ipl_data, params, "orange_cap")


def _pool_purple_cap(ipl_data, params):
    return _pool_award(ipl_data, params, "purple_cap")


def _pool_player_of_tournament(ipl_data, params):
    return _pool_award(ipl_data, params, "player_of_tournament")


def _pool_costliest_player(ipl_data, params):
    return _pool_award(ipl_data, params, "costliest_player")


def _pool_winning_captain(ipl_data, params):
    return _pool_award(ipl_data, params, "winning_captain")


def _pool_team_players(ipl_data, params):
    if len(params) < 2:
        return set()
    team_name = _resolve_team(ipl_data, params[0])
    try:
        season = int(params[1])
    except ValueError:
        return set()
    return {
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name and pt["season"] == season
    }


def _pool_team_all_seasons(ipl_data, params):
    if len(params) < 1:
        return set()
    team_name = _resolve_team(ipl_data, params[0])
    return {
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name
    }


def _pool_winning_squad(ipl_data, params):
    if len(params) < 1:
        return set()
    try:
        season = int(params[0])
    except ValueError:
        return set()
    winner = next(
        (w for w in ipl_data.get("ipl_wins", []) if w["season"] == season),
        None,
    )
    if winner is None:
        return set()
    team_name = winner["team_name"]
    return {
        pt["player_name"]
        for pt in ipl_data.get("player_teams", [])
        if pt["team_name"] == team_name and pt["season"] == season
    }


def _pool_top_run_scorers(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("batting_career_stats", [])}


def _pool_top_wicket_takers(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("bowling_career_stats", [])}


def _pool_most_fifties(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("batting_career_stats", [])}


def _pool_most_matches(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("batting_career_stats", [])}


def _pool_high_strike_rate(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("high_strike_rate_batsmen", [])}


def _pool_highest_batting_avg(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("highest_batting_avg", [])}


def _pool_catches_by_fielder(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("catches_by_fielder", [])}


def _pool_dismissals_by_keeper(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("dismissals_by_keeper", [])}


def _pool_allrounders(ipl_data, params):
    return {e["name"] for e in ipl_data.get("allrounders", [])}


def _pool_most_ducks(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("most_ducks", [])}


def _pool_fifers(ipl_data, params):
    return {e["player_name"] for e in ipl_data.get("five_wicket_hauls", [])}


def _pool_batting_records(ipl_data, params):
    return {e["player"] for e in ipl_data.get("records", {}).get("batting_records", [])}


def _pool_bowling_records(ipl_data, params):
    return {e["player"] for e in ipl_data.get("records", {}).get("bowling_records", [])}


def _pool_season_records(ipl_data, params):
    return {e["player"] for e in ipl_data.get("records", {}).get("season_records", [])}


def _pool_fielding_records(ipl_data, params):
    return {e["player"] for e in ipl_data.get("records", {}).get("fielding_records", [])}


def _pool_team_legends_batting(ipl_data, params):
    """Mirrors gen_team_legends_batting — must replicate the top-12 cap."""
    if len(params) < 1:
        return set()
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
    top12 = sorted(bat_map, key=lambda n: bat_map[n], reverse=True)[:12]
    return set(top12)


def _pool_team_legends_bowling(ipl_data, params):
    """Mirrors gen_team_legends_bowling — must replicate the top-12 cap."""
    if len(params) < 1:
        return set()
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
    top12 = sorted(bowl_map, key=lambda n: bowl_map[n], reverse=True)[:12]
    return set(top12)


def _pool_country(ipl_data, params):
    if len(params) < 1:
        return set()
    country = params[0].replace("_", " ")
    return {
        e["name"]
        for e in ipl_data.get("foreign_players", [])
        if e.get("country") == country
    }


def _pool_state(ipl_data, params):
    if len(params) < 1:
        return set()
    state = params[0].replace("_", " ")
    entries = ipl_data.get("india_state_wise", {}).get(state, [])
    return {e["name"] for e in entries}


def _pool_ranji(ipl_data, params):
    if len(params) < 1:
        return set()
    ranji_team = params[0].replace("_", " ")
    entries = ipl_data.get("ranji_team_wise", {}).get(ranji_team, [])
    return {e["name"] for e in entries}


def _pool_played_both(ipl_data, params):
    if len(params) < 2:
        return set()
    team1 = _resolve_team(ipl_data, params[0])
    team2 = _resolve_team(ipl_data, params[1])
    player_teams: dict[str, set[str]] = defaultdict(set)
    for pt in ipl_data.get("player_teams", []):
        player_teams[pt["player_name"]].add(pt["team_name"])
    return {
        name for name, teams in player_teams.items()
        if team1 in teams and team2 in teams
    }


def _pool_multi_team(ipl_data, params):
    if len(params) < 1:
        return set()
    try:
        min_teams = int(params[0])
    except ValueError:
        return set()
    return {
        e["player_name"]
        for e in ipl_data.get("multi_team_players", [])
        if e.get("team_count", 0) >= min_teams
    }


def _pool_longest_serving(ipl_data, params):
    season_counts: dict[str, set[int]] = defaultdict(set)
    for pt in ipl_data.get("player_teams", []):
        season_counts[pt["player_name"]].add(pt["season"])
    ranked = sorted(season_counts.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    return {name for name, _ in ranked}


def _pool_legends(ipl_data, params):
    if len(params) < 1:
        return set()
    known = {pt["player_name"] for pt in ipl_data.get("player_teams", [])}
    if params[0] == "india":
        return {name for name in LEGENDS_INDIA if name in known}
    if params[0] == "overseas":
        return {name for name in LEGENDS_OVERSEAS if name in known}
    return set()


def _pool_empty(ipl_data, params):
    return set()


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_POOL_DISPATCH = {
    "orange_cap":           _pool_orange_cap,
    "purple_cap":           _pool_purple_cap,
    "player_of_tournament": _pool_player_of_tournament,
    "costliest_player":     _pool_costliest_player,
    "winning_captain":      _pool_winning_captain,
    "team_players":         _pool_team_players,
    "team_all_seasons":     _pool_team_all_seasons,
    "winning_squad":        _pool_winning_squad,
    "top_run_scorers":      _pool_top_run_scorers,
    "top_wicket_takers":    _pool_top_wicket_takers,
    "most_fifties":         _pool_most_fifties,
    "most_matches":         _pool_most_matches,
    "high_strike_rate":     _pool_high_strike_rate,
    "highest_batting_avg":  _pool_highest_batting_avg,
    "catches_by_fielder":   _pool_catches_by_fielder,
    "dismissals_by_keeper": _pool_dismissals_by_keeper,
    "allrounders":          _pool_allrounders,
    "most_ducks":           _pool_most_ducks,
    "fifers":               _pool_fifers,
    "batting_records":      _pool_batting_records,
    "bowling_records":      _pool_bowling_records,
    "season_records":       _pool_season_records,
    "fielding_records":     _pool_fielding_records,
    "team_legends_batting": _pool_team_legends_batting,
    "team_legends_bowling": _pool_team_legends_bowling,
    "country":              _pool_country,
    "state":                _pool_state,
    "ranji":                _pool_ranji,
    "played_both":          _pool_played_both,
    "multi_team":           _pool_multi_team,
    "longest_serving":      _pool_longest_serving,
    "legends":              _pool_legends,
    # Non-player categories
    "coaches":              _pool_empty,
    "head_coaches":         _pool_empty,
    "batting_coaches":      _pool_empty,
    "bowling_coaches":      _pool_empty,
    "fielding_coaches":     _pool_empty,
    "ipl_champions":        _pool_empty,
    "team_owners":          _pool_empty,
}
