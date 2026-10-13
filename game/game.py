"""Giao diện game mà solver và GUI dùng. CHỈ ĐƯỢC GỌI QUA 3 HÀM DƯỚI ĐÂY.

Quy ước:
- Hành động: "U", "D", "L", "R"; "S" = đổi cube đang điều khiển (chỉ khi đang tách).
- Thứ tự sinh hành động CỐ ĐỊNH: U, D, L, R, S (để DFS lặp lại được kết quả).
- Nước đi không hợp lệ (rơi, ra ngoài, đứng trên ô dễ vỡ...) KHÔNG xuất hiện trong
  get_successors; solver không cần biết luật thua.
- Chi phí mặc định mỗi bước = 1. UCS có thể truyền cost_fn riêng.
"""
from typing import Callable, List, Optional, Tuple

from .level_loader import Level
from .state import State

Action = str
ACTIONS = ("U", "D", "L", "R", "S")
DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

# cost_fn(old_state, action, new_state) -> float
CostFn = Callable[[State, Action, State], float]


class Game:
    def __init__(self, level: Level, cost_fn: Optional[CostFn] = None):
        self.level = level
        self.cost_fn = cost_fn

    def initial_state(self) -> State:
        """Khối đứng ở ô start, cầu theo trạng thái ban đầu trong level."""
        r, c = self.level.start
        return State(r, c, 0, self.level.initial_bridge_mask(), None)

    def is_goal(self, s: State) -> bool:
        """Thắng khi khối ĐỨNG (không tách) trên ô đích."""
        raise NotImplementedError  # TODO [A5]

    def get_successors(self, s: State) -> List[Tuple[Action, State, float]]:
        """Trả về [(action, new_state, cost), ...] chỉ gồm nước đi HỢP LỆ."""
        raise NotImplementedError  # TODO [A8] -> [B] ô nâng cao -> [C7] tách/ghép

    def step_cost(self, old: State, action: Action, new: State) -> float:
        return 1.0 if self.cost_fn is None else self.cost_fn(old, action, new)
