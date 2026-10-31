"""Vẽ các ô địa hình đặc biệt (dễ vỡ, cầu nối) và các nút công tắc trên sàn Bloxorz."""
from dataclasses import replace
from functools import lru_cache
from math import cos, pi, sin

import pygame

from game.level_loader import Level
from gui.render_board import _draw_floor_tile, _poly_aa, _tile_quad

FRAGILE_TOP = (229, 147, 57)
FRAGILE_EDGE = (139, 78, 36)
SOIL_FRONT = (128, 92, 62)
SOIL_LEFT = (105, 72, 48)
SOIL_DARK = (82, 54, 34)
BRIDGE_TOP = (177, 137, 85)
BRIDGE_EDGE = (98, 72, 47)
SOFT_TOP = (105, 210, 211)
HEAVY_INK = (255, 225, 126)
SPLIT_INK = (232, 196, 255)
MARKER_EDGE = (49, 65, 62)
DETAIL_AA_SCALE = 3
DISC_SEGMENTS = 24


def terrain_view(level: Level, bridge_mask: int) -> Level:
    """Ẩn các cầu đang đóng khi vẽ địa hình và dựng hình học vách đá lân cận.
    """
    closed = [bridge.pos for bridge in level.bridges.values()
              if not bridge_mask & (1 << bridge.id)]
    if not closed:
        return level
    rows = [list(row) for row in level.grid]
    for r, c in closed:
        rows[r][c] = "."
    return replace(level, grid=["".join(row) for row in rows])


def _point(x: int, y: int, tw: int, th: int, skew: int,
           u: float, v: float) -> tuple[int, int]:
    # Nội suy tọa độ theo hai cạnh của tứ giác ô sàn (_tile_quad).
    tl, tr, _, bl = _tile_quad(x, y, tw, th, skew)
    return (round(tl[0] + u * (tr[0] - tl[0]) + v * (bl[0] - tl[0])),
            round(tl[1] + u * (tr[1] - tl[1]) + v * (bl[1] - tl[1])))


@lru_cache(maxsize=128)
def _stroke_image(color: tuple[int, int, int], points: tuple[tuple[int, int], ...],
                  width: int) -> pygame.Surface:
    # Chỉ lưu cache hình học cục bộ để khi di chuyển bàn cờ không cần rasterize lại.
    padding = width + 2
    size = (max(x for x, _ in points) + 2 * padding + 1,
            max(y for _, y in points) + 2 * padding + 1)
    scale = DETAIL_AA_SCALE
    image = pygame.Surface((size[0] * scale, size[1] * scale), pygame.SRCALPHA)
    # Giữ nguyên giá trị RGB cho các pixel trong suốt để tránh viền đen khi downsampling.
    image.fill((*color, 0))
    scaled = [((x + padding) * scale, (y + padding) * scale) for x, y in points]
    pygame.draw.lines(image, color, False, scaled, width * scale)
    return pygame.transform.smoothscale(image, size)


def _smooth_lines(surface: pygame.Surface, color: tuple[int, int, int],
                  points: list[tuple[int, int]], width: int = 1) -> None:
    origin_x = min(x for x, _ in points)
    origin_y = min(y for _, y in points)
    local = tuple((x - origin_x, y - origin_y) for x, y in points)
    padding = width + 2
    surface.blit(_stroke_image(color, local, width),
                 (origin_x - padding, origin_y - padding))


def draw_fragile_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                      x: int, y: int, tw: int, th: int, skew: int) -> None:
    """Vẽ ô sàn đất cam dễ vỡ kèm vết nứt bên dưới khối gạch."""
    _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)
    _poly_aa(surface, FRAGILE_TOP, _tile_quad(x, y, tw, th, skew), FRAGILE_EDGE)
    crack = [_point(x, y, tw, th, skew, u, v) for u, v in
             ((0.55, 0.12), (0.43, 0.40), (0.60, 0.55), (0.46, 0.85))]
    _smooth_lines(surface, FRAGILE_EDGE, crack, max(2, tw // 22))


def draw_shattering_fragile_tile(surface: pygame.Surface, x: int, y: int,
                                 tw: int, th: int, skew: int, vt: float) -> None:
    """Vẽ ô đất dễ vỡ nứt thành các tảng đất 3D và vụn đất sụp rơi xuống vực."""
    if vt > 0.88:
        return

    # 5 Tảng đất 3D (chunky earth blocks) ghép kín khít ô sàn ban đầu
    chunks_def = [
        # (uv_polygon, drift_x, drift_y, rot_speed, is_center)
        ([(0.0, 0.0), (0.55, 0.0), (0.48, 0.38), (0.0, 0.45)],
         -8.0, -6.0, -1.2, False),  # Tảng Tây Bắc
        ([(0.55, 0.0), (1.0, 0.0), (1.0, 0.42), (0.58, 0.46), (0.48, 0.38)],
          9.0, -7.0,  1.1, False),  # Tảng Đông Bắc
        ([(1.0, 0.42), (1.0, 1.0), (0.46, 1.0), (0.44, 0.62), (0.58, 0.46)],
         10.0,  8.0,  1.3, False),  # Tảng Đông Nam
        ([(0.0, 0.45), (0.36, 0.48), (0.44, 0.62), (0.46, 1.0), (0.0, 1.0)],
         -9.0,  9.0, -1.0, False),  # Tảng Tây Nam
        ([(0.48, 0.38), (0.58, 0.46), (0.44, 0.62), (0.36, 0.48)],
          0.0,  0.0,  0.6, True),   # Khối tâm chấn cúp sụp đầu tiên
    ]

    alpha = max(0, min(255, int(255 * (1.0 - vt * 1.15))))
    shard_surf = surface
    if alpha < 250:
        shard_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    top_col = (*FRAGILE_TOP, alpha) if alpha < 250 else FRAGILE_TOP
    edge_col = (*FRAGILE_EDGE, alpha) if alpha < 250 else FRAGILE_EDGE
    soil_f_col = (*SOIL_FRONT, alpha) if alpha < 250 else SOIL_FRONT
    soil_l_col = (*SOIL_LEFT, alpha) if alpha < 250 else SOIL_LEFT
    soil_d_col = (*SOIL_DARK, alpha) if alpha < 250 else SOIL_DARK

    # Độ dày tầng đất thực tế
    soil_depth = max(4, int(16 * (1.0 - vt * 0.5)))

    rendered_chunks = []
    for uv_pts, dir_x, dir_y, rot_speed, is_center in chunks_def:
        pts = [_point(x, y, tw, th, skew, u, v) for u, v in uv_pts]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)

        # Trọng lực kéo sụp: tảng tâm chấn sụp nhanh hơn các tảng rìa
        gravity = 710.0 if is_center else 640.0
        fall_y = gravity * vt * vt

        angle = rot_speed * vt
        cos_a = cos(angle)
        sin_a = sin(angle)

        off_x = dir_x * (vt * 1.1)
        off_y = fall_y + dir_y * (vt * 0.9)

        rot_top = []
        for px, py in pts:
            rx = cx + (px - cx) * cos_a - (py - cy) * sin_a + off_x
            ry = cy + (px - cx) * sin_a + (py - cy) * cos_a + off_y
            rot_top.append((int(round(rx)), int(round(ry))))

        rendered_chunks.append((cy + off_y, rot_top))

    # Sắp xếp vẽ từ sau ra trước (Painter's Algorithm theo trục Y)
    rendered_chunks.sort(key=lambda item: item[0])

    for _, rot_top in rendered_chunks:
        n_pts = len(rot_top)
        # 1. Vẽ các vách đất bên 3D (3D soil walls) lộ ra khi tảng đất bị nứt tách
        for i in range(n_pts):
            p1 = rot_top[i]
            p2 = rot_top[(i + 1) % n_pts]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            vis = -dx - 0.35 * dy
            if vis > 0:  # Cạnh hướng về phía camera
                wall_quad = [p1, p2, (p2[0], p2[1] + soil_depth), (p1[0], p1[1] + soil_depth)]
                wall_col = soil_f_col if abs(dx) >= abs(dy) else soil_l_col
                _poly_aa(shard_surf, wall_col, wall_quad, edge_color=wall_col)
                pygame.draw.line(shard_surf, soil_d_col,
                                 (p1[0], p1[1] + soil_depth),
                                 (p2[0], p2[1] + soil_depth), 1)

        # 2. Vẽ mặt trên thảm đất nứt (Fragile clay top surface)
        _poly_aa(shard_surf, top_col, rot_top, edge_color=edge_col)

    # 3. Các cục đất vụn dạng khối 3D (Chunky 3D soil clods) rơi theo trọng lực
    soil_crumbs = (
        ( 0.35, -0.28,  6.0, -4.0, 5, 4),
        (-0.28, -0.32, -5.0, -3.0, 4, 3),
        ( 0.22,  0.36,  5.0,  4.0, 5, 5),
        (-0.32,  0.28, -6.0,  5.0, 4, 4),
        ( 0.05,  0.15,  3.0,  2.0, 6, 5),
        (-0.10, -0.10, -3.0, -2.0, 5, 4),
        ( 0.42,  0.18,  7.0,  3.0, 4, 4),
        (-0.38, -0.05, -7.0,  1.0, 5, 4),
    )
    for cu, cv, vx, vy, cw, ch in soil_crumbs:
        crumb_center = _point(x, y, tw, th, skew, 0.5 + cu, 0.5 + cv)
        px = int(round(crumb_center[0] + vx * vt))
        py = int(round(crumb_center[1] + vy * vt + 670.0 * vt * vt))
        cd = max(2, ch - 1)
        pygame.draw.rect(shard_surf, soil_f_col, (px, py, cw, cd))
        pygame.draw.rect(shard_surf, top_col, (px, py - cd // 2, cw, cd // 2 + 1))

    if alpha < 250:
        surface.blit(shard_surf, (0, 0))


def draw_bridge_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                     x: int, y: int, tw: int, th: int, skew: int,
                     opened: bool = True) -> None:
    """Vẽ bề mặt ván gỗ cho cầu đang mở; cầu đang đóng sẽ không tạo mặt sàn."""
    if not opened:
        return
    _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)
    _poly_aa(surface, BRIDGE_TOP, _tile_quad(x, y, tw, th, skew), BRIDGE_EDGE)
    for v in (0.2, 0.4, 0.6, 0.8):
        _smooth_lines(surface, BRIDGE_EDGE,
                      [_point(x, y, tw, th, skew, 0.04, v),
                       _point(x, y, tw, th, skew, 0.96, v)])


@lru_cache(maxsize=128)
def _disc_image(color: tuple[int, int, int], tw: int, th: int,
                skew: int) -> pygame.Surface:
    scale = DETAIL_AA_SCALE
    padding = 2
    size = (tw + abs(skew) + 2 * padding, th + 2 * padding)
    image = pygame.Surface((size[0] * scale, size[1] * scale), pygame.SRCALPHA)
    points = [_point((padding - min(0, skew)) * scale, padding * scale,
                     tw * scale, th * scale, skew * scale,
                     0.5 + 0.30 * cos(i * 2 * pi / DISC_SEGMENTS),
                     0.5 + 0.34 * sin(i * 2 * pi / DISC_SEGMENTS))
              for i in range(DISC_SEGMENTS)]
    _poly_aa(image, color, points, MARKER_EDGE)
    # Nhân trước kênh alpha (premultiply) để làm mượt biên trong suốt khi downscale.
    return pygame.transform.smoothscale(image.premul_alpha(), size)


def _disc(surface: pygame.Surface, color: tuple[int, int, int],
          x: int, y: int, tw: int, th: int, skew: int) -> None:
    surface.blit(_disc_image(color, tw, th, skew), (x + min(0, skew) - 2, y - 2),
                 special_flags=pygame.BLEND_PREMULTIPLIED)


def draw_soft_switch(surface: pygame.Surface, x: int, y: int,
                     tw: int, th: int, skew: int) -> None:
    """Vẽ công tắc nhẹ (soft switch) dạng đĩa tròn màu lục lam."""
    _disc(surface, SOFT_TOP, x, y, tw, th, skew)


def draw_heavy_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Vẽ công tắc nặng (heavy switch) có dấu chữ X màu vàng."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for start, end in (((0.31, 0.27), (0.69, 0.73)),
                       ((0.31, 0.73), (0.69, 0.27))):
        _smooth_lines(surface, HEAVY_INK,
                      [_point(x, y, tw, th, skew, *start),
                       _point(x, y, tw, th, skew, *end)], max(1, tw // 17))


def draw_split_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Vẽ công tắc phân tách (split switch) với hai dấu ngoặc màu tím đối xứng."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for mirror in (False, True):
        points = [_point(x, y, tw, th, skew, 1 - u if mirror else u, v)
                  for u, v in ((0.40, 0.27), (0.32, 0.37), (0.29, 0.50),
                               (0.32, 0.63), (0.40, 0.73))]
        _smooth_lines(surface, SPLIT_INK, points, max(1, tw // 25))


def draw_switch(surface: pygame.Surface, kind: str, x: int, y: int,
                tw: int, th: int, skew: int) -> None:
    """Vẽ ký hiệu công tắc tương ứng theo loại (soft, heavy, split)."""
    drawers = {"soft": draw_soft_switch, "heavy": draw_heavy_switch,
               "split": draw_split_switch}
    drawers[kind](surface, x, y, tw, th, skew)
