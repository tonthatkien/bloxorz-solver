"""Unit test lưới màn chơi: phân loại ô, hợp lệ, thắng, nước đi (A1)."""
import unittest

from game.block import DOWN, LEFT, RIGHT, UP, Block
from game.board import TILE_EMPTY, TILE_FLOOR, TILE_GOAL, Board
from game.state import HORIZ, STAND, VERT

GRID = [
    "###..",
    "###..",
    "##G##",
    "..###",
]


def make_board() -> Board:
    return Board.from_strings(GRID)


class TestTiles(unittest.TestCase):
    def test_from_strings_classifies_tiles(self):
        board = make_board()
        self.assertEqual(board.tile(0, 0), TILE_FLOOR)
        self.assertEqual(board.tile(0, 3), TILE_EMPTY)
        self.assertEqual(board.tile(2, 2), TILE_GOAL)

    def test_space_is_empty(self):
        self.assertEqual(Board.from_strings(["# #"]).tile(0, 1), TILE_EMPTY)

    def test_outside_grid_is_empty(self):
        board = make_board()
        for r, c in ((-1, 0), (0, -1), (4, 0), (0, 5), (99, 99)):
            with self.subTest(pos=(r, c)):
                self.assertEqual(board.tile(r, c), TILE_EMPTY)
                self.assertFalse(board.is_floor(r, c))

    def test_goal_is_standable_floor(self):
        board = make_board()
        self.assertTrue(board.is_floor(2, 2))
        self.assertTrue(board.is_goal(2, 2))
        self.assertFalse(board.is_goal(0, 0))


class TestIsValid(unittest.TestCase):
    def test_standing_on_floor_and_goal_is_valid(self):
        board = make_board()
        self.assertTrue(board.is_valid(Block(0, 0, STAND)))
        self.assertTrue(board.is_valid(Block(2, 2, STAND)))

    def test_standing_on_empty_or_outside_falls(self):
        board = make_board()
        self.assertFalse(board.is_valid(Block(3, 0, STAND)))
        self.assertFalse(board.is_valid(Block(-1, 0, STAND)))

    def test_half_block_over_void_falls(self):
        board = make_board()
        self.assertFalse(board.is_valid(Block(0, 2, HORIZ)))  # (0,3) là ô trống
        self.assertFalse(board.is_valid(Block(3, 4, HORIZ)))  # (3,5) ngoài lưới
        self.assertFalse(board.is_valid(Block(3, 2, VERT)))   # (4,2) ngoài lưới

    def test_lying_block_fully_on_floor_is_valid(self):
        board = make_board()
        self.assertTrue(board.is_valid(Block(2, 1, HORIZ)))
        self.assertTrue(board.is_valid(Block(1, 2, VERT)))


class TestIsWin(unittest.TestCase):
    def test_standing_on_goal_wins(self):
        self.assertTrue(make_board().is_win(Block(2, 2, STAND)))

    def test_lying_across_goal_does_not_win(self):
        board = make_board()
        self.assertFalse(board.is_win(Block(2, 1, HORIZ)))
        self.assertFalse(board.is_win(Block(2, 2, HORIZ)))
        self.assertFalse(board.is_win(Block(1, 2, VERT)))
        self.assertFalse(board.is_win(Block(2, 2, VERT)))

    def test_standing_off_goal_does_not_win(self):
        self.assertFalse(make_board().is_win(Block(0, 0, STAND)))


class TestValidMoves(unittest.TestCase):
    def test_corner_has_two_moves(self):
        moves = make_board().valid_moves(Block(0, 0, STAND))
        self.assertEqual([d for d, _ in moves], [DOWN, RIGHT])

    def test_moves_follow_u_d_l_r_order(self):
        # Từ ô đích: D rơi ra ngoài lưới nên chỉ còn U, L, R.
        moves = make_board().valid_moves(Block(2, 2, STAND))
        self.assertEqual([d for d, _ in moves], [UP, LEFT, RIGHT])

    def test_moves_carry_rolled_block(self):
        moves = make_board().valid_moves(Block(0, 0, STAND))
        self.assertEqual(moves, [(DOWN, Block(1, 0, VERT)), (RIGHT, Block(0, 1, HORIZ))])


if __name__ == "__main__":
    unittest.main()