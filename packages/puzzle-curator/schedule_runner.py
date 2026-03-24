"""
schedule_runner.py — Generate IPL Clusters puzzles from curation_schedule.md.

Reads the curation_schedule.md table, finds rows with generator specs filled in,
and generates puzzle JSON files for each.

Usage:
  # Dry run — show what would be generated without writing files
  python schedule_runner.py --dry-run

  # Generate all pending puzzles (status [ ] with specs filled)
  python schedule_runner.py

  # Generate a single date
  python schedule_runner.py --date 2026-03-28

  # Generate a date range
  python schedule_runner.py --from 2026-03-23 --to 2026-04-12

Options:
  --schedule    Path to curation_schedule.md  (default: ./curation_schedule.md)
  --data-file   Path to ipl_data.json         (default: ../data-pipeline/data/ipl_data.json)
  --output      Puzzle output directory        (default: ../../apps/web/public/puzzles/ipl)
  --dry-run     Print what would be generated without writing files
  --date        Generate only this date (YYYY-MM-DD)
  --from        Start of date range (YYYY-MM-DD, inclusive)
  --to          End of date range (YYYY-MM-DD, inclusive)
  --force       Overwrite existing puzzle files
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

from ambiguity import check_ambiguity
from category_generators import generate_category
from hash_util import hash_items

_MAX_RESAMPLE = 10  # max re-draws per conflicting category before giving up

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLORS = ["yellow", "green", "blue", "purple"]
SKIP_VALUES = {"—", "-", "tbd", "TBD", ""}
DONE_STATUS = "[x]"
YEAR = 2026  # all dates in the schedule are 2026

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_schedule(md_path: Path) -> list[dict]:
    """
    Parse curation_schedule.md and return a list of puzzle rows.

    Each row dict:
      {
        "edition":  int,
        "date":     str (YYYY-MM-DD),
        "status":   str,
        "specs":    [yellow_spec, green_spec, blue_spec, purple_spec],
        "matches":  str,
        "raw":      str (original line)
      }

    Rows are included only if they have a parseable date and at least one spec.
    """
    rows = []
    text = md_path.read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()
        # Must look like a table data row: starts and ends with |
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]

        # Minimum columns: Ed | Date | Day | ... | Yellow | Green | Blue | Purple | Status
        # We need at least 9 cells (Ed + Date + Day + Phase/Match cols + 4 specs + status)
        if len(cells) < 8:
            continue

        # Skip header/separator rows
        if cells[0] in ("Ed", "---", "") or set(cells[0]) == {"-"}:
            continue

        # Parse edition number
        try:
            edition = int(cells[0])
        except ValueError:
            continue

        # Parse date: "23 Mar", "28 Mar", etc.
        date_str = _parse_date(cells[1])
        if date_str is None:
            continue

        # Status is always the last cell
        status = cells[-1]

        # The 4 spec columns are always the last 5 cells (4 specs + 1 status)
        spec_cells = [s.strip().strip("`") for s in cells[-5:-1]]
        if len(spec_cells) != 4:
            continue

        # Match description: varies by table (Phase PRE has no match col, Phase 1/2 does)
        # We grab it as whatever is between Day column and the specs — just store raw
        matches_col = cells[3] if len(cells) > 5 else ""

        rows.append({
            "edition": edition,
            "date":    date_str,
            "status":  status,
            "specs":   spec_cells,
            "matches": matches_col,
            "raw":     line,
        })

    return rows


def _parse_date(raw: str) -> str | None:
    """Convert '23 Mar' or '23 Mar 2026' → '2026-03-23'. Returns None if unparseable."""
    raw = raw.strip()
    parts = raw.split()
    if len(parts) < 2:
        return None
    try:
        day = int(parts[0])
        month = MONTH_MAP.get(parts[1].lower()[:3])
        if month is None:
            return None
        year = int(parts[2]) if len(parts) >= 3 else YEAR
        return f"{year}-{month:02d}-{day:02d}"
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def _specs_ready(specs: list[str]) -> bool:
    """Return True if all 4 spec cells are non-empty and not placeholder values."""
    return len(specs) == 4 and all(s.strip().lower() not in SKIP_VALUES for s in specs)


def _in_range(d: str, from_date: str | None, to_date: str | None) -> bool:
    if from_date and d < from_date:
        return False
    if to_date and d > to_date:
        return False
    return True


# ---------------------------------------------------------------------------
# Puzzle generation
# ---------------------------------------------------------------------------

def load_ipl_data(data_path: Path) -> dict:
    if not data_path.exists():
        print(f"ERROR: data file not found: {data_path}")
        sys.exit(1)
    with data_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_used_items(output_dir: Path,
                    skip_date: str | None = None) -> dict[str, set[str]]:
    """
    Collect items from existing puzzle files keyed by spec.

    Returns {spec: {item, ...}} so exclusions are per-spec:
    a player excluded from 'team_legends_batting:MI' is still available
    for 'team_players:MI:2026' in a future puzzle.

    Only categories that carry a 'spec' field are indexed.  Legacy puzzle
    files without 'spec' are silently skipped for exclusion purposes.
    """
    used: dict[str, set[str]] = defaultdict(set)
    for f in sorted(output_dir.glob("????-??-??.json")):
        if skip_date and f.stem == skip_date:
            continue
        try:
            puzzle = json.loads(f.read_text(encoding="utf-8"))
            for cat in puzzle.get("categories", []):
                spec = cat.get("spec", "")
                if spec:
                    used[spec].update(cat.get("items", []))
        except (json.JSONDecodeError, KeyError):
            pass
    return used


def _next_edition(output_dir: Path) -> int:
    return len(list(output_dir.glob("????-??-??.json"))) + 1


def _shuffle(items: list) -> list:
    import random
    a = list(items)
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


def generate_puzzle(row: dict, ipl_data: dict, output_dir: Path,
                    used_items: dict[str, set[str]], dry_run: bool, force: bool) -> bool:
    """
    Generate and write a puzzle for one schedule row.
    Returns True on success, False on skip/error.

    Exclusion logic:
    - picked  : items already chosen in THIS puzzle (global within puzzle)
                prevents the same player appearing in two slots on the same day
    - used_items[spec] : items used for this spec in ALL past puzzles
                prevents the same player repeating in the same category type
    """
    date_str = row["date"]
    out_path = output_dir / f"{date_str}.json"

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Ed {row['edition']} — {date_str}")

    if out_path.exists() and not force:
        print(f"  SKIP: {out_path.name} already exists (use --force to overwrite)")
        return False

    categories = []
    picked: set[str] = set()

    for color, spec in zip(COLORS, row["specs"]):
        spec = spec.strip()
        # Exclude: items used previously for THIS spec + items already picked today
        exclude = used_items.get(spec, set()) | picked
        try:
            result = generate_category(ipl_data, spec, exclude)
        except ValueError as e:
            print(f"  ERROR [{color}] {spec}: {e}")
            return False

        categories.append({
            "color": color,
            "title": result["title"],
            "items": result["items"],
            "spec":  spec,
        })
        picked.update(result["items"])
        print(f"  {color:8s} [{spec}] -> {result['title']}: {result['items']}")

    # Ambiguity check: ensure no placed item also qualifies for another category
    conflicts = check_ambiguity(ipl_data, categories)
    if conflicts:
        for _attempt in range(_MAX_RESAMPLE):
            if not conflicts:
                break
            # Pick the color whose items cause the most conflicts
            color_counts: dict[str, int] = {}
            for _item, placed, _also in conflicts:
                color_counts[placed] = color_counts.get(placed, 0) + 1
            target_color = max(color_counts, key=color_counts.get)
            target_idx = COLORS.index(target_color)
            target_spec = categories[target_idx]["spec"]

            other_items = {
                item
                for cat in categories if cat["color"] != target_color
                for item in cat["items"]
            }
            resample_exclude = used_items.get(target_spec, set()) | other_items

            try:
                new_result = generate_category(ipl_data, target_spec, resample_exclude)
                old_items = categories[target_idx]["items"]
                categories[target_idx]["items"] = new_result["items"]
                print(f"  Resampled {target_color.upper()} [{target_spec}]:")
                print(f"    was: {old_items}")
                print(f"    now: {new_result['items']}")
            except ValueError:
                break  # pool exhausted — can't improve

            conflicts = check_ambiguity(ipl_data, categories)

    if conflicts:
        print("  AMBIGUITY WARNING — unresolved after resampling:")
        for item, placed, also in conflicts:
            print(f"    '{item}' placed in {placed.upper()} also qualifies for {also.upper()}")
        print("  Use --reshuffle or --set-items to fix manually.")
    else:
        print("  AMBIGUITY CHECK: PASS")

    # Always print final state so it matches what gets written to the file
    print("\n  Final categories:")
    for cat in categories:
        print(f"  {cat['color']:8s} [{cat['spec']}] -> {cat['title']}: {cat['items']}")

    if dry_run:
        return True

    # Build puzzle JSON
    all_items = [item for cat in categories for item in cat["items"]]
    edition = row["edition"]

    puzzle = {
        "id":       date_str,
        "date":     date_str,
        "edition":  edition,
        "items":    _shuffle(all_items),
        "categories": [
            {
                "color": cat["color"],
                "title": cat["title"],
                "spec":  cat["spec"],
                "hash":  hash_items(cat["items"]),
            }
            for cat in categories
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(puzzle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Written -> {out_path}")

    # Update used_items per-spec for subsequent puzzles in the same run
    for cat in categories:
        used_items[cat["spec"]].update(cat["items"])
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schedule_runner",
        description="Generate IPL Clusters puzzles from curation_schedule.md",
    )
    parser.add_argument(
        "--schedule",
        default=str(Path(__file__).parent / "curation_schedule.md"),
        metavar="PATH",
        help="Path to curation_schedule.md (default: ./curation_schedule.md)",
    )
    parser.add_argument(
        "--data-file",
        default=str(Path(__file__).parent / "../data-pipeline/data/ipl_data.json"),
        metavar="PATH",
        help="Path to ipl_data.json",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "../../apps/web/public/puzzles/ipl"),
        metavar="DIR",
        help="Puzzle output directory",
    )
    parser.add_argument("--dry-run",  action="store_true", help="Preview without writing files")
    parser.add_argument("--force",    action="store_true", help="Overwrite existing puzzle files")
    parser.add_argument("--date",     metavar="YYYY-MM-DD", help="Generate only this date")
    parser.add_argument("--from",     dest="from_date", metavar="YYYY-MM-DD")
    parser.add_argument("--to",       dest="to_date",   metavar="YYYY-MM-DD")
    parser.add_argument(
        "--reshuffle",
        metavar="COLOR",
        choices=COLORS,
        help="Re-sample one category in the existing puzzle for --date (new random draw, same spec)",
    )
    parser.add_argument(
        "--set-items",
        metavar="COLOR:p1,p2,p3,p4",
        help="Replace 4 items in one category and regenerate its hash (requires --date)",
    )
    return parser


def cmd_reshuffle(args: argparse.Namespace, ipl_data: dict,
                  output_dir: Path, used_items: dict[str, set[str]]) -> int:
    """Re-sample one category in an existing puzzle file (same spec, new random draw)."""
    date_str = args.date
    out_path = output_dir / f"{date_str}.json"
    target_color = args.reshuffle

    if not out_path.exists():
        print(f"ERROR: puzzle not found: {out_path}")
        return 1

    puzzle = json.loads(out_path.read_text(encoding="utf-8"))
    categories = puzzle.get("categories", [])

    target_cat = next((c for c in categories if c["color"] == target_color), None)
    if target_cat is None:
        print(f"ERROR: no '{target_color}' category in puzzle {date_str}")
        return 1

    spec = target_cat.get("spec", "")
    if not spec:
        print(f"ERROR: '{target_color}' category has no spec field — cannot reshuffle")
        return 1

    old_items = target_cat.get("items", [])

    # Exclude: items from the other 3 categories + items used by this spec in prior puzzles
    other_items = {
        item
        for c in categories if c["color"] != target_color
        for item in c.get("items", [])
    }
    resample_exclude = used_items.get(spec, set()) | other_items

    try:
        new_result = generate_category(ipl_data, spec, resample_exclude)
    except ValueError as e:
        print(f"ERROR: could not resample '{target_color}' ({spec}): {e}")
        return 1

    new_items = new_result["items"]
    print(f"\nReshuffling {target_color.upper()} [{spec}]")
    print(f"  Old: {old_items}")
    print(f"  New: {new_items}")

    target_cat["items"] = new_items
    target_cat["hash"] = hash_items(new_items)

    all_items = [item for c in categories for item in c.get("items", [])]
    puzzle["items"] = _shuffle(all_items)

    out_path.write_text(json.dumps(puzzle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Written -> {out_path}")
    return 0


def cmd_set_items(args: argparse.Namespace, output_dir: Path) -> int:
    """Replace 4 items in one category and regenerate its hash."""
    date_str = args.date
    out_path = output_dir / f"{date_str}.json"

    if not out_path.exists():
        print(f"ERROR: puzzle not found: {out_path}")
        return 1

    # Parse "COLOR:p1,p2,p3,p4" — split on first colon only
    raw = args.set_items
    try:
        colon_idx = raw.index(":")
    except ValueError:
        print("ERROR: --set-items format is 'COLOR:p1,p2,p3,p4'")
        return 1
    color = raw[:colon_idx].strip()
    new_items = [s.strip() for s in raw[colon_idx + 1:].split(",")]

    if color not in COLORS:
        print(f"ERROR: invalid color '{color}'. Must be one of: {COLORS}")
        return 1
    if len(new_items) != 4:
        print(f"ERROR: expected exactly 4 items, got {len(new_items)}: {new_items}")
        return 1

    puzzle = json.loads(out_path.read_text(encoding="utf-8"))
    categories = puzzle.get("categories", [])

    target_cat = next((c for c in categories if c["color"] == color), None)
    if target_cat is None:
        print(f"ERROR: no '{color}' category in puzzle {date_str}")
        return 1

    old_items = target_cat.get("items", [])
    print(f"\nSetting items for {color.upper()}")
    print(f"  Old: {old_items}")
    print(f"  New: {new_items}")

    target_cat["items"] = new_items
    target_cat["hash"] = hash_items(new_items)

    all_items = [item for c in categories for item in c.get("items", [])]
    puzzle["items"] = _shuffle(all_items)

    out_path.write_text(json.dumps(puzzle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Written -> {out_path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    schedule_path = Path(args.schedule)
    data_path     = Path(args.data_file)
    output_dir    = Path(args.output)

    # --- Surgical fix modes (early return, no schedule processing needed) ---

    if args.reshuffle:
        if not args.date:
            print("ERROR: --reshuffle requires --date")
            return 1
        ipl_data = load_ipl_data(data_path)
        used_items = load_used_items(output_dir, skip_date=args.date)
        return cmd_reshuffle(args, ipl_data, output_dir, used_items)

    if args.set_items:
        if not args.date:
            print("ERROR: --set-items requires --date")
            return 1
        return cmd_set_items(args, output_dir)

    # --- Normal schedule-based generation ---

    if not schedule_path.exists():
        print(f"ERROR: schedule not found: {schedule_path}")
        return 1

    print("=" * 60)
    print("  IPL Schedule Runner")
    print("=" * 60)
    print(f"  Schedule : {schedule_path}")
    print(f"  Data     : {data_path}")
    print(f"  Output   : {output_dir}")
    if args.dry_run:
        print("  Mode     : DRY RUN (no files written)")
    print()

    # Load data
    ipl_data = load_ipl_data(data_path)
    print(f"Loaded ipl_data.json: {len(ipl_data.get('players', []))} players, "
          f"{len(ipl_data.get('awards', []))} awards, "
          f"{len(ipl_data.get('records', {}).get('batting_records', []))} batting records, "
          f"{len(ipl_data.get('records', {}).get('bowling_records', []))} bowling records")

    # Parse schedule
    rows = parse_schedule(schedule_path)
    print(f"Parsed {len(rows)} rows from schedule\n")

    # Apply filters
    if args.date:
        rows = [r for r in rows if r["date"] == args.date]
    else:
        rows = [r for r in rows if _in_range(r["date"], args.from_date, args.to_date)]

    # Only process rows that have specs ready and aren't already done
    pending = [r for r in rows if _specs_ready(r["specs"]) and r["status"] != DONE_STATUS]
    skipped_no_specs = len(rows) - len(pending) - sum(1 for r in rows if r["status"] == DONE_STATUS)
    already_done     = sum(1 for r in rows if r["status"] == DONE_STATUS)

    print(f"Rows to process : {len(pending)}")
    print(f"Already done    : {already_done}")
    print(f"Specs not ready : {skipped_no_specs}")

    if not pending:
        print("\nNothing to generate.")
        return 0

    # Load used items from existing puzzles (cumulative collision avoidance)
    used_items = load_used_items(output_dir)
    total_used = sum(len(v) for v in used_items.values())
    print(f"\nExisting puzzles: {len(list(output_dir.glob('????-??-??.json')))} "
          f"({total_used} items already used across {len(used_items)} specs)")

    # Generate
    success = failed = 0
    for row in pending:
        ok = generate_puzzle(row, ipl_data, output_dir, used_items,
                             dry_run=args.dry_run, force=args.force)
        if ok:
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"  Done: {success} generated, {failed} failed/skipped")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(1)
