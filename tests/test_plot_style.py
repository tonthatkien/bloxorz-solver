"""Pure report-style checks without importing Matplotlib or GUI dependencies."""
import unittest

from experiments.plot_style import display_value, solver_color


class TestPlotStyle(unittest.TestCase):
    """Protect report units and stable algorithm colors across partial datasets."""

    def test_algorithm_colors_do_not_depend_on_other_present_series(self) -> None:
        expected = {"bfs": "#1F77B4", "dfs": "#FF7F0E", "ucs": "#2CA02C", "astar": "#D62728"}
        for subset in (tuple(expected), ("ucs", "astar"), ("dfs", "ucs")):
            self.assertEqual([solver_color(n) for n in subset], [expected[n] for n in subset])
        self.assertEqual(solver_color("astar_zero"), expected["astar"])

    def test_memory_uses_decimal_mb_and_seconds_are_not_rescaled(self) -> None:
        self.assertEqual(display_value("peak_memory_kb", 976.5625), 1)
        self.assertAlmostEqual(display_value("peak_memory_kb", 1024), 1.048576)
        self.assertEqual(display_value("time_sec", .001), .001)
        for field in ("expanded_nodes", "length", "cost"):
            self.assertEqual(display_value(field, 7), 7)


if __name__ == "__main__":
    unittest.main()
