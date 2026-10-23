"""Hàm chi phí bước (cost function) và các hàm heuristic cho bộ giải A*.
"""

import math
from collections import deque
from typing import Dict, Tuple

from game.state import HORIZ, STAND, VERT, State

COST_NORMAL: float = 1.0    # Bước lăn thông thường trên ô sàn chắc chắn
COST_FRAGILE: float = 1.5   # Bước lăn khiến một phần khối nằm lên ô dễ vỡ
COST_SWITCH: float = 1.2    # Bước lăn kích hoạt công tắc bất kỳ
COST_SWAP: float = 0.5      # Hành động 'S' – hoán đổi cube đang điều khiển

COST_MIN: float = COST_NORMAL


def step_cost(game, old_state: State, action: str, new_state: State) -> float:
    # Hành động hoán đổi cube không di chuyển vị trí thực
    if action == "S":
        return COST_SWAP

    level = game.level

    # Tập ô mà khối mới chiếm sau khi lăn
    if new_state.split is not None:
        new_cells = list(new_state.split)
    elif new_state.orient == STAND:
        new_cells = [(new_state.r, new_state.c)]
    elif new_state.orient == HORIZ:
        new_cells = [(new_state.r, new_state.c), (new_state.r, new_state.c + 1)]
    else:  
        new_cells = [(new_state.r, new_state.c), (new_state.r + 1, new_state.c)]

    # Kiểm tra có kích hoạt công tắc
    if old_state.bridges != new_state.bridges:
        return COST_SWITCH

    # Kiểm tra công tắc split
    if old_state.split is None and new_state.split is not None:
        return COST_SWITCH

    # Kiểm tra có đè lên ô dễ vỡ 
    for cell in new_cells:
        if cell in level.fragile:
            return COST_FRAGILE

    return COST_NORMAL


def block_centroid(state: State) -> Tuple[float, float]:
    if state.split is not None:
        r, c = state.split[0]   # cube đang điều khiển
        return float(r), float(c)
    if state.orient == STAND:
        return float(state.r), float(state.c)
    if state.orient == HORIZ:
        return float(state.r), state.c + 0.5
    
    return state.r + 0.5, float(state.c)


def bfs_distance_map(
    grid: list,
    goal: Tuple[int, int],
    rows: int,
    cols: int,
) -> Dict[Tuple[int, int], int]:
    dist: Dict[Tuple[int, int], int] = {}
    queue: deque = deque()
    queue.append(goal)
    dist[goal] = 0
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) not in dist and grid[nr][nc] != ".":
                    dist[(nr, nc)] = dist[(r, c)] + 1
                    queue.append((nr, nc))
    return dist


# Heuristic 0: Baseline (h = 0)
def h_zero(game, state: State) -> float:
    return 0.0


# Heuristic 1: Khoảng cách Manhattan tỷ lệ hoá (h_manhattan)
def h_manhattan(game, state: State) -> float:
    goal = game.level.goal
    rc, cc = _block_centroid(state)
    manhattan = abs(rc - goal[0]) + abs(cc - goal[1])
    return math.ceil(manhattan / 2.0) * COST_MIN


# Heuristic 2: Manhattan orient
def h_manhattan_orient(game, state: State) -> float:
    goal = game.level.goal
    rc, cc = _block_centroid(state)
    d = abs(rc - goal[0]) + abs(cc - goal[1])
    base = math.ceil(d / 2.0) * COST_MIN

    if state.split is None and state.orient != STAND and d <= 2:
        return base + COST_MIN
    return base

# Heuristic 3: BFS hạ biên trên lưới nới lỏng (h_relaxed_maze)
class _RelaxedMazeCache:
    _cache: Dict[tuple, Dict[Tuple[int, int], int]] = {}

    @classmethod
    def get(
        cls,
        grid: list,
        goal: Tuple[int, int],
        rows: int,
        cols: int,
    ) -> Dict[Tuple[int, int], int]:
        key = (tuple(grid), goal)
        if key not in cls._cache:
            cls._cache[key] = _bfs_distance_map(grid, goal, rows, cols)
        return cls._cache[key]


def h_relaxed_maze(game, state: State) -> float:
    level = game.level
    dist_map = _RelaxedMazeCache.get(
        level.grid, level.goal, level.rows, level.cols
    )

    if state.split is not None:
        # Khi tách: dùng vị trí cube đang điều khiển (split[0])
        pos = state.split[0]
    elif state.orient == STAND:
        pos = (state.r, state.c)
    elif state.orient == HORIZ:
        # Lấy ô gần goal hơn
        c1 = (state.r, state.c)
        c2 = (state.r, state.c + 1)
        d1 = dist_map.get(c1, 10**9)
        d2 = dist_map.get(c2, 10**9)
        pos = c1 if d1 <= d2 else c2
    else:  # VERT
        c1 = (state.r, state.c)
        c2 = (state.r + 1, state.c)
        d1 = dist_map.get(c1, 10**9)
        d2 = dist_map.get(c2, 10**9)
        pos = c1 if d1 <= d2 else c2

    d = dist_map.get(pos, 10**9)
    if d == 10**9:
        return float(d)   # goal không thể tới → trả về vô cực
    return math.ceil(d / 2.0) * COST_MIN
