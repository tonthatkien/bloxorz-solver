"""Lưới màn chơi: phân loại ô sàn / trống / đích (A1)."""
from typing import List, Optional, Sequence, Tuple

from .block import Block, STANDING, DIRECTIONS

EMPTY, FLOOR, GOAL = 0, 1, 2

# Ký tự dùng khi dựng board từ chuỗi (tiện cho test)
_CHAR = {"#": EMPTY, " ": EMPTY, ".": FLOOR, "S": FLOOR, "G": GOAL}


class Board:
    def __init__(self, grid: Sequence[Sequence[int]]):
        self.grid = [list(row) for row in grid]
        self.rows = len(self.grid)
        self.cols = max((len(r) for r in self.grid), default=0)
        self.goal: Optional[Tuple[int, int]] = None
        for r, row in enumerate(self.grid):
            for c, t in enumerate(row):
                if t == GOAL:
                    self.goal = (r, c)

    @classmethod
    def from_strings(cls, lines: Sequence[str]) -> "Board":
        """'.' sàn, 'G' đích, '#' hoặc ' ' trống."""
        return cls([[_CHAR[ch] for ch in line] for line in lines])

    # --- truy vấn ô ---
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < len(self.grid[r])

    def tile(self, r: int, c: int) -> int:
        return self.grid[r][c] if self.in_bounds(r, c) else EMPTY

    def is_floor(self, r: int, c: int) -> bool:
        """Ô đứng được (sàn hoặc đích)."""
        return self.tile(r, c) in (FLOOR, GOAL)

    def is_goal(self, r: int, c: int) -> bool:
        return self.tile(r, c) == GOAL

    # --- luật cho khối ---
    def is_valid(self, block: Block) -> bool:
        """Hợp lệ khi mọi ô khối chiếm đều là sàn/đích (ra ngoài/ô trống = rơi = thua)."""
        return all(self.is_floor(r, c) for r, c in block.cells())

    def is_win(self, block: Block) -> bool:
        return block.orient == STANDING and self.is_goal(block.r, block.c)

    def next_blocks(self, block: Block):
        """Sinh (hướng, khối mới) cho các nước đi hợp lệ."""
        for d in DIRECTIONS:
            nb = block.move(d)
            if self.is_valid(nb):
                yield d, nb