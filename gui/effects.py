from typing import Tuple
import pygame

from game.state import STAND, HORIZ, VERT
from gui.render_board import _poly_aa
from gui.render_block import _face_color, draw_animated_block


def draw_goal_dissolve_block(surface: pygame.Surface,
                             r: int, c: int, orient: int,
                             alpha: int,
                             tw: int, th: int,
                             off: Tuple[int, int], skew: int,
                             sink: float = 0.0) -> None:
    """Vẽ khối chìm dần vào ô Goal và tan biến.
    """
    cube_h = 60
    lx = 1 if orient != HORIZ else 2
    ly = 1 if orient != VERT else 2
    lz = 2 if orient == STAND else 1
    h = max(0.0, lz - sink)
    if h <= 0.001 or alpha <= 0:
        return

    x0, y0, z0 = float(c), float(r), 0.0
    x1, y1, z1 = x0 + lx, y0 + ly, float(h)
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
    for _, v_indices, n0 in faces:
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


VOID_FALL_GRAVITY = 38.0


def draw_void_fall_block(surface: pygame.Surface,
                         r: int, c: int, orient: int, action: str,
                         t: float,
                         tw: int, th: int,
                         off: Tuple[int, int], skew: int) -> None:
    """Khối đã lăn hụt hoàn toàn ra ngoài sàn: lật tiếp quanh mép, trượt ra ngoài và rơi nhanh hơn sàn.

    (r, c, orient, action) là tư thế lúc bắt đầu lăn; t là số giây kể từ lúc lăn xong 90 độ.
    """
    dx = {'L': -1.0, 'R': 1.0}.get(action, 0.0)
    dy = {'U': -1.0, 'D': 1.0}.get(action, 0.0)
    drift = 0.0 if action == 'U' else 0.7 * t                              # trượt tiếp ra phía ngoài mép
    extra = min(3.0, 3.5 * t)                    # lật thêm quanh mép, rủ xuống
    drop = (dx * drift, dy * drift, -0.5 * VOID_FALL_GRAVITY * t * t)
    draw_animated_block(surface, r, c, orient, action, 1.0, tw, th, off, skew,
                        extra_angle=extra, drop=drop, shadow=False)


def draw_void_tip_block(surface: pygame.Surface,
                        r: int, c: int, orient: int, void_first: bool,
                        t: float,
                        tw: int, th: int,
                        off: Tuple[int, int], skew: int) -> None:
    """Khối nằm vắt ngang mép: một ô gác sàn, một ô treo trên hố. Khối chúi xuống phía hố
    (xoay quanh mép sàn, nửa gác sàn nhấc lên) rồi trượt ra và rơi.

    (r, c, orient) là tư thế khối sau khi lăn hụt (HORIZ hoặc VERT). void_first=True nếu ô hụt là
    ô đầu (r, c); ngược lại ô hụt là ô thứ hai.
    """
    sign = -1.0 if void_first else 1.0
    tilt = min(1.6, 3.0 * t)
    t2 = max(0.0, t - 0.15)
    if orient == HORIZ:
        pivot = (c + 1.0, float(r), 'Y')
        slide = (sign * 0.9 * t2, 0.0)
    else:
        pivot = (float(c), r + 1.0, 'X')
        slide = (0.0, sign * 0.9 * t2)
    drop = (slide[0], slide[1], -0.5 * VOID_FALL_GRAVITY * t2 * t2)
    draw_animated_block(surface, r, c, orient, 'D', 0.0, tw, th, off, skew,
                        drop=drop, shadow=False,
                        pivot_override=(pivot[0], pivot[1], pivot[2], sign * tilt))
