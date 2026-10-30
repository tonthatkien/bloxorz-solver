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
    """Vẽ ô dễ vỡ bị khối nặng nứt tách thành nhiều mảnh 3D rồi sụp rơi xuống vực."""
    if vt > 0.88:
        return

    tc = (x + tw * 0.5 + skew * 0.5, y + th * 0.5)

    # 6 Mảnh vỡ đa giác 3D ghép khít ô sàn ban đầu
    cc = (0.52, 0.48)
    shards_def = [
        # (vertices in (u, v), drift_x, drift_y, rot_speed)
        ([(0.0, 0.0), (0.50, 0.0), cc, (0.0, 0.35)], -12.0,  -8.0, -1.8),  # Tây Bắc
        ([(0.50, 0.0), (1.0, 0.0), (1.0, 0.35), cc],  11.0,  -9.0,  2.1),  # Đông Bắc
        ([(1.0, 0.35), (1.0, 0.75), cc],              16.0,  -3.0, -1.5),  # Đông
        ([cc, (1.0, 0.75), (1.0, 1.0), (0.50, 1.0)],  13.0,  10.0,  1.7),  # Đông Nam
        ([cc, (0.50, 1.0), (0.0, 1.0), (0.0, 0.65)], -10.0,  12.0, -2.0),  # Tây Nam
        ([cc, (0.0, 0.65), (0.0, 0.35)],             -14.0,   3.0,  1.4),  # Tây
    ]

    # Rơi gia tốc tự do xuống hố vực cùng khối (không nổ ngược lên)
    fall_y = 660.0 * vt * vt
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

        # Mảnh vỡ hơi nghiêng và tách nhẹ sang bên khi sụp lở
        angle = rot_speed * vt
        cos_a = cos(angle)
        sin_a = sin(angle)

        off_x = dir_x * (vt * 1.1)
        off_y = fall_y + dir_y * (vt * 0.9)

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

    # Vài vụn dăm vỡ nhỏ rơi tự do cùng các tảng vỡ
    crumbs = (
        ( 0.35, -0.30,  8.0, -5.0, 2),
        (-0.30, -0.25, -7.0, -4.0, 2),
        ( 0.25,  0.35,  6.0,  5.0, 2),
        (-0.25,  0.40, -6.0,  6.0, 2),
    )
    for dx, dy, vx, vy, sz in crumbs:
        px = tc[0] + dx * tw * 0.3 + vx * vt
        py = tc[1] + dy * th * 0.3 + vy * vt + 680.0 * vt * vt
        pygame.draw.circle(shard_surf, edge_color, (int(round(px)), int(round(py))), sz)

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
