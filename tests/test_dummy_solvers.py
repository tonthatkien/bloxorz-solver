"""Khung test solver trên DummyGame. Bỏ comment khi solver tương ứng đã xong."""
import unittest

from game.dummy_game import DummyGame


class TestDummy(unittest.TestCase):
    def test_dummy_interface(self):
        g = DummyGame(5)
        s = g.initial_state()
        self.assertFalse(g.is_goal(s))
        self.assertTrue(g.get_successors(s))

    # def test_bfs(self):
    #     from solvers import bfs
    #     res = bfs.solve(DummyGame(10))
    #     self.assertTrue(res.solved)


if __name__ == "__main__":
    unittest.main()
