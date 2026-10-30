"""F4 CSV/aggregation regressions; these tests require only the standard library."""
import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from experiments.plot_data import (Run, check_heuristics, geometric_mean, paired_values,
                                   read_runs, summarize, validate_summary)


def measured(level: str, series: str, nodes: int = 4, seconds: float = 1,
             mode: str = "unit") -> Run:
    """Create a complete measurement on one condition."""
    values = {"time_sec": seconds, "peak_memory_kb": 10., "expanded_nodes": float(nodes),
              "length": 2., "cost": 2., "h_start": 0., "optimal_cost": 2.,
              "tightness": 0., "node_ratio": nodes / 4, "time_ratio": seconds}
    return Run("g1", level, mode, series, True, values, "", True)


class TestPlotData(unittest.TestCase):
    """Protect fair pairing, failure handling and interpretation of F3 summaries."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "data.csv"

    def write(self, rows: list[dict]) -> None:
        """Write small CSV inputs with the same header semantics as F3."""
        with self.path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def row(self, **changes: object) -> dict:
        """Return one standard solver CSV row."""
        result = {"group": "g1", "level": "g1_basic_01", "cost_mode": "unit", "solver": "bfs",
                  "solved": "True", "length": "2", "cost": "2", "expanded_nodes": "4",
                  "time_sec": "0.1", "peak_memory_kb": "10", "note": ""}
        result.update(changes)
        return result

    def test_false_is_not_truthy_and_missing_solution_metrics_stay_absent(self) -> None:
        self.write([self.row(solved="False", length="", cost="", expanded_nodes="",
                             note="timeout")])
        run = read_runs(self.path)[0]
        self.assertFalse(run.solved)
        self.assertIsNone(run.values["length"])
        self.assertIsNone(run.values["cost"])
        self.assertIsNone(run.values["expanded_nodes"])

    def test_bad_boolean_nonfinite_negative_or_fractional_counts_are_rejected(self) -> None:
        for changes in ({"solved": "maybe"}, {"time_sec": "nan"}, {"cost": "inf"},
                        {"peak_memory_kb": "-1"}, {"expanded_nodes": "2.5"},
                        {"length": ""}, {"note": "invalid_path"}):
            with self.subTest(changes=changes):
                self.write([self.row(**changes)])
                with self.assertRaises(ValueError):
                    read_runs(self.path)

    def test_duplicate_conditions_and_missing_headers_are_rejected(self) -> None:
        self.write([self.row(), self.row()])
        with self.assertRaises(ValueError):
            read_runs(self.path)
        self.path.write_text("level,solver\ng1_basic_01,bfs\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing columns"):
            read_runs(self.path)

    def test_geometric_mean_is_not_the_arithmetic_mean(self) -> None:
        self.assertAlmostEqual(geometric_mean([.25, 4]), 1)
        self.assertIsNone(geometric_mean([None]))

    def test_pairing_keeps_cost_modes_separate(self) -> None:
        rows = [measured("g1_basic_01", "zero"), measured("g1_basic_01", "advanced", 1),
                measured("g1_basic_01", "zero", mode="weighted"),
                measured("g1_basic_01", "advanced", 8, mode="weighted")]
        unit, _ = paired_values(rows, "unit", "expanded_nodes")
        weighted, _ = paired_values(rows, "weighted", "expanded_nodes")
        self.assertEqual(unit["advanced"], [.25])
        self.assertEqual(weighted["advanced"], [2])

    def test_failed_or_missing_heuristic_excludes_the_level_for_every_series(self) -> None:
        rows = [measured("g1_basic_01", "zero"), measured("g1_basic_01", "advanced", 1),
                measured("g1_basic_02", "zero"),
                replace(measured("g1_basic_02", "advanced"), solved=False, note="timeout"),
                measured("g1_basic_03", "zero")]
        values, total = paired_values(rows, "unit", "expanded_nodes")
        self.assertEqual(total, 3)
        self.assertEqual(values, {"zero": [1], "advanced": [.25]})

    def test_zero_timing_does_not_become_a_false_ratio_win(self) -> None:
        rows = [measured("g1_basic_01", "zero"),
                measured("g1_basic_01", "advanced", seconds=0)]
        values, total = paired_values(rows, "unit", "time_sec")
        self.assertEqual(total, 1)
        self.assertEqual(values, {"zero": [], "advanced": []})

    def test_nonoptimal_or_rounded_zero_ratio_excludes_the_common_condition(self) -> None:
        zero = measured("g1_basic_01", "zero")
        advanced = measured("g1_basic_01", "advanced", 1)
        for bad in (replace(advanced, optimal=False),
                    replace(advanced, values={**advanced.values, "time_ratio": 0})):
            with self.subTest(bad=bad):
                values, total = paired_values([zero, bad], "unit", "time_sec")
                self.assertEqual(total, 1)
                self.assertEqual(values, {"zero": [], "advanced": []})

    def test_ties_count_for_all_winners(self) -> None:
        rows = [measured("g1_basic_01", "zero"), measured("g1_basic_01", "advanced")]
        result = summarize(rows)
        self.assertEqual(result["unit", "all", "zero"]["node_wins"], 1)
        self.assertEqual(result["unit", "all", "advanced"]["node_wins"], 1)

    def test_derived_ratios_and_missing_baseline_are_checked(self) -> None:
        rows = [measured("g1_basic_01", "zero"), measured("g1_basic_01", "advanced", 1)]
        check_heuristics(rows)
        with self.assertRaisesRegex(ValueError, "Missing zero"):
            check_heuristics(rows[1:])
        broken = replace(rows[1], values={**rows[1].values, "node_ratio": .9})
        with self.assertRaisesRegex(ValueError, "node_ratio"):
            check_heuristics([rows[0], broken])

    def test_summary_is_verified_and_stale_values_are_rejected(self) -> None:
        runs = [measured("g1_basic_01", "zero"), measured("g1_basic_01", "advanced", 1)]
        rows = [{"cost_mode": mode, "group": group, "heuristic": series, **values}
                for (mode, group, series), values in summarize(runs).items()]
        self.write(rows)
        validate_summary(self.path, runs)
        rows[0]["geo_node_ratio"] = 9
        self.write(rows)
        with self.assertRaisesRegex(ValueError, "geo_node_ratio"):
            validate_summary(self.path, runs)
        self.write(rows[1:])
        with self.assertRaisesRegex(ValueError, "conditions"):
            validate_summary(self.path, runs)


if __name__ == "__main__":
    unittest.main()
