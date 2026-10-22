import math
from typing import Tuple
import pygame

from game.state import State, STAND, HORIZ, VERT
from gui.board import _poly_aa


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


def draw_block(surface: pygame.Surface, state: State, tw: int, th: int,
               off: Tuple[int, int], skew: int) -> None:
    """Vẽ khối gỗ 3D tĩnh ở tư thế hiện tại."""
    draw_animated_block(surface, state.r, state.c, state.orient, 'D', 0.0, tw, th, off, skew)
