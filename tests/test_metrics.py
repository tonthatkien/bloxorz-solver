"""Test module đo (E1) bằng solver đồ chơi trên DummyGame."""
import unittest
from collections import deque

from game.dummy_game import DummyGame
from solvers.base import LimitChecker, Limits, SearchResult, reconstruct_path
from solvers.metrics import format_result, measure, result_to_row, verify_path


def toy_bfs(game, limits=None) -> SearchResult:
    """BFS tối giản chỉ để thử module đo (không phải BFS nộp bài - đó là việc E2)."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    parent = {start: None}
    queue = deque([start])
    expanded = 0
    while queue:
        state = queue.popleft()
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(state):
            return SearchResult(True, reconstruct_path(parent, state), expanded)
        for action, nxt, _cost in game.get_successors(state):
            if nxt not in parent:
                parent[nxt] = (state, action)
                queue.append(nxt)
    return SearchResult(False, [], expanded)


def toy_dfs(game, limits=None) -> SearchResult:
    """DFS tối giản (stack + visited) để so sánh với toy_bfs."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    parent = {start: None}
    stack = [start]
    expanded = 0
    while stack:
        state = stack.pop()
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(state):
            return SearchResult(True, reconstruct_path(parent, state), expanded)
        for action, nxt, _cost in reversed(game.get_successors(state)):
            if nxt not in parent:
                parent[nxt] = (state, action)
                stack.append(nxt)
    return SearchResult(False, [], expanded)


class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.game = DummyGame(10)

    def test_bfs_measurements_filled(self):
        res = measure(toy_bfs, self.game)
        self.assertTrue(res.solved)
        self.assertEqual(res.length, len(res.path))
        self.assertEqual(res.length, 5)          # 5 lần "D" (+2) là ngắn nhất
        self.assertGreater(res.expanded_nodes, 0)
        self.assertGreater(res.time_sec, 0)
        self.assertGreater(res.peak_memory_kb, 0)

    def test_cost_is_filled_from_path(self):
        res = measure(toy_bfs, self.game)
        self.assertEqual(res.cost, 15.0)         # 5 bước D, mỗi bước cost 3

    def test_dfs_path_is_valid(self):
        res = measure(toy_dfs, self.game)
        self.assertTrue(res.solved)
        self.assertTrue(verify_path(self.game, res.path)[0])
        self.assertGreaterEqual(res.length, 5)   # DFS không ngắn hơn BFS

    def test_verify_rejects_bad_paths(self):
        self.assertFalse(verify_path(self.game, ["R", "R"])[0])      # chưa tới đích
        self.assertFalse(verify_path(self.game, ["L"])[0])           # nước đi không hợp lệ

    def test_node_limit_is_reported(self):
        res = measure(toy_bfs, self.game, Limits(max_nodes=3))
        self.assertFalse(res.solved)
        self.assertEqual(res.note, "node_limit")

    def test_row_and_format(self):
        res = measure(toy_bfs, self.game)
        row = result_to_row("dummy", "bfs", res)
        self.assertEqual(row["solver"], "bfs")
        self.assertEqual(row["length"], 5)
        self.assertIn("expanded=", format_result(res))


if __name__ == "__main__":
    unittest.main()