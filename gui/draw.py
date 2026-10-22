import math
import random
from typing import List, Optional, Tuple

import pygame
import pygame.gfxdraw

from game.level_loader import Level
from game.state import State, STAND, HORIZ, VERT, cells

C = {
    # Thảm cỏ
    'grass_light':   (142, 198,  92),
    'grass_dark':    (124, 182,  76),
    'grass_line':    ( 98, 150,  54),

    # Vách mép sàn
    'soil_front':    (130,  92,  64),
    'soil_left':     (105,  72,  48),
    'grass_rim_f':   (115, 170,  70),
    'grass_rim_l':   ( 95, 145,  55),

    # Hố
    'chasm_sky':     ( 95, 158, 225),
    'chasm_cloud':   (240, 248, 255),
    'chasm_wall_b':  ( 88,  58,  38),
    'chasm_wall_l':  ( 68,  42,  26),
    'chasm_shadow':  ( 20,  30,  45, 110),

    # Khối Gỗ
    'wood_top':      (196, 115,  60),
    'wood_front':    (150,  78,  35),
    'wood_left':     ( 92,  42,  16),
    'wood_highlight':(225, 148,  95),
    'wood_crease':   ( 58,  24,   8),

    # Bóng đổ
    'shadow_core':   ( 25,  45,  20, 140),
    'shadow_soft':   ( 35,  65,  30,  70),
}

TILE_DEPTH: int = 14   # Độ dày tầng đất

# Đám mây
CLOUDS_DATA = [
    (180,   90, 220, 56, 0.88),
    (980,   85, 250, 62, 0.85),
    (100,  360, 210, 52, 0.80),
    (1160, 350, 230, 56, 0.80),
    (260,  640, 260, 65, 0.80),
    (960,  630, 280, 70, 0.85),
]


def _make_cloud_stamp(cw: int, ch: int) -> pygame.Surface:
    scale = 4
    sw = (cw + 40) * scale
    sh = (ch + 35) * scale
    c_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    scx = sw // 2
    scy = int(sh * 0.62)
    scw = cw * scale
    sch = ch * scale
    shw = scw // 2
    shh = sch // 2

    pygame.draw.ellipse(c_surf, (245, 250, 255, 255), (scx - shw, scy - shh, scw, sch))
    pygame.draw.ellipse(c_surf, (255, 255, 255, 255),
                        (scx - int(scw * 0.28), scy - int(shh * 1.45), int(scw * 0.48), int(sch * 1.15)))
    pygame.draw.ellipse(c_surf, (255, 255, 255, 255),
                        (scx + int(scw * 0.05), scy - int(shh * 1.25), int(scw * 0.38), int(sch * 1.00)))
    pygame.draw.ellipse(c_surf, (248, 252, 255, 255),
                        (scx - int(shw * 0.85), scy - int(shh * 1.10), int(scw * 0.32), int(sch * 0.80)))
    pygame.draw.ellipse(c_surf, (248, 252, 255, 255),
                        (scx + int(shw * 0.45), scy - int(shh * 1.05), int(scw * 0.35), int(sch * 0.78)))

    return pygame.transform.smoothscale(c_surf, (sw // scale, sh // scale))


_cached_sky: Optional[Tuple[int, int, pygame.Surface]] = None


def _render_sky_surface(win_w: int, win_h: int) -> pygame.Surface:
    surf = pygame.Surface((win_w, win_h))
    top_color = (68, 138, 212)
    bot_color = (135, 192, 242)

    for y in range(0, win_h, 2):
        t = y / win_h
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * t)
        pygame.draw.rect(surf, (r, g, b), (0, y, win_w, 2))

    scale_x = win_w / 1280.0
    scale_y = win_h / 720.0

    for cx, cy, cw, ch, alpha_s in CLOUDS_DATA:
        actual_cx = int(cx * scale_x)
        actual_cy = int(cy * scale_y)
        actual_cw = max(20, int(cw * min(scale_x, scale_y)))
        actual_ch = max(10, int(ch * min(scale_x, scale_y)))

        stamp = _make_cloud_stamp(actual_cw, actual_ch)
        stamp.set_alpha(int(230 * alpha_s))
        sx = actual_cx - stamp.get_width() // 2
        sy = actual_cy - int(stamp.get_height() * 0.62)
        surf.blit(stamp, (sx, sy))

    return surf


def draw_sky_with_clouds(surface: pygame.Surface, win_w: int, win_h: int) -> None:
    global _cached_sky
    if _cached_sky is None or _cached_sky[0] != win_w or _cached_sky[1] != win_h:
        _cached_sky = (win_w, win_h, _render_sky_surface(win_w, win_h))
    surface.blit(_cached_sky[2], (0, 0))


def _poly_aa(surface: pygame.Surface, color, points: List[Tuple[int, int]], edge_color=None) -> None:
    pygame.gfxdraw.filled_polygon(surface, points, color)
    ec = edge_color if edge_color else color
    pygame.gfxdraw.aapolygon(surface, points, ec)


def grid_to_iso(r: int, c: int, tw: int, th: int,
                off: Tuple[int, int], skew: int) -> Tuple[int, int]:
    return off[0] + c * tw + r * skew, off[1] + r * th


def calculate_iso_layout(rows: int, cols: int,
                         win_w: int, win_h: int,
                         margin: int = 70,
                         ) -> Tuple[int, int, Tuple[int, int], int]:
    tw = 68
    th = 38
    skew = 22

    map_w = cols * tw + rows * skew
    map_h = rows * th + 130

    scale = min(1.0, (win_w - 2 * margin) / map_w, (win_h - 2 * margin) / map_h)
    if scale < 1.0:
        tw = int(tw * scale)
        th = int(th * scale)
        skew = int(skew * scale)
        map_w = cols * tw + rows * skew
        map_h = rows * th + int(130 * scale)

    off_x = (win_w - map_w) // 2
    off_y = (win_h - map_h) // 2 + 80
    return tw, th, (off_x, off_y), skew


def _tile_quad(x: int, y: int, tw: int, th: int, skew: int) -> List[Tuple[int, int]]:
    return [
        (x,              y),
        (x + tw,         y),
        (x + tw + skew,  y + th),
        (x + skew,       y + th),
    ]


def _draw_floor_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                     x: int, y: int, tw: int, th: int, skew: int) -> None:
    quad = _tile_quad(x, y, tw, th, skew)
    tl, tr, br, bl = quad
    d = TILE_DEPTH

    # Vách mép vực trước
    if r + 1 >= level.rows or level.grid[r + 1][c] == '.':
        front_face = [bl, br, (br[0], br[1] + d), (bl[0], bl[1] + d)]
        _poly_aa(surface, C['soil_front'], front_face)
        grass_rim = [bl, br, (br[0], br[1] + 3), (bl[0], bl[1] + 3)]
        _poly_aa(surface, C['grass_rim_f'], grass_rim)

    # Vách mép vực trái
    if c - 1 < 0 or level.grid[r][c - 1] == '.':
        left_face = [tl, bl, (bl[0], bl[1] + d), (tl[0], tl[1] + d)]
        _poly_aa(surface, C['soil_left'], left_face)
        grass_rim_l = [tl, bl, (bl[0], bl[1] + 3), (tl[0], tl[1] + 3)]
        _poly_aa(surface, C['grass_rim_l'], grass_rim_l)

    # Mặt trên thảm cỏ
    top_c = C['grass_light'] if (r + c) % 2 == 0 else C['grass_dark']
    line_c = C['grass_line']

    _poly_aa(surface, top_c, quad, line_c)


def _draw_goal_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                    x: int, y: int, tw: int, th: int, skew: int) -> None:
    """Vẽ hố đích"""
    quad = _tile_quad(x, y, tw, th, skew)
    tl, tr, br, bl = quad
    d = TILE_DEPTH

    # Mép vực ngoài nếu hố nằm ở rìa ngoài cùng
    if r + 1 >= level.rows or level.grid[r + 1][c] == '.':
        _poly_aa(surface, C['soil_front'], [bl, br, (br[0], br[1] + d), (bl[0], bl[1] + d)])
    if c - 1 < 0 or level.grid[r][c - 1] == '.':
        _poly_aa(surface, C['soil_left'], [tl, bl, (bl[0], bl[1] + d), (tl[0], tl[1] + d)])

    # Độ dời cạnh xiên theo độ sâu d = 14px
    t = d / float(th)
    dx = t * skew

    # 4 điểm của đáy lỗ thủng hình bình hành (Aperture):
    p1 = (int(tl[0] + dx), tl[1] + d)
    p2 = (tr[0], tr[1] + d)
    p3 = (int(br[0] - dx), br[1])
    p4 = bl

    # 1. Đáy lỗ nhìn xuyên thấu xuống nền dưới
    sky_under = (118, 180, 238)
    _poly_aa(surface, sky_under, [p1, p2, p3, p4])

    # 2. Vách đất phía sau (Back Earth Wall): tl -> tr -> p2 -> p1
    _poly_aa(surface, (108, 76, 52), [tl, tr, p2, p1])

    # 3. Vách đất bên phải (Right Earth Wall): tr -> br -> p3 -> p2
    _poly_aa(surface, (125, 88, 60), [tr, br, p3, p2])

    # 4. Góc giao nhau giữa 2 vách có bóng đổ
    corner_shadow = [tr, p2, (p2[0] - 4, p2[1]), (tr[0] - 4, tr[1])]
    _poly_aa(surface, (70, 45, 28), corner_shadow)

    # 5. Viền miệng hố
    pygame.gfxdraw.polygon(surface, quad, C['grass_line'])
    pygame.gfxdraw.aapolygon(surface, quad, C['grass_line'])


def _face_color(normal: Tuple[float, float, float]) -> Tuple[int, int, int]:
    nx, ny, nz = normal
    r, g, b, total = 0.0, 0.0, 0.0, 0.0

    if nz > 0:
        w = nz * nz
        r += w * 196.0; g += w * 115.0; b += w * 60.0; total += w
    elif nz < 0:
        w = nz * nz
        r += w * 125.0; g += w * 62.0;  b += w * 28.0; total += w

    if ny > 0:
        w = ny * ny
        r += w * 150.0; g += w * 78.0;  b += w * 35.0; total += w
    elif ny < 0:
        w = ny * ny
        r += w * 115.0; g += w * 55.0;  b += w * 24.0; total += w

    if nx > 0:
        w = nx * nx
        r += w * 175.0; g += w * 96.0;  b += w * 46.0; total += w
    elif nx < 0:
        w = nx * nx
        r += w * 92.0;  g += w * 42.0;  b += w * 16.0; total += w

    if total > 1e-6:
        r /= total; g /= total; b /= total
    else:
        r, g, b = 150.0, 78.0, 35.0

    return (int(round(r)), int(round(g)), int(round(b)))


def draw_animated_block(surface: pygame.Surface,
                        r: int, c: int, orient: int,
                        action: str, progress: float,
                        tw: int, th: int,
                        off: Tuple[int, int], skew: int) -> None:
    cube_h = 60

    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1

    if action == 'U':
        pivot, axis, sign = (c, r), 'X', -1
    elif action == 'D':
        pivot, axis, sign = (c, r + ly), 'X', 1
    elif action == 'L':
        pivot, axis, sign = (c, r), 'Y', -1
    else:  # 'R'
        pivot, axis, sign = (c + lx, r), 'Y', 1

    angle = sign * (math.pi / 2.0) * progress

    x0, y0, z0 = float(c), float(r), 0.0
    x1, y1, z1 = x0 + lx, y0 + ly, float(lz)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
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

    def proj(p):
        return (off[0] + p[0] * tw + p[1] * skew,
                off[1] + p[1] * th - p[2] * cube_h)

    proj_verts = [proj(v) for v in rot_verts]

    # Bóng tiếp xúc dưới khối
    shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    s_alpha = max(35, int(130 * (1.0 - 0.45 * math.sin(progress * math.pi))))
    bot_shadow = [
        (int(off[0] + v[0] * tw + v[1] * skew),
         int(off[1] + v[1] * th))
        for v in (rot_verts[0], rot_verts[1], rot_verts[2], rot_verts[3])
    ]
    pygame.draw.polygon(shadow_surf, (25, 45, 20, s_alpha // 2), [(p[0] + 4, p[1] + 3) for p in bot_shadow])
    pygame.draw.polygon(shadow_surf, (20, 35, 15, s_alpha), bot_shadow)
    surface.blit(shadow_surf, (0, 0))

    # Loại bỏ mặt sau và sắp xếp theo chiều sâu
    v_cam = (-skew / tw, 1.0, th / cube_h)

    visible_faces = []
    for fname, v_indices, n0 in faces:
        n = rot_v(n0)
        v_dot = n[0] * v_cam[0] + n[1] * v_cam[1] + n[2] * v_cam[2]
        if v_dot > 1e-4:
            center_x = sum(rot_verts[idx][0] for idx in v_indices) / 4.0
            center_y = sum(rot_verts[idx][1] for idx in v_indices) / 4.0
            center_z = sum(rot_verts[idx][2] for idx in v_indices) / 4.0
            depth = center_y * th - center_z * cube_h + center_x * 0.5

            col = _face_color(n)
            pts = [proj_verts[idx] for idx in v_indices]
            visible_faces.append((depth, fname, pts, col))

    visible_faces.sort(key=lambda item: item[0])
    for _, fname, pts, col in visible_faces:
        int_pts = [(int(round(p[0])), int(round(p[1]))) for p in pts]
        _poly_aa(surface, col, int_pts)


def draw_goal_dissolve_block(surface: pygame.Surface,
                              r: int, c: int, orient: int,
                              alpha: int,
                              tw: int, th: int,
                              off: Tuple[int, int], skew: int) -> None:
    """Vẽ khối đứng trên ô Goal"""
    cube_h = 60
    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1

    x0, y0, z0 = float(c), float(r), 0.0
    x1, y1, z1 = x0 + lx, y0 + ly, float(lz)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
    ]

    def proj(p):
        return (off[0] + p[0] * tw + p[1] * skew,
                off[1] + p[1] * th - p[2] * cube_h)

    proj_verts = [proj(v) for v in verts]
    v_cam = (-skew / tw, 1.0, th / cube_h)

    target_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    visible_faces = []
    for fname, v_indices, n0 in faces:
        v_dot = n0[0] * v_cam[0] + n0[1] * v_cam[1] + n0[2] * v_cam[2]
        if v_dot > 1e-4:
            center_x = sum(verts[idx][0] for idx in v_indices) / 4.0
            center_y = sum(verts[idx][1] for idx in v_indices) / 4.0
            center_z = sum(verts[idx][2] for idx in v_indices) / 4.0
            depth = center_y * th - center_z * cube_h + center_x * 0.5

            col = _face_color(n0)
            pts = [proj_verts[idx] for idx in v_indices]
            visible_faces.append((depth, pts, col))

    visible_faces.sort(key=lambda item: item[0])
    for _, pts, col in visible_faces:
        int_pts = [(int(round(p[0])), int(round(p[1]))) for p in pts]
        _poly_aa(target_surf, col, int_pts)

    target_surf.set_alpha(max(0, min(255, alpha)))
    surface.blit(target_surf, (0, 0))


def draw_spawn_block(surface: pygame.Surface,
                     r: int, c: int, orient: int,
                     z_elev: float,
                     tw: int, th: int,
                     off: Tuple[int, int], skew: int) -> None:
    """Vẽ khối gỗ khi rơi từ trên trời xuống sàn (Spawn Drop) với bóng sàn động."""
    cube_h = 60
    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1

    # 1. Bóng tiếp xúc trên sàn (tại z = 0)
    # Khi z_elev cao, bóng mờ và loang rộng; khi sát đất, bóng đậm và khít đáy khối
    s_alpha = max(20, int(135.0 / (1.0 + 0.45 * max(0.0, z_elev))))
    expand = min(14.0, max(0.0, z_elev * 1.5))

    bx0, by0 = float(c), float(r)
    bx1, by1 = bx0 + lx, by0 + ly
    tl = (off[0] + bx0 * tw + by0 * skew - expand, off[1] + by0 * th - expand * 0.4)
    tr = (off[0] + bx1 * tw + by0 * skew + expand, off[1] + by0 * th - expand * 0.4)
    br = (off[0] + bx1 * tw + by1 * skew + expand, off[1] + by1 * th + expand * 0.4)
    bl = (off[0] + bx0 * tw + by1 * skew - expand, off[1] + by1 * th + expand * 0.4)

    shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(shadow_surf, (20, 35, 15, s_alpha), [tl, tr, br, bl])
    surface.blit(shadow_surf, (0, 0))

    # 2. Khối gỗ 3D tại độ cao z_elev
    x0, y0, z0 = float(c), float(r), float(z_elev)
    x1, y1, z1 = x0 + lx, y0 + ly, float(z_elev + lz)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
    ]

    def proj(p):
        return (off[0] + p[0] * tw + p[1] * skew,
                off[1] + p[1] * th - p[2] * cube_h)

    proj_verts = [proj(v) for v in verts]
    v_cam = (-skew / tw, 1.0, th / cube_h)

    visible_faces = []
    for fname, v_indices, n0 in faces:
        v_dot = n0[0] * v_cam[0] + n0[1] * v_cam[1] + n0[2] * v_cam[2]
        if v_dot > 1e-4:
            center_x = sum(verts[idx][0] for idx in v_indices) / 4.0
            center_y = sum(verts[idx][1] for idx in v_indices) / 4.0
            center_z = sum(verts[idx][2] for idx in v_indices) / 4.0
            depth = center_y * th - center_z * cube_h + center_x * 0.5

            col = _face_color(n0)
            pts = [proj_verts[idx] for idx in v_indices]
            visible_faces.append((depth, pts, col))

    visible_faces.sort(key=lambda item: item[0])
    for _, pts, col in visible_faces:
        int_pts = [(int(round(p[0])), int(round(p[1]))) for p in pts]
        _poly_aa(surface, col, int_pts)


def draw_void_fall_block(surface: pygame.Surface,
                         r: int, c: int, orient: int,
                         action: str,
                         angle: float,
                         dz: float,
                         dr: float, dc: float,
                         tw: int, th: int,
                         off: Tuple[int, int], skew: int,
                         scale: float = 1.0,
                         alpha: int = 255) -> None:
    """Vẽ khối khi rơi tự do"""
    if alpha <= 0:
        return

    cube_h = 60

    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1

    if action == 'U':
        pivot, axis = (c, r), 'X'
    elif action == 'D':
        pivot, axis = (c, r + ly), 'X'
    elif action == 'L':
        pivot, axis = (c, r), 'Y'
    else:  # 'R'
        pivot, axis = (c + lx, r), 'Y'

    x0, y0, z0 = float(c), float(r), 0.0
    x1, y1, z1 = x0 + lx, y0 + ly, float(lz)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]

    faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
    ]

    px, py = pivot
    ca, sa = math.cos(angle), math.sin(angle)

    def rot_p(p):
        vx, vy, vz = p
        if axis == 'X':
            dy, dz_v = vy - py, vz
            return (vx + dc, py + dy * ca + dz_v * sa + dr, -dy * sa + dz_v * ca + dz)
        else:
            dx_v, dz_v = vx - px, vz
            return (px + dx_v * ca + dz_v * sa + dc, vy + dr, -dx_v * sa + dz_v * ca + dz)

    def rot_v(v):
        vx, vy, vz = v
        if axis == 'X':
            return (vx, vy * ca + vz * sa, -vy * sa + vz * ca)
        else:
            return (vx * ca + vz * sa, vy, -vx * sa + vz * ca)

    rot_verts = [rot_p(v) for v in verts]

    if scale != 1.0:
        cx = sum(v[0] for v in rot_verts) / 8.0
        cy = sum(v[1] for v in rot_verts) / 8.0
        cz = sum(v[2] for v in rot_verts) / 8.0
        rot_verts = [(cx + (v[0] - cx) * scale,
                      cy + (v[1] - cy) * scale,
                      cz + (v[2] - cz) * scale) for v in rot_verts]

    def proj(p):
        return (off[0] + p[0] * tw + p[1] * skew,
                off[1] + p[1] * th - p[2] * cube_h)

    proj_verts = [proj(v) for v in rot_verts]
    v_cam = (-skew / tw, 1.0, th / cube_h)

    target_surf = surface
    if alpha < 255:
        target_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    visible_faces = []
    for fname, v_indices, n0 in faces:
        n = rot_v(n0)
        v_dot = n[0] * v_cam[0] + n[1] * v_cam[1] + n[2] * v_cam[2]
        if v_dot > 1e-4:
            center_x = sum(rot_verts[idx][0] for idx in v_indices) / 4.0
            center_y = sum(rot_verts[idx][1] for idx in v_indices) / 4.0
            center_z = sum(rot_verts[idx][2] for idx in v_indices) / 4.0
            depth = center_y * th - center_z * cube_h + center_x * 0.5

            col = _face_color(n)
            pts = [proj_verts[idx] for idx in v_indices]
            visible_faces.append((depth, fname, pts, col))

    visible_faces.sort(key=lambda item: item[0])
    for _, fname, pts, col in visible_faces:
        int_pts = [(int(round(p[0])), int(round(p[1]))) for p in pts]
        _poly_aa(target_surf, col, int_pts)

    if alpha < 255:
        target_surf.set_alpha(max(0, min(255, alpha)))
        surface.blit(target_surf, (0, 0))


def rodrigues_rot(v: Tuple[float, float, float],
                  k: Tuple[float, float, float],
                  angle: float) -> Tuple[float, float, float]:
    ca, sa = math.cos(angle), math.sin(angle)
    kxv = (k[1] * v[2] - k[2] * v[1],
           k[2] * v[0] - k[0] * v[2],
           k[0] * v[1] - k[1] * v[0])
    kdv = k[0] * v[0] + k[1] * v[1] + k[2] * v[2]
    return (
        v[0] * ca + kxv[0] * sa + k[0] * kdv * (1.0 - ca),
        v[1] * ca + kxv[1] * sa + k[1] * kdv * (1.0 - ca),
        v[2] * ca + kxv[2] * sa + k[2] * kdv * (1.0 - ca),
    )


def generate_shatter_pieces(r: int, c: int, orient: int, action: str) -> list:
    """Tạo 8 mảnh gỗ vụn 3D (2x2x2 voxels) khi khối lăn hụt.
    Mỗi mảnh mang vị trí ban đầu (tại góc lật 90 độ), vận tốc văng nổ ngoại vi (burst),
    mômen quán tính lăn theo hướng hụt, và trục xoay 3D ngẫu nhiên"""
    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1

    if action == 'U':   pivot, axis = (c, r), 'X'
    elif action == 'D': pivot, axis = (c, r + ly), 'X'
    elif action == 'L': pivot, axis = (c, r), 'Y'
    else:               pivot, axis = (c + lx, r), 'Y'

    sign = -1.0 if action in ('U', 'L') else 1.0
    base_angle = sign * 0.5 * math.pi
    ca, sa = math.cos(base_angle), math.sin(base_angle)
    px, py = pivot

    def rot_base(p):
        vx, vy, vz = p
        if axis == 'X':
            dy, dz_v = vy - py, vz
            return (vx, py + dy * ca + dz_v * sa, -dy * sa + dz_v * ca)
        else:
            dx_v, dz_v = vx - px, vz
            return (px + dx_v * ca + dz_v * sa, vy, -dx_v * sa + dz_v * ca)

    sx, sy, sz = lx / 2.0, ly / 2.0, lz / 2.0
    pieces = []

    mom_x, mom_y = 0.0, 0.0
    if action == 'U':   mom_y = -2.2
    elif action == 'D': mom_y =  2.2
    elif action == 'L': mom_x = -2.2
    elif action == 'R': mom_x =  2.2

    rng = random.Random(int(r * 100 + c * 10 + (1 if orient == STAND else 2)))
    cx = c + lx / 2.0
    cy = r + ly / 2.0
    cz = lz / 2.0
    rcx, rcy, rcz = rot_base((cx, cy, cz))

    for ix in range(2):
        for iy in range(2):
            for iz in range(2):
                bx = c + (ix + 0.5) * sx
                by = r + (iy + 0.5) * sy
                bz = (iz + 0.5) * sz
                rx, ry, rz = rot_base((bx, by, bz))

                ex = (rx - rcx) * 2.8 + mom_x * 0.9 + rng.uniform(-0.3, 0.3)
                ey = (ry - rcy) * 2.8 + mom_y * 0.9 + rng.uniform(-0.3, 0.3)
                ez = (rz - rcz) * 2.0 + 1.2 + rng.uniform(-0.2, 0.4)

                axis_s = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
                mag = math.sqrt(sum(a * a for a in axis_s)) or 1.0
                spin_axis = (axis_s[0] / mag, axis_s[1] / mag, axis_s[2] / mag)
                spin_speed = rng.uniform(5.0, 10.0)

                pieces.append({
                    'init_pos': (rx, ry, rz),
                    'size': (sx * 0.42, sy * 0.42, sz * 0.42),
                    'vel': (ex, ey, ez),
                    'spin_axis': spin_axis,
                    'spin_speed': spin_speed,
                })
    return pieces


def draw_shatter_block(surface: pygame.Surface,
                       pieces: list,
                       t: float,
                       alpha: int,
                       tw: int, th: int,
                       off: Tuple[int, int],
                       skew: int) -> None:
    """Vẽ các mảnh vỡ vụn 3D phân tán ra không gian (Voxel Shatter).
    Mỗi mảnh voxel xoay tự do theo trục riêng và rơi theo gia tốc trọng trường g=12.0."""
    if alpha <= 0 or not pieces:
        return

    cube_h = 60
    g = 12.0
    v_cam = (-skew / tw, 1.0, th / cube_h)

    box_faces = [
        ('TOP',    [4, 5, 6, 7], ( 0.0,  0.0,  1.0)),
        ('BOTTOM', [3, 2, 1, 0], ( 0.0,  0.0, -1.0)),
        ('FRONT',  [3, 2, 6, 7], ( 0.0,  1.0,  0.0)),
        ('BACK',   [1, 0, 4, 5], ( 0.0, -1.0,  0.0)),
        ('LEFT',   [0, 3, 7, 4], (-1.0,  0.0,  0.0)),
        ('RIGHT',  [2, 1, 5, 6], ( 1.0,  0.0,  0.0)),
    ]

    target_surf = surface
    if alpha < 255:
        target_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    all_faces = []
    for p in pieces:
        x = p['init_pos'][0] + p['vel'][0] * t
        y = p['init_pos'][1] + p['vel'][1] * t
        z = p['init_pos'][2] + p['vel'][2] * t - 0.5 * g * (t * t)

        angle = p['spin_speed'] * t
        k = p['spin_axis']
        hx, hy, hz = p['size']

        local_v = [
            (-hx, -hy, -hz), ( hx, -hy, -hz), ( hx,  hy, -hz), (-hx,  hy, -hz),
            (-hx, -hy,  hz), ( hx, -hy,  hz), ( hx,  hy,  hz), (-hx,  hy,  hz),
        ]
        world_v = []
        for lv in local_v:
            rv = rodrigues_rot(lv, k, angle)
            world_v.append((x + rv[0], y + rv[1], z + rv[2]))

        proj_v = [(off[0] + wv[0] * tw + wv[1] * skew,
                   off[1] + wv[1] * th - wv[2] * cube_h) for wv in world_v]

        for fname, v_indices, n0 in box_faces:
            n = rodrigues_rot(n0, k, angle)
            v_dot = n[0] * v_cam[0] + n[1] * v_cam[1] + n[2] * v_cam[2]
            if v_dot > 1e-4:
                c_y = sum(world_v[idx][1] for idx in v_indices) / 4.0
                c_z = sum(world_v[idx][2] for idx in v_indices) / 4.0
                c_x = sum(world_v[idx][0] for idx in v_indices) / 4.0
                depth = c_y * th - c_z * cube_h + c_x * 0.5
                col = _face_color(n)
                pts = [proj_v[idx] for idx in v_indices]
                all_faces.append((depth, pts, col))

    all_faces.sort(key=lambda item: item[0])
    for _, pts, col in all_faces:
        int_pts = [(int(round(pt[0])), int(round(pt[1]))) for pt in pts]
        _poly_aa(target_surf, col, int_pts)

    if alpha < 255:
        target_surf.set_alpha(max(0, min(255, alpha)))
        surface.blit(target_surf, (0, 0))


def draw_block(surface: pygame.Surface, state: State, tw: int, th: int,
               off: Tuple[int, int], skew: int) -> None:
    """Vẽ khối gỗ 3D tĩnh ở tư thế hiện tại."""
    draw_animated_block(surface, state.r, state.c, state.orient, 'D', 0.0, tw, th, off, skew)


def draw_scene(surface: pygame.Surface,
               level: Level,
               state: Optional[State],
               tw: int, th: int,
               off: Tuple[int, int],
               skew: int,
               anim_state: Optional[Tuple[int, int, int, str, float]] = None,
               fall_state: Optional[tuple] = None,
               spawn_state: Optional[Tuple[int, int, int, float]] = None) -> None:
    """Vẽ toàn bộ khung cảnh: Sàn đảo bay và Khối gỗ (tĩnh, lăn animation, rơi xuất phát, vỡ vụn hoặc mờ dần)."""
    is_void = (fall_state is not None and fall_state[0] == 'void')
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')

    # Xếp lớp chiều sâu khi khối rơi vực:
    if is_void:
        _, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc, v_scale, v_alpha = fall_state
        ly = 1 if v_orient != VERT else 2
        cut_row = vr + ly - 1

    # Vẽ từng hàng sàn theo trục Y (từ sau ra trước)
    for r in range(level.rows):
        for c in range(level.cols):
            ch = level.grid[r][c]
            if ch == '.':
                continue

            x, y = grid_to_iso(r, c, tw, th, off, skew)
            if ch == 'G':
                _draw_goal_tile(surface, level, r, c, x, y, tw, th, skew)
            else:
                _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)

        # Chèn khối rơi void cũ sau khi đã vẽ xong hàng cut_row
        if is_void and r == cut_row and v_alpha > 0:
            draw_void_fall_block(surface, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc,
                                 tw, th, off, skew, scale=v_scale, alpha=v_alpha)

    # Nếu rơi ở hàng cuối cùng của đảo, vẽ khối sau khi vẽ toàn bộ sàn
    if is_void and cut_row >= level.rows and v_alpha > 0:
        draw_void_fall_block(surface, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc,
                             tw, th, off, skew, scale=v_scale, alpha=v_alpha)

    # Hiệu ứng Vỡ Vụn (Shatter): Các mảnh voxel nổ tung văng ra không gian
    if is_shatter:
        _, s_pieces, s_t, s_alpha = fall_state
        draw_shatter_block(surface, s_pieces, s_t, s_alpha, tw, th, off, skew)

    # 3. Rơi vào hố Goal: Khối mờ dần tự nhiên, đứng nguyên tại ô
    if is_goal:
        _, gr, gc, g_orient, g_alpha = fall_state
        draw_goal_dissolve_block(surface, gr, gc, g_orient, g_alpha, tw, th, off, skew)

    # 4. Khối đang spawn rơi từ trên trời xuống, đang lăn hoặc khối tĩnh
    if spawn_state is not None:
        sr, sc, sorient, sz = spawn_state
        draw_spawn_block(surface, sr, sc, sorient, sz, tw, th, off, skew)
    elif anim_state is not None:
        ar, ac, aorient, aaction, aprogress = anim_state
        draw_animated_block(surface, ar, ac, aorient, aaction, aprogress, tw, th, off, skew)
    elif state is not None and fall_state is None:
        draw_block(surface, state, tw, th, off, skew)
