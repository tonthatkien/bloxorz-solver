"""Unit test cho solvers/astar.py (task E2)."""
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

from game.dummy_game import DummyGame
from game.game import Game
from game.level_loader import load_level
from solvers import astar
from solvers.base import Limits
from solvers.heuristics import (h_manhattan, h_manhattan_orient, h_relaxed_maze, h_zero,
                                make_cost_fn)
from solvers.metrics import measure, verify_path
from tests.test_metrics import toy_bfs

LEVEL_PATH = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"
HEURISTICS = {"h_zero": h_zero, "h_manhattan": h_manhattan,
              "h_manhattan_orient": h_manhattan_orient, "h_relaxed_maze": h_relaxed_maze}


def dummy_h(game, state) -> float:
    """h = n - r. Admissible và consistent trên DummyGame vì mỗi đơn vị tiến tốn >= 1."""
    return float(game.n - state.r)


def as_solver(heuristic):
    """Bọc solve_with thành hàm (game, limits) để dùng với measure()."""
    def solver(game, limits=None):
        return astar.solve_with(game, heuristic, limits)
    return solver


def make_unsolvable_game() -> Game:
    """Đích ở (0,4) bị ngăn bởi ô trống (0,3); chỉ có 2 state lăn qua lại."""
    level = SimpleNamespace(start=(0, 0), grid=["###.G"], initial_bridge_mask=lambda: 0)
    return Game(level)


class TestAStarDummyGame(unittest.TestCase):
    """DummyGame có chi phí không đồng đều: R, L tốn 1; D (+2) tốn 3."""

    def setUp(self):
        self.game = DummyGame(10)

    def test_finds_optimal_cost_not_fewest_moves(self):
        res = astar.solve_with(self.game, dummy_h)
        self.assertTrue(res.solved)
        self.assertEqual(res.path, ["R"] * 10)        # 5 lần D chỉ tốn 15 > 10
        self.assertAlmostEqual(res.cost, 10.0)

    def test_zero_heuristic_equals_ucs_cost(self):
        res = astar.solve_with(self.game, h_zero)
        self.assertAlmostEqual(res.cost, 10.0)

    def test_good_heuristic_expands_no_more_than_zero(self):
        informed = astar.solve_with(self.game, dummy_h).expanded_nodes
        blind = astar.solve_with(self.game, h_zero).expanded_nodes
        self.assertLessEqual(informed, blind)

    def test_solution_is_valid_and_measured(self):
        res = measure(as_solver(dummy_h), self.game)
        self.assertEqual(verify_path(self.game, res.path), (True, 10.0))
        self.assertAlmostEqual(res.cost, 10.0)
        self.assertGreater(res.expanded_nodes, 0)

    def test_start_is_goal(self):
        res = astar.solve_with(DummyGame(0), dummy_h)
        self.assertTrue(res.solved)
        self.assertEqual((res.path, res.cost, res.expanded_nodes), ([], 0.0, 1))

    def test_infinite_heuristic_prunes_state(self):
        def h(game, state):
            return math.inf if state.r == 5 else dummy_h(game, state)
        res = astar.solve_with(self.game, h)
        self.assertEqual(res.path, ["R"] * 4 + ["D"] + ["R"] * 4)   # nhảy qua ô 5
        self.assertAlmostEqual(res.cost, 11.0)

    def test_infinite_heuristic_at_start_is_unsolved(self):
        res = astar.solve_with(self.game, lambda g, s: math.inf)
        self.assertFalse(res.solved)

    def test_node_limit_is_reported(self):
        res = measure(as_solver(dummy_h), self.game, Limits(max_nodes=3))
        self.assertFalse(res.solved)
        self.assertEqual(res.note, "node_limit")


class TestAStarRealLevel(unittest.TestCase):
    def setUp(self):
        level = load_level(str(LEVEL_PATH))
        self.unit_game = Game(level)                                  # mỗi bước 1.0
        self.weighted_game = Game(level, cost_fn=make_cost_fn(level))  # chi phí của F1

    def test_every_heuristic_gives_valid_path(self):
        for game in (self.unit_game, self.weighted_game):
            for name, h in HEURISTICS.items():
                with self.subTest(heuristic=name):
                    res = astar.solve_with(game, h)
                    self.assertTrue(res.solved)
                    valid, cost = verify_path(game, res.path)
                    self.assertTrue(valid)
                    self.assertAlmostEqual(res.cost, cost)

    def test_every_heuristic_matches_ucs_cost(self):
        # A* với h_zero chính là UCS; heuristic admissible phải ra cùng chi phí tối ưu.
        for game in (self.unit_game, self.weighted_game):
            optimal = astar.solve_with(game, h_zero).cost
            for name, h in HEURISTICS.items():
                with self.subTest(heuristic=name):
                    self.assertAlmostEqual(astar.solve_with(game, h).cost, optimal)

    def test_unit_cost_length_matches_bfs(self):
        res = astar.solve(self.unit_game)
        self.assertEqual(len(res.path), len(toy_bfs(self.unit_game).path))

    def test_default_solve_matches_default_heuristic(self):
        res = astar.solve(self.unit_game)
        same = astar.solve_with(self.unit_game, astar.DEFAULT_HEURISTIC)
        self.assertEqual((res.path, res.expanded_nodes), (same.path, same.expanded_nodes))

    def test_informed_heuristic_expands_no_more_than_zero(self):
        blind = astar.solve_with(self.unit_game, h_zero).expanded_nodes
        informed = astar.solve_with(self.unit_game, h_manhattan_orient).expanded_nodes
        self.assertLessEqual(informed, blind)

    def test_unsolvable_level_terminates(self):
        res = astar.solve_with(make_unsolvable_game(), h_zero)
        self.assertFalse(res.solved)
        self.assertEqual(res.expanded_nodes, 2)


if __name__ == "__main__":
    unittest.main()
