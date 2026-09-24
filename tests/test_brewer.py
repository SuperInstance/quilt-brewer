"""Tests for quilt-brewer."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quilt_brewer import brew, BREW_RECIPES, run_brew, __version__


class TestBrewer(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.0")

    def test_recipes_dict(self):
        self.assertIsInstance(BREW_RECIPES, dict)
        self.assertGreater(len(BREW_RECIPES), 3)

    def test_each_recipe_has_required_keys(self):
        required = ["name", "substrate_kind", "polarity_rules", "description"]
        for rname, recipe in BREW_RECIPES.items():
            for k in required:
                self.assertIn(k, recipe, f"recipe {rname} missing {k}")

    def test_polarity_rules_have_three_states(self):
        for rname, recipe in BREW_RECIPES.items():
            rules = recipe["polarity_rules"]
            self.assertIn("ACCEPT", rules, f"{rname} missing ACCEPT")
            self.assertIn("DRIFT", rules, f"{rname} missing DRIFT")
            self.assertIn("REFUSE", rules, f"{rname} missing REFUSE")


class TestBrewProcess(unittest.TestCase):
    def test_brew_creates_files(self):
        with tempfile.TemporaryDirectory() as dest:
            result = brew("quilt-perception", dest)
            self.assertTrue(result["ok"], f"brew failed: {result}")

            self.assertEqual(len(result["files_written"]), 6)
            for f in result["files_written"]:
                self.assertTrue(os.path.exists(f), f"missing file: {f}")

    def test_brew_creates_testable_substrate(self):
        with tempfile.TemporaryDirectory() as dest:
            result = brew("quilt-perception", dest)
            self.assertTrue(result["ok"])
            self.assertGreater(result["tests_total"], 0)
            self.assertEqual(result["tests_pass"], result["tests_total"])

    def test_brew_creates_schema_compliant_substrate(self):
        with tempfile.TemporaryDirectory() as dest:
            result = brew("quilt-perception", dest)
            self.assertTrue(result["ok"])
            self.assertTrue(result["schema_compliant"])

    def test_brew_rejects_unknown_recipe(self):
        with tempfile.TemporaryDirectory() as dest:
            result = brew("does-not-exist", dest)
            self.assertFalse(result["ok"])
            self.assertIn("unknown recipe", result["error"])

    def test_brew_each_recipe(self):
        for rname in BREW_RECIPES:
            with tempfile.TemporaryDirectory() as dest:
                result = brew(rname, dest)
                self.assertTrue(result["ok"], f"brew {rname} failed: {result}")
                self.assertGreater(len(result["files_written"]), 0)


class TestBrewedSubstrate(unittest.TestCase):
    """The brewed substrate should be importable and work standalone."""

    def setUp(self):
        self.dest = tempfile.mkdtemp()
        brew("quilt-perception", self.dest)
        sys.path.insert(0, os.path.join(self.dest, "src"))
        self.addCleanup(self._cleanup_path)

    def _cleanup_path(self):
        sys.path = [p for p in sys.path if not p.endswith("src")]

    def test_can_import_brewed_substrate(self):
        from quilt_perception import SensorStreamSubstrate
        s = SensorStreamSubstrate()
        self.assertEqual(len(s.receipts), 0)

    def test_brewed_substrate_runs_through_polarities(self):
        from quilt_perception import SensorStreamSubstrate
        s = SensorStreamSubstrate()
        r1 = s.step("c1", {"v": 1}, "ok")
        r2 = s.step("c2", {"v": 2}, "warn")
        r3 = s.step("c3", {"v": 3}, "fail")
        r4 = s.step("c4", {"v": 4}, "ok")

        self.assertEqual(r1.polarity, "ACCEPT")
        self.assertEqual(r2.polarity, "DRIFT")
        self.assertEqual(r3.polarity, "REFUSE")
        self.assertEqual(r4.polarity, "ACCEPT")

        self.assertTrue(s.chain_intact())
        self.assertEqual(r2.prev_witness_id, r1.witness_id)
        self.assertEqual(r3.prev_witness_id, r2.witness_id)
        self.assertEqual(r4.prev_witness_id, r3.witness_id)


class TestBrewCLI(unittest.TestCase):
    def test_run_brew_returns_zero_on_success(self):
        with tempfile.TemporaryDirectory() as dest:
            import io
            from contextlib import redirect_stdout

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = run_brew("quilt-perception", dest)
            self.assertEqual(rc, 0)

    def test_run_brew_returns_nonzero_on_unknown(self):
        with tempfile.TemporaryDirectory() as dest:
            rc = run_brew("does-not-exist", dest)
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
