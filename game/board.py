"""Lưới màn chơi: phân loại ô sàn / trống / đích (A1)."""
from typing import Optional, Sequence, Tuple

from .block import MOVE_DIRECTIONS, STAND, Block

TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_GOAL = 2

# Ký tự dùng khi dựng bản đồ từ chuỗi (tiện cho test)
_CHAR_TO_TILE = {"#": TILE_EMPTY, " ": TILE_EMPTY, ".": TILE_FLOOR, "G": TILE_GOAL}


class Board:
    """Lưới ô của màn chơi; chỉ chứa phần địa hình tĩnh (sàn, trống, đích)."""

    def __init__(self, grid: Sequence[Sequence[int]]) -> None:
        self.grid = [list(row) for row in grid]
        self.rows = len(self.grid)
        self.goal: Optional[Tuple[int, int]] = None
        for r, row in enumerate(self.grid):
            for c, tile in enumerate(row):
                if tile == TILE_GOAL:
                    self.goal = (r, c)

    @classmethod
    def from_strings(cls, lines: Sequence[str]) -> "Board":
        """Dựng từ chuỗi: '.' sàn, 'G' đích, '#' hoặc ' ' trống."""
        return cls([[_CHAR_TO_TILE[ch] for ch in line] for line in lines])

    def tile(self, r: int, c: int) -> int:
        """Loại ô tại (r, c); ngoài lưới coi như ô trống."""
        if 0 <= r < self.rows and 0 <= c < len(self.grid[r]):
            return self.grid[r][c]
        return TILE_EMPTY

    def is_floor(self, r: int, c: int) -> bool:
        """Ô đứng được (sàn hoặc đích)."""
        return self.tile(r, c) in (TILE_FLOOR, TILE_GOAL)

    def is_goal(self, r: int, c: int) -> bool:
        """Ô đích."""
        return self.tile(r, c) == TILE_GOAL

    def is_valid(self, block: Block) -> bool:
        """Hợp lệ khi mọi ô khối chiếm đều là sàn/đích (ra ngoài hoặc ô trống = rơi)."""
        return all(self.is_floor(r, c) for r, c in block.cells())

    def is_win(self, block: Block) -> bool:
        """Thắng khi khối đứng trên ô đích (nằm vắt qua đích thì chưa thắng)."""
        return block.orient == STAND and self.is_goal(block.r, block.c)

    def valid_moves(self, block: Block) -> list:
        """Danh sách (hướng, khối mới) của các nước đi hợp lệ, theo thứ tự U, D, L, R."""
        moves = []
        for direction in MOVE_DIRECTIONS:
            rolled = block.roll(direction)
            if self.is_valid(rolled):
                moves.append((direction, rolled))
        return moves