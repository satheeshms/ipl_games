"""
curator.py — Puzzle Curator CLI for IPL Connections.

Usage:
  python3 curator.py create --date 2026-03-20 --output ../../apps/web/public/puzzles/
  python3 curator.py validate --file ../../apps/web/public/puzzles/2026-03-20.json
"""

import argparse
import itertools
import json
import random
import sys
from pathlib import Path

from hash_util import hash_items, verify_known_hashes

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLORS = ["yellow", "green", "blue", "purple"]

COLOR_DESCRIPTIONS = {
    "yellow": "YELLOW — Easiest (obvious IPL groupings)",
    "green":  "GREEN  — Moderate (requires IPL knowledge)",
    "blue":   "BLUE   — Hard (nuanced facts / less-known trivia)",
    "purple": "PURPLE — Hardest (wordplay, puns, obscure connections)",
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def shuffle(items: list) -> list:
    """Fisher-Yates shuffle — returns a new list."""
    a = list(items)
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


def search_data(query: str, ipl_data: dict) -> list[str]:
    """Return up to 10 player/team names matching query (case-insensitive substring)."""
    q = query.lower()
    results: list[str] = []
    for player in ipl_data.get("players", []):
        if q in player["name"].lower():
            results.append(player["name"])
    for team in ipl_data.get("teams", []):
        if q in team["name"].lower():
            results.append(team["name"])
    return results[:10]


# ---------------------------------------------------------------------------
# `create` subcommand
# ---------------------------------------------------------------------------


def cmd_create(args: argparse.Namespace) -> int:
    print("=" * 60)
    print("  IPL Connections — Puzzle Creator")
    print("=" * 60)

    # 1. Verify hash_util is working correctly
    print("\n[1/7] Verifying hash_util …")
    if not verify_known_hashes():
        print("ERROR: hash_util verification failed. Aborting.")
        return 1
    print("  Hash verification: PASS")

    # 2. Load optional data file for search helper
    ipl_data: dict = {}
    if args.data_file:
        data_path = Path(args.data_file)
        if not data_path.exists():
            print(f"WARNING: data file not found: {data_path}. Search helper disabled.")
        else:
            with data_path.open(encoding="utf-8") as fh:
                ipl_data = json.load(fh)
            player_count = len(ipl_data.get("players", []))
            team_count = len(ipl_data.get("teams", []))
            print(f"  Loaded data file: {player_count} players, {team_count} teams")

    # 3. Collect categories interactively
    print("\n[2/7] Enter puzzle categories\n")
    categories_data: list[dict] = []  # [{color, title, items:[str]}]

    for color in COLORS:
        desc = COLOR_DESCRIPTIONS[color]
        print(f"  ── {desc} ──")

        # Title
        while True:
            title = input(f"  Category title for {color.upper()}: ").strip()
            if title:
                break
            print("  Title cannot be empty. Try again.")

        # Items — prompt until exactly 4 unique items collected
        items: list[str] = []
        print(f"  Enter 4 items for {color.upper()} (one per line, blank line to finish entry):")
        while len(items) < 4:
            remaining = 4 - len(items)
            prompt_label = f"  Item {len(items) + 1}/{4}"

            # Optional search helper
            if ipl_data:
                search_query = input(f"{prompt_label} — Search (or press Enter to type directly): ").strip()
                if search_query:
                    matches = search_data(search_query, ipl_data)
                    if matches:
                        print("  Matches:")
                        for idx, m in enumerate(matches, 1):
                            print(f"    {idx}. {m}")
                    else:
                        print("  No matches found.")

            item = input(f"{prompt_label} — Item name: ").strip()
            if not item:
                if len(items) < 4:
                    print(f"  Need {remaining} more item(s). Please enter an item name.")
                continue
            if item in items:
                print(f"  '{item}' already added to this category. Enter a different item.")
                continue
            items.append(item)
            print(f"  Added: {item}  ({len(items)}/4)")

        categories_data.append({"color": color, "title": title, "items": items})
        print()

    # 4. Validate: no duplicate items across all 4 categories
    print("[3/7] Checking for duplicate items …")
    all_items: list[str] = []
    duplicates: list[str] = []
    for cat in categories_data:
        for item in cat["items"]:
            if item in all_items:
                duplicates.append(item)
            else:
                all_items.append(item)

    if duplicates:
        print(f"ERROR: Duplicate items found across categories: {duplicates}")
        print("Please re-run and enter unique items in each category.")
        return 1
    print("  No duplicates found: OK")

    # 5. Compute SHA-256 hash for each category
    print("\n[4/7] Computing category hashes …")
    categories_out: list[dict] = []
    for cat in categories_data:
        h = hash_items(cat["items"])
        categories_out.append({
            "color": cat["color"],
            "title": cat["title"],
            "hash": h,
        })
        print(f"  {cat['color'].upper():8s} '{cat['title']}' → {h[:16]}…")

    # 6. Shuffle all 16 items
    print("\n[5/7] Shuffling items …")
    shuffled_items = shuffle(all_items)
    print(f"  Items shuffled: {shuffled_items}")

    # 7. Determine edition number
    print("\n[6/7] Determining edition number …")
    output_dir = Path(args.output)
    if args.edition is not None:
        edition = args.edition
        print(f"  Edition (from --edition flag): {edition}")
    else:
        # Count existing YYYY-MM-DD.json puzzle files (exclude dev.json etc.)
        existing = [
            f for f in output_dir.glob("????-??-??.json")
            if f.is_file()
        ]
        edition = len(existing) + 1
        print(f"  Auto-detected edition: {edition} ({len(existing)} existing puzzle(s) found)")

    # 8. Write puzzle JSON
    print(f"\n[7/7] Writing puzzle file …")
    puzzle: dict = {
        "id": args.date,
        "date": args.date,
        "edition": edition,
        "items": shuffled_items,
        "categories": categories_out,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{args.date}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, indent=2, ensure_ascii=False)
    print(f"  Written: {out_path.resolve()}")

    # 9. Print summary for review
    print("\n" + "=" * 60)
    print("  PUZZLE SUMMARY")
    print("=" * 60)
    print(json.dumps(puzzle, indent=2, ensure_ascii=False))
    print("=" * 60)
    print(f"\nPuzzle #{edition} for {args.date} saved successfully.")
    return 0


# ---------------------------------------------------------------------------
# `validate` subcommand
# ---------------------------------------------------------------------------


def cmd_validate(args: argparse.Namespace) -> int:
    file_path = Path(args.file)
    print("=" * 60)
    print(f"  IPL Connections — Puzzle Validator")
    print(f"  File: {file_path}")
    print("=" * 60)

    errors: list[str] = []

    # 1. JSON parses correctly
    print("\n[1] Parsing JSON …")
    try:
        with file_path.open(encoding="utf-8") as fh:
            puzzle = json.load(fh)
        print("  JSON parse: OK")
    except FileNotFoundError:
        print(f"  ERROR: File not found: {file_path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"  ERROR: Invalid JSON: {exc}")
        return 1

    # 2. Required fields present
    print("\n[2] Checking required fields …")
    required_fields = ["id", "date", "edition", "items", "categories"]
    for field in required_fields:
        if field not in puzzle:
            errors.append(f"Missing required field: '{field}'")
        else:
            print(f"  '{field}': OK")

    if errors:
        _print_errors(errors)
        return 1

    # 3. Exactly 16 items
    print("\n[3] Checking item count …")
    item_count = len(puzzle["items"])
    if item_count != 16:
        errors.append(f"Expected 16 items, found {item_count}")
    else:
        print(f"  Item count: {item_count} — OK")

    # 4. Exactly 4 categories with correct colors (one each)
    print("\n[4] Checking categories …")
    categories = puzzle.get("categories", [])
    cat_count = len(categories)
    if cat_count != 4:
        errors.append(f"Expected 4 categories, found {cat_count}")
    else:
        print(f"  Category count: {cat_count} — OK")

    found_colors = [c.get("color") for c in categories]
    for required_color in COLORS:
        if found_colors.count(required_color) != 1:
            errors.append(f"Expected exactly one '{required_color}' category; found {found_colors.count(required_color)}")
        else:
            print(f"  Color '{required_color}': OK")

    # 5. No duplicate items
    print("\n[5] Checking for duplicate items …")
    items: list[str] = puzzle.get("items", [])
    seen: set[str] = set()
    dupes: list[str] = []
    for item in items:
        if item in seen:
            dupes.append(item)
        seen.add(item)
    if dupes:
        errors.append(f"Duplicate items: {dupes}")
    else:
        print(f"  No duplicates: OK")

    # 6. Each category hash is a valid 64-char hex string
    print("\n[6] Checking hash format …")
    for cat in categories:
        color = cat.get("color", "?")
        h = cat.get("hash", "")
        if not (isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)):
            errors.append(f"Category '{color}' has invalid hash: '{h}'")
        else:
            print(f"  '{color}' hash format: OK")

    if errors:
        _print_errors(errors)
        return 1

    # 7. Hash round-trip: find which 4 items produce each category hash
    print("\n[7] Verifying category hashes (round-trip, C(16,4)=1820 combinations) …")
    hash_errors: list[str] = []
    for cat in categories:
        color = cat["color"]
        stored_hash = cat["hash"]
        matched = False
        for combo in itertools.combinations(puzzle["items"], 4):
            if hash_items(list(combo)) == stored_hash:
                matched = True
                print(f"  '{color}' hash verified: {list(combo)}")
                break
        if not matched:
            hash_errors.append(
                f"Category '{color}' (title: '{cat.get('title', '?')}') hash does not match any combination of 4 items"
            )

    if hash_errors:
        errors.extend(hash_errors)

    # Final result
    print("\n" + "=" * 60)
    if errors:
        _print_errors(errors)
        print("  Result: FAIL")
        print("=" * 60)
        return 1
    else:
        print("  Result: PASS — puzzle is valid")
        print("=" * 60)
        return 0


def _print_errors(errors: list[str]) -> None:
    print("\n  ERRORS:")
    for err in errors:
        print(f"    - {err}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="curator",
        description="IPL Connections — Puzzle Curator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- create ---------------------------------------------------------------
    create_p = subparsers.add_parser(
        "create",
        help="Interactively create a new puzzle JSON file",
    )
    create_p.add_argument(
        "--date",
        required=True,
        metavar="YYYY-MM-DD",
        help="Puzzle date (used as file name and puzzle id)",
    )
    create_p.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Output directory for the puzzle JSON file",
    )
    create_p.add_argument(
        "--edition",
        type=int,
        default=None,
        metavar="N",
        help="Edition number (auto-detected from existing files if omitted)",
    )
    create_p.add_argument(
        "--data-file",
        default=None,
        metavar="PATH",
        help="Optional path to ipl_data.json for the search helper",
    )

    # -- validate -------------------------------------------------------------
    validate_p = subparsers.add_parser(
        "validate",
        help="Validate an existing puzzle JSON file",
    )
    validate_p.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to the puzzle JSON file to validate",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAborted by user (Ctrl+C). No file was written.")
        sys.exit(1)
