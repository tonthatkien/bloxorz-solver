"""Solver A* (task E2): mở rộng nút có f = g + h nhỏ nhất.

- g: tổng chi phí thật từ trạng thái đầu (lấy từ số thứ 3 của game.get_successors, nên
  dùng đúng hàm chi phí mà Game được tạo với, đồng đều hoặc make_cost_fn).
- h: heuristic `h(game, state) -> float` trong solvers/heuristics.py.
- Heuristic mặc định là h_manhattan_orient: admissible và consistent với COST_MIN = 1.0
  (chứng minh ở docs/cost_heuristic.md), nên A* cho chi phí tối ưu, bằng UCS.
  Với h_zero thì A* chính là UCS.

Chi tiết cài đặt:
- Hàng đợi ưu tiên heapq với tuple (f, counter, g, state). `counter` phá hòa để Python không
  bao giờ phải so sánh hai State với nhau (CODING_STANDARDS mục 4).
- `best_g[state]` là chi phí nhỏ nhất đã biết tới state. Khi tìm được đường rẻ hơn thì push thêm
  một bản mới; bản cũ nằm lại trong heap và bị bỏ qua khi pop ra (g > best_g), không được đếm
  vào expanded ("lazy deletion").
- Kiểm tra đích khi pop (không phải lúc sinh) để đảm bảo tối ưu với chi phí không đồng đều.
- Nếu heuristic trả math.inf thì trạng thái đó không thể tới đích, bỏ qua luôn.

`solve(game, limits)` giữ đúng hợp đồng chung; `solve_with` cho phép thử heuristic khác
(thực nghiệm, test).
"""
import heapq
import math
from typing import Callable, Optional

from game.state import State

from .base import LimitChecker, Limits, SearchResult, reconstruct_path
from .heuristics import h_manhattan_orient

Heuristic = Callable[[object, State], float]
DEFAULT_HEURISTIC: Heuristic = h_manhattan_orient


def solve_with(game, heuristic: Heuristic, limits: Optional[Limits] = None) -> SearchResult:
    """A* với heuristic tùy chọn; `cost` trong kết quả là g của nút đích."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    h_start = heuristic(game, start)
    if math.isinf(h_start):
        return SearchResult(solved=False)
    best_g = {start: 0.0}
    parent = {start: None}
    counter = 0
    heap = [(h_start, counter, 0.0, start)]
    expanded = 0
    while heap:
        _f, _tie, g, state = heapq.heappop(heap)
        if g > best_g[state]:
            continue
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(state):
            path = reconstruct_path(parent, state)
            return SearchResult(solved=True, path=path, expanded_nodes=expanded,
                                length=len(path), cost=g)
        for action, nxt, step in game.get_successors(state):
            new_g = g + step
            if new_g >= best_g.get(nxt, math.inf):
                continue
            h_next = heuristic(game, nxt)
            if math.isinf(h_next):
                continue
            best_g[nxt] = new_g
            parent[nxt] = (state, action)
            counter += 1
            heapq.heappush(heap, (new_g + h_next, counter, new_g, nxt))
    return SearchResult(solved=False, expanded_nodes=expanded)


def solve(game, limits: Optional[Limits] = None) -> SearchResult:
    """A* với heuristic mặc định (chữ ký chung của mọi solver)."""
    return solve_with(game, DEFAULT_HEURISTIC, limits)