"""Thuật toán BFS."""

import math
from collections import deque
from typing import Optional

from game.state import State

from .base import LimitChecker, Limits, SearchResult, reconstruct_path


def _finite_cost(step_cost: float) -> float:
    """Đổi chi phí bước đi thành số hữu hạn để báo cáo tổng chi phí của đường đi."""
    try:
        cost = float(step_cost)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Chi phí chuyển trạng thái phải là một số hữu hạn.") from error
    if not math.isfinite(cost):
        raise ValueError("Chi phí chuyển trạng thái phải là một số hữu hạn.")
    return cost


def solve(game, limits: Optional[Limits] = None) -> SearchResult:
    """Tìm đường đi có ít hành động nhất, dùng FIFO và đánh dấu visited khi đưa vào hàng đợi."""
    checker = LimitChecker(limits)
    start = game.initial_state()
    frontier: deque[State] = deque([start])
    visited = {start}
    parent: dict[State, Optional[tuple[State, str]]] = {start: None}
    path_cost = {start: 0.0}
    expanded = 0

    while frontier:
        current = frontier.popleft()
        expanded += 1
        checker.tick(expanded)
        if game.is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(
                solved=True,
                path=path,
                expanded_nodes=expanded,
                length=len(path),
                cost=path_cost[current],
            )

        for action, next_state, step_cost in game.get_successors(current):
            if next_state in visited:
                continue
            visited.add(next_state)
            parent[next_state] = (current, action)
            path_cost[next_state] = path_cost[current] + _finite_cost(step_cost)
            frontier.append(next_state)

    return SearchResult(expanded_nodes=expanded)
