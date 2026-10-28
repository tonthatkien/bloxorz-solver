"""Thuật toán UCS."""

import heapq
import itertools
import math
from typing import Optional

from game.game import Game
from game.state import State

from .base import LimitChecker, Limits, SearchResult, reconstruct_path


def _finite_cost(step_cost: float) -> float:
    """Chuyển chi phí bước sang số hữu hạn để UCS có thể so sánh chính xác."""
    try:
        cost = float(step_cost)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Chi phí chuyển trạng thái phải là một số hữu hạn.") from error
    if not math.isfinite(cost):
        raise ValueError("Chi phí chuyển trạng thái phải là một số hữu hạn.")
    # UCS tổng quát cho phép chi phí 0.
    # Nếu có cạnh 0, solve() chỉ cập nhật khi tìm được đường rẻ hơn nên chu trình
    # 0 không enqueue lại trạng thái với cùng chi phí trên không gian hữu hạn.
    if cost < 0:
        raise ValueError("Chi phí chuyển trạng thái không âm để UCS đảm bảo tối ưu.")
    return cost


def solve(game: Game, limits: Optional[Limits] = None) -> SearchResult:
    """Tìm đường đi có tổng chi phí nhỏ nhất bằng hàng đợi ưu tiên UCS."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    # Số thứ tự giúp heap xử lý trạng thái cùng chi phí mà không so sánh các trạng thái.
    order = itertools.count()
    frontier: list[tuple[float, int, State]] = [(0.0, next(order), start)]
    cost_so_far = {start: 0.0}
    parent: dict[State, Optional[tuple[State, str]]] = {start: None}
    expanded = 0

    while frontier:
        current_cost, _, current = heapq.heappop(frontier)
        if current_cost > cost_so_far[current]:
            continue
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(
                solved=True,
                path=path,
                expanded_nodes=expanded,
                length=len(path),
                cost=current_cost,
            )

        for action, next_state, raw_step_cost in game.get_successors(current):
            step_cost = _finite_cost(raw_step_cost)
            next_cost = current_cost + step_cost
            if not math.isfinite(next_cost):
                raise ValueError("Tổng chi phí đường đi phải là một số hữu hạn.")
            if next_state in cost_so_far and next_cost >= cost_so_far[next_state]:
                continue
            cost_so_far[next_state] = next_cost
            parent[next_state] = (current, action)
            heapq.heappush(frontier, (next_cost, next(order), next_state))

    return SearchResult(expanded_nodes=expanded)
