import heapq
import math
from typing import Callable, Optional, Union

from game.state import State

from .base import LimitChecker, Limits, SearchResult, reconstruct_path
from .heuristics_advanced import HEURISTICS, Heuristic, get_heuristic, h_advanced

DEFAULT_HEURISTIC: Heuristic = h_advanced


def _validate_heuristic_value(h_val: float) -> None:
    """Heuristic phải là số thực không âm và không NaN (bảo vệ admissible)."""
    if math.isnan(h_val) or h_val < 0:
        raise ValueError("Heuristic phải là số thực không âm.")


def _validate_step_cost(step: float) -> None:
    """Chi phí bước đi phải hữu hạn và không âm.

    A* chỉ tối ưu khi mọi cạnh có chi phí >= 0 hữu hạn (đề mục 3.4, 3.5).
    step âm có thể tạo chu trình âm -> best_g giảm vô hạn -> A* không kết thúc.
    step NaN/inf làm hỏng so sánh heapq y như NaN heuristic.
    """
    if not math.isfinite(step) or step < 0:
        raise ValueError("Chi phí chuyển trạng thái phải là số hữu hạn không âm.")


def solve_with(game, heuristic: Union[str, Heuristic],
               limits: Optional[Limits] = None, record_trace: bool = False) -> SearchResult:
    """A* với heuristic tùy chọn (hàm hoặc tên); `cost` trong kết quả là g của nút đích."""
    h = get_heuristic(heuristic)
    checker = LimitChecker(limits)
    start = game.initial_state()
    h_start = h(game, start)
    _validate_heuristic_value(h_start)
    if math.isinf(h_start):
        return SearchResult(solved=False)
    best_g = {start: 0.0}
    parent = {start: None}
    counter = 0
    heap = [(h_start, counter, 0.0, start)]
    expanded = 0
    order = []
    while heap:
        _f, _tie, g, state = heapq.heappop(heap)
        if g > best_g[state]:
            continue
        expanded += 1
        checker.tick(expanded)
        if record_trace:
            order.append(state)
        if game.is_goal(state):
            path = reconstruct_path(parent, state)
            return SearchResult(solved=True, path=path, expanded_nodes=expanded,
                                length=len(path), cost=g, expanded_order=order)
        for action, nxt, step in game.get_successors(state):
            _validate_step_cost(step)           
            new_g = g + step
            if new_g >= best_g.get(nxt, math.inf):
                continue
            h_next = h(game, nxt)
            _validate_heuristic_value(h_next)
            if math.isinf(h_next):
                continue
            best_g[nxt] = new_g
            parent[nxt] = (state, action)
            counter += 1
            heapq.heappush(heap, (new_g + h_next, counter, new_g, nxt))
    return SearchResult(solved=False, expanded_nodes=expanded, expanded_order=order)


def solver_for(heuristic: Union[str, Heuristic]) -> Callable[..., SearchResult]:
    """Trả về hàm solve(game, limits=None) dùng heuristic đã chọn (kiểm tra tên ngay)."""
    h = get_heuristic(heuristic)

    def solver(game, limits: Optional[Limits] = None, record_trace: bool = False) -> SearchResult:
        return solve_with(game, h, limits, record_trace)

    return solver


def solve(game, limits: Optional[Limits] = None, record_trace: bool = False) -> SearchResult:
    """A* với heuristic mặc định (chữ ký chung của mọi solver)."""
    return solve_with(game, DEFAULT_HEURISTIC, limits, record_trace)