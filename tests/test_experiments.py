"""Unit test cho experiments/ (task F3): run_all, benchmark_heuristics, common.

Chỉ chạy trên màn nhỏ g1_basic_01 với repeats=1 để nhanh; kết quả ghi vào thư mục tạm.
"""
import csv
import tempfile
import tracemalloc
import unittest
from pathlib import Path

from experiments import benchmark_heuristics as bench
from experiments import common, run_all
from solvers import bfs
from solvers.base import Limits

LEVEL = common.LEVEL_DIR / "g1_basic_01.json"
FAST = Limits(max_nodes=200_000, timeout_sec=30.0)
OPTIMAL_LENGTH = 8  # g1_basic_01: xem tests/test_bfs.py, test_astar.py


def fake_row(solver: str, mode: str = "unit", **changes) -> dict:
    """Dòng kết quả giả để thử logic kiểm tra mà không cần chạy solver."""
    row = {"group": "g1", "level": "x", "cost_mode": mode, "solver": solver, "solved": True,
           "length": 5, "cost": 5.0, "expanded_nodes": 10, "time_sec": 0.1,
           "peak_memory_kb": 1.0, "note": ""}
    row.update(changes)
    return row


class TestCommonHelpers(unittest.TestCase):
    def test_group_of(self):
        self.assertEqual(common.group_of("g2_fragile_01"), "g2")
        self.assertEqual(common.group_of("g4_mixed_04"), "g4")
        self.assertEqual(common.group_of("t2_core_happy"), "other")

    def test_list_levels_is_sorted_and_excludes_demo_by_default(self):
        stems = [p.stem for p in common.list_levels()]
        self.assertIn("g1_basic_01", stems)
        groups = [common.group_of(s) for s in stems]
        self.assertEqual(groups, sorted(groups))

    def test_select_levels_by_prefix(self):
        paths = common.list_levels()
        picked = common.select_levels(paths, ["g2_fragile_01", "g4"])
        self.assertTrue(picked)
        for path in picked:
            self.assertTrue(path.stem.startswith(("g2_fragile_01", "g4")))
        self.assertEqual(common.select_levels(paths, []), paths)

    def test_write_csv_creates_parent_and_round_trips(self):
        rows = [fake_row("bfs"), fake_row("dfs", length=7)]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "r.csv"
            common.write_csv(rows, out)
            with open(out, newline="", encoding="utf-8") as handle:
                back = list(csv.DictReader(handle))
        self.assertEqual(list(back[0].keys()), common.FIELDNAMES)
        self.assertEqual([r["solver"] for r in back], ["bfs", "dfs"])
        self.assertEqual(back[1]["length"], "7")


class TestRunExperiments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = run_all.run_experiments(
            [LEVEL], run_all.build_solvers(), common.MODES, FAST, repeats=1)

    def row(self, mode: str, solver: str) -> dict:
        return next(r for r in self.rows if r["cost_mode"] == mode and r["solver"] == solver)

    def test_one_row_per_level_mode_and_solver_with_expected_columns(self):
        self.assertEqual(len(self.rows), 4 * len(common.MODES))
        for row in self.rows:
            self.assertEqual(list(row.keys()).sort(), common.FIELDNAMES.copy().sort())
            self.assertEqual(set(row), set(common.FIELDNAMES))
            self.assertTrue(row["solved"], row)
            self.assertEqual(row["group"], "g1")

    def test_unit_mode_optimal_solvers_agree_with_bfs(self):
        for name in ("bfs", "ucs", "astar"):
            self.assertEqual(self.row("unit", name)["length"], OPTIMAL_LENGTH, name)
        self.assertGreaterEqual(self.row("unit", "dfs")["length"], OPTIMAL_LENGTH)

    def test_weighted_mode_ucs_and_astar_have_equal_cost_and_not_worse_than_bfs(self):
        ucs_cost = self.row("weighted", "ucs")["cost"]
        self.assertAlmostEqual(self.row("weighted", "astar")["cost"], ucs_cost)
        self.assertLessEqual(ucs_cost, self.row("weighted", "bfs")["cost"] + common.TOL)

    def test_sanity_check_passes_on_real_results(self):
        self.assertEqual(run_all.sanity_check(self.rows), [])

    def test_cut_results_leave_blank_cells(self):
        rows = run_all.run_experiments([LEVEL], {"bfs": bfs.solve}, ("unit",),
                                       Limits(max_nodes=3), repeats=1)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertFalse(row["solved"])
        self.assertEqual(row["note"], "node_limit")
        self.assertEqual((row["length"], row["cost"], row["expanded_nodes"]), ("", "", ""))

    def test_solver_error_is_recorded_and_tracemalloc_is_not_left_on(self):
        calls = {"n": 0}

        def flaky(game, limits=None):
            calls["n"] += 1
            if calls["n"] >= 2:      # lần 1 = đo thời gian; lần 2 = đo bộ nhớ (tracemalloc bật)
                raise RuntimeError("boom")
            return bfs.solve(game, limits)

        rows = run_all.run_experiments([LEVEL], {"flaky": flaky, "bfs": bfs.solve},
                                       ("unit",), FAST, repeats=1)
        self.assertFalse(tracemalloc.is_tracing())
        self.assertFalse(rows[0]["solved"])
        self.assertTrue(str(rows[0]["note"]).startswith("error: RuntimeError"))
        self.assertTrue(rows[1]["solved"])   # solver sau đó vẫn chạy bình thường

    def test_main_writes_csv_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sub" / "r.csv"
            code = run_all.main(["--levels", "g1_basic_01", "--repeats", "1",
                                 "--astar-heuristics", "manhattan_orient",
                                 "--out", str(out), "-q"])
            with open(out, newline="", encoding="utf-8") as handle:
                back = list(csv.DictReader(handle))
        self.assertEqual(code, 0)
        self.assertEqual(len(back), 5 * len(common.MODES))
        self.assertIn("astar_manhattan_orient", {r["solver"] for r in back})


class TestSanityCheck(unittest.TestCase):
    def consistent(self, mode="unit"):
        return [fake_row("bfs", mode), fake_row("ucs", mode), fake_row("astar", mode),
                fake_row("dfs", mode, length=7, cost=7.0)]

    def test_consistent_rows_have_no_problem(self):
        self.assertEqual(run_all.sanity_check(self.consistent()), [])

    def test_optimal_solvers_disagreeing_is_reported(self):
        rows = self.consistent()
        rows[1] = fake_row("ucs", length=6, cost=6.0)
        self.assertTrue(run_all.sanity_check(rows))

    def test_weighted_bfs_may_cost_more_but_dfs_cannot_beat_ucs(self):
        rows = [fake_row("bfs", "weighted", cost=6.0), fake_row("ucs", "weighted", length=6),
                fake_row("astar", "weighted", length=6),
                fake_row("dfs", "weighted", length=9, cost=9.0)]
        self.assertEqual(run_all.sanity_check(rows), [])
        rows[3] = fake_row("dfs", "weighted", length=9, cost=4.0)
        self.assertTrue(run_all.sanity_check(rows))

    def test_error_and_invalid_rows_are_reported(self):
        rows = self.consistent()
        rows[3] = fake_row("dfs", solved=False, length="", cost="", note="error: RuntimeError: x")
        self.assertTrue(any("lỗi" in p for p in run_all.sanity_check(rows)))
        rows = self.consistent()
        rows[0] = fake_row("bfs", note="invalid_path")
        self.assertTrue(any("invalid_path" in p for p in run_all.sanity_check(rows)))

    def test_cut_solver_is_not_counted_as_disagreement(self):
        rows = self.consistent()
        rows[3] = fake_row("dfs", solved=False, length="", cost="", expanded_nodes="",
                           note="timeout")
        self.assertEqual(run_all.sanity_check(rows), [])


class TestHeuristicBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = bench.run_benchmark(
            [LEVEL], ["advanced", "manhattan_orient"], common.MODES, FAST, repeats=1)

    def row(self, mode: str, name: str) -> dict:
        return next(r for r in self.rows if r["cost_mode"] == mode and r["heuristic"] == name)

    def test_baseline_is_always_added_and_order_is_stable(self):
        self.assertEqual(bench.ordered_heuristics(["advanced"]), ["zero", "advanced"])
        self.assertEqual(len(self.rows), 3 * len(common.MODES))

    def test_every_row_has_expected_columns(self):
        for row in self.rows:
            self.assertEqual(set(row), set(bench.HEURISTIC_FIELDNAMES))

    def test_baseline_ratio_is_one_and_all_heuristics_are_optimal(self):
        for mode in common.MODES:
            self.assertEqual(self.row(mode, "zero")["node_ratio"], 1.0)
            for name in ("zero", "manhattan_orient", "advanced"):
                self.assertTrue(self.row(mode, name)["optimal"], (mode, name))
        self.assertEqual(bench.check_benchmark(self.rows), [])

    def test_informed_heuristics_expand_no_more_than_zero_with_unit_cost(self):
        zero_nodes = self.row("unit", "zero")["expanded_nodes"]
        for name in ("manhattan_orient", "advanced"):
            self.assertLessEqual(self.row("unit", name)["expanded_nodes"], zero_nodes)

    def test_advanced_is_exact_at_start_on_plain_level_with_unit_cost(self):
        self.assertAlmostEqual(self.row("unit", "advanced")["tightness"], 1.0, places=3)
        self.assertEqual(self.row("unit", "zero")["tightness"], 0.0)

    def test_summary_has_all_group_for_every_heuristic(self):
        summary = bench.summarize(self.rows)
        keys = {(r["cost_mode"], r["group"], r["heuristic"]) for r in summary}
        for mode in common.MODES:
            for name in ("zero", "manhattan_orient", "advanced"):
                self.assertIn((mode, "all", name), keys)
                self.assertIn((mode, "g1", name), keys)
        self.assertIn("nodes/zero", bench.format_summary(summary))

    def test_main_writes_both_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, summary_out = Path(tmp) / "h.csv", Path(tmp) / "s.csv"
            code = bench.main(["--levels", "g1_basic_01", "--heuristics", "manhattan_orient",
                               "advanced", "--modes", "unit", "--repeats", "1",
                               "--out", str(out), "--summary-out", str(summary_out), "-q"])
            with open(out, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            with open(summary_out, newline="", encoding="utf-8") as handle:
                summary = list(csv.DictReader(handle))
        self.assertEqual(code, 0)
        self.assertEqual({r["heuristic"] for r in rows}, {"zero", "manhattan_orient", "advanced"})
        self.assertEqual(list(summary[0].keys()), bench.SUMMARY_FIELDNAMES)


class TestBenchmarkLogic(unittest.TestCase):
    def bench_row(self, level, name, nodes, **changes):
        row = fake_row("x", level=level, heuristic=name, expanded_nodes=nodes,
                       h_start=0.0, optimal=True, tightness=0.0, node_ratio="", time_ratio="")
        row.update(changes)
        return row

    def test_derived_columns_and_summary_math(self):
        rows = [self.bench_row("A", "zero", 100), self.bench_row("A", "h", 25),
                self.bench_row("B", "zero", 100), self.bench_row("B", "h", 100)]
        for row in rows:
            row["heuristic"] = row["heuristic"] if row["heuristic"] != "h" else "advanced"
        bench.add_derived(rows)
        self.assertEqual([r["node_ratio"] for r in rows], [1.0, 0.25, 1.0, 1.0])
        summary = {(r["group"], r["heuristic"]): r for r in bench.summarize(rows)}
        advanced = summary[("all", "advanced")]
        self.assertAlmostEqual(advanced["geo_node_ratio"], 0.5)   # sqrt(0.25 * 1.0)
        self.assertEqual(advanced["node_wins"], 2)                # thắng A, hòa B
        self.assertEqual(summary[("all", "zero")]["node_wins"], 1)

    def test_non_admissible_heuristic_is_reported(self):
        rows = [self.bench_row("A", "zero", 100, h_start=0.0, cost=5.0),
                self.bench_row("A", "advanced", 20, h_start=9.0, cost=7.0)]
        bench.add_derived(rows)
        self.assertIs(rows[1]["optimal"], False)
        problems = bench.check_benchmark(rows)
        self.assertEqual(len(problems), 2)   # cost khác tối ưu + tightness > 1


if __name__ == "__main__":
    unittest.main()
