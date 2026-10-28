"""Solver A* (task E2): mở rộng nút có f = g + h nhỏ nhất.

- g: tổng chi phí thật từ trạng thái đầu (lấy từ số thứ 3 của game.get_successors, nên
  dùng đúng hàm chi phí mà Game được tạo với, đồng đều hoặc make_cost_fn).
- h: heuristic `h(game, state) -> float`, truyền vào bằng HÀM hoặc bằng TÊN trong
  solvers.heuristics_advanced.HEURISTICS ("zero", "manhattan", "manhattan_orient",
  "relaxed_maze", "switch_aware", "split_cubes", "advanced").
- Heuristic mặc định là h_advanced: admissible và consistent trên mọi nhóm màn (chứng minh ở
  docs/cost_heuristic.md, mục III), nên A* cho chi phí tối ưu, bằng UCS.
  Với "zero" thì A* chính là UCS.

Chi tiết cài đặt:
- Hàng đợi ưu tiên heapq với tuple (f, counter, g, state). `counter` phá hòa để Python không
  bao giờ phải so sánh hai State với nhau (CODING_STANDARDS mục 4).
- `best_g[state]` là chi phí nhỏ nhất đã biết tới state. Khi tìm được đường rẻ hơn thì push thêm
  một bản mới; bản cũ nằm lại trong heap và bị bỏ qua khi pop ra (g > best_g), không được đếm
  vào expanded ("lazy deletion"). Cách này vẫn đúng kể cả khi heuristic không consistent.
- Kiểm tra đích khi pop (không phải lúc sinh) để đảm bảo tối ưu với chi phí không đồng đều.
- Nếu heuristic trả math.inf thì trạng thái đó không thể tới đích, bỏ qua luôn.

`solve(game, limits)` giữ đúng hợp đồng chung; `solve_with` chọn heuristic; `solver_for` trả
về một hàm `(game, limits) -> SearchResult` để dùng với measure()/run_measured, GUI, thực nghiệm.
"""
import heapq
import math
from typing import Callable, Optional, Union

from game.state import State

from .base import LimitChecker, Limits, SearchResult, reconstruct_path
from .heuristics_advanced import HEURISTICS, Heuristic, get_heuristic, h_advanced

DEFAULT_HEURISTIC: Heuristic = h_advanced


def _validate_heuristic_value(h_val: float) -> None:
    """Kiểm tra giá trị heuristic phải là số thực không âm và không phải NaN."""
    if math.isnan(h_val) or h_val < 0:
        raise ValueError("Heuristic phải là số thực không âm.")


def solve_with(game, heuristic: Union[str, Heuristic],
               limits: Optional[Limits] = None) -> SearchResult:
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
            h_next = h(game, nxt)
            _validate_heuristic_value(h_next)
            if math.isinf(h_next):
                continue
            best_g[nxt] = new_g
            parent[nxt] = (state, action)
            counter += 1
            heapq.heappush(heap, (new_g + h_next, counter, new_g, nxt))
    return SearchResult(solved=False, expanded_nodes=expanded)


def solver_for(heuristic: Union[str, Heuristic]) -> Callable[..., SearchResult]:
    """Trả về hàm solve(game, limits=None) dùng heuristic đã chọn (kiểm tra tên ngay)."""
    h = get_heuristic(heuristic)

    def solver(game, limits: Optional[Limits] = None) -> SearchResult:
        return solve_with(game, h, limits)

    return solver


def solve(game, limits: Optional[Limits] = None) -> SearchResult:
    """A* với heuristic mặc định (chữ ký chung của mọi solver)."""
    return solve_with(game, DEFAULT_HEURISTIC, limits)