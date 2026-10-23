"""Khối 1x1x2 và các phép lăn (A1)."""
from dataclasses import dataclass
from typing import List, Tuple

# Tư thế của khối
STAND = 0   # đứng: chiếm (r, c)
HORIZ = 1   # nằm ngang: chiếm (r, c) và (r, c + 1)
VERT = 2    # nằm dọc: chiếm (r, c) và (r + 1, c)

# Hướng đi, theo thứ tự cố định của get_successors
UP, DOWN, LEFT, RIGHT = "U", "D", "L", "R"
MOVE_DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

# (tư thế, hướng) -> (tư thế mới, d_row, d_col). (r, c) luôn là ô trên-trái của khối.
_ROLL_TABLE = {
    (STAND, UP): (VERT, -2, 0),
    (STAND, DOWN): (VERT, 1, 0),
    (STAND, LEFT): (HORIZ, 0, -2),
    (STAND, RIGHT): (HORIZ, 0, 1),
    (HORIZ, UP): (HORIZ, -1, 0),
    (HORIZ, DOWN): (HORIZ, 1, 0),
    (HORIZ, LEFT): (STAND, 0, -1),
    (HORIZ, RIGHT): (STAND, 0, 2),
    (VERT, UP): (STAND, -1, 0),
    (VERT, DOWN): (STAND, 2, 0),
    (VERT, LEFT): (VERT, 0, -1),
    (VERT, RIGHT): (VERT, 0, 1),
}


@dataclass(frozen=True)
class Block:
    """Vị trí + tư thế của khối. Bất biến và hashable nên dùng được trong visited/heapq."""

    r: int
    c: int
    orient: int = STAND

    def cells(self) -> List[Tuple[int, int]]:
        """Các ô khối đang chiếm."""
        if self.orient == STAND:
            return [(self.r, self.c)]
        if self.orient == HORIZ:
            return [(self.r, self.c), (self.r, self.c + 1)]
        return [(self.r, self.c), (self.r + 1, self.c)]

    def roll(self, direction: str) -> "Block":
        """Lăn một bước theo hướng cho trước (chưa kiểm tra hợp lệ trên bản đồ)."""
        orient, d_row, d_col = _ROLL_TABLE[(self.orient, direction)]
        return Block(self.r + d_row, self.c + d_col, orient)