"""Game GIẢ (đường thẳng 1 chiều) để người viết solver test sớm, chưa cần chờ game core.

State dùng State(r=vị trí); đích ở vị trí n; "R" +1 (chi phí 1), "L" -1 (chi phí 1),
"D" +2 (chi phí 3). Cùng giao diện với Game: initial_state / is_goal / get_successors.
Khi game thật xong, đổi sang dùng Game là được.
"""
from .state import State


class DummyGame:
    def __init__(self, n: int = 10):
        self.n = n
        self.cost_fn = None

    def initial_state(self) -> State:
        return State(0, 0)

    def is_goal(self, s: State) -> bool:
        return s.r == self.n

    def get_successors(self, s: State):
        out = []
        for act, d, cost in (("L", -1, 1.0), ("R", 1, 1.0), ("D", 2, 3.0)):
            nr = s.r + d
            if 0 <= nr <= self.n:
                out.append((act, State(nr, 0), cost))
        return out
