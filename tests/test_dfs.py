"""Unit test cho solvers/dfs.py (task E2)."""
import unittest
from pathlib import Path
from types import SimpleNamespace

from game.dummy_game import DummyGame
from game.game import Game
from game.level_loader import load_level
from solvers import dfs
from solvers.base import Limits
from solvers.metrics import measure, verify_path
from tests.test_metrics import toy_bfs

LEVEL_PATH = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"


def make_unsolvable_game() -> Game:
    """Đích ở (0,4) bị ngăn bởi ô trống (0,3); chỉ có 2 state lăn qua lại (STAND, HORIZ)."""
    level = SimpleNamespace(start=(0, 0), grid=["###.G"], initial_bridge_mask=lambda: 0)
    return Game(level)


class TestDfs(unittest.TestCase):
    def test_solves_dummy_game_with_valid_path(self):
        game = DummyGame(10)
        res = dfs.solve(game)
        self.assertTrue(res.solved)
        self.assertEqual(res.length, len(res.path))
        self.assertTrue(verify_path(game, res.path)[0])

    def test_solves_real_level_with_valid_path(self):
        game = Game(load_level(str(LEVEL_PATH)))
        res = dfs.solve(game)
        self.assertTrue(res.solved)
        self.assertTrue(verify_path(game, res.path)[0])

    def test_path_is_not_shorter_than_bfs(self):
        game = Game(load_level(str(LEVEL_PATH)))
        self.assertGreaterEqual(len(dfs.solve(game).path), len(toy_bfs(game).path))

    def test_start_is_goal_returns_empty_path(self):
        res = dfs.solve(DummyGame(0))
        self.assertTrue(res.solved)
        self.assertEqual(res.path, [])
        self.assertEqual(res.expanded_nodes, 1)

    def test_unsolvable_level_terminates_with_visited(self):
        res = dfs.solve(make_unsolvable_game())
        self.assertFalse(res.solved)
        self.assertEqual(res.path, [])
        self.assertEqual(res.expanded_nodes, 2)   # mỗi state chỉ được mở rộng đúng một lần

    def test_result_is_deterministic(self):
        game = Game(load_level(str(LEVEL_PATH)))
        first, second = dfs.solve(game), dfs.solve(game)
        self.assertEqual(first.path, second.path)
        self.assertEqual(first.expanded_nodes, second.expanded_nodes)

    def test_measure_fills_cost_and_metrics(self):
        game = DummyGame(10)
        res = measure(dfs.solve, game)
        self.assertTrue(res.solved)
        self.assertGreater(res.expanded_nodes, 0)
        self.assertGreater(res.peak_memory_kb, 0)
        self.assertAlmostEqual(res.cost, verify_path(game, res.path)[1])

    def test_node_limit_is_reported(self):
        res = measure(dfs.solve, DummyGame(10), Limits(max_nodes=3))
        self.assertFalse(res.solved)
        self.assertEqual(res.note, "node_limit")

    def test_cost_matches_path_cost_without_measure(self):
        """dfs.solve phải trả cost khớp tổng step của path (không cần measure)."""
        game = Game(load_level(str(LEVEL_PATH)))
        res = dfs.solve(game)
        self.assertTrue(res.solved)
        _, expected = verify_path(game, res.path)
        self.assertAlmostEqual(res.cost, expected)

    def test_cost_is_non_negative_and_gte_optimal(self):
        """DFS không tối ưu: cost >= cost tối ưu (BFS cùng cost function)."""
        game = Game(load_level(str(LEVEL_PATH)))
        res = dfs.solve(game)
        self.assertGreaterEqual(res.cost, toy_bfs(game).cost)

if __name__ == "__main__":
    unittest.main()