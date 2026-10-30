"""Advanced terrain and switch markers in the board's existing oblique projection."""
from dataclasses import replace
from functools import lru_cache
from math import cos, pi, sin

import pygame

from game.level_loader import Level
from gui.render_board import _draw_floor_tile, _poly_aa, _tile_quad

FRAGILE_TOP = (229, 147, 57)
FRAGILE_EDGE = (139, 78, 36)
FRAGILE_SIDE = (110, 58, 22)
BRIDGE_TOP = (177, 137, 85)
BRIDGE_EDGE = (98, 72, 47)
SOFT_TOP = (105, 210, 211)
HEAVY_INK = (255, 225, 126)
SPLIT_INK = (232, 196, 255)
MARKER_EDGE = (49, 65, 62)
DETAIL_AA_SCALE = 3
DISC_SEGMENTS = 24


def terrain_view(level: Level, bridge_mask: int) -> Level:
    """Hide closed bridges for both drawing and neighboring cliff-edge geometry.

    This is a display-only copy. The original Level and runtime State remain unchanged.
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
    # Interpolate along the two edges of render_board._tile_quad.
    tl, tr, _, bl = _tile_quad(x, y, tw, th, skew)
    return (round(tl[0] + u * (tr[0] - tl[0]) + v * (bl[0] - tl[0])),
            round(tl[1] + u * (tr[1] - tl[1]) + v * (bl[1] - tl[1])))


@lru_cache(maxsize=128)
def _stroke_image(color: tuple[int, int, int], points: tuple[tuple[int, int], ...],
                  width: int) -> pygame.Surface:
    # Cache only local geometry so moving a board does not rerasterize its details.
    padding = width + 2
    size = (max(x for x, _ in points) + 2 * padding + 1,
            max(y for _, y in points) + 2 * padding + 1)
    scale = DETAIL_AA_SCALE
    image = pygame.Surface((size[0] * scale, size[1] * scale), pygame.SRCALPHA)
    # Keep RGB constant under transparent pixels to avoid dark downsampling fringes.
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
    """Draw orange fragile terrain with a crack below any block drawn afterward."""
    _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)
    _poly_aa(surface, FRAGILE_TOP, _tile_quad(x, y, tw, th, skew), FRAGILE_EDGE)
    crack = [_point(x, y, tw, th, skew, u, v) for u, v in
             ((0.55, 0.12), (0.43, 0.40), (0.60, 0.55), (0.46, 0.85))]
    _smooth_lines(surface, FRAGILE_EDGE, crack, max(2, tw // 22))


def draw_shattering_fragile_tile(surface: pygame.Surface, x: int, y: int,
                                 tw: int, th: int, skew: int, vt: float) -> None:
    """Vẽ ô dễ vỡ nổ tung dữ dội thành các mảnh 3D xoay văng lên và rơi xuống hố vực."""
    if vt > 0.88:
        return

    tc = (x + tw * 0.5 + skew * 0.5, y + th * 0.5)

    # 1. Sóng xung kích (Shockwave ring) bùng nổ trên mặt phẳng sàn khi va chạm
    if vt < 0.32:
        st = vt / 0.32
        sw_w = max(4, int(tw * (0.35 + 1.25 * st)))
        sw_h = max(4, int(th * (0.35 + 1.25 * st)))
        sw_surf = pygame.Surface((sw_w + 4, sw_h + 4), pygame.SRCALPHA)
        sw_alpha = max(0, min(255, int(210 * (1.0 - st))))
        sw_col = (255, 220, 130, sw_alpha)
        pygame.draw.ellipse(sw_surf, sw_col, (2, 2, sw_w, sw_h), max(1, int(3 * (1.0 - st))))
        surface.blit(sw_surf, (int(round(tc[0] - sw_w * 0.5 - 2)),
                               int(round(tc[1] - sw_h * 0.5 - 2))))

    # 2. 6 Mảnh vỡ đa giác 3D (3D chunky polygonal shards) ghép khít ô sàn ban đầu
    cc = (0.52, 0.48)
    shards_def = [
        ([(0.0, 0.0), (0.50, 0.0), cc, (0.0, 0.35)], -32.0, -24.0, -4.5),  # Tây Bắc
        ([(0.50, 0.0), (1.0, 0.0), (1.0, 0.35), cc],  28.0, -26.0,  5.2),  # Đông Bắc
        ([(1.0, 0.35), (1.0, 0.75), cc],              44.0,  -8.0, -3.8),  # Đông
        ([cc, (1.0, 0.75), (1.0, 1.0), (0.50, 1.0)],  32.0,  28.0,  4.2),  # Đông Nam
        ([cc, (0.50, 1.0), (0.0, 1.0), (0.0, 0.65)], -26.0,  32.0, -5.0),  # Tây Nam
        ([cc, (0.0, 0.65), (0.0, 0.35)],             -40.0,   8.0,  3.6),  # Tây
    ]

    # Độ nảy ngược lên trên lúc chấn động (Upward burst kick) trước khi rơi tự do
    burst_up = -65.0 * sin(min(1.0, vt * 4.0) * pi)
    fall_y = 700.0 * vt * vt + burst_up
    alpha = max(0, min(255, int(255 * (1.0 - vt * 1.15))))

    shard_surf = surface
    if alpha < 250:
        shard_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    top_color = (*FRAGILE_TOP, alpha) if alpha < 250 else FRAGILE_TOP
    edge_color = (*FRAGILE_EDGE, alpha) if alpha < 250 else FRAGILE_EDGE
    side_color = (*FRAGILE_SIDE, alpha) if alpha < 250 else FRAGILE_SIDE
    chunk_depth = max(2, int(8 * (1.0 - vt * 0.8)))

    for uv_pts, dir_x, dir_y, rot_speed in shards_def:
        pts = [_point(x, y, tw, th, skew, u, v) for u, v in uv_pts]
        n_pts = len(pts)
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)

        angle = rot_speed * vt
        cos_a = cos(angle)
        sin_a = sin(angle)

        off_x = dir_x * (vt * 2.8)
        off_y = fall_y + dir_y * (vt * 2.2)

        rot_pts = []
        for px, py in pts:
            rx = cx + (px - cx) * cos_a - (py - cy) * sin_a + off_x
            ry = cy + (px - cx) * sin_a + (py - cy) * cos_a + off_y
            rot_pts.append((int(round(rx)), int(round(ry))))

        # Vẽ các mặt bên 3D (3D side faces) hướng về phía camera
        for i in range(n_pts):
            p1 = rot_pts[i]
            p2 = rot_pts[(i + 1) % n_pts]
            if p2[0] - p1[0] > 0:
                side_quad = [p1, p2, (p2[0], p2[1] + chunk_depth), (p1[0], p1[1] + chunk_depth)]
                _poly_aa(shard_surf, side_color, side_quad, edge_color=edge_color)

        _poly_aa(shard_surf, top_color, rot_pts, edge_color=edge_color)

    # 3. Mảnh vụn và tia lửa (Sparks & Debris chips) bắn nhanh ra ngoại vi
    debris_data = (
        ( 0.85, -0.65,  60.0, -45.0, (255, 215, 110), 3),
        (-0.75, -0.55, -55.0, -38.0, (255, 185,  60), 2),
        ( 0.45, -0.90,  42.0, -55.0, (245, 165,  50), 3),
        (-0.35, -0.85, -45.0, -50.0, (255, 230, 130), 2),
        ( 0.95,  0.15,  75.0, -18.0, (235, 145,  40), 2),
        (-0.95,  0.20, -70.0, -12.0, (205, 105,  30), 3),
        ( 0.70,  0.70,  55.0,  30.0, (255, 195,  75), 2),
        (-0.65,  0.75, -50.0,  35.0, (245, 155,  48), 3),
        ( 0.20,  0.95,  32.0,  50.0, (185,  88,  25), 3),
        (-0.15,  0.90, -30.0,  45.0, (255, 205,  85), 2),
        ( 0.55, -0.30,  78.0, -25.0, (255, 235, 140), 2),
        (-0.50, -0.35, -75.0, -28.0, (225, 135,  42), 3),
        ( 0.35,  0.45,  58.0,  18.0, (255, 180,  58), 2),
        (-0.40,  0.50, -52.0,  22.0, (195,  98,  32), 3),
        ( 0.10, -0.60,  45.0, -42.0, (255, 245, 160), 1),
        (-0.80, -0.10, -65.0, -18.0, (215, 118,  36), 2),
    )
    p_alpha = max(0, min(255, int(255 * (1.0 - vt * 1.15))))
    for dx, dy, vx, vy, base_col, size in debris_data:
        px = tc[0] + dx * tw * 0.35 + vx * vt * 1.5
        py = tc[1] + dy * th * 0.35 + vy * vt * 1.5 + 680.0 * vt * vt
        sz = max(1, int(size * (1.0 - vt * 0.85)))
        col = (*base_col, p_alpha) if p_alpha < 250 else base_col
        pygame.draw.circle(shard_surf, col, (int(round(px)), int(round(py))), sz)

    if alpha < 250:
        surface.blit(shard_surf, (0, 0))



def draw_bridge_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                     x: int, y: int, tw: int, th: int, skew: int,
                     opened: bool = True) -> None:
    """Draw a plank surface for an open bridge; a closed bridge contributes no floor."""
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
    # Premultiply mixed fill/edge colors before filtering transparent boundaries.
    return pygame.transform.smoothscale(image.premul_alpha(), size)


def _disc(surface: pygame.Surface, color: tuple[int, int, int],
          x: int, y: int, tw: int, th: int, skew: int) -> None:
    surface.blit(_disc_image(color, tw, th, skew), (x + min(0, skew) - 2, y - 2),
                 special_flags=pygame.BLEND_PREMULTIPLIED)


def draw_soft_switch(surface: pygame.Surface, x: int, y: int,
                     tw: int, th: int, skew: int) -> None:
    """Draw the soft switch as a cyan rounded pressure plate."""
    _disc(surface, SOFT_TOP, x, y, tw, th, skew)


def draw_heavy_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Draw a contrasting X for the heavy switch without evaluating activation."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for start, end in (((0.31, 0.27), (0.69, 0.73)),
                       ((0.31, 0.73), (0.69, 0.27))):
        _smooth_lines(surface, HEAVY_INK,
                      [_point(x, y, tw, th, skew, *start),
                       _point(x, y, tw, th, skew, *end)], max(1, tw // 17))


def draw_split_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Draw paired purple brackets for the split switch; no cube logic lives here."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for mirror in (False, True):
        points = [_point(x, y, tw, th, skew, 1 - u if mirror else u, v)
                  for u, v in ((0.40, 0.27), (0.32, 0.37), (0.29, 0.50),
                               (0.32, 0.63), (0.40, 0.73))]
        _smooth_lines(surface, SPLIT_INK, points, max(1, tw // 25))


def draw_switch(surface: pygame.Surface, kind: str, x: int, y: int,
                tw: int, th: int, skew: int) -> None:
    """Draw the marker belonging to a validated switch type."""
    drawers = {"soft": draw_soft_switch, "heavy": draw_heavy_switch,
               "split": draw_split_switch}
    drawers[kind](surface, x, y, tw, th, skew)
