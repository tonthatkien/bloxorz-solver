"""Test record_trace của 4 solver và run_measured."""
import unittest
from pathlib import Path

from game.dummy_game import DummyGame
from game.game import Game
from game.level_loader import load_level
from solvers import astar, bfs, dfs, ucs
from solvers.base import run_measured

LEVEL = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"
SOLVERS = {"bfs": bfs, "dfs": dfs, "ucs": ucs, "astar": astar}


class TestTrace(unittest.TestCase):
    def setUp(self):
        self.game = Game(load_level(str(LEVEL)))

    def test_trace_off_by_default(self):
        for name, mod in SOLVERS.items():
            with self.subTest(solver=name):
                self.assertEqual(mod.solve(self.game).expanded_order, [])

    def test_trace_length_matches_expanded_nodes(self):
        for name, mod in SOLVERS.items():
            with self.subTest(solver=name):
                res = mod.solve(self.game, record_trace=True)
                self.assertTrue(res.solved)
                self.assertEqual(len(res.expanded_order), res.expanded_nodes)

    def test_trace_starts_at_initial_and_ends_at_goal(self):
        for name, mod in SOLVERS.items():
            with self.subTest(solver=name):
                order = mod.solve(self.game, record_trace=True).expanded_order
                self.assertEqual(order[0], self.game.initial_state())
                self.assertTrue(self.game.is_goal(order[-1]))
                self.assertEqual(len(order), len(set(order)))  # mỗi state mở rộng 1 lần

    def test_trace_does_not_change_result(self):
        for name, mod in SOLVERS.items():
            with self.subTest(solver=name):
                plain = mod.solve(self.game)
                traced = mod.solve(self.game, record_trace=True)
                self.assertEqual((plain.path, plain.expanded_nodes, plain.cost),
                                 (traced.path, traced.expanded_nodes, traced.cost))

    def test_unsolved_trace_covers_all_expanded(self):
        res = bfs.solve(DummyGame(0), record_trace=True)   # start là goal
        self.assertEqual(len(res.expanded_order), 1)

    def test_run_measured_fills_trace_only_when_asked(self):
        off = run_measured(bfs.solve, self.game, repeats=1)
        on = run_measured(bfs.solve, self.game, repeats=1, record_trace=True)
        self.assertEqual(off.expanded_order, [])
        self.assertEqual(len(on.expanded_order), on.expanded_nodes)

    def test_run_measured_works_with_solver_lacking_record_trace(self):
        def old_style(game, limits=None):
            return bfs.solve(game, limits)
        res = run_measured(old_style, self.game, repeats=1)
        self.assertTrue(res.solved)


if __name__ == "__main__":
    unittest.main()