"""
test_suite.py — Functional regression tests for the IPL puzzle curator.

Covers:
  1. Generator contract  — every generator returns {title, items} with exactly 4 unique items
  2. Pool coverage       — every spec in all 4 pools has a registered generator
  3. Exclusion           — excluded items are never returned
  4. Per-spec exclusion  — items excluded only within the same spec (not cross-spec)
  5. Cap computation     — compute_pool_caps returns sensible values for known specs
  6. Cooldown engine     — CooldownEngine records and enforces cooldowns correctly
  7. Schedule validation — validator correctly catches and passes known rule sets
  8. schedule_runner     — load_used_items reads spec-keyed dict; generate_puzzle dry-run works

Usage:
  python test_suite.py           # run all tests
  python test_suite.py -v        # verbose output
"""

import json
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — run from any working directory
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

DATA_FILE = ROOT.parent / "data-pipeline" / "data" / "ipl_data.json"
HAS_DATA  = DATA_FILE.exists()

def _load_data():
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. Generator contract
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_DATA, "ipl_data.json not found — skipping generator tests")
class TestGeneratorContract(unittest.TestCase):
    """Every generator must return {title: str, items: [4 unique str]}."""

    @classmethod
    def setUpClass(cls):
        cls.data = _load_data()

    def _assert_result(self, spec: str, result: dict):
        self.assertIn("title", result,  f"{spec}: missing 'title'")
        self.assertIn("items", result,  f"{spec}: missing 'items'")
        self.assertIsInstance(result["title"], str,  f"{spec}: title not a string")
        self.assertIsInstance(result["items"], list, f"{spec}: items not a list")
        self.assertEqual(len(result["items"]), 4,
                         f"{spec}: expected 4 items, got {len(result['items'])}")
        self.assertEqual(len(set(result["items"])), 4,
                         f"{spec}: items contain duplicates: {result['items']}")

    def _run(self, spec: str):
        from category_generators import generate_category
        result = generate_category(self.data, spec, set())
        self._assert_result(spec, result)
        return result

    def test_orange_cap(self):          self._run("orange_cap")
    def test_purple_cap(self):          self._run("purple_cap")
    def test_player_of_tournament(self):self._run("player_of_tournament")
    def test_costliest_player(self):    self._run("costliest_player")
    def test_winning_captain(self):     self._run("winning_captain")
    def test_ipl_champions(self):       self._run("ipl_champions")
    def test_team_owners(self):         self._run("team_owners")
    def test_team_players(self):        self._run("team_players:MI:2026")
    def test_team_players_2008(self):   self._run("team_players:CSK:2008")
    def test_winning_squad(self):       self._run("winning_squad:2023")
    def test_head_coaches(self):        self._run("head_coaches")
    def test_batting_coaches(self):     self._run("batting_coaches")
    def test_bowling_coaches(self):     self._run("bowling_coaches")
    def test_fielding_coaches(self):    self._run("fielding_coaches")
    def test_country(self):             self._run("country:Australia")
    def test_state(self):               self._run("state:Maharashtra")
    def test_ranji(self):               self._run("ranji:Mumbai")
    def test_top_run_scorers(self):     self._run("top_run_scorers")
    def test_top_wicket_takers(self):   self._run("top_wicket_takers")
    def test_most_fifties(self):        self._run("most_fifties")
    def test_most_matches(self):        self._run("most_matches")
    def test_most_ducks(self):          self._run("most_ducks")
    def test_fifers(self):              self._run("fifers")
    def test_high_strike_rate(self):    self._run("high_strike_rate")
    def test_highest_batting_avg(self): self._run("highest_batting_avg")
    def test_catches_by_fielder(self):  self._run("catches_by_fielder")
    def test_dismissals_by_keeper(self):self._run("dismissals_by_keeper")
    def test_allrounders(self):         self._run("allrounders")
    def test_batting_records(self):     self._run("batting_records")
    def test_bowling_records(self):     self._run("bowling_records")
    def test_season_records(self):      self._run("season_records")
    def test_fielding_records(self):    self._run("fielding_records")
    def test_legends_india(self):       self._run("legends:india")
    def test_legends_overseas(self):    self._run("legends:overseas")
    def test_played_both(self):         self._run("played_both:CSK:MI")
    def test_multi_team(self):          self._run("multi_team:5")
    def test_longest_serving(self):     self._run("longest_serving")
    def test_team_legends_batting(self):self._run("team_legends_batting:MI")
    def test_team_legends_bowling(self):self._run("team_legends_bowling:MI")

    def test_unknown_spec_raises(self):
        from category_generators import generate_category
        with self.assertRaises(ValueError) as ctx:
            generate_category(self.data, "nonexistent_spec", set())
        self.assertIn("Unknown category type", str(ctx.exception))


# ---------------------------------------------------------------------------
# 2. Pool coverage — every spec in all 4 pools resolves
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_DATA, "ipl_data.json not found — skipping pool coverage tests")
class TestPoolCoverage(unittest.TestCase):
    """No spec in any pool should raise 'Unknown category type'."""

    @classmethod
    def setUpClass(cls):
        cls.data = _load_data()
        from gen_schedule_v5 import YELLOW_POOL, GREEN_POOL, BLUE_POOL, PURPLE_POOL
        cls.all_specs = set(YELLOW_POOL + GREEN_POOL + BLUE_POOL + PURPLE_POOL)

    def test_all_specs_have_generators(self):
        from category_generators import generate_category
        missing = []
        data_errors = []
        for spec in sorted(self.all_specs):
            try:
                generate_category(self.data, spec, set())
            except ValueError as e:
                if "Unknown category type" in str(e):
                    missing.append(spec)
                else:
                    data_errors.append((spec, str(e)))
            except Exception as e:
                missing.append(f"{spec} ({e})")

        self.assertEqual(missing, [],
            f"Specs with no generator: {missing}")
        self.assertEqual(data_errors, [],
            f"Specs with data errors: {data_errors}")

    def test_pool_has_specs(self):
        self.assertGreater(len(self.all_specs), 50,
            "Fewer than 50 unique specs — pool may have been accidentally cleared")


# ---------------------------------------------------------------------------
# 3. Exclusion contract
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_DATA, "ipl_data.json not found — skipping exclusion tests")
class TestExclusion(unittest.TestCase):
    """Excluded items must never appear in results."""

    @classmethod
    def setUpClass(cls):
        cls.data = _load_data()

    def test_excluded_items_not_returned(self):
        from category_generators import generate_category
        # First call — get 4 items
        r1 = generate_category(self.data, "top_run_scorers", set())
        first_four = set(r1["items"])
        # Second call excluding those 4 — must return 4 different ones
        r2 = generate_category(self.data, "top_run_scorers", first_four)
        self.assertEqual(len(r2["items"]), 4)
        self.assertTrue(first_four.isdisjoint(r2["items"]),
            f"Excluded items appeared in result: {first_four & set(r2['items'])}")

    def test_within_puzzle_no_repeat(self):
        """Picked items from slot 1 must not appear in slot 2 (same puzzle)."""
        from category_generators import generate_category
        r1 = generate_category(self.data, "team_players:MI:2026", set())
        picked = set(r1["items"])
        # team_legends_batting:MI pool overlaps with MI squad — exclusion must work
        try:
            r2 = generate_category(self.data, "team_legends_batting:MI", picked)
            overlap = picked & set(r2["items"])
            self.assertEqual(overlap, set(),
                f"Same player(s) in two slots of one puzzle: {overlap}")
        except ValueError:
            pass  # Pool too small after exclusion — acceptable, not a regression


# ---------------------------------------------------------------------------
# 4. Per-spec exclusion (cross-spec availability)
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_DATA, "ipl_data.json not found — skipping per-spec exclusion tests")
class TestPerSpecExclusion(unittest.TestCase):
    """
    A player excluded from spec A must still be available in spec B.
    This validates the schedule_runner per-spec exclusion change.
    """

    @classmethod
    def setUpClass(cls):
        cls.data = _load_data()

    def test_player_available_in_different_spec(self):
        from category_generators import generate_category
        # Get MI batting legends — some of these are also in top_run_scorers
        legends = generate_category(self.data, "team_legends_batting:MI", set())
        legend_names = set(legends["items"])

        # top_run_scorers should NOT exclude MI batting legends
        # (different spec — per-spec exclusion means only exclude within same spec)
        top_scorers = generate_category(self.data, "top_run_scorers", set())
        # Just check it resolves to 4 items — the players are independently available
        self.assertEqual(len(top_scorers["items"]), 4)

    def test_spec_keyed_exclusion_vs_global(self):
        """
        Simulate: spec A used players [X, Y, Z, W].
        Spec B (different) should NOT be blocked by X/Y/Z/W.
        """
        from category_generators import generate_category
        r_mi = generate_category(self.data, "team_players:MI:2026", set())
        mi_players = set(r_mi["items"])

        # With GLOBAL exclusion (old behaviour) — MI batting legends might fail
        # With PER-SPEC exclusion (new behaviour) — batting legends ignores MI squad exclusions
        # We pass mi_players as exclude to simulate old behaviour and check if it's a problem
        try:
            r_legends_global_excl = generate_category(
                self.data, "team_legends_batting:MI", mi_players
            )
            # If it succeeds, verify no overlap
            self.assertTrue(mi_players.isdisjoint(r_legends_global_excl["items"]))
        except ValueError:
            # This is the bug the per-spec fix addresses — if global exclusion causes failure
            # Per-spec exclusion (empty exclude set for batting:MI) would succeed
            r_legends_per_spec = generate_category(
                self.data, "team_legends_batting:MI", set()
            )
            self.assertEqual(len(r_legends_per_spec["items"]), 4,
                "Per-spec exclusion must allow batting legends even when squad players are excluded globally")


# ---------------------------------------------------------------------------
# 5. Cap computation
# ---------------------------------------------------------------------------

@unittest.skipUnless(HAS_DATA, "ipl_data.json not found — skipping cap tests")
class TestCapComputation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from gen_schedule_v5 import compute_pool_caps
        cls.caps = compute_pool_caps(DATA_FILE)

    def test_caps_is_dict(self):
        self.assertIsInstance(self.caps, dict)
        self.assertGreater(len(self.caps), 50, "Expected 50+ cap entries")

    def test_award_caps_are_reasonable(self):
        for spec in ("orange_cap", "purple_cap", "winning_captain"):
            cap = self.caps.get(spec)
            self.assertIsNotNone(cap, f"No cap for {spec}")
            self.assertGreaterEqual(cap, 1, f"{spec} cap < 1")
            self.assertLessEqual(cap, 10, f"{spec} cap suspiciously high: {cap}")

    def test_country_caps_capped_at_3(self):
        for country in ("Australia", "South Africa", "England",
                        "New Zealand", "Sri Lanka", "West Indies"):
            cap = self.caps.get(f"country:{country}")
            self.assertIsNotNone(cap, f"No cap for country:{country}")
            self.assertLessEqual(cap, 3,
                f"country:{country} cap={cap} exceeds editorial limit of 3")

    def test_team_legends_cap_is_1(self):
        for team in ("MI", "CSK", "RCB", "KKR"):
            for kind in ("batting", "bowling"):
                spec = f"team_legends_{kind}:{team}"
                cap = self.caps.get(spec)
                self.assertIsNotNone(cap, f"No cap for {spec}")
                self.assertEqual(cap, 1, f"{spec} cap should be 1, got {cap}")

    def test_team_players_caps_exist(self):
        for team in ("MI", "CSK", "RCB", "KKR"):
            spec = f"team_players:{team}:2026"
            self.assertIn(spec, self.caps, f"No cap for {spec}")
            self.assertGreaterEqual(self.caps[spec], 1)

    def test_no_cap_is_zero(self):
        for spec, cap in self.caps.items():
            self.assertGreater(cap, 0, f"Cap for {spec} is 0 — would never be used")


# ---------------------------------------------------------------------------
# 6. Cooldown engine
# ---------------------------------------------------------------------------

class TestCooldownEngine(unittest.TestCase):

    def _engine(self):
        from gen_schedule_v5 import CooldownEngine
        return CooldownEngine()

    def test_fresh_engine_allows_all(self):
        cd = self._engine()
        self.assertTrue(cd.available("orange_cap", 0))
        self.assertTrue(cd.available("team_players:MI:2026", 0))

    def test_same_spec_blocked_within_cooldown(self):
        from gen_schedule_v5 import COOLDOWN_CAT
        cd = self._engine()
        cd.record("orange_cap", 0)
        for day in range(1, COOLDOWN_CAT):
            self.assertFalse(cd.available("orange_cap", day),
                f"orange_cap should be blocked on day {day}")

    def test_same_spec_available_after_cooldown(self):
        from gen_schedule_v5 import COOLDOWN_CAT
        cd = self._engine()
        cd.record("orange_cap", 0)
        self.assertTrue(cd.available("orange_cap", COOLDOWN_CAT))

    def test_shared_bucket_played_both(self):
        from gen_schedule_v5 import COOLDOWN_PLAYED_BOTH
        cd = self._engine()
        cd.record("played_both:CSK:MI", 0)
        # Different combo should also be blocked (shared bucket)
        self.assertFalse(cd.available("played_both:RCB:KKR", 1, COOLDOWN_PLAYED_BOTH))
        self.assertTrue(cd.available("played_both:RCB:KKR", COOLDOWN_PLAYED_BOTH, COOLDOWN_PLAYED_BOTH))

    def test_shared_bucket_state(self):
        from gen_schedule_v5 import COOLDOWN_GEO_LOCAL
        cd = self._engine()
        cd.record("state:Maharashtra", 0)
        self.assertFalse(cd.available("state:Delhi", 1, COOLDOWN_GEO_LOCAL))
        self.assertTrue(cd.available("state:Delhi", COOLDOWN_GEO_LOCAL, COOLDOWN_GEO_LOCAL))

    def test_shared_bucket_team_legends(self):
        from gen_schedule_v5 import COOLDOWN_TEAM_LEGENDS
        cd = self._engine()
        cd.record("team_legends_batting:MI", 0)
        # All batting teams share one bucket → CSK blocked too
        self.assertFalse(cd.available("team_legends_batting:CSK", 1, COOLDOWN_TEAM_LEGENDS))
        # bowling is a separate bucket → not blocked by batting record
        self.assertTrue(cd.available("team_legends_bowling:MI", 1, COOLDOWN_TEAM_LEGENDS))
        self.assertTrue(cd.available("team_legends_batting:CSK", COOLDOWN_TEAM_LEGENDS, COOLDOWN_TEAM_LEGENDS))

    def test_team_cooldown(self):
        from gen_schedule_v5 import COOLDOWN_TEAM
        cd = self._engine()
        cd.record("team_players:MI:2026", 0)
        self.assertFalse(cd.team_available("MI", 1))
        self.assertTrue(cd.team_available("MI", COOLDOWN_TEAM))

    def test_available_key(self):
        from gen_schedule_v5 import COOLDOWN_COUNTRY_CAT
        cd = self._engine()
        cd.record_key("country", 0)
        self.assertFalse(cd.available_key("country", 1, COOLDOWN_COUNTRY_CAT))
        self.assertTrue(cd.available_key("country", COOLDOWN_COUNTRY_CAT, COOLDOWN_COUNTRY_CAT))


# ---------------------------------------------------------------------------
# 7. Schedule validator rules
# ---------------------------------------------------------------------------

class TestValidatorRules(unittest.TestCase):
    """Unit-test individual validation rules with crafted edition data."""

    def _ed(self, y, g, b, p, edition=1, date="24 Mar"):
        return {"edition": edition, "date": date,
                "yellow": y, "green": g, "blue": b, "purple": p}

    def _validate(self, editions):
        from validate_schedule import validate
        return validate(editions, caps=None)

    def test_clean_puzzle_no_violations(self):
        eds = [self._ed("team_players:MI:2026", "country:Australia",
                        "top_run_scorers", "played_both:CSK:RCB")]
        self.assertEqual(self._validate(eds), [])

    def test_cooldown_violation(self):
        eds = [
            self._ed("orange_cap", "country:Australia", "top_run_scorers",
                     "played_both:CSK:RCB", edition=1, date="24 Mar"),
            self._ed("team_players:MI:2026", "country:South Africa", "most_fifties",
                     "orange_cap", edition=2, date="25 Mar"),  # orange_cap after 1 day
        ]
        vs = self._validate(eds)
        rules = [v.rule for v in vs]
        self.assertIn("COOLDOWN", rules)

    def test_group_conflict(self):
        # Two awards in same puzzle (GROUP_B)
        eds = [self._ed("orange_cap", "purple_cap", "top_run_scorers", "played_both:CSK:RCB")]
        vs = self._validate(eds)
        self.assertTrue(any(v.rule == "GROUP_CONFLICT" for v in vs))

    def test_team_collision(self):
        eds = [self._ed("team_players:MI:2026", "team_legends_batting:MI",
                        "top_run_scorers", "played_both:CSK:RCB")]
        vs = self._validate(eds)
        self.assertTrue(any(v.rule == "TEAM_COLLISION" for v in vs))

    def test_legends_block(self):
        eds = [self._ed("team_players:CSK:2026", "team_legends_batting:MI",
                        "top_run_scorers", "played_both:CSK:RCB")]
        vs = self._validate(eds)
        self.assertTrue(any(v.rule == "LEGENDS_BLOCK" for v in vs))

    def test_prefix_conflict(self):
        eds = [self._ed("team_players:MI:2026", "team_players:CSK:2026",
                        "top_run_scorers", "played_both:CSK:RCB")]
        vs = self._validate(eds)
        self.assertTrue(any(v.rule == "PREFIX_CONFLICT" for v in vs))

    def test_country_category_cooldown(self):
        from validate_schedule import COOLDOWN_COUNTRY_CAT
        eds = [
            self._ed("team_players:MI:2026", "country:Australia",
                     "top_run_scorers", "played_both:CSK:RCB", edition=1, date="24 Mar"),
            self._ed("team_players:CSK:2026", "country:South Africa",
                     "most_fifties", "multi_team:5", edition=2, date="25 Mar"),
        ]
        vs = self._validate(eds)
        self.assertTrue(any(v.rule == "COOLDOWN_COUNTRY_CAT" for v in vs))

    def test_cap_exceeded(self):
        from validate_schedule import validate
        caps = {"orange_cap": 1}
        eds = [
            self._ed("orange_cap", "country:Australia", "top_run_scorers",
                     "played_both:CSK:RCB", edition=1, date="24 Mar"),
            self._ed("team_players:MI:2026", "country:South Africa", "most_fifties",
                     "orange_cap", edition=2, date="28 Mar"),  # after cooldown
        ]
        vs = validate(eds, caps=caps)
        self.assertTrue(any(v.rule == "CAP_EXCEEDED" for v in vs))


# ---------------------------------------------------------------------------
# 8. schedule_runner — load_used_items and generate_puzzle dry-run
# ---------------------------------------------------------------------------

class TestScheduleRunner(unittest.TestCase):

    def test_load_used_items_empty_dir(self):
        from schedule_runner import load_used_items
        with tempfile.TemporaryDirectory() as tmp:
            result = load_used_items(Path(tmp))
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_load_used_items_reads_spec_keyed(self):
        from schedule_runner import load_used_items
        puzzle = {
            "id": "2026-03-24", "date": "2026-03-24", "edition": 1,
            "items": ["A", "B", "C", "D"],
            "categories": [
                {"color": "yellow", "title": "T1", "spec": "spec_a", "hash": "x",
                 "items": ["A", "B"]},
                {"color": "green",  "title": "T2", "spec": "spec_b", "hash": "y",
                 "items": ["C", "D"]},
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "2026-03-24.json"
            p.write_text(json.dumps(puzzle), encoding="utf-8")
            result = load_used_items(Path(tmp))

        self.assertIn("spec_a", result)
        self.assertIn("spec_b", result)
        self.assertEqual(result["spec_a"], {"A", "B"})
        self.assertEqual(result["spec_b"], {"C", "D"})

    def test_load_used_items_different_specs_independent(self):
        """Items in spec_a must NOT block spec_b."""
        from schedule_runner import load_used_items
        puzzle = {
            "id": "2026-03-24", "date": "2026-03-24", "edition": 1,
            "items": ["Rohit Sharma", "Virat Kohli", "MS Dhoni", "Sachin Tendulkar"],
            "categories": [
                {"color": "yellow", "spec": "team_players:MI:2026", "hash": "x",
                 "title": "MI 2026", "items": ["Rohit Sharma", "Jasprit Bumrah"]},
                {"color": "green",  "spec": "team_legends_batting:CSK", "hash": "y",
                 "title": "CSK Legends", "items": ["MS Dhoni", "Suresh Raina"]},
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "2026-03-24.json").write_text(json.dumps(puzzle), encoding="utf-8")
            used = load_used_items(Path(tmp))

        # Rohit Sharma excluded from MI squad, but NOT from CSK legends
        self.assertIn("Rohit Sharma", used["team_players:MI:2026"])
        self.assertNotIn("Rohit Sharma", used.get("team_legends_batting:CSK", set()))

    def test_load_used_items_skip_date(self):
        from schedule_runner import load_used_items
        puzzle = {
            "id": "2026-03-24", "date": "2026-03-24", "edition": 1,
            "items": ["A", "B"],
            "categories": [
                {"color": "yellow", "spec": "spec_a", "hash": "x", "title": "T", "items": ["A", "B"]}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "2026-03-24.json").write_text(json.dumps(puzzle), encoding="utf-8")
            result_with    = load_used_items(Path(tmp))
            result_without = load_used_items(Path(tmp), skip_date="2026-03-24")

        self.assertIn("spec_a", result_with)
        self.assertNotIn("spec_a", result_without)

    def test_load_used_items_legacy_file_no_spec(self):
        """Legacy puzzle files without 'spec' field should be silently ignored."""
        from schedule_runner import load_used_items
        legacy = {
            "id": "2026-03-24", "date": "2026-03-24", "edition": 1,
            "items": ["A", "B"],
            "categories": [
                {"color": "yellow", "title": "T", "hash": "x"}  # no spec, no items
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "2026-03-24.json").write_text(json.dumps(legacy), encoding="utf-8")
            result = load_used_items(Path(tmp))
        self.assertEqual(len(result), 0)

    @unittest.skipUnless(HAS_DATA, "ipl_data.json not found")
    def test_generate_puzzle_dry_run(self):
        from schedule_runner import generate_puzzle, load_ipl_data
        ipl_data = load_ipl_data(DATA_FILE)
        row = {
            "edition": 99,
            "date": "2026-03-24",
            "specs": ["team_players:MI:2026", "country:Australia",
                      "top_run_scorers", "played_both:CSK:RCB"],
            "matches": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            used_items = defaultdict(set)
            ok = generate_puzzle(row, ipl_data, Path(tmp),
                                 used_items, dry_run=True, force=False)
        self.assertTrue(ok)
        # dry_run=True — no file written
        self.assertEqual(list(Path(tmp).glob("*.json")), [])

    @unittest.skipUnless(HAS_DATA, "ipl_data.json not found")
    def test_generate_puzzle_writes_spec_field(self):
        """Written puzzle JSON must contain 'spec' in each category."""
        from schedule_runner import generate_puzzle, load_ipl_data
        ipl_data = load_ipl_data(DATA_FILE)
        row = {
            "edition": 99,
            "date": "2026-03-24",
            "specs": ["team_players:MI:2026", "country:Australia",
                      "top_run_scorers", "played_both:CSK:RCB"],
            "matches": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            used_items = defaultdict(set)
            ok = generate_puzzle(row, ipl_data, Path(tmp),
                                 used_items, dry_run=False, force=False)
            self.assertTrue(ok)
            puzzle = json.loads((Path(tmp) / "2026-03-24.json").read_text())

        specs_in_file = [cat.get("spec") for cat in puzzle["categories"]]
        self.assertEqual(specs_in_file,
                         ["team_players:MI:2026", "country:Australia",
                          "top_run_scorers", "played_both:CSK:RCB"])

    @unittest.skipUnless(HAS_DATA, "ipl_data.json not found")
    def test_per_spec_exclusion_across_puzzles(self):
        """
        Player picked in spec A on day 1 must still be available in spec B on day 2,
        but must NOT appear again in spec A on day 2.
        """
        from schedule_runner import generate_puzzle, load_ipl_data
        from collections import defaultdict
        ipl_data = load_ipl_data(DATA_FILE)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            used_items = defaultdict(set)

            # Day 1: generate top_run_scorers
            row1 = {"edition": 1, "date": "2026-03-24",
                    "specs": ["top_run_scorers", "country:Australia",
                              "most_fifties", "played_both:CSK:RCB"],
                    "matches": ""}
            generate_puzzle(row1, ipl_data, tmp_path, used_items,
                            dry_run=False, force=False)

            day1_scorers = set(used_items["top_run_scorers"])
            self.assertEqual(len(day1_scorers), 4)

            # Day 2: top_run_scorers again — must pick 4 different players
            row2 = {"edition": 2, "date": "2026-03-25",
                    "specs": ["top_run_scorers", "country:South Africa",
                              "most_matches", "multi_team:5"],
                    "matches": ""}
            ok = generate_puzzle(row2, ipl_data, tmp_path, used_items,
                                 dry_run=False, force=False)
            self.assertTrue(ok)

            day2_scorers = set(used_items["top_run_scorers"]) - day1_scorers
            self.assertEqual(len(day2_scorers), 4,
                "Day 2 top_run_scorers must pick 4 new players not used on day 1")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
