"""
promote_known_names.py — Merge known_names.json into known_names_override.json.

known_names_override.json is the single source of truth for display names used
by the puzzle curator.  This script promotes high-confidence automated results
from known_names.json into the override file so that future curator runs and
fetch_known_names.py re-runs all read from one place.

Rules:
  - Override entries always win (manual curation takes precedence).
  - Only entries where known_name != canonical are promoted (no no-ops).
  - After promotion, known_names.json is reset to an empty object because
    its contents are now fully absorbed into the override.

Usage:
    cd packages/data-pipeline
    python promote_known_names.py
    python promote_known_names.py --dry-run
    python promote_known_names.py --input data/known_names.json \\
                                  --override data/known_names_override.json
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote known_names.json entries into known_names_override.json."
    )
    parser.add_argument("--input",    default="data/known_names.json",
                        help="Automated results file (source)")
    parser.add_argument("--override", default="data/known_names_override.json",
                        help="Manual override file (destination / source of truth)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Print what would change without writing files")
    args = parser.parse_args()

    input_path    = Path(args.input)
    override_path = Path(args.override)

    # Load automated results
    if not input_path.exists():
        print(f"Nothing to promote: {args.input} not found.")
        return
    with input_path.open(encoding="utf-8") as f:
        automated: dict[str, dict] = json.load(f)

    # Load existing overrides (create empty if absent)
    existing_override: dict[str, str] = {}
    if override_path.exists():
        with override_path.open(encoding="utf-8") as f:
            existing_override = json.load(f)

    # Merge: override entries win; only promote entries that actually expand the name
    added   = {}
    skipped_override = []
    skipped_same     = []

    for canonical, entry in automated.items():
        known_name = entry.get("known_name", "")
        if canonical in existing_override:
            skipped_override.append(canonical)
            continue
        if not known_name or known_name == canonical:
            skipped_same.append(canonical)
            continue
        added[canonical] = known_name

    merged = {**added, **existing_override}   # override entries keep priority
    merged = dict(sorted(merged.items()))     # sort for stable diffs

    print(f"Entries in override (unchanged) : {len(existing_override)}")
    print(f"New entries to promote          : {len(added)}")
    print(f"Skipped (already in override)   : {len(skipped_override)}")
    print(f"Skipped (no expansion / same)   : {len(skipped_same)}")
    print(f"Total entries after merge       : {len(merged)}")

    if added:
        print("\nNew entries being promoted:")
        for k, v in sorted(added.items()):
            print(f"  {k!r:25} -> {v!r}")

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    override_path.parent.mkdir(parents=True, exist_ok=True)
    with override_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated {override_path}")

    # Reset known_names.json — its contents are now in the override
    with input_path.open("w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
    print(f"Reset {input_path} (contents absorbed into override)")


if __name__ == "__main__":
    main()
