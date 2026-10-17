import pytest

from game.block import Block, STANDING, LYING_H, LYING_V, UP, DOWN, LEFT, RIGHT
from game.board import Board

# 12 trường hợp chuyển: (tư thế, hướng) -> khối mới, bắt đầu từ (5, 5)
MOVES = [
    (Block(5, 5, STANDING), UP,    Block(3, 5, LYING_V)),
    (Block(5, 5, STANDING), DOWN,  Block(6, 5, LYING_V)),
    (Block(5, 5, STANDING), LEFT,  Block(5, 3, LYING_H)),
    (Block(5, 5, STANDING), RIGHT, Block(5, 6, LYING_H)),
    (Block(5, 5, LYING_H),  UP,    Block(4, 5, LYING_H)),
    (Block(5, 5, LYING_H),  DOWN,  Block(6, 5, LYING_H)),
    (Block(5, 5, LYING_H),  LEFT,  Block(5, 4, STANDING)),
    (Block(5, 5, LYING_H),  RIGHT, Block(5, 7, STANDING)),
    (Block(5, 5, LYING_V),  UP,    Block(4, 5, STANDING)),
    (Block(5, 5, LYING_V),  DOWN,  Block(7, 5, STANDING)),
    (Block(5, 5, LYING_V),  LEFT,  Block(5, 4, LYING_V)),
    (Block(5, 5, LYING_V),  RIGHT, Block(5, 6, LYING_V)),
]


@pytest.mark.parametrize("start,d,expected", MOVES)
def test_move(start, d, expected):
    assert start.move(d) == expected


@pytest.mark.parametrize("start,d,_", MOVES)
def test_move_roundtrip(start, d, _):
    """Lăn rồi lăn ngược lại phải về chỗ cũ."""
    back = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}[d]
    assert start.move(d).move(back) == start


def test_cells():
    assert Block(1, 1, STANDING).cells() == [(1, 1)]
    assert Block(1, 1, LYING_H).cells() == [(1, 1), (1, 2)]
    assert Block(1, 1, LYING_V).cells() == [(1, 1), (2, 1)]


BOARD = Board.from_strings([
    "...##",
    "...##",
    "..G..",
    "##...",
])


def test_tile_classification():
    assert BOARD.is_floor(0, 0) and not BOARD.is_goal(0, 0)
    assert BOARD.is_goal(2, 2) and BOARD.is_floor(2, 2)
    assert not BOARD.is_floor(0, 3)
    assert not BOARD.is_floor(-1, 0) and not BOARD.is_floor(0, 99)
    assert BOARD.goal == (2, 2)


def test_valid():
    assert BOARD.is_valid(Block(0, 0, STANDING))
    assert BOARD.is_valid(Block(0, 0, LYING_H))
    assert BOARD.is_valid(Block(0, 0, LYING_V))


def test_invalid_empty_or_outside():
    assert not BOARD.is_valid(Block(0, 2, LYING_H))    # đè ô trống (0,3)
    assert not BOARD.is_valid(Block(3, 0, STANDING))   # ô trống
    assert not BOARD.is_valid(Block(-1, 0, STANDING))  # ngoài lưới
    assert not BOARD.is_valid(Block(3, 4, LYING_H))    # thò ra ngoài phải


def test_win_only_standing_on_goal():
    assert BOARD.is_win(Block(2, 2, STANDING))
    assert not BOARD.is_win(Block(2, 2, LYING_H))      # nằm trên đích: chưa thắng
    assert not BOARD.is_win(Block(2, 1, LYING_H))
    assert not BOARD.is_win(Block(0, 0, STANDING))


def test_next_blocks_filters_invalid():
    moves = dict(BOARD.next_blocks(Block(0, 0, STANDING)))
    assert set(moves) == {DOWN, RIGHT}                 # UP/LEFT rơi ra ngoài