"""Giao diện game mà solver và GUI dùng. CHỈ ĐƯỢC GỌI QUA 3 HÀM DƯỚI ĐÂY.
Quy ước:
- Hành động: "U", "D", "L", "R"; "S" = đổi cube đang điều khiển (chỉ khi đang tách).
- Thứ tự sinh hành động CỐ ĐỊNH: U, D, L, R, S (để DFS lặp lại được kết quả).
- Nước đi không hợp lệ (rơi, ra ngoài, đứng trên ô dễ vỡ...) KHÔNG xuất hiện trong
  get_successors; solver không cần biết luật thua.
- Chi phí mặc định mỗi bước = 1. UCS có thể truyền cost_fn riêng.
"""
from typing import Callable, List, Optional, Tuple

from .block import Block
from .board import Board
from .level_loader import Level
from .state import STAND, State

Action = str
ACTIONS = ("U", "D", "L", "R", "S")

# cost_fn(old_state, action, new_state) -> float
CostFn = Callable[[State, Action, State], float]


class Game:
    """Giao diện duy nhất của solver/GUI: initial_state, is_goal, get_successors."""

    def __init__(self, level: Level, cost_fn: Optional[CostFn] = None):
        self.level = level
        self.cost_fn = cost_fn
        # Dựng một lần, không dựng lại mỗi lần get_successors (CODING_STANDARDS mục 7)
        self.board = Board.from_strings(level.grid)

    def initial_state(self) -> State:
        """Khối đứng ở ô start, cầu theo trạng thái ban đầu trong level."""
        r, c = self.level.start
        return State(r, c, STAND, self.level.initial_bridge_mask(), None)

    def is_goal(self, s: State) -> bool:
        """Thắng khi khối ĐỨNG (không tách) trên ô đích."""
        return s.split is None and self.board.is_win(Block(s.r, s.c, s.orient))

    def get_successors(self, s: State) -> List[Tuple[Action, State, float]]:
        """Trả về [(action, new_state, cost), ...] chỉ gồm nước đi HỢP LỆ (thứ tự U, D, L, R)."""
        # TODO [B]: ô dễ vỡ, cầu, công tắc | [C]: tách/ghép, cube đơn, hành động "S"
        result: List[Tuple[Action, State, float]] = []
        for action, block in self.board.valid_moves(Block(s.r, s.c, s.orient)):
            new_state = State(block.r, block.c, block.orient, s.bridges, s.split)
            result.append((action, new_state, self.step_cost(s, action, new_state)))
        return result

    def step_cost(self, old: State, action: Action, new: State) -> float:
        """Chi phí một bước: mặc định 1.0, hoặc theo cost_fn nếu có."""
        return 1.0 if self.cost_fn is None else self.cost_fn(old, action, new)