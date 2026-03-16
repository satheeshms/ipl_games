"""
auto_curator.py — Auto-generate IPL Connections puzzles from ipl_data.json.

Usage:
  # Generate a puzzle from category type specs
  python auto_curator.py generate \\
    --date 2026-03-20 \\
    --output ../../apps/web/public/puzzles/ \\
    --data-file ../data-pipeline/data/ipl_data.json \\
    --categories yellow:orange_cap green:purple_cap blue:ipl_champions purple:team_players:CSK:2025

  # Check a puzzle for item overlap with all other puzzles in the directory
  python auto_curator.py check \\
    --file ../../apps/web/public/puzzles/2026-03-20.json \\
    --puzzles-dir ../../apps/web/public/puzzles/

Available category types:
  orange_cap, purple_cap, player_of_tournament, costliest_player,
  winning_captain, ipl_champions,
  team_players:<TEAM>:<SEASON>   e.g. team_players:CSK:2025
  coaches:<SEASON>               e.g. coaches:2025
"""

import argparse
import json
import sys
from pathlib import Path

from category_generators import generate_category, GENERATORS
from hash_util import hash_items

COLORS = ["yellow", "green", "blue", "purple"]

COLOR_LABELS = {
    "yellow": "YELLOW (Easiest)",
    "green":  "GREEN  (Moderate)",
    "blue":   "BLUE   (Hard)",
    "purple": "PURPLE (Hardest)",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_ipl_data(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: data file not found: {path}")
        sys.exit(1)
    data = load_json(path)
    print(f"  Loaded: {len(data.get('players', []))} players, "
          f"{len(data.get('teams', []))} teams, "
          f"{len(data.get('awards', []))} awards, "
          f"{len(data.get('ipl_wins', []))} ipl_wins, "
          f"{len(data.get('coaches', []))} coaches")
    return data


def load_used_items(puzzles_dir: Path, skip_file: Path | None = None) -> set[str]:
    """Return all items used in existing puzzle files (optionally skipping one file)."""
    used: set[str] = set()
    for f in sorted(puzzles_dir.glob("????-??-??.json")):
        if skip_file and f.resolve() == skip_file.resolve():
            continue
        try:
            puzzle = load_json(f)
            used.update(puzzle.get("items", []))
        except (json.JSONDecodeError, KeyError):
            pass
    return used


def _next_edition(puzzles_dir: Path) -> int:
    existing = list(puzzles_dir.glob("????-??-??.json"))
    return len(existing) + 1


def shuffle(items: list) -> list:
    import random
    a = list(items)
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


# ---------------------------------------------------------------------------
# `generate` subcommand
# ---------------------------------------------------------------------------

def cmd_generate(args: argparse.Namespace) -> int:
    print("=" * 60)
    print("  IPL Connections — Auto Puzzle Generator")
    print("=" * 60)

    output_dir = Path(args.output)
    data_path = Path(args.data_file)

    # Check output file doesn't already exist
    out_path = output_dir / f"{args.date}.json"
    if out_path.exists():
        print(f"ERROR: puzzle file already exists: {out_path}")
        print("Choose a different date or delete the existing file.")
        return 1

    # Load data
    print(f"\nLoading {data_path} ...")
    ipl_data = load_ipl_data(data_path)

    # Load previously used items to prevent cross-puzzle collisions
    print(f"\nScanning existing puzzles in {output_dir} ...")
    used_items = load_used_items(output_dir)
    print(f"  {len(used_items)} items already used across {len(list(output_dir.glob('????-??-??.json')))} existing puzzle(s)")

    # Parse and validate category specs
    color_specs: dict[str, str] = {}  # color -> type_spec
    for spec in args.categories:
        parts = spec.split(":", 1)
        if len(parts) != 2:
            print(f"ERROR: invalid category spec '{spec}'. Format: color:type[:params]")
            return 1
        color, type_spec = parts
        if color not in COLORS:
            print(f"ERROR: invalid color '{color}'. Must be one of: {COLORS}")
            return 1
        color_specs[color] = type_spec

    missing_colors = [c for c in COLORS if c not in color_specs]
    if missing_colors:
        print(f"ERROR: missing categories for colors: {missing_colors}")
        print("All 4 colors (yellow, green, blue, purple) must be specified.")
        return 1

    # Generate each category
    print("\nGenerating categories...")
    categories: list[dict] = []
    picked_items: set[str] = set()
    exclude = used_items | picked_items

    for color in COLORS:
        type_spec = color_specs[color]
        try:
            result = generate_category(ipl_data, type_spec, exclude)
        except ValueError as e:
            print(f"\nERROR generating {color.upper()} ({type_spec}): {e}")
            return 1

        categories.append({
            "color": color,
            "title": result["title"],
            "items": result["items"],
        })
        picked_items.update(result["items"])
        exclude = used_items | picked_items
        print(f"  {COLOR_LABELS[color]}: {result['title']}")

    # Preview
    print("\n" + "=" * 60)
    print(f"  PUZZLE PREVIEW  —  {args.date}")
    print("=" * 60)
    all_items: list[str] = []
    for cat in categories:
        label = COLOR_LABELS[cat["color"]]
        print(f"\n  {label}")
        print(f"  Title: {cat['title']}")
        for i, item in enumerate(cat["items"], 1):
            print(f"    {i}. {item}")
        all_items.extend(cat["items"])

    print(f"\n  All 16 items: {all_items}")
    print("=" * 60)

    # Confirm
    try:
        answer = input("\nSave this puzzle? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return 1

    if answer != "y":
        print("Puzzle discarded. Nothing written.")
        return 0

    # Build and write puzzle JSON
    edition = _next_edition(output_dir)

    categories_out = [
        {
            "color": cat["color"],
            "title": cat["title"],
            "hash": hash_items(cat["items"]),
        }
        for cat in categories
    ]

    puzzle = {
        "id": args.date,
        "date": args.date,
        "edition": edition,
        "items": shuffle(all_items),
        "categories": categories_out,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(puzzle, f, indent=2, ensure_ascii=False)

    print(f"\nPuzzle #{edition} written to: {out_path.resolve()}")
    print("Run the following to validate:")
    print(f"  python curator.py validate --file {out_path}")
    return 0


# ---------------------------------------------------------------------------
# `check` subcommand
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    target_path = Path(args.file)
    puzzles_dir = Path(args.puzzles_dir)

    print("=" * 60)
    print("  IPL Connections — Cross-Puzzle Collision Check")
    print(f"  Target: {target_path.name}")
    print("=" * 60)

    if not target_path.exists():
        print(f"ERROR: file not found: {target_path}")
        return 1

    try:
        target = load_json(target_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {target_path}: {e}")
        return 1

    target_items: list[str] = target.get("items", [])
    if not target_items:
        print("ERROR: puzzle has no items.")
        return 1

    # Build item -> [puzzle_date, ...] map from all other puzzles
    item_sources: dict[str, list[str]] = {}
    checked = 0
    for f in sorted(puzzles_dir.glob("????-??-??.json")):
        if f.resolve() == target_path.resolve():
            continue
        try:
            puzzle = load_json(f)
            date = puzzle.get("date", f.stem)
            for item in puzzle.get("items", []):
                item_sources.setdefault(item, []).append(date)
            checked += 1
        except (json.JSONDecodeError, KeyError):
            print(f"  WARNING: could not parse {f.name}, skipping.")

    print(f"\nChecked {checked} existing puzzle(s).\n")

    collisions = {item: item_sources[item] for item in target_items if item in item_sources}

    if not collisions:
        print("  Result: PASS — no item collisions with existing puzzles.")
        return 0

    print(f"  Result: FAIL — {len(collisions)} collision(s) found:\n")
    for item, dates in collisions.items():
        print(f"  - '{item}'  (also in: {', '.join(dates)})")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto_curator",
        description="Auto-generate IPL Connections puzzles from ipl_data.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- generate -------------------------------------------------------------
    gen_p = sub.add_parser("generate", help="Auto-generate a puzzle from category specs")
    gen_p.add_argument("--date", required=True, metavar="YYYY-MM-DD",
                       help="Puzzle date (used as filename)")
    gen_p.add_argument("--output", required=True, metavar="DIR",
                       help="Directory to write the puzzle JSON")
    gen_p.add_argument("--data-file", required=True, metavar="PATH",
                       help="Path to ipl_data.json")
    gen_p.add_argument("--categories", required=True, nargs=4,
                       metavar="COLOR:TYPE[:PARAMS]",
                       help=(
                           "Exactly 4 category specs, one per color. "
                           "Format: color:type[:param1[:param2]]. "
                           f"Colors: {COLORS}. "
                           f"Types: {sorted(GENERATORS.keys())}. "
                           "Example: yellow:orange_cap green:purple_cap "
                           "blue:ipl_champions purple:team_players:CSK:2025"
                       ))

    # -- check ----------------------------------------------------------------
    chk_p = sub.add_parser("check", help="Check a puzzle for item collisions with existing puzzles")
    chk_p.add_argument("--file", required=True, metavar="PATH",
                       help="Puzzle JSON file to check")
    chk_p.add_argument("--puzzles-dir", required=True, metavar="DIR",
                       help="Directory containing existing puzzle JSON files")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "check":
        return cmd_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(1)
