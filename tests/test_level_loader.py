import glob
import unittest

from game.level_loader import load_level
from game.state import State, cells, STAND, HORIZ, VERT


class TestLoader(unittest.TestCase):
    def test_all_levels_load(self):
        paths = glob.glob("levels/*.json")
        self.assertTrue(paths)
        for p in paths:
            load_level(p)

    def test_state_hashable_and_cells(self):
        self.assertEqual(hash(State(1, 2)), hash(State(1, 2)))
        self.assertEqual(cells(State(1, 2, STAND)), [(1, 2)])
        self.assertEqual(cells(State(1, 2, HORIZ)), [(1, 2), (1, 3)])
        self.assertEqual(cells(State(1, 2, VERT)), [(1, 2), (2, 2)])


if __name__ == "__main__":
    unittest.main()
