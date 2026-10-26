import glob
import unittest

from game.level_loader import LevelValidationError, load_level, parse_level
from game.state import State, cells, STAND, HORIZ, VERT


def _split_level(cubes: list[list[int]]) -> dict:
    """Build split metadata on ordinary floor, away from the switch and goal."""
    return {
        "grid": ["#####", "#####", "#####", "#####", "####G"],
        "start": [0, 0],
        "goal": [4, 4],
        "switches": [{"type": "split", "pos": [3, 3], "cubes": cubes}],
    }


class TestLoader(unittest.TestCase):
    def test_all_levels_load(self):
        paths = glob.glob("levels/*.json")
        self.assertTrue(paths)
        for p in paths:
            load_level(p)

    def test_split_rejects_orthogonally_adjacent_destinations(self) -> None:
        for pair in ([[1, 1], [1, 2]], [[1, 1], [2, 1]]):
            for cubes in (pair, list(reversed(pair))):
                with self.subTest(cubes=cubes):
                    with self.assertRaises(LevelValidationError) as caught:
                        parse_level(_split_level(cubes))
                    message = str(caught.exception)
                    self.assertIn("switches[0].cubes", message)
                    self.assertIn(str(tuple(cubes[0])), message)
                    self.assertIn(str(tuple(cubes[1])), message)
                    self.assertIn("cannot be orthogonally adjacent", message)

    def test_split_rejects_coincident_destinations(self) -> None:
        with self.assertRaisesRegex(LevelValidationError, "cubes.*distinct"):
            parse_level(_split_level([[1, 1], [1, 1]]))

    def test_split_accepts_diagonal_and_separated_destinations_in_either_order(self) -> None:
        for pair in ([[1, 1], [2, 2]], [[1, 1], [1, 3]]):
            for cubes in (pair, list(reversed(pair))):
                with self.subTest(cubes=cubes):
                    level = parse_level(_split_level(cubes))
                    self.assertEqual(level.switches[(3, 3)].cubes,
                                     [tuple(position) for position in cubes])

    def test_state_hashable_and_cells(self):
        self.assertEqual(hash(State(1, 2)), hash(State(1, 2)))
        self.assertEqual(cells(State(1, 2, STAND)), [(1, 2)])
        self.assertEqual(cells(State(1, 2, HORIZ)), [(1, 2), (1, 3)])
        self.assertEqual(cells(State(1, 2, VERT)), [(1, 2), (2, 2)])


if __name__ == "__main__":
    unittest.main()
