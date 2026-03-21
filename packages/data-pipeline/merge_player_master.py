"""
merge_player_master.py

Merges home_country / state / ranji_team data from:
  1. packages/data-pipeline/data/players_master_partial_with_country_state_renji.json
  2. packages/data-pipeline/data/batches/*enriched*.json

onto the base players_master.json and writes a new file.

Output file: packages/data-pipeline/data/players_master_enriched.json
  (or players_master_enriched_2.json etc. if it already exists — never overwrites)

Field mapping (enriched batch → output):
  name          → Player  (lookup key)
  full_name     → full_name
  home_country  → country
  state         → state
  ranji_team    → ranji_team

"N/A" values from enriched batches are treated as not-yet-populated (kept as-is).
"""

import json
import glob
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BATCHES_DIR = os.path.join(DATA_DIR, "batches")

MASTER_PATH   = os.path.join(DATA_DIR, "players_master.json")
PARTIAL_PATH  = os.path.join(DATA_DIR, "players_master_partial_with_country_state_renji.json")
OUTPUT_BASE   = os.path.join(DATA_DIR, "players_master_enriched.json")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def unique_output_path(base_path: str) -> str:
    """Return base_path if it doesn't exist, otherwise base_path_2, _3 …"""
    if not os.path.exists(base_path):
        return base_path
    root, ext = os.path.splitext(base_path)
    counter = 2
    while True:
        candidate = f"{root}_{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def normalise_value(v):
    """Return None for blank/N/A sentinels, else the original value."""
    if v is None:
        return None
    if isinstance(v, str) and v.strip().lower() in ("n/a", "", "none"):
        return None
    if isinstance(v, list) and all(
        isinstance(i, str) and i.strip().lower() in ("n/a", "", "none") for i in v
    ):
        return None
    return v


# ---------------------------------------------------------------------------
# load sources
# ---------------------------------------------------------------------------

def load_master() -> list[dict]:
    with open(MASTER_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_partial() -> dict[str, dict]:
    """Returns {Player: {full_name, country, state, ranji_team}}"""
    with open(PARTIAL_PATH, encoding="utf-8") as f:
        records = json.load(f)

    lookup: dict[str, dict] = {}
    for r in records:
        name = r.get("Player")
        if not name:
            continue
        lookup[name] = {
            "full_name":  normalise_value(r.get("full_name")),
            "country":    normalise_value(r.get("country")),
            "state":      normalise_value(r.get("state")),
            "ranji_team": normalise_value(r.get("ranji_team")),
        }
    return lookup


def load_enriched_batches() -> dict[str, dict]:
    """Returns {name: {full_name, country, state, ranji_team}} from all enriched batch files."""
    pattern = os.path.join(BATCHES_DIR, "*enriched*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print("  [warn] No enriched batch files found in", BATCHES_DIR)
        return {}

    lookup: dict[str, dict] = {}
    for path in files:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)

        for r in records:
            name = r.get("name")
            if not name:
                continue
            # Convert ranji_team string → list for consistency with partial file
            ranji = normalise_value(r.get("ranji_team"))
            if isinstance(ranji, str):
                ranji = [ranji]

            lookup[name] = {
                "full_name":  normalise_value(r.get("full_name")),
                "country":    normalise_value(r.get("home_country")),
                "state":      normalise_value(r.get("state")),
                "ranji_team": ranji,
            }

        print(f"  Loaded {len(records):3d} records from {os.path.basename(path)}")

    return lookup


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def merge(master: list[dict], partial: dict[str, dict], enriched: dict[str, dict]) -> list[dict]:
    """
    Priority (highest wins):
      1. enriched batch  (most recently curated)
      2. partial file    (previously curated)
      3. keep as missing

    Rules:
      - full_name and country are set for all players.
      - state and ranji_team are set ONLY for Indian players (country == "India").
    """
    merged = []
    stats = {"enriched": 0, "partial": 0, "missing": 0}

    for player in master:
        name = player["Player"]
        out = dict(player)  # copy all base fields

        e = enriched.get(name, {})
        p = partial.get(name, {})

        def pick(field: str):
            return e.get(field) or p.get(field)

        full_name  = pick("full_name")
        country    = pick("country")

        if full_name: out["full_name"] = full_name
        if country:   out["country"]   = country

        # state and ranji_team only for Indian players
        is_india = (country or "").strip().lower() == "india"
        if is_india:
            state      = pick("state")
            ranji_team = pick("ranji_team")
            if state:      out["state"]      = state
            if ranji_team: out["ranji_team"] = ranji_team

        # track coverage
        if country:
            stats["enriched" if name in enriched else "partial"] += 1
        else:
            stats["missing"] += 1

        merged.append(out)

    return merged, stats


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("Loading sources …")
    master   = load_master()
    partial  = load_partial()
    enriched = load_enriched_batches()

    print(f"\n  Base master  : {len(master)} players")
    print(f"  Partial file : {len(partial)} entries")
    print(f"  Enriched     : {len(enriched)} entries")

    print("\nMerging …")
    result, stats = merge(master, partial, enriched)

    output_path = unique_output_path(OUTPUT_BASE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    india     = [p for p in result if (p.get("country") or "").lower() == "india"]
    overseas  = [p for p in result if p.get("country") and (p.get("country") or "").lower() != "india"]
    no_country = [p for p in result if not p.get("country")]

    india_missing_state = [p["Player"] for p in india if not p.get("state")]
    india_missing_ranji = [p["Player"] for p in india if not p.get("ranji_team")]
    overseas_with_state = [p["Player"] for p in overseas if p.get("state")]
    overseas_with_ranji = [p["Player"] for p in overseas if p.get("ranji_team")]

    print(f"\nDone. Written to: {output_path}")
    print(f"\n  Country populated from enriched batches : {stats['enriched']}")
    print(f"  Country populated from partial file     : {stats['partial']}")
    print(f"  Still missing country                   : {stats['missing']}")
    print(f"\n  Indian players        : {len(india)}")
    print(f"    missing state       : {len(india_missing_state)}")
    print(f"    missing ranji_team  : {len(india_missing_ranji)}")
    print(f"  Overseas players      : {len(overseas)}")
    print(f"  No country yet        : {len(no_country)}")

    if overseas_with_state:
        print(f"\n  [warn] Overseas players with state set (should be none): {overseas_with_state}")
    if overseas_with_ranji:
        print(f"  [warn] Overseas players with ranji_team set (should be none): {overseas_with_ranji}")


if __name__ == "__main__":
    main()
