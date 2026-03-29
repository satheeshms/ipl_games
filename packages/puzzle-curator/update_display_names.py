"""
update_display_names.py — Refresh display_names in existing puzzle JSON files.

Reads known_names_override.json (single source of truth) and rewrites the
display_names field in one or more puzzle JSONs without touching any other
field (items, categories, hashes, etc. are all left intact).

Usage:
    # Update today's puzzle
    python update_display_names.py

    # Update a specific puzzle by date
    python update_display_names.py 2026-03-26

    # Update all puzzles in the default directory
    python update_display_names.py --all

    # Dry run (show what would change, don't write)
    python update_display_names.py --all --dry-run

    # Specify a custom puzzles directory
    python update_display_names.py --all --puzzles-dir /path/to/puzzles
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from hash_util import build_display_names, load_known_names

# Default puzzles directory relative to repo root
_REPO_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_PUZZLES_DIR = _REPO_ROOT / "apps" / "web" / "public" / "puzzles" / "ipl"


def update_puzzle_file(
    path: Path,
    known_names: dict[str, str],
    dry_run: bool = False,
) -> bool:
    """Update display_names in a single puzzle JSON file.

    Returns True if the file was (or would be) changed.
    """
    with path.open(encoding="utf-8") as f:
        puzzle = json.load(f)

    items: list[str] = puzzle.get("items", [])
    new_display_names = build_display_names(items, known_names)

    old_display_names: dict[str, str] = puzzle.get("display_names", {})

    if new_display_names == old_display_names:
        print(f"  no change   {path.name}")
        return False

    # Show the diff
    added = {k: v for k, v in new_display_names.items() if k not in old_display_names}
    removed = {k: v for k, v in old_display_names.items() if k not in new_display_names}
    changed = {
        k: (old_display_names[k], new_display_names[k])
        for k in new_display_names
        if k in old_display_names and old_display_names[k] != new_display_names[k]
    }

    tag = "[dry-run] " if dry_run else ""
    print(f"  {tag}updated    {path.name}")
    for k, v in added.items():
        print(f"    + {k!r} -> {v!r}")
    for k, v in removed.items():
        print(f"    - {k!r} (was {v!r})")
    for k, (old_v, new_v) in changed.items():
        print(f"    ~ {k!r}: {old_v!r} -> {new_v!r}")

    if dry_run:
        return True

    # Write back: set or remove the field, preserving all other keys
    if new_display_names:
        puzzle["display_names"] = new_display_names
    else:
        puzzle.pop("display_names", None)

    with path.open("w", encoding="utf-8") as f:
        json.dump(puzzle, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh display_names in puzzle JSON files from known_names_override.json"
    )
    parser.add_argument(
        "date",
        nargs="?",
        help="Puzzle date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all puzzle files in the puzzles directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )
    parser.add_argument(
        "--puzzles-dir",
        type=Path,
        default=_DEFAULT_PUZZLES_DIR,
        help=f"Directory containing puzzle JSON files (default: {_DEFAULT_PUZZLES_DIR})",
    )
    parser.add_argument(
        "--override",
        type=Path,
        default=None,
        help="Path to known_names_override.json (default: data-pipeline/data/known_names_override.json)",
    )
    args = parser.parse_args()

    known_names = load_known_names(args.override)
    if not known_names:
        print("WARNING: known_names_override.json is empty or missing — no display names to apply.")

    puzzles_dir: Path = args.puzzles_dir
    if not puzzles_dir.exists():
        print(f"ERROR: puzzles directory not found: {puzzles_dir}")
        sys.exit(1)

    if args.all:
        files = sorted(puzzles_dir.glob("*.json"))
        if not files:
            print(f"No JSON files found in {puzzles_dir}")
            sys.exit(0)
        print(f"Scanning {len(files)} puzzle(s) in {puzzles_dir} ...")
    else:
        target_date = args.date or date.today().isoformat()
        candidate = puzzles_dir / f"{target_date}.json"
        if not candidate.exists():
            print(f"ERROR: puzzle file not found: {candidate}")
            sys.exit(1)
        files = [candidate]
        print(f"Updating {candidate.name} ...")

    changed = 0
    for f in files:
        if update_puzzle_file(f, known_names, dry_run=args.dry_run):
            changed += 1

    action = "would update" if args.dry_run else "updated"
    print(f"\nDone. {action} {changed}/{len(files)} file(s).")


if __name__ == "__main__":
    main()
