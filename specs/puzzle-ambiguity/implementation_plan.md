# Puzzle Ambiguity Fix — Implementation Plan

## Problem

When generating puzzles, a player can semantically qualify for more than one category. For example, Shane Watson qualifies as Australian (`country:Australia`), a top run scorer (`top_run_scorers`), AND played for both CSK & MI (`played_both:CSK:MI`). The current `exclude` set only prevents the same player appearing twice in one puzzle — it does not detect that a placed player is also a valid member of another category, creating solver ambiguity.

## Solution: Two Layers

1. **Automated layer** — detect ambiguity at generation time and attempt resampling automatically.
2. **Manual fallback layer** — when auto-resample fails or the curator notices issues after the fact, surgical fix flags on `schedule_runner.py` let the curator reshuffle a single color or manually override its items.

---

## Files to Change

| File | Type | What |
|---|---|---|
| `packages/puzzle-curator/ambiguity.py` | New | `get_candidate_pool()` + `check_ambiguity()` |
| `packages/puzzle-curator/category_generators.py` | Modify | Inject `"spec"` into `generate_category()` return dict |
| `packages/puzzle-curator/schedule_runner.py` | Modify | Ambiguity check + resample loop in `generate_puzzle()`; new `--reshuffle` and `--set-items` flags |
| `packages/puzzle-curator/generators/cross_team.py` | Modify | Rename `_LEGENDS_INDIA` → `LEGENDS_INDIA`, `_LEGENDS_OVERSEAS` → `LEGENDS_OVERSEAS` |

---

## Layer 1 — Automated Detection + Resample

### 1a. Create `ambiguity.py`

**`get_candidate_pool(ipl_data, spec) -> set[str]`**

Mirrors each generator's pool-computation logic but returns **all** valid candidates (no sampling, no exclusions). Returns `set()` for non-player categories (coaches, ipl_champions, team_owners).

Critical detail: `team_legends_batting` and `team_legends_bowling` must replicate the `[:12]` top-players cap that the generator uses — otherwise the ambiguity check produces false positives.

Dispatch table:

| Spec type | Pool source |
|---|---|
| `orange_cap`, `purple_cap`, `player_of_tournament`, `costliest_player`, `winning_captain` | `ipl_data["awards"]` filtered by type |
| `team_players:T:S` | `player_teams` where team+season match |
| `team_all_seasons:T` | `player_teams` where team matches |
| `winning_squad:S` | `ipl_wins` → winning team → `player_teams` |
| `top_run_scorers` | `batting_career_stats` where runs ≥ 3000 |
| `top_wicket_takers` | `bowling_career_stats` where wickets ≥ 100 |
| `most_fifties`, `most_matches` | all of `batting_career_stats` |
| `high_strike_rate` | `ipl_data["high_strike_rate_batsmen"]` |
| `highest_batting_avg` | `ipl_data["highest_batting_avg"]` |
| `catches_by_fielder` | `ipl_data["catches_by_fielder"]` |
| `dismissals_by_keeper` | `ipl_data["dismissals_by_keeper"]` |
| `allrounders` | `ipl_data["allrounders"]` (key: `name`) |
| `most_ducks` | `ipl_data["most_ducks"]` |
| `fifers` | `ipl_data["five_wicket_hauls"]` |
| `batting_records`, `bowling_records`, `season_records`, `fielding_records` | `ipl_data["records"][type]` |
| `team_legends_batting:T` | batting stats ∩ team players → **top 12 by runs** |
| `team_legends_bowling:T` | bowling stats ∩ team players → **top 12 by wickets** |
| `country:C` | `foreign_players` where country matches |
| `state:S` | `ipl_data["india_state_wise"][S]` |
| `ranji:T` | `ipl_data["ranji_team_wise"][T]` |
| `played_both:T1:T2` | `player_teams` grouped by player, filter to those with both teams |
| `multi_team:N` | `multi_team_players` where team_count ≥ N |
| `longest_serving` | top 20 players by distinct seasons in `player_teams` |
| `legends:india` | `LEGENDS_INDIA` from `generators.cross_team` |
| `legends:overseas` | `LEGENDS_OVERSEAS` from `generators.cross_team` |
| coaches, ipl_champions, team_owners, unknown | `set()` |

**`check_ambiguity(ipl_data, categories) -> list[tuple[str, str, str]]`**

```
Input:  categories = [{"color", "title", "items": [4 names], "spec"}, ...]
Output: list of (item_name, placed_in_color, also_qualifies_for_color)

For each category C_i, get pool_i = get_candidate_pool(ipl_data, C_i["spec"])
For each item in C_i["items"]:
  For each other category C_j:
    if item in pool_j → record (item, C_i.color, C_j.color)
```

### 1b. Modify `category_generators.py`

In `generate_category()` (line 391), inject spec into result at both return sites:

```python
result = gen_fn(ipl_data, params, exclude)   # existing line
result["spec"] = spec                         # add this
return result
```

Same for the coaches special-dispatch block (2 return sites).

### 1c. Modify `schedule_runner.py`: `generate_puzzle()`

Add import: `from ambiguity import check_ambiguity`

After generating all 4 categories, before writing the file:

```python
MAX_RESAMPLE = 10

conflicts = check_ambiguity(ipl_data, categories)

for attempt in range(MAX_RESAMPLE):
    if not conflicts:
        break
    target_color = most_conflicted_color(conflicts)  # color with most conflict entries
    target_idx   = COLORS.index(target_color)
    target_spec  = categories[target_idx]["spec"]

    other_items = {item for cat in categories if cat["color"] != target_color
                        for item in cat["items"]}
    resample_exclude = used_items.get(target_spec, set()) | other_items

    try:
        new_result = generate_category(ipl_data, target_spec, resample_exclude)
        categories[target_idx]["items"] = new_result["items"]
    except ValueError:
        break  # pool exhausted

    conflicts = check_ambiguity(ipl_data, categories)

if conflicts:
    print("  AMBIGUITY WARNING — unresolved after resampling:")
    for item, placed, also in conflicts:
        print(f"    '{item}' in {placed.upper()} also fits {also.upper()}")
    print("  Use --reshuffle or --set-items to fix manually.")
else:
    print("  AMBIGUITY CHECK: PASS")
```

### 1d. Modify `generators/cross_team.py`

Rename:
- `_LEGENDS_INDIA` → `LEGENDS_INDIA` (update 2 internal usages)
- `_LEGENDS_OVERSEAS` → `LEGENDS_OVERSEAS` (update 2 internal usages)

---

## Layer 2 — Manual Fix Flags (fallback)

### New flags on `schedule_runner.py`

Add to `build_parser()`:

```python
parser.add_argument(
    "--reshuffle",
    metavar="COLOR",
    choices=COLORS,
    help="Re-sample one category in the existing puzzle for --date (new random draw, same spec)"
)
parser.add_argument(
    "--set-items",
    metavar="COLOR:p1,p2,p3,p4",
    help="Replace 4 items in one category and regenerate its hash (requires --date)"
)
```

Both require `--date`. Both modify the existing puzzle file in-place (implied `--force`).

### `cmd_reshuffle(args, ipl_data, output_dir, used_items)`

```
1. Load puzzle JSON from output_dir/date.json (error if not found)
2. Find category for args.reshuffle color, read its "spec"
3. Build exclude = items from other 3 categories + used_items[spec] (skip_date=args.date)
4. Call generate_category(ipl_data, spec, exclude) → new 4 items
5. Update category["items"] and category["hash"] = hash_items(new items)
6. Rebuild puzzle["items"] = _shuffle(all 16 items)
7. Write JSON back
8. Print: old items → new items
```

### `cmd_set_items(args, output_dir)`

```
1. Parse "COLOR:p1,p2,p3,p4" → color + list of 4 names
2. Load puzzle JSON
3. Find category for color
4. Update category["items"] = new_items
5. Update category["hash"] = hash_items(new_items)
6. Rebuild puzzle["items"] = _shuffle(all 16 items)
7. Write JSON back
8. Print confirmation
```

### Dispatch in `main()` (early return before schedule loop)

```python
if args.reshuffle:
    if not args.date:
        print("ERROR: --reshuffle requires --date"); return 1
    ipl_data = load_ipl_data(data_path)
    used_items = load_used_items(output_dir, skip_date=args.date)
    return cmd_reshuffle(args, ipl_data, output_dir, used_items)

if args.set_items:
    if not args.date:
        print("ERROR: --set-items requires --date"); return 1
    return cmd_set_items(args, output_dir)
```

---

## Example Usage

```bash
# Normal generation — auto-detects and resamples ambiguity:
python schedule_runner.py --date 2026-03-28

# If ambiguity warning remains, reshuffle the blue category (new random draw, same spec):
python schedule_runner.py --date 2026-03-28 --reshuffle blue

# Or manually set specific players for purple:
python schedule_runner.py --date 2026-03-28 --set-items "purple:SR Watson,MA Agarwal,SK Raina,V Kohli"
```

---

## Verification

1. Generate a known-ambiguous puzzle (e.g., `country:Australia` + `top_run_scorers` in same puzzle).
2. Confirm auto-resample runs and either resolves the conflict or prints a warning.
3. If warning remains, run `--reshuffle` and confirm different 4 players, other 3 categories unchanged.
4. Run `--set-items` and confirm exact player names, hash recalculated.
5. Load puzzle JSON in browser — hashes must still verify correctly.
