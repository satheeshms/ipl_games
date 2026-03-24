"""
convert_2024_squad.py — Convert Wikipedia-format squad files to ipl2024-squad CSV.

Reads tab-separated team files from `data/team/2024 squad/<TEAM_CODE>` and writes
`data/ipl2024-squad` in the same 3-column CSV format as ipl2025-squad / ipl2026-squad.

Input file format (9 tab-separated columns):
  No. | Name | Nat | Birth date | Batting | Bowling | Signed year | Salary | Notes

Handles:
  - Preamble lines before the header row
  - Section header rows (Captain, Batters, Wicket-keepers, etc.)
  - Captain auto-detection from the "Captain" section header
  - Both "Withdrew" and "Withdrawn" spellings
  - Captain persistence past withdrawn players (e.g. PBKS 2024)

Usage:
    python3 convert_2024_squad.py
    python3 convert_2024_squad.py --data-dir data/ --squad-dir "data/team/2024 squad"
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


# Reuse canonical team codes from squad_loader
sys.path.insert(0, str(Path(__file__).parent))
from squad_loader import TEAM_CODES

# Footnote ref pattern e.g. [a], [b], [c1]
_FOOTNOTE_RE = re.compile(r"\[[^\]]*\]")


def load_coaches_2024(data_dir: Path) -> dict[str, str]:
    """Return {canonical_team_name: head_coach} for the 2024 season."""
    ndjson_path = data_dir / "manual_coaches_all.ndjson"
    if not ndjson_path.exists():
        print(f"  [warn] {ndjson_path} not found — coaches will be blank")
        return {}

    content = ndjson_path.read_text(encoding="utf-8").strip()
    blocks = [
        json.loads(block.strip())
        for block in re.split(r"\n(?=\{)", content)
        if block.strip()
    ]

    for block in blocks:
        if block.get("ipl_season") == 2024:
            return {
                team["team_name"]: team.get("head_coach", "")
                for team in block.get("teams", [])
            }

    print("  [warn] No 2024 block found in manual_coaches_all.ndjson")
    return {}


def parse_team_file(path: Path) -> list[str]:
    """
    Parse a Wikipedia-format squad file and return a list of player names.
    The captain (if detectable) has ' (C)' appended.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    # Find header row: first line whose tab-split fields contain "Name"
    header_idx = None
    for i, line in enumerate(lines):
        fields = line.split("\t")
        if "Name" in fields:
            header_idx = i
            break

    if header_idx is None:
        print(f"  [warn] {path.name}: no header row found, skipping")
        return []

    players: list[str] = []
    next_is_captain = False

    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped:
            continue

        fields = line.split("\t")

        # Section header row (fewer than 9 fields)
        if len(fields) < 9:
            if stripped.lower() == "captain":
                next_is_captain = True
            continue

        # Player row
        name = fields[1].strip()
        if not name:
            continue

        notes_raw = fields[8] if len(fields) > 8 else ""
        notes = _FOOTNOTE_RE.sub("", notes_raw).strip()

        # Skip withdrawn players
        if "withdrew" in notes.lower() or "withdrawn" in notes.lower():
            continue

        if next_is_captain:
            name = f"{name} (C)"
            next_is_captain = False

        players.append(name)

    return players


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Wikipedia-format squad files to ipl2024-squad CSV."
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"),
        help="Directory containing manual_coaches_all.ndjson and output location"
    )
    parser.add_argument(
        "--squad-dir", type=Path, default=Path("data/team/2024 squad"),
        help="Directory containing per-team squad files named by team code"
    )
    args = parser.parse_args()

    if not args.squad_dir.exists():
        print(f"ERROR: squad-dir not found: {args.squad_dir}")
        sys.exit(1)

    coaches = load_coaches_2024(args.data_dir)

    # Reverse map: canonical name -> team code (for coach lookup)
    canonical_to_code = {v: k for k, v in TEAM_CODES.items()}

    output_path = args.data_dir / "ipl2024-squad"
    rows: list[tuple[str, str, str]] = []
    missing_coach = []

    # Process in TEAM_CODES order for consistent output
    for code in TEAM_CODES:
        team_file = args.squad_dir / code
        if not team_file.exists():
            print(f"  [skip] {code}: file not found at {team_file}")
            continue

        canonical = TEAM_CODES[code]
        coach = coaches.get(canonical, "")
        if not coach:
            missing_coach.append(code)

        players = parse_team_file(team_file)
        if not players:
            print(f"  [warn] {code}: no players parsed")
            continue

        squad_str = ", ".join(players)
        rows.append((code, coach, squad_str))
        captain = next((p for p in players if "(C)" in p), None)
        print(f"  {code}: {len(players)} players, captain={captain or 'none detected'}")

    if not rows:
        print("No rows to write. Exiting.")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team", "Head Coach", "Complete Squad List"])
        writer.writerows(rows)

    print(f"\nWritten: {output_path} ({len(rows)} teams)")

    if missing_coach:
        print(f"[warn] Missing coach for: {missing_coach}")


if __name__ == "__main__":
    main()
