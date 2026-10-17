"""Khối 1x1x2 và các phép lăn (A1)."""
from dataclasses import dataclass
from typing import List, Tuple

# Tư thế
STANDING = "U"   # đứng: chiếm 1 ô (r, c)
LYING_H = "H"    # nằm ngang: chiếm (r, c) và (r, c+1)
LYING_V = "V"    # nằm dọc:   chiếm (r, c) và (r+1, c)

# Hướng đi
UP, DOWN, LEFT, RIGHT = "UP", "DOWN", "LEFT", "RIGHT"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

# (tư thế, hướng) -> (tư thế mới, dr, dc); (r, c) luôn là ô trên-trái của khối
_ROLL = {
    (STANDING, UP):    (LYING_V, -2, 0),
    (STANDING, DOWN):  (LYING_V, +1, 0),
    (STANDING, LEFT):  (LYING_H, 0, -2),
    (STANDING, RIGHT): (LYING_H, 0, +1),
    (LYING_H, UP):     (LYING_H, -1, 0),
    (LYING_H, DOWN):   (LYING_H, +1, 0),
    (LYING_H, LEFT):   (STANDING, 0, -1),
    (LYING_H, RIGHT):  (STANDING, 0, +2),
    (LYING_V, UP):     (STANDING, -1, 0),
    (LYING_V, DOWN):   (STANDING, +2, 0),
    (LYING_V, LEFT):   (LYING_V, 0, -1),
    (LYING_V, RIGHT):  (LYING_V, 0, +1),
}


@dataclass(frozen=True)
class Block:
    """Bất biến + hashable nên dùng trực tiếp trong visited/heap."""
    r: int
    c: int
    orient: str = STANDING

    def cells(self) -> List[Tuple[int, int]]:
        if self.orient == STANDING:
            return [(self.r, self.c)]
        if self.orient == LYING_H:
            return [(self.r, self.c), (self.r, self.c + 1)]
        return [(self.r, self.c), (self.r + 1, self.c)]

    def move(self, direction: str) -> "Block":
        """Lăn 1 bước (chưa kiểm tra hợp lệ trên board)."""
        orient, dr, dc = _ROLL[(self.orient, direction)]
        return Block(self.r + dr, self.c + dc, orient)

    def is_standing(self) -> bool:
        return self.orient == STANDING