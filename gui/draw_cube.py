"""Module vẽ khối lập phương đơn (1x1x1) khi ở trạng thái tách (Task D4).

Quy ước:
- Khi tách, state.split = ((r1, c1), (r2, c2)).
- Phong cách 3 (Minimalist Pure): Thuần khiết như Bloxorz nguyên bản.
- split[0]: Cube đang điều khiển (Active) -> Gỗ Vàng Sáng (Warm Golden Wood).
- split[1]: Cube đứng yên (Inactive) -> Đá Xám Tro (Slate Stone) ngủ đông.
- Nhận diện 100% bằng chất liệu trực quan, không có mũi tên/icon lơ lửng che tầm nhìn.
- Kích thước mỗi cube đơn là 1x1x1 (lx=1, ly=1, lz=1).
"""
import math
from typing import List, Optional, Tuple
import pygame
import pygame.gfxdraw

from gui.render_board import _poly_aa

CUBE_HEIGHT: int = 60

# Màu sắc chỉ thị Kim Cương 3D (Indicator)
INDICATOR_LIGHT: Tuple[int, int, int] = (255, 255, 255)       # Trắng ngọc (Pure White)
INDICATOR_SHADOW: Tuple[int, int, int] = (203, 213, 225)      # Bạc tro (Silver Slate 300)
INDICATOR_EDGE: Tuple[int, int, int] = (15, 23, 42)           # Slate 900 viền sắc nét
INDICATOR_RIDGE: Tuple[int, int, int] = (148, 163, 184)       # Sống giữa Slate 400

# Tương thích ngược biến cũ nếu có module tham chiếu
INDICATOR_FILL: Tuple[int, int, int] = INDICATOR_LIGHT


def _wood_face_color(normal: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Tính màu mặt cho cube gỗ vàng sáng (Active) theo hướng pháp tuyến."""
    nx, ny, nz = normal
    r, g, b, total = 0.0, 0.0, 0.0, 0.0

    if nz > 0:   # Mặt trên
        w = nz * nz
        r += w * 215.0; g += w * 140.0; b += w * 72.0; total += w
    elif nz < 0: # Mặt đáy
        w = nz * nz
        r += w * 125.0; g += w * 62.0;  b += w * 28.0; total += w

    if ny > 0:   # Mặt trước
        w = ny * ny
        r += w * 168.0; g += w * 95.0;  b += w * 42.0; total += w
    elif ny < 0: # Mặt sau
        w = ny * ny
        r += w * 120.0; g += w * 60.0;  b += w * 26.0; total += w

    if nx > 0:   # Mặt phải
        w = nx * nx
        r += w * 190.0; g += w * 110.0; b += w * 52.0; total += w
    elif nx < 0: # Mặt trái
        w = nx * nx
        r += w * 105.0; g += w * 50.0;  b += w * 20.0; total += w

    if total > 1e-6:
        r /= total; g /= total; b /= total
    else:
        r, g, b = 168.0, 95.0, 42.0

    return (int(round(r)), int(round(g)), int(round(b)))


def _stone_face_color(normal: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Tính màu mặt cho cube đá xám hóa cứng (Inactive) theo hướng pháp tuyến."""
    nx, ny, nz = normal
    r, g, b, total = 0.0, 0.0, 0.0, 0.0

    if nz > 0:   # Mặt trên
        w = nz * nz
        r += w * 138.0; g += w * 148.0; b += w * 158.0; total += w
    elif nz < 0: # Mặt đáy
        w = nz * nz
        r += w * 72.0;  g += w * 78.0;  b += w * 85.0;  total += w

    if ny > 0:   # Mặt trước
        w = ny * ny
        r += w * 102.0; g += w * 112.0; b += w * 122.0; total += w
    elif ny < 0: # Mặt sau
        w = ny * ny
        r += w * 80.0;  g += w * 88.0;  b += w * 96.0;  total += w

    if nx > 0:   # Mặt phải
        w = nx * nx
        r += w * 122.0; g += w * 132.0; b += w * 142.0; total += w
    elif nx < 0: # Mặt trái
        w = nx * nx
        r += w * 68.0;  g += w * 74.0;  b += w * 80.0;  total += w

    if total > 1e-6:
        r /= total; g /= total; b /= total
    else:
        r, g, b = 102.0, 112.0, 122.0

    return (int(round(r)), int(round(g)), int(round(b)))


def _proj(p: Tuple[float, float, float], tw: int, th: int,
          off: Tuple[int, int], skew: int, cube_h: int = CUBE_HEIGHT) -> Tuple[float, float]:
    """Chiếu tọa độ không gian 3D (x, y, z) sang tọa độ màn hình isometric 2D."""
    return (off[0] + p[0] * tw + p[1] * skew,
            off[1] + p[1] * th - p[2] * cube_h)


def draw_active_indicator(surface: pygame.Surface,
                          r: int, c: int,
                          tw: int, th: int,
                          off: Tuple[int, int], skew: int,
                          now_ms: int,
                          fill_color: Optional[Tuple[int, int, int]] = None,
                          edge_color: Optional[Tuple[int, int, int]] = None,
                          shadow_color: Optional[Tuple[int, int, int]] = None) -> None:
    """Theo Phong cách 3 (Minimalist Pure): Không vẽ bất kỳ icon lơ lửng nào."""
    pass


def _draw_cube_geometry(surface: pygame.Surface,
                        verts: List[Tuple[float, float, float]],
                        rot_func,
                        is_active: bool,
                        tw: int, th: int,
                        off: Tuple[int, int], skew: int) -> None:
    """Vẽ 6 mặt của một cube 1x1x1 đã xoay/dịch với khử mặt sau và sắp xếp chiều sâu."""
    faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
    ]

    proj_verts = [_proj(v, tw, th, off, skew) for v in verts]
    v_cam = (-skew / tw, 1.0, th / CUBE_HEIGHT)

    visible_faces = []
    color_func = _wood_face_color if is_active else _stone_face_color

    for _, v_indices, n0 in faces:
        n = rot_func(n0)
        v_dot = n[0] * v_cam[0] + n[1] * v_cam[1] + n[2] * v_cam[2]
        if v_dot > 1e-4:
            center_x = sum(verts[idx][0] for idx in v_indices) / 4.0
            center_y = sum(verts[idx][1] for idx in v_indices) / 4.0
            center_z = sum(verts[idx][2] for idx in v_indices) / 4.0
            depth = center_y * th - center_z * CUBE_HEIGHT + center_x * 0.5

            col = color_func(n)
            pts = [proj_verts[idx] for idx in v_indices]
            visible_faces.append((depth, pts, col))

    visible_faces.sort(key=lambda item: item[0])
    for _, pts, col in visible_faces:
        int_pts = [(int(round(p[0])), int(round(p[1]))) for p in pts]
        _poly_aa(surface, col, int_pts)


def draw_single_cube(surface: pygame.Surface,
                     r: int, c: int,
                     is_active: bool,
                     tw: int, th: int,
                     off: Tuple[int, int], skew: int,
                     offset_xy: Tuple[float, float] = (0.0, 0.0),
                     drop_z: float = 0.0,
                     shadow: bool = True) -> None:
    """Vẽ một khối lập phương đơn 1x1x1 tại tọa độ (r, c), hỗ trợ độ cao drop_z khi rơi."""
    # 1. Bóng tiếp xúc trên sàn (tại z = 0)
    bx0, by0 = float(c) + offset_xy[0], float(r) + offset_xy[1]
    bx1, by1 = bx0 + 1.0, by0 + 1.0

    if shadow and drop_z >= -0.05:
        tl = _proj((bx0, by0, 0.0), tw, th, off, skew)
        tr = _proj((bx1, by0, 0.0), tw, th, off, skew)
        br = _proj((bx1, by1, 0.0), tw, th, off, skew)
        bl = _proj((bx0, by1, 0.0), tw, th, off, skew)

        shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s_alpha = 130 if is_active else 85
        pygame.draw.polygon(shadow_surf, (20, 35, 15, s_alpha), [tl, tr, br, bl])
        surface.blit(shadow_surf, (0, 0))

    # 2. Đỉnh 3D của cube 1x1x1
    x0, y0, z0 = bx0, by0, drop_z
    x1, y1, z1 = bx1, by1, 1.0 + drop_z
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    _draw_cube_geometry(surface, verts, lambda n: n, is_active, tw, th, off, skew)


def draw_animated_single_cube(surface: pygame.Surface,
                              r: int, c: int,
                              action: str, progress: float,
                              is_active: bool,
                              tw: int, th: int,
                              off: Tuple[int, int], skew: int) -> None:
    """Vẽ hoạt ảnh lăn 90 độ của khối lập phương đơn 1x1x1."""
    if action == 'U':
        pivot, axis, sign = (c, r), 'X', -1
    elif action == 'D':
        pivot, axis, sign = (c, r + 1), 'X', 1
    elif action == 'L':
        pivot, axis, sign = (c, r), 'Y', -1
    else:  # 'R'
        pivot, axis, sign = (c + 1, r), 'Y', 1

    angle = sign * (math.pi / 2.0) * progress

    x0, y0, z0 = float(c), float(r), 0.0
    x1, y1, z1 = x0 + 1.0, y0 + 1.0, 1.0
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    px, py = pivot
    ca, sa = math.cos(angle), math.sin(angle)

    def rot_p(p):
        vx, vy, vz = p
        if axis == 'X':
            dy, dz = vy - py, vz
            return (vx, py + dy * ca + dz * sa, -dy * sa + dz * ca)
        else:
            dx, dz = vx - px, vz
            return (px + dx * ca + dz * sa, vy, -dx * sa + dz * ca)

    def rot_v(v):
        vx, vy, vz = v
        if axis == 'X':
            return (vx, vy * ca + vz * sa, -vy * sa + vz * ca)
        else:
            return (vx * ca + vz * sa, vy, -vx * sa + vz * ca)

    rot_verts = [rot_p(v) for v in verts]

    # Bóng tiếp xúc dưới khối đang lăn
    shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    s_alpha = max(35, int(130 * (1.0 - 0.45 * math.sin(progress * math.pi))))
    bot_shadow = [
        _proj((rot_verts[i][0], rot_verts[i][1], 0.0), tw, th, off, skew)
        for i in (0, 1, 2, 3)
    ]
    pygame.draw.polygon(shadow_surf, (20, 35, 15, s_alpha), bot_shadow)
    surface.blit(shadow_surf, (0, 0))

    _draw_cube_geometry(surface, rot_verts, rot_v, is_active, tw, th, off, skew)


def draw_split_cubes(surface: pygame.Surface,
                     split: Tuple[Tuple[int, int], Tuple[int, int]],
                     tw: int, th: int,
                     off: Tuple[int, int], skew: int,
                     anim_info: Optional[Tuple[int, int, str, float]] = None,
                     merge_progress: Optional[float] = None,
                     indicator_colors: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None) -> None:
    """Vẽ cả 2 cube (active & inactive) với thứ tự chiều sâu và chỉ thị trực quan."""
    c_active, c_inactive = split
    now_ms = pygame.time.get_ticks()

    # Sắp xếp vẽ theo chiều sâu Isometric (r nhỏ vẽ trước, r lớn vẽ sau)
    # Nếu anim_info có giá trị: cube active đang lăn
    active_rolling = anim_info is not None

    # Tính độ dịch chuyển hút vào nhau (Merge Attraction Effect)
    off_act = (0.0, 0.0)
    off_inact = (0.0, 0.0)
    if merge_progress is not None:
        # Hút về tâm vách ngăn giữa 2 ô
        dr = (c_inactive[0] - c_active[0]) * 0.45 * merge_progress
        dc = (c_inactive[1] - c_active[1]) * 0.45 * merge_progress
        off_act = (dc, dr)
        off_inact = (-dc, -dr)

    # Chiều sâu hiển thị
    depth_act = c_active[0] * 1000 + c_active[1]
    depth_inact = c_inactive[0] * 1000 + c_inactive[1]

    def render_active() -> None:
        if active_rolling:
            ar, ac, aact, aprogress = anim_info
            draw_animated_single_cube(
                surface, ar, ac, aact, aprogress, True, tw, th, off, skew
            )
        else:
            draw_single_cube(
                surface, c_active[0], c_active[1], True, tw, th, off, skew, offset_xy=off_act
            )

    def render_inactive() -> None:
        draw_single_cube(
            surface, c_inactive[0], c_inactive[1], False, tw, th, off, skew, offset_xy=off_inact
        )

    if depth_act < depth_inact:
        render_active()
        render_inactive()
    else:
        render_inactive()
        render_active()
