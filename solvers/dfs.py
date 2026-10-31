"""Solver DFS: ngăn xếp tự quản lý + tập visited (task E2).

Cách hoạt động:
- Frontier là một list dùng như stack (pop lấy phần tử cuối), không dùng đệ quy để tránh
  RecursionError khi đường đi dài.
- `parent` vừa để truy vết đường đi, vừa là tập visited: một trạng thái chỉ được push một lần.
  State bao gồm cả bitmask cầu và thông tin tách cube nên hai trạng thái khác cầu là khác nhau.
- `g_values` lưu chi phí lũy kế từ start tới từng state (theo đúng path mà `parent` sẽ dựng lại),
  để `SearchResult.cost` có giá trị thực ngay cả khi không đi qua `measure()` — cần cho bảng
  tổng hợp của `experiments/run_all.py`.
- Duyệt successor theo thứ tự đảo ngược để hành động đầu tiên (U, D, L, R, S) nằm trên đỉnh
  stack và được xét trước, nhờ đó kết quả lặp lại được.

Tính chất: luôn kết thúc (không gian trạng thái hữu hạn, có visited) và tìm ra lời giải nếu có,
nhưng lời giải KHÔNG đảm bảo ngắn nhất hay rẻ nhất. Vì `g_values` chỉ được ghi lần đầu khi state
được push (visited), `cost` phản ánh chi phí của path DFS tìm được, không phải chi phí tối ưu.

Quy ước đếm: mỗi lần lấy một nút ra khỏi stack thì expanded += 1, rồi mới kiểm tra đích
(giống toy_bfs/toy_dfs trong tests/test_metrics.py).
"""
from typing import Optional

from .base import LimitChecker, Limits, SearchResult, reconstruct_path


def solve(game, limits: Optional[Limits] = None,
          record_trace: bool = False) -> SearchResult:
    """Tìm lời giải bằng DFS; trả SearchResult(solved=False) nếu hết không gian tìm kiếm."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    parent = {start: None}
    g_values = {start: 0.0}
    stack = [start]
    expanded = 0
    order = []
    while stack:
        state = stack.pop()
        expanded += 1
        checker.tick(expanded)
        if record_trace:
            order.append(state)
        if game.is_goal(state):
            path = reconstruct_path(parent, state)
            return SearchResult(solved=True, path=path, expanded_nodes=expanded,
                                length=len(path), cost=g_values[state],
                                expanded_order=order)
        for action, nxt, step in reversed(game.get_successors(state)):
            if nxt not in parent:
                parent[nxt] = (state, action)
                g_values[nxt] = g_values[state] + step
                stack.append(nxt)
    return SearchResult(solved=False, expanded_nodes=expanded, expanded_order=order)