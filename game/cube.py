"""Di chuyển, đổi cube điều khiển và tự ghép hai cube đơn (C1).

Quy ước:
- Khi split khác None, split = ((r1, c1), (r2, c2)); phần tử đầu là cube đang điều khiển.
- Khi split có giá trị, r=0, c=0, orient=STAND để trạng thái luôn được chuẩn hóa.
- Hành động S đổi cube đang điều khiển; U, D, L, R di chuyển cube đó đúng một ô.
- Khi hai cube kề cạnh sau khi di chuyển, chúng tự ghép thành khối 1x1x2.
"""
from typing import Optional

from .level_loader import Level
from .state import Cell, HORIZ, STAND, State, VERT

CUBE_DIRECTIONS: dict[str, Cell] = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}


def swap_active_cube(state: State) -> State:
    """Đổi cube đang điều khiển khi khối ở trạng thái split."""
    if state.split is None:
        raise ValueError("Chỉ có thể đổi cube điều khiển khi khối đang ở trạng thái split.")
    c1, c2 = state.split
    return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(c2, c1))


def try_merge(cube_a: Cell, cube_b: Cell, bridges: int) -> Optional[State]:
    """Ghép hai cube kề cạnh thành khối nằm ngang hoặc thẳng đứng.

    Trả về trạng thái khối liền nếu hai vị trí cách nhau một ô theo hàng hoặc cột;
    nếu không kề nhau thì trả về None.
    """
    r1, col1 = cube_a
    r2, col2 = cube_b

    if r1 == r2 and abs(col1 - col2) == 1:
        return State(r=r1, c=min(col1, col2), orient=HORIZ, bridges=bridges, split=None)

    if col1 == col2 and abs(r1 - r2) == 1:
        return State(r=min(r1, r2), c=col1, orient=VERT, bridges=bridges, split=None)

    return None


def _is_walkable(level: Level, state: State, position: Cell) -> bool:
    """Kiểm tra ô có sàn đỡ theo trạng thái đóng/mở cầu hiện tại hay không."""
    row, column = position
    if not (0 <= row < level.rows and 0 <= column < level.cols):
        return False
    if level.grid[row][column] not in ("#", "G"):
        return False
    for bridge in level.bridges.values():
        if bridge.pos == position:
            return bool(state.bridges & (1 << bridge.id))
    return True


def move_cube(state: State, action: str, level: Level) -> Optional[State]:
    """Di chuyển cube đang điều khiển một ô hoặc đổi cube điều khiển.
    Tiền điều kiện: state.split không chứa 2 cube kề nhau; caller (C2) phải
    chuẩn hóa bằng try_merge trước khi gọi.

    Raises:
        ValueError: Nếu state chưa tách hoặc vi phạm tiền điều kiện (hai cube
            đang kề nhau). Guard này chỉ là kiểm tra bất biến.
    """
    if state.split is None:
        raise ValueError("move_cube chỉ xử lý trạng thái split.")
    if try_merge(state.split[0], state.split[1], state.bridges) is not None:
        raise ValueError("Hai cube đang kề nhau; hãy ghép chúng trước khi di chuyển.")

    if action == "S":
        return swap_active_cube(state)

    if action not in CUBE_DIRECTIONS:
        raise ValueError(f"Hướng di chuyển không hợp lệ cho cube: {action}")

    dr, dc = CUBE_DIRECTIONS[action]
    active_r, active_c = state.split[0]
    new_active: Cell = (active_r + dr, active_c + dc)
    inactive: Cell = state.split[1]
    if new_active == inactive or not _is_walkable(level, state, new_active):
        return None

    merged = try_merge(new_active, inactive, state.bridges)
    if merged is not None:
        return merged

    return State(r=0, c=0, orient=STAND, bridges=state.bridges, split=(new_active, inactive))