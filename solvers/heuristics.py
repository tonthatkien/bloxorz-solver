"""Hàm chi phí bước (cost function) và các hàm heuristic cho bộ giải A*.
"""

import math
from collections import deque
from typing import Dict, List, Sequence, Tuple

from game.game import CostFn, Game
from game.level_loader import Level
from game.state import HORIZ, STAND, State

COST_NORMAL: float = 1.0    # Bước lăn thông thường trên ô sàn chắc chắn
COST_FRAGILE: float = 1.5   # Bước lăn khiến một phần khối nằm lên ô dễ vỡ
COST_SWITCH: float = 1.2    # Bước lăn kích hoạt công tắc bất kỳ
COST_SWAP: float = 0.5      # Hành động 'S' – hoán đổi cube đang điều khiển

COST_MIN: float = COST_NORMAL  # Mọi bước lăn tốn ít nhất mức này.


def _step_cost(
    level: Level,
    old_state: State,
    action: str,
    new_state: State,
) -> float:
    """Tính chi phí một hành động theo luật và địa hình của màn chơi."""
    # Hành động hoán đổi cube không di chuyển vị trí thực
    if action == "S":
        return COST_SWAP

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
    if new_state.split is None:
        for cell in new_cells:
            if cell in level.fragile:
                return COST_FRAGILE

    return COST_NORMAL


def step_cost(game: Game, old_state: State, action: str, new_state: State) -> float:
    """Tính chi phí một bước từ đối tượng Game hiện tại."""
    return _step_cost(game.level, old_state, action, new_state)


def make_cost_fn(level: Level) -> CostFn:
    """Tạo callback ba tham số tương thích với `Game(level, cost_fn=...)`."""

    def cost_fn(old_state: State, action: str, new_state: State) -> float:
        return _step_cost(level, old_state, action, new_state)

    return cost_fn


def _uses_split_mechanics(level: Level, state: State) -> bool:
    """Cho biết heuristic hình học có thể bị split hoặc đổi cube làm sai lệch."""
    has_split_switch = any(switch.type == "split" for switch in level.switches.values())
    return state.split is not None or has_split_switch


def _block_centroid(state: State) -> Tuple[float, float]:
    """Trả về tọa độ tâm hình học của khối 1x1x2 liền."""
    if state.orient == STAND:
        return float(state.r), float(state.c)
    if state.orient == HORIZ:
        return float(state.r), state.c + 0.5

    return state.r + 0.5, float(state.c)


def _bfs_distance_map(
    grid: Sequence[str],
    goal: Tuple[int, int],
    rows: int,
    cols: int,
) -> Dict[Tuple[int, int], int]:
    """Tính khoảng cách BFS từ goal tới các ô đi được trên lưới."""
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
def h_zero(game: Game, state: State) -> float:
    """Trả về 0; đây là heuristic admissible và consistent cho mọi màn."""
    return 0.0


# Heuristic 1: Khoảng cách Manhattan tỷ lệ hoá (h_manhattan)
def h_manhattan(game: Game, state: State) -> float:
    if _uses_split_mechanics(game.level, state):
        return 0.0

    goal = game.level.goal
    rc, cc = _block_centroid(state)
    manhattan = abs(rc - goal[0]) + abs(cc - goal[1])
    return math.ceil(manhattan / 2.0) * COST_MIN


# Heuristic 2: Manhattan orient
def h_manhattan_orient(game: Game, state: State) -> float:
    if _uses_split_mechanics(game.level, state):
        return 0.0

    goal = game.level.goal
    rc, cc = _block_centroid(state)
    d = abs(rc - goal[0]) + abs(cc - goal[1])
    return math.ceil(d / 1.5) * COST_MIN

# Heuristic 3: BFS hạ biên trên lưới nới lỏng (h_relaxed_maze)
class _RelaxedMazeCache:
    """Cache bảng khoảng cách cho cùng lưới và goal."""

    _cache: Dict[tuple, Dict[Tuple[int, int], int]] = {}

    @classmethod
    def get(
        cls,
        grid: List[str],
        goal: Tuple[int, int],
        rows: int,
        cols: int,
    ) -> Dict[Tuple[int, int], int]:
        """Lấy bảng khoảng cách đã cache hoặc tính bảng mới bằng BFS."""
        key = (tuple(grid), goal)
        if key not in cls._cache:
            cls._cache[key] = _bfs_distance_map(grid, goal, rows, cols)
        return cls._cache[key]


def h_relaxed_maze(game: Game, state: State) -> float:
    level = game.level
    if _uses_split_mechanics(level, state):
        return 0.0

    dist_map = _RelaxedMazeCache.get(
        level.grid, level.goal, level.rows, level.cols
    )

    if state.orient == STAND:
        pos = (state.r, state.c)
    elif state.orient == HORIZ:
        # Lấy ô gần goal hơn
        c1 = (state.r, state.c)
        c2 = (state.r, state.c + 1)
        d1 = dist_map.get(c1, math.inf)
        d2 = dist_map.get(c2, math.inf)
        pos = c1 if d1 <= d2 else c2
    else:  # VERT
        c1 = (state.r, state.c)
        c2 = (state.r + 1, state.c)
        d1 = dist_map.get(c1, math.inf)
        d2 = dist_map.get(c2, math.inf)
        pos = c1 if d1 <= d2 else c2

    d = dist_map.get(pos)
    if d is None:
        return math.inf  # Không có đường trên lưới nới lỏng nên không có lời giải.
    return math.ceil(d / 2.0) * COST_MIN
