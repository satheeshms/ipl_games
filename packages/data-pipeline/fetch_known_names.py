"""
fetch_known_names.py — Collect known/popular display names for initial-style canonical player names.

Sources (in priority order):
  1. known_names_override.json  — manual curator overrides, never overwritten by this script
  2. Cricsheet People Register  — people.csv from cricsheet.org (downloaded if absent)
  3. Wikipedia API              — search + page summary fallback
  4. Wikidata SPARQL            — structured fallback for still-unmatched players

Output: data/known_names.json
  {
    "<canonical_name>": {
      "known_name": "Full Known Name",
      "source": "override | cricsheet | wikipedia | wikidata",
      "confidence": "high | low"
    }
  }

Only initial-style names (first token ≤ 2 chars) are processed — names already in full form
(e.g. "Rohit Sharma") are skipped since they need no display alias.

Usage:
    cd packages/data-pipeline
    python fetch_known_names.py
    python fetch_known_names.py --db data/ipl.db --output data/known_names.json
    python fetch_known_names.py --skip-wikipedia --skip-wikidata   # Cricsheet only
    python fetch_known_names.py --dry-run                          # print results, don't write
"""

import argparse
import csv
import io
import json
import re
import sqlite3
import time
import unicodedata
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRICSHEET_URL = "https://cricsheet.org/register/people.csv"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "ipl-games-known-names/1.0 (https://github.com/satheeshms/ipl_games; educational cricket puzzle game)"
}

# Wikidata: occupation = cricketer (Q12299841)
WIKIDATA_QUERY = """
SELECT ?playerLabel WHERE {{
  ?player wdt:P106 wd:Q12299841 .
  ?player rdfs:label ?playerLabel .
  FILTER(LANG(?playerLabel) = "en")
  FILTER(LCASE(?playerLabel) = "{name_lower}")
}}
LIMIT 5
"""

# Seconds between Wikipedia/Wikidata requests
WIKI_DELAY = 1.0


# ---------------------------------------------------------------------------
# Name parsing helpers
# ---------------------------------------------------------------------------

def _normalise(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def parse_canonical(name: str) -> tuple[list[str], str]:
    """
    Split a canonical name like "SK Yadav" or "F du Plessis" into
    (initials, surname) where initials are the individual characters from
    leading tokens of length ≤ 2, and surname is the remaining tokens joined.

    "SK Yadav"     -> (["S", "K"], "Yadav")
    "BB McCullum"  -> (["B", "B"], "McCullum")
    "F du Plessis" -> (["F"], "du Plessis")
    "A Nel"        -> (["A"], "Nel")
    """
    tokens = name.strip().split()
    initials: list[str] = []
    rest: list[str] = []
    consuming_initials = True
    for tok in tokens:
        if consuming_initials and len(tok) <= 2 and tok[0].isupper():
            # Expand "SK" -> ["S", "K"], "F" -> ["F"]
            initials.extend(list(tok.upper()))
        else:
            consuming_initials = False
            rest.append(tok)
    return initials, " ".join(rest)


def name_matches_initials(full_name: str, initials: list[str], surname: str) -> bool:
    """
    Check whether `full_name` (e.g. "Suryakumar Yadav") is consistent with
    the given initials and surname.

    Rules:
    - Surname must match the tail of the full name (case-insensitive).
    - The first initial (initials[0]) must match the first character of the
      Cricsheet first name. Only the first initial is required — Cricsheet
      entries frequently omit middle names (e.g. "Mitchell Starc" rather than
      "Mitchell Aaron Starc"), so checking all initials would cause too many
      false negatives. Uniqueness of the surname+first-initial combination
      drives confidence, not exhaustive initial matching.
    """
    if not initials:
        return False

    norm_full = _normalise(full_name)
    norm_surname = _normalise(surname)

    # Surname check — tail of normalised full name
    if not norm_full.endswith(norm_surname):
        return False

    # Strip surname to get first-name portion
    first_part = norm_full[: len(norm_full) - len(norm_surname)].strip()
    if not first_part:
        return False

    # First initial of canonical must match first character of the full first name
    return first_part[0] == initials[0].lower()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def load_initial_style_names(db_path: str) -> list[str]:
    """Return all player names whose first token is ≤ 2 chars (initial-style)."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT name FROM players ORDER BY name").fetchall()
    conn.close()
    return [r[0] for r in rows if r[0] and len(r[0].split()[0]) <= 2]


# ---------------------------------------------------------------------------
# Override file
# ---------------------------------------------------------------------------

def load_override(path: str) -> dict[str, str]:
    """Load manual overrides: { canonical_name: known_name }. Returns {} if absent."""
    p = Path(path)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Source 1 — Cricsheet People Register
# ---------------------------------------------------------------------------

def download_cricsheet(dest_path: str, delay: float = 1.0) -> bool:
    """Download people.csv from cricsheet.org if not already present. Returns True on success."""
    p = Path(dest_path)
    if p.exists():
        print(f"  [cricsheet] Using cached {dest_path}")
        return True
    print(f"  [cricsheet] Downloading people.csv from cricsheet.org …")
    try:
        resp = requests.get(CRICSHEET_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(resp.content)
        print(f"  [cricsheet] Saved to {dest_path} ({len(resp.content):,} bytes)")
        return True
    except requests.RequestException as e:
        print(f"  [cricsheet] Download failed: {e}")
        return False


def build_cricsheet_index(csv_path: str) -> dict[str, list[dict]]:
    """
    Parse Cricsheet people.csv into a dict keyed by normalised surname.
    Each value is a list of { name, cricinfo_id }.
    """
    index: dict[str, list[dict]] = {}
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_name = (row.get("name") or "").strip()
            if not full_name:
                continue
            # Last token of the name = surname
            tokens = full_name.split()
            # Handle compound surnames like "du Plessis" (tokens after first-name initials)
            # For indexing purposes we use the last token only as the primary key
            surname_key = _normalise(tokens[-1])
            entry = {
                "name": full_name,
                "cricinfo_id": (row.get("cricinfo_id") or "").strip(),
            }
            index.setdefault(surname_key, []).append(entry)
    return index


def match_cricsheet(
    canonical: str,
    index: dict[str, list[dict]],
) -> tuple[str | None, str]:
    """
    Try to match `canonical` (e.g. "SK Yadav") against the Cricsheet index.
    Returns (known_name, confidence) or (None, "").
    """
    initials, surname = parse_canonical(canonical)
    if not surname:
        return None, ""

    # Look up by last surname token (handles "du Plessis" -> key "plessis")
    last_token = _normalise(surname.split()[-1])
    candidates = index.get(last_token, [])

    # Filter: full surname must match + initials consistent
    matches = [
        c for c in candidates
        if name_matches_initials(c["name"], initials, surname)
    ]

    if len(matches) == 1:
        return matches[0]["name"], "high"
    if len(matches) > 1:
        # Multiple plausible matches — return the first but flag as low confidence
        return matches[0]["name"], "low"
    return None, ""


# ---------------------------------------------------------------------------
# Source 2 — Wikipedia API
# ---------------------------------------------------------------------------

def _wikipedia_page_is_cricketer(title: str) -> tuple[str | None, bool]:
    """
    Fetch the Wikipedia page summary for `title` and return
    (clean_title, is_cricketer).  Strips disambiguation suffixes like
    "(cricketer)" or "(South African cricketer)" from the returned title.
    """
    try:
        resp = requests.get(
            WIKIPEDIA_SUMMARY_URL.format(title=requests.utils.quote(title)),
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            return None, False
        data = resp.json()
    except requests.RequestException:
        return None, False

    time.sleep(WIKI_DELAY)

    description = (data.get("description") or "").lower()
    extract = (data.get("extract") or "").lower()
    is_cricketer = any(
        word in description or word in extract[:400]
        for word in ("cricketer", "cricket", "ipl", "indian premier league", "batsman", "bowler")
    )
    if not is_cricketer:
        return None, False

    # Strip disambiguation suffix: "David Miller (cricketer)" -> "David Miller"
    raw = data.get("title") or title
    clean = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
    return clean, True


def match_wikipedia(canonical: str) -> tuple[str | None, str]:
    """
    Search Wikipedia by SURNAME ONLY (not the full abbreviated canonical name),
    then filter candidates whose first letter matches the canonical's first initial.
    This is far more reliable than searching the abbreviated form directly.

    Returns (known_name, confidence) or (None, "").
    """
    initials, surname = parse_canonical(canonical)
    if not initials or not surname:
        return None, ""

    first_init = initials[0].upper()
    # Use only the last token of a compound surname as the search term to
    # avoid over-constraining (e.g. "du Plessis" -> search "Plessis")
    search_surname = surname.split()[-1]

    try:
        resp = requests.get(
            WIKIPEDIA_SEARCH_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{search_surname} cricketer",
                "srlimit": 10,
                "format": "json",
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
    except requests.RequestException as e:
        print(f"    [wikipedia] Search error for '{canonical}': {e}")
        return None, ""

    time.sleep(WIKI_DELAY)

    # Filter results: title must contain the surname AND start with the first initial
    candidates = []
    for result in results:
        title = result.get("title", "")
        # Strip disambiguation suffix for comparison
        base = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
        tokens = base.split()
        if not tokens:
            continue
        if surname.lower() not in base.lower():
            continue
        if tokens[0][0].upper() != first_init:
            continue
        candidates.append(title)

    if not candidates:
        return None, ""

    # Verify the top candidate via page summary (confirms it's actually a cricketer)
    for title in candidates[:3]:
        clean, ok = _wikipedia_page_is_cricketer(title)
        if ok and clean:
            _, surn = parse_canonical(canonical)
            confidence = "high" if len(candidates) == 1 else "low"
            return clean, confidence

    return None, ""


# ---------------------------------------------------------------------------
# Source 3 — Wikidata SPARQL
# ---------------------------------------------------------------------------

def match_wikidata(canonical: str) -> tuple[str | None, str]:
    """
    Query Wikidata for cricketers (P106=Q12299841) whose English label contains
    the canonical surname, then filter by first initial.
    Returns (known_name, confidence) or (None, "").
    """
    initials, surname = parse_canonical(canonical)
    if not initials or not surname:
        return None, ""

    # Use last token of compound surname for the CONTAINS filter
    search_surname = _normalise(surname.split()[-1])

    sparql = f"""
SELECT ?playerLabel WHERE {{
  ?player wdt:P106 wd:Q12299841 .
  ?player rdfs:label ?playerLabel .
  FILTER(LANG(?playerLabel) = "en")
  FILTER(CONTAINS(LCASE(?playerLabel), "{search_surname}"))
}}
LIMIT 30
"""
    try:
        resp = requests.get(
            WIKIDATA_SPARQL_URL,
            params={"query": sparql, "format": "json"},
            headers={**HEADERS, "Accept": "application/sparql-results+json"},
            timeout=30,
        )
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
    except requests.RequestException as e:
        print(f"    [wikidata] Query error for '{canonical}': {e}")
        return None, ""

    time.sleep(WIKI_DELAY)

    candidates = [b["playerLabel"]["value"] for b in bindings]
    # Filter by surname presence and first initial
    first_init = initials[0].lower()
    consistent = [
        c for c in candidates
        if surname.lower() in c.lower() and c.split()[0][0].lower() == first_init
    ]

    if len(consistent) == 1:
        return consistent[0], "high"
    if len(consistent) > 1:
        return consistent[0], "low"
    return None, ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch known player names for IPL puzzle display.")
    parser.add_argument("--db", default="data/ipl.db", help="Path to ipl.db")
    parser.add_argument("--output", default="data/known_names.json", help="Output JSON path")
    parser.add_argument("--override", default="data/known_names_override.json", help="Manual override JSON")
    parser.add_argument("--cricsheet", default="data/cricsheet_people.csv", help="Cricsheet people.csv path")
    parser.add_argument("--skip-wikipedia", action="store_true", help="Skip Wikipedia fallback")
    parser.add_argument("--skip-wikidata", action="store_true", help="Skip Wikidata fallback")
    parser.add_argument("--unresolved", default="data/known_names_unresolved.json",
                        help="Output path for names that could not be expanded")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing output file")
    args = parser.parse_args()

    output_path = Path(args.output)

    # ── Load manual overrides ──
    overrides = load_override(args.override)
    print(f"Loaded {len(overrides)} manual overrides from {args.override}")

    # ── Load candidate names from DB ──
    names = load_initial_style_names(args.db)
    print(f"Found {len(names)} initial-style player names in DB")

    # ── Build Cricsheet index ──
    cricsheet_ok = download_cricsheet(args.cricsheet)
    cricsheet_index: dict[str, list[dict]] = {}
    if cricsheet_ok:
        cricsheet_index = build_cricsheet_index(args.cricsheet)
        print(f"Cricsheet index built: {sum(len(v) for v in cricsheet_index.values()):,} entries")

    # ── Load existing resolved output (resume-safe) ──
    # Only keep entries where the known_name actually differs from the canonical
    # name — discard any stale same-name entries written by older versions.
    existing: dict[str, dict] = {}
    if output_path.exists():
        with output_path.open(encoding="utf-8") as f:
            raw = json.load(f)
        existing = {k: v for k, v in raw.items() if v.get("known_name") != k}
        print(f"Loaded {len(existing)} existing resolved entries from {args.output}")

    # ── Process each name ──
    resolved: dict[str, dict] = dict(existing)   # canonical -> entry (expanded names only)
    unresolved: list[str] = []                    # canonical names with no expansion found
    stats = {"override": 0, "cricsheet_high": 0, "wikipedia_high": 0, "wikidata_high": 0,
             "no_expansion": 0, "unresolved": 0, "skipped": 0}

    for canonical in names:
        # Already resolved with high confidence in a previous run — skip
        if canonical in existing and existing[canonical]["confidence"] == "high":
            stats["skipped"] += 1
            continue

        # 1. Manual override — always wins; skip if value is same as canonical
        if canonical in overrides:
            known_name = overrides[canonical]
            if known_name and known_name != canonical:
                resolved[canonical] = {
                    "known_name": known_name,
                    "source": "override",
                    "confidence": "high",
                }
                stats["override"] += 1
            else:
                # Override explicitly set to same value or empty — treat as unresolved
                unresolved.append(canonical)
                stats["no_expansion"] += 1
            continue

        # 2. Cricsheet
        known, confidence = None, ""
        source = ""
        if cricsheet_index:
            known, confidence = match_cricsheet(canonical, cricsheet_index)
            if known and known != canonical:
                source = "cricsheet"
                if confidence == "high":
                    stats["cricsheet_high"] += 1
            else:
                known = None  # same name or no match — don't count as resolved

        # 3. Wikipedia fallback
        if not known and not args.skip_wikipedia:
            known, confidence = match_wikipedia(canonical)
            if known and known != canonical:
                source = "wikipedia"
                if confidence == "high":
                    stats["wikipedia_high"] += 1
            else:
                known = None

        # 4. Wikidata fallback
        if not known and not args.skip_wikidata:
            known, confidence = match_wikidata(canonical)
            if known and known != canonical:
                source = "wikidata"
                if confidence == "high":
                    stats["wikidata_high"] += 1
            else:
                known = None

        if known and confidence == "high":
            resolved[canonical] = {
                "known_name": known,
                "source": source,
                "confidence": "high",
            }
            print(f"  {canonical!r:25} -> {known!r} [{source}]")
        else:
            # Low confidence or no match — needs manual verification
            unresolved.append(canonical)
            if known:
                stats["unresolved"] += 1
                print(f"  {canonical!r:25} -> {known!r} [{source}] [low confidence -> unresolved]")
            else:
                stats["unresolved"] += 1
                print(f"  {canonical!r:25} -> unresolved")

    # ── Summary ──
    print()
    print("-- Summary ----------------------------------------------")
    print(f"  Override (expanded)  : {stats['override']}")
    print(f"  Override (no change) : {stats['no_expansion']}")
    print(f"  Cricsheet (high)     : {stats['cricsheet_high']}")
    print(f"  Wikipedia (high)     : {stats['wikipedia_high']}")
    print(f"  Wikidata (high)      : {stats['wikidata_high']}")
    print(f"  Unresolved           : {stats['unresolved']}")
    print(f"  Skipped (cache)      : {stats['skipped']}")
    print(f"  Total processed      : {len(names)}")
    print(f"  Resolved (high conf) : {len(resolved)}")
    print(f"  -> To review: add corrections to {args.override} and re-run.")

    # ── Write output ──
    if args.dry_run:
        print("\n[dry-run] Output not written.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(resolved, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\nWrote {len(resolved)} expanded entries to {args.output}")

    unresolved_path = Path(args.unresolved)
    # Deduplicate while preserving order; exclude anything that ended up in resolved
    unresolved_unique = list(dict.fromkeys(n for n in unresolved if n not in resolved))
    # Also carry forward any previously unresolved names not yet processed this run
    prev_unresolved_path = Path(args.unresolved)
    if prev_unresolved_path.exists():
        with prev_unresolved_path.open(encoding="utf-8") as f:
            prev = json.load(f)
        for n in prev:
            if n not in resolved and n not in unresolved_unique:
                unresolved_unique.append(n)
    unresolved_path.parent.mkdir(parents=True, exist_ok=True)
    with unresolved_path.open("w", encoding="utf-8") as f:
        json.dump(unresolved_unique, f, ensure_ascii=False, indent=2, sort_keys=False)
    print(f"Wrote {len(unresolved_unique)} unresolved names to {args.unresolved}")


if __name__ == "__main__":
    main()
