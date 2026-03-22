"""
generators/cross_team.py — Cross-team and legacy category generators.

  played_both:TEAM1:TEAM2  — players who played for both teams
  multi_team:N+            — players who played for N+ teams
  longest_serving          — players with the most IPL seasons
  legends:india            — curated Indian Test legends in IPL
  legends:overseas         — curated foreign Test legends in IPL
"""

from collections import defaultdict
from category_generators import _pick, _resolve_team


# ---------------------------------------------------------------------------
# Cross-team generators
# ---------------------------------------------------------------------------

def gen_played_both(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players who have played for both TEAM1 and TEAM2.

    Params: [team1_code, team2_code]
    Example: played_both:CSK:MI

    Source: ipl_data['player_teams'] — computed at runtime.
    Notable pools: CSK-RCB(23), KKR-MI(26), CSK-MI(17)
    """
    if len(params) < 2:
        raise ValueError(
            "played_both requires 2 params: team1 and team2. Example: played_both:CSK:MI"
        )

    team1 = _resolve_team(ipl_data, params[0])
    team2 = _resolve_team(ipl_data, params[1])

    # Build per-player team sets
    player_teams: dict[str, set[str]] = defaultdict(set)
    for pt in ipl_data.get("player_teams", []):
        player_teams[pt["player_name"]].add(pt["team_name"])

    names = [
        name for name, teams in player_teams.items()
        if team1 in teams and team2 in teams
    ]

    if not names:
        raise ValueError(
            f"played_both: no players found who played for both '{team1}' and '{team2}'."
        )

    items = _pick(names, exclude, f"played_both:{team1}:{team2}")
    short1, short2 = params[0], params[1]
    return {"title": f"Played for Both {short1} & {short2}", "items": items}


def gen_multi_team(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players who have played for N or more IPL teams (nomads).

    Params: [N]  — minimum team count (integer)
    Example: multi_team:5

    Source: ipl_data['multi_team_players'] — pre-computed list with 'team_count'.
    Total pool: 37 players (all with 5+ teams). Filter by team_count >= N.
    """
    if len(params) < 1:
        raise ValueError("multi_team requires 1 param: min team count. Example: multi_team:5")

    try:
        min_teams = int(params[0])
    except ValueError:
        raise ValueError(f"multi_team: invalid count '{params[0]}' (must be an integer)")

    entries = ipl_data.get("multi_team_players", [])
    names = [
        e["player_name"] for e in entries
        if e.get("team_count", 0) >= min_teams
    ]

    if not names:
        raise ValueError(
            f"multi_team: no players found with {min_teams}+ teams. "
            "Try a lower threshold."
        )

    items = _pick(names, exclude, f"multi_team:{min_teams}+")
    return {"title": f"Played for {min_teams}+ IPL Teams", "items": items}


def gen_longest_serving(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 players with the most distinct IPL seasons played.

    Source: ipl_data['player_teams'] — count distinct seasons per player.
    """
    season_counts: dict[str, set[int]] = defaultdict(set)
    for pt in ipl_data.get("player_teams", []):
        season_counts[pt["player_name"]].add(pt["season"])

    # Sort by number of seasons descending, keep top 20 as the pool
    ranked = sorted(season_counts.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    names = [name for name, _ in ranked]

    items = _pick(names, exclude, "longest_serving")
    return {"title": "Longest Serving IPL Players", "items": items}


# ---------------------------------------------------------------------------
# Legend generators — curated editorial lists
# ---------------------------------------------------------------------------

# Indian Test legends who played IPL (curated, not auto-derived)
_LEGENDS_INDIA = [
    "SR Tendulkar",   # MI 2008-2013
    "R Dravid",       # RR, RCB 2008-2013
    "SC Ganguly",     # KKR 2008-2012
    "VVS Laxman",     # DCH, SRH 2008-2012
    "A Kumble",       # RCB, MI 2008-2010
    "V Sehwag",       # DD, KXIP 2008-2015
    "Yuvraj Singh",   # KXIP, MI, RCB, PBKS, SRH 2008-2019
    "Harbhajan Singh",# MI, CSK 2008-2019
    "Z Khan",         # MI, RCB, DC 2008-2013
    "IK Pathan",      # CSK, KKR, PBKS, RPS, SRH 2008-2017
    "MS Dhoni",       # CSK 2008-2023 (included here for legend status)
    "YK Pathan",      # RR, KKR 2008-2017
]

# Foreign Test legends who played IPL (curated, not auto-derived)
_LEGENDS_OVERSEAS = [
    "SK Warne",       # RR 2008-2011
    "AC Gilchrist",   # DCH 2008-2013
    "RT Ponting",     # KKR, MI 2008-2013
    "JH Kallis",      # RCB, KKR 2008-2014
    "KP Pietersen",   # RCB, DC, DD 2009-2014
    "M Muralitharan", # CSK, RCB 2008-2014
    "DL Vettori",     # RCB 2008-2012
    "A Symonds",      # DCH, MI 2008-2011
    "SM Pollock",     # MI 2008
    "MEK Hussey",     # CSK 2008-2013
    "CL Cairns",      # KKR 2008
    "MF Maharoof",    # CSK, KKR 2008-2012
    "Shoaib Akhtar",  # KKR 2008
    "BC Lara",        # KKR 2009
    "WW Hinds",       # RR 2008-2009
]


def _gen_legends(ipl_data: dict, curated_list: list[str],
                 label: str, exclude: set) -> dict:
    """Shared logic for legends generators — verify names exist in player_teams."""
    known = {pt["player_name"] for pt in ipl_data.get("player_teams", [])}
    available = [name for name in curated_list if name in known]

    if len(available) < 4:
        raise ValueError(
            f"legends:{label}: only {len(available)} legend(s) found in player data "
            f"(need 4). Check player name spellings against ipl_data player_teams."
        )

    items = _pick(available, exclude, f"legends:{label}")
    return items


def gen_legends_india(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 Indian Test legends who played IPL.
    Source: Curated hardcoded list, verified against ipl_data['player_teams'].
    """
    items = _gen_legends(ipl_data, _LEGENDS_INDIA, "india", exclude)
    return {"title": "Indian Legends of IPL", "items": items}


def gen_legends_overseas(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Pick 4 foreign Test legends who played IPL.
    Source: Curated hardcoded list, verified against ipl_data['player_teams'].
    """
    items = _gen_legends(ipl_data, _LEGENDS_OVERSEAS, "overseas", exclude)
    return {"title": "Overseas Legends of IPL", "items": items}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GENERATORS = {
    "played_both":      gen_played_both,
    "multi_team":       gen_multi_team,
    "longest_serving":  gen_longest_serving,
    "legends": {
        "india":    gen_legends_india,
        "overseas": gen_legends_overseas,
    },
}
