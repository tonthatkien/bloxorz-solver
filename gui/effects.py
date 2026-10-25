import math
import random
from typing import Tuple
import pygame

from game.state import STAND, HORIZ, VERT
from gui.render_board import _poly_aa
from gui.render_block import _face_color


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



# Tham khảo công thức quay Rodrigues: https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
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


# Tham khảo vật lý chuyển động rơi tự do dưới trọng lực: https://en.wikipedia.org/wiki/Free_fall
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
