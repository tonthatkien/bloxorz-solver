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
from .cube import move_cube, try_merge
from .level_loader import Level
from .split import activate_split_switch
from .state import STAND, State
from .tiles import TileRules

Action = str
ACTIONS = ("U", "D", "L", "R", "S")

# cost_fn(old_state, action, new_state) -> float
CostFn = Callable[[State, Action, State], float]


class Game:
    """Giao diện duy nhất của solver/GUI: initial_state, is_goal, get_successors."""

    def __init__(self, level: Level, cost_fn: Optional[CostFn] = None) -> None:
        self.level = level
        self.cost_fn = cost_fn
        # Dựng một lần, không dựng lại mỗi lần get_successors (CODING_STANDARDS mục 7)
        self.board = Board.from_strings(level.grid)
        self.tile_rules = TileRules.from_level(level)

    def initial_state(self) -> State:
        """Khối đứng ở ô start, cầu theo trạng thái ban đầu trong level."""
        r, c = self.level.start
        return State(r, c, STAND, self.level.initial_bridge_mask(), None)

    def is_goal(self, s: State) -> bool:
        """Thắng khi khối ĐỨNG (không tách) trên ô đích."""
        return s.split is None and self.board.is_win(Block(s.r, s.c, s.orient))

    def get_successors(self, s: State) -> List[Tuple[Action, State, float]]:
        """Sinh nước U, D, L, R, S; chỉ tính chi phí sau khi chốt trạng thái cuối."""
        moves: List[Tuple[Action, Optional[State]]]
        if s.split is not None:
            # Trạng thái split kề nhau vi phạm tiền điều kiện C1, không có nước hợp lệ.
            if try_merge(s.split[0], s.split[1], s.bridges) is not None:
                return []
            moves = [(action, move_cube(s, action, self.level)) for action in ACTIONS]
        else:
            block = Block(s.r, s.c, s.orient)
            moves = [(action, State(pose.r, pose.c, pose.orient, s.bridges))
                     for action, pose in self.board.valid_moves(block)]

        result: List[Tuple[Action, State, float]] = []
        for action, moved in moves:
            if moved is None:
                continue
            # B2 kiểm tra sàn trước/sau hiệu ứng, gồm cả cube đang đứng yên.
            resolved = self.tile_rules.resolve_landing(s, moved)
            if resolved is None:
                continue
            # Theo C2, chỉ lăn khối thường mới kích hoạt split, không phải lúc ghép.
            if s.split is None:
                split_state = activate_split_switch(s, resolved, self.level)
                if split_state is not None:
                    resolved = split_state
                    # Dịch chuyển đổi footprint; phải kiểm tra cả hai điểm đến.
                    if not self.tile_rules.is_supported(resolved):
                        continue
            result.append((action, resolved, self.step_cost(s, action, resolved)))
        return result

    def step_cost(self, old: State, action: Action, new: State) -> float:
        """Chi phí một bước: mặc định 1.0, hoặc theo cost_fn nếu có."""
        return 1.0 if self.cost_fn is None else self.cost_fn(old, action, new)
