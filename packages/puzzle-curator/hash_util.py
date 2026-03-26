"""
hash_util.py — SHA-256 hashing for IPL Connections puzzle curator.

Must produce identical output to the browser's lib/hash.ts:
  const sorted = [...items].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  const input = sorted.join('|');
  // SHA-256 of UTF-8 encoded input
"""

import hashlib
from itertools import combinations


def hash_items(items: list[str]) -> str:
    """SHA-256 of case-insensitively sorted items joined with '|'.

    Must match the browser Web Crypto implementation in lib/hash.ts.
    Sort uses str.casefold() which mirrors the JS localeCompare sensitivity:'base'
    behaviour for ASCII/Latin characters used in IPL player names.
    """
    sorted_items = sorted(items, key=str.casefold)
    input_str = "|".join(sorted_items)
    return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


def find_category_items(all_items: list[str], target_hash: str) -> list[str]:
    """Return the 4 items from all_items whose hash matches target_hash, or []."""
    for combo in combinations(all_items, 4):
        if hash_items(list(combo)) == target_hash:
            return list(combo)
    return []


# ---------------------------------------------------------------------------
# Known-hash cross-validation
# Values come from public/puzzles/dev.json, which was produced by the browser
# Web Crypto implementation.  If these pass, Python and browser are in sync.
# ---------------------------------------------------------------------------

KNOWN_HASHES: dict[str, dict] = {
    "CSK Players": {
        "items": ["MS Dhoni", "Ruturaj Gaikwad", "Deepak Chahar", "Ravindra Jadeja"],
        "expected": "753706144fc233169880b91c9005090779ac9a468be8f76632d9499979e891b3",
    },
    "Player Nicknames": {
        "items": ["Thala", "Hitman", "King", "Universe Boss"],
        "expected": "58d9d8330433ba08338a9f9834d8ff62cbdc165806cbddf6b7edbffea508d23a",
    },
}


def verify_known_hashes() -> bool:
    """Return True if all known hashes match.

    Used as a sanity check to confirm the Python implementation produces the
    same digests as the browser's Web Crypto SHA-256 routine.
    """
    all_ok = True
    for name, data in KNOWN_HASHES.items():
        got = hash_items(data["items"])
        ok = got == data["expected"]
        if not ok:
            print(f"  HASH MISMATCH for '{name}': got {got}")
            all_ok = False
    return all_ok


if __name__ == "__main__":
    ok = verify_known_hashes()
    print("PASS" if ok else "FAIL")
