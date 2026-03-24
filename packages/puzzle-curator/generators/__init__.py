"""
generators/__init__.py — Combines all generator modules into a single GENERATORS dict.

Handles special dispatch cases:
  - legends:india / legends:overseas  (sub-keyed in cross_team)
  - coaches:SEASON vs coaches:TEAM:SEASON  (param count determines which generator)
"""

from .stats import GENERATORS as _STATS
from .geographic import GENERATORS as _GEO
from .cross_team import GENERATORS as _CROSS, gen_legends_india, gen_legends_overseas
from .management import GENERATORS as _MGMT, gen_coaches_team_season


def _gen_legends_dispatch(ipl_data: dict, params: list, exclude: set) -> dict:
    """
    Dispatch legends:india or legends:overseas based on first param.
    Spec format: legends:india  or  legends:overseas
    """
    if not params:
        raise ValueError(
            "legends requires 1 param: 'india' or 'overseas'. "
            "Example: legends:india"
        )
    variant = params[0].lower()
    if variant == "india":
        return gen_legends_india(ipl_data, params[1:], exclude)
    elif variant == "overseas":
        return gen_legends_overseas(ipl_data, params[1:], exclude)
    else:
        raise ValueError(
            f"legends: unknown variant '{params[0]}'. Use 'india' or 'overseas'."
        )


# Build combined registry
GENERATORS: dict = {
    **_STATS,
    **_GEO,
    "played_both":     _CROSS["played_both"],
    "multi_team":      _CROSS["multi_team"],
    "longest_serving": _CROSS["longest_serving"],
    "legends":         _gen_legends_dispatch,
    "winning_squad":   _MGMT["winning_squad"],
}
