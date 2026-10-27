"""Solver DFS: ngăn xếp tự quản lý + tập visited (task E2).

Cách hoạt động:
- Frontier là một list dùng như stack (pop lấy phần tử cuối), không dùng đệ quy để tránh
  RecursionError khi đường đi dài.
- `parent` vừa để truy vết đường đi, vừa là tập visited: một trạng thái chỉ được push một lần.
  State bao gồm cả bitmask cầu và thông tin tách cube nên hai trạng thái khác cầu là khác nhau.
- Duyệt successor theo thứ tự đảo ngược để hành động đầu tiên (U, D, L, R, S) nằm trên đỉnh
  stack và được xét trước, nhờ đó kết quả lặp lại được.

Tính chất: luôn kết thúc (không gian trạng thái hữu hạn, có visited) và tìm ra lời giải nếu có,
nhưng lời giải KHÔNG đảm bảo ngắn nhất hay rẻ nhất.

Quy ước đếm: mỗi lần lấy một nút ra khỏi stack thì expanded += 1, rồi mới kiểm tra đích
(giống toy_bfs/toy_dfs trong tests/test_metrics.py). `cost` do solvers.metrics.measure điền.
"""
from typing import Optional

from .base import LimitChecker, Limits, SearchResult, reconstruct_path


def solve(game, limits: Optional[Limits] = None) -> SearchResult:
    """Tìm lời giải bằng DFS; trả SearchResult(solved=False) nếu hết không gian tìm kiếm."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    parent = {start: None}
    stack = [start]
    expanded = 0
    while stack:
        state = stack.pop()
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(state):
            path = reconstruct_path(parent, state)
            return SearchResult(solved=True, path=path, expanded_nodes=expanded,
                                length=len(path))
        for action, nxt, _cost in reversed(game.get_successors(state)):
            if nxt not in parent:
                parent[nxt] = (state, action)
                stack.append(nxt)
    return SearchResult(solved=False, expanded_nodes=expanded)