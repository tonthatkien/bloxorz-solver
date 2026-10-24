"""Unit test khối 1x1x2: 12 phép lăn và ô khối chiếm (A1)."""
import unittest

from game.block import DOWN, LEFT, MOVE_DIRECTIONS, RIGHT, UP, Block
from game.state import HORIZ, STAND, VERT

# (tư thế, hướng) -> (r, c, tư thế mới) khi lăn từ (5, 5)
ROLL_CASES = {
    (STAND, UP): (3, 5, VERT),
    (STAND, DOWN): (6, 5, VERT),
    (STAND, LEFT): (5, 3, HORIZ),
    (STAND, RIGHT): (5, 6, HORIZ),
    (HORIZ, UP): (4, 5, HORIZ),
    (HORIZ, DOWN): (6, 5, HORIZ),
    (HORIZ, LEFT): (5, 4, STAND),
    (HORIZ, RIGHT): (5, 7, STAND),
    (VERT, UP): (4, 5, STAND),
    (VERT, DOWN): (7, 5, STAND),
    (VERT, LEFT): (5, 4, VERT),
    (VERT, RIGHT): (5, 6, VERT),
}


class TestBlockCells(unittest.TestCase):
    def test_standing_occupies_one_cell(self):
        self.assertEqual(Block(2, 3, STAND).cells(), [(2, 3)])

    def test_horizontal_occupies_two_cells_in_a_row(self):
        self.assertEqual(Block(2, 3, HORIZ).cells(), [(2, 3), (2, 4)])

    def test_vertical_occupies_two_cells_in_a_column(self):
        self.assertEqual(Block(2, 3, VERT).cells(), [(2, 3), (3, 3)])


class TestBlockRoll(unittest.TestCase):
    def test_all_twelve_rolls(self):
        for (orient, direction), (r, c, new_orient) in ROLL_CASES.items():
            with self.subTest(orient=orient, direction=direction):
                self.assertEqual(Block(5, 5, orient).roll(direction), Block(r, c, new_orient))

    def test_table_covers_every_orientation_and_direction(self):
        self.assertEqual(
            set(ROLL_CASES), {(o, d) for o in (STAND, HORIZ, VERT) for d in MOVE_DIRECTIONS})

    def test_rolled_cells_match_expected_footprint(self):
        self.assertEqual(Block(5, 5, STAND).roll(UP).cells(), [(3, 5), (4, 5)])
        self.assertEqual(Block(5, 5, STAND).roll(RIGHT).cells(), [(5, 6), (5, 7)])
        self.assertEqual(Block(5, 5, HORIZ).roll(RIGHT).cells(), [(5, 7)])
        self.assertEqual(Block(5, 5, VERT).roll(DOWN).cells(), [(7, 5)])

    def test_roll_and_reverse_returns_to_start(self):
        pairs = ((UP, DOWN), (DOWN, UP), (LEFT, RIGHT), (RIGHT, LEFT))
        for orient in (STAND, HORIZ, VERT):
            for forward, back in pairs:
                with self.subTest(orient=orient, direction=forward):
                    block = Block(5, 5, orient)
                    self.assertEqual(block.roll(forward).roll(back), block)

    def test_block_is_immutable_and_hashable(self):
        block = Block(1, 1)
        block.roll(UP)
        self.assertEqual(block, Block(1, 1, STAND))
        self.assertEqual(len({block, Block(1, 1, STAND)}), 1)


if __name__ == "__main__":
    unittest.main()