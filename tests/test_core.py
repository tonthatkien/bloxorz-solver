"""Unit test lõi game: Board và Block (A1)."""
import unittest
import json
import os

from game.block import DOWN, HORIZ, LEFT, RIGHT, STAND, UP, VERT, Block
from game.board import Board

BOARD = Board.from_strings([
    "###..",
    "###..",
    "##G##",
    "..###",
])


class TestRoll(unittest.TestCase):
    """12 trường hợp chuyển (3 tư thế x 4 hướng), bắt đầu từ (5, 5)."""

    def check(self, start_orient, direction, expected):
        self.assertEqual(Block(5, 5, start_orient).roll(direction), expected)

    def test_stand_up(self):
        self.check(STAND, UP, Block(3, 5, VERT))

    def test_stand_down(self):
        self.check(STAND, DOWN, Block(6, 5, VERT))

    def test_stand_left(self):
        self.check(STAND, LEFT, Block(5, 3, HORIZ))

    def test_stand_right(self):
        self.check(STAND, RIGHT, Block(5, 6, HORIZ))

    def test_horiz_up(self):
        self.check(HORIZ, UP, Block(4, 5, HORIZ))

    def test_horiz_down(self):
        self.check(HORIZ, DOWN, Block(6, 5, HORIZ))

    def test_horiz_left(self):
        self.check(HORIZ, LEFT, Block(5, 4, STAND))

    def test_horiz_right(self):
        self.check(HORIZ, RIGHT, Block(5, 7, STAND))

    def test_vert_up(self):
        self.check(VERT, UP, Block(4, 5, STAND))

    def test_vert_down(self):
        self.check(VERT, DOWN, Block(7, 5, STAND))

    def test_vert_left(self):
        self.check(VERT, LEFT, Block(5, 4, VERT))

    def test_vert_right(self):
        self.check(VERT, RIGHT, Block(5, 6, VERT))

    def test_roll_then_reverse_returns_to_start(self):
        opposite = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
        for orient in (STAND, HORIZ, VERT):
            for direction in opposite:
                start = Block(5, 5, orient)
                self.assertEqual(start.roll(direction).roll(opposite[direction]), start)


class TestCells(unittest.TestCase):
    def test_cells_per_orientation(self):
        self.assertEqual(Block(1, 1, STAND).cells(), [(1, 1)])
        self.assertEqual(Block(1, 1, HORIZ).cells(), [(1, 1), (1, 2)])
        self.assertEqual(Block(1, 1, VERT).cells(), [(1, 1), (2, 1)])


class TestBoard(unittest.TestCase):
    def test_tile_classification(self):
        self.assertTrue(BOARD.is_floor(0, 0))
        self.assertTrue(BOARD.is_goal(2, 2))
        self.assertTrue(BOARD.is_floor(2, 2))
        self.assertFalse(BOARD.is_floor(0, 3))
        self.assertEqual(BOARD.goal, (2, 2))

    def test_outside_grid_is_not_floor(self):
        self.assertFalse(BOARD.is_floor(-1, 0))
        self.assertFalse(BOARD.is_floor(0, 99))

    def test_block_on_floor_is_valid(self):
        for orient in (STAND, HORIZ, VERT):
            self.assertTrue(BOARD.is_valid(Block(0, 0, orient)))

    def test_block_over_empty_tile_is_invalid(self):
        self.assertFalse(BOARD.is_valid(Block(0, 2, HORIZ)))
        self.assertFalse(BOARD.is_valid(Block(3, 0, STAND)))

    def test_block_outside_grid_is_invalid(self):
        self.assertFalse(BOARD.is_valid(Block(-1, 0, STAND)))
        self.assertFalse(BOARD.is_valid(Block(3, 4, HORIZ)))

    def test_standing_on_goal_wins(self):
        self.assertTrue(BOARD.is_win(Block(2, 2, STAND)))

    def test_lying_over_goal_does_not_win(self):
        self.assertFalse(BOARD.is_win(Block(2, 2, HORIZ)))
        self.assertFalse(BOARD.is_win(Block(2, 1, HORIZ)))

    def test_standing_off_goal_does_not_win(self):
        self.assertFalse(BOARD.is_win(Block(0, 0, STAND)))

    def test_valid_moves_drop_falling_moves_and_keep_order(self):
        directions = [d for d, _ in BOARD.valid_moves(Block(0, 0, STAND))]
        self.assertEqual(directions, [DOWN, RIGHT])

LEVEL_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")  # chỉnh theo repo
LEVEL_FILES = ["g1_basic_01.json", "g2_fragile_01.json", "g3_switch_demo.json"]


def load_level(name):
    with open(os.path.join(LEVEL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


class TestJsonLevels(unittest.TestCase):
    def test_hash_is_floor_dot_is_void(self):
        for name in LEVEL_FILES:
            with self.subTest(level=name):
                data = load_level(name)
                board = Board.from_strings(data["grid"])
                for r, line in enumerate(data["grid"]):
                    for c, ch in enumerate(line):
                        if ch == "#":
                            self.assertTrue(board.is_floor(r, c), (r, c))
                        elif ch == ".":
                            self.assertFalse(board.is_floor(r, c), (r, c))

    def test_goal_matches_json(self):
        for name in LEVEL_FILES:
            with self.subTest(level=name):
                data = load_level(name)
                board = Board.from_strings(data["grid"])
                self.assertEqual(board.goal, tuple(data["goal"]))
                self.assertTrue(board.is_win(Block(*data["goal"], STAND)))

    def test_start_is_valid_standing_position(self):
        for name in LEVEL_FILES:
            with self.subTest(level=name):
                data = load_level(name)
                board = Board.from_strings(data["grid"])
                self.assertTrue(board.is_valid(Block(*data["start"], STAND)))

if __name__ == "__main__":
    unittest.main()