"""
generators/season_stats.py — Current-season live stats generators.

Reads from season_stats_2026.json (one directory up from generators/).
Completely independent of ipl_data.json — update the JSON file directly
as the season progresses. No dedup rules apply to these category types.
"""

import json
from pathlib import Path

from category_generators import _pick

_SEASON_FILE = Path(__file__).parent.parent / "season_stats_2026.json"


def _load() -> dict:
    if not _SEASON_FILE.exists():
        raise ValueError(
            f"season_stats_2026.json not found at {_SEASON_FILE}. "
            "Create the file with current season data."
        )
    with _SEASON_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _from_season(key: str, title: str, ipl_data: dict, params: list, exclude: set) -> dict:
    data = _load()
    entries = data.get(key, [])
    if not entries:
        raise ValueError(
            f"'{key}' is empty in season_stats_2026.json. "
            "Update the file with current season player data."
        )
    names = list(dict.fromkeys(e["player_name"] for e in entries))
    if len(names) < 4:
        raise ValueError(
            f"'{key}' in season_stats_2026.json has only {len(names)} player(s) — need 4."
        )
    # Intentionally ignore exclude: season stats are meant to repeat across puzzles.
    return {"title": title, "items": names[:4]}


def gen_top_run_getters(ipl_data: dict, params: list, exclude: set) -> dict:
    return _from_season(
        "top_run_getters",
        "IPL 2026 Top Run Getters",
        ipl_data, params, exclude,
    )


def gen_top_run_scorer_top4(ipl_data: dict, params: list, exclude: set) -> dict:
    return _from_season(
        "top_run_scorer_top4_teams",
        "Leading Run Scorer from Each Top-4 Team (IPL 2026)",
        ipl_data, params, exclude,
    )


def gen_top_wicket_taker_top4(ipl_data: dict, params: list, exclude: set) -> dict:
    return _from_season(
        "top_wicket_taker_top4_teams",
        "Leading Wicket Taker from Each Top-4 Team (IPL 2026)",
        ipl_data, params, exclude,
    )


GENERATORS = {
    "top_run_getters":       gen_top_run_getters,
    "top_run_scorer_top4":   gen_top_run_scorer_top4,
    "top_wicket_taker_top4": gen_top_wicket_taker_top4,
}
