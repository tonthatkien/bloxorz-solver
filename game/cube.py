"""Cơ chế di chuyển, hoán đổi và tự động ghép cho 2 cube đơn (Task C1).

QUY ƯỚC DỰ ÁN (đã chốt trong state.py và AGENTS.md):
- Khi split is not None: split = ((r1, c1), (r2, c2)).
  - split[0] LUÔN LÀ cube đang được điều khiển (active).
  - split[1] là cube đứng yên (inactive).
  - r=0, c=0, orient=STAND được chuẩn hóa để State có hash duy nhất.
- Hành động 'S': hoán đổi quyền điều khiển giữa 2 cube.
- Hành động 'U', 'D', 'L', 'R': active cube lăn 1 ô (1x1x1 không có orientation).
- Tự động ghép (Merge): Nếu sau khi di chuyển, 2 cube kề cạnh nhau (Manhattan distance = 1),
  chúng tự động ghép lại thành khối 1x1x2 (split=None).
"""
from typing import Optional, Tuple

from .state import Cell, HORIZ, STAND, State, VERT

# Độ dời tọa độ (dr, dc) cho 4 hướng di chuyển của cube đơn 1x1x1
CUBE_DIRECTIONS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}


def swap_active_cube(state: State) -> State:
    """Hoán đổi cube đang điều khiển khi ở trạng thái split (hành động 'S')."""
    if state.split is None:
        raise ValueError("Chỉ có thể hoán đổi cube khi ở trạng thái phân tách (split is not None).")
    c1, c2 = state.split
    return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(c2, c1))


def try_merge(c1: Cell, c2: Cell, bridges: int) -> Optional[State]:
    """Kiểm tra và ghép 2 cube nếu kề cạnh (Manhattan distance == 1).

    Trả về State khối liền 1x1x2 (split=None) nếu kề nhau, ngược lại trả về None.
    """
    r1, col1 = c1
    r2, col2 = c2

    # Cùng hàng, kề cột -> ghép thành HORIZ
    if r1 == r2 and abs(col1 - col2) == 1:
        return State(r=r1, c=min(col1, col2), orient=HORIZ, bridges=bridges, split=None)

    # Cùng cột, kề hàng -> ghép thành VERT
    if col1 == col2 and abs(r1 - r2) == 1:
        return State(r=min(r1, r2), c=col1, orient=VERT, bridges=bridges, split=None)

    return None


def move_cube(state: State, action: str) -> State:
    """Di chuyển cube đang kích hoạt (active cube) hoặc đổi cube điều khiển.

    Args:
        state: Trạng thái hiện tại (bắt buộc state.split is not None).
        action: Một trong các hành động ('U', 'D', 'L', 'R', 'S').

    Returns:
        State mới sau khi di chuyển/hoán đổi/ghép nối.
    """
    if state.split is None:
        raise ValueError("move_cube chỉ xử lý trạng thái phân tách (state.split is not None).")

    if action == "S":
        return swap_active_cube(state)

    if action not in CUBE_DIRECTIONS:
        raise ValueError(f"Hành động không hợp lệ cho cube: {action}")

    dr, dc = CUBE_DIRECTIONS[action]
    active_r, active_c = state.split[0]
    new_active: Cell = (active_r + dr, active_c + dc)
    inactive: Cell = state.split[1]

    # Kiểm tra tự động ghép nối nếu 2 cube kề cạnh nhau
    merged = try_merge(new_active, inactive, state.bridges)
    if merged is not None:
        return merged

    # Nếu chưa kề nhau, duy trì trạng thái split với vị trí mới của active cube
    return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(new_active, inactive))






#     """Cơ chế di chuyển, hoán đổi và tự động ghép cho 2 cube đơn (Task C1)."""
# from typing import Optional, Tuple
# from .state import Cell, HORIZ, STAND, State, VERT

# CUBE_DIRECTIONS = {
#     "U": (-1, 0),
#     "D": (1, 0),
#     "L": (0, -1),
#     "R": (0, 1),
# }

# def swap_active_cube(state: State) -> State:
#     """Hoán đổi cube đang điều khiển khi ở trạng thái split (hành động 'S')."""
#     if state.split is None:
#         raise ValueError("Chỉ có thể hoán đổi cube khi ở trạng thái phân tách (split is not None).")
#     c1, c2 = state.split
#     return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(c2, c1))

# def try_merge(c1: Cell, c2: Cell, bridges: int) -> Optional[State]:
#     """Kiểm tra và ghép 2 cube nếu kề cạnh (Manhattan distance == 1)."""
#     r1, col1 = c1
#     r2, col2 = c2
#     if r1 == r2 and abs(col1 - col2) == 1:
#         return State(r=r1, c=min(col1, col2), orient=HORIZ, bridges=bridges, split=None)
#     if col1 == col2 and abs(r1 - r2) == 1:
#         return State(r=min(r1, r2), c=col1, orient=VERT, bridges=bridges, split=None)
#     return None

# def move_cube(state: State, action: str) -> State:
#     """Di chuyển cube đang kích hoạt (active cube) hoặc đổi cube điều khiển."""
#     if state.split is None:
#         raise ValueError("move_cube chỉ xử lý trạng thái phân tách (state.split is not None).")
#     if action == "S":
#         return swap_active_cube(state)
#     if action not in CUBE_DIRECTIONS:
#         raise ValueError(f"Hành động không hợp lệ cho cube: {action}")

#     dr, dc = CUBE_DIRECTIONS[action]
#     active_r, active_c = state.split[0]
#     new_active: Cell = (active_r + dr, active_c + dc)
#     inactive: Cell = state.split[1]

#     merged = try_merge(new_active, inactive, state.bridges)
#     if merged is not None:
#         return merged

#     return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(new_active, inactive))
