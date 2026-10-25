from typing import List, Tuple
import pygame
import pygame.gfxdraw

from game.level_loader import Level

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


def _poly_aa(surface: pygame.Surface, color, points: List[Tuple[int, int]], edge_color=None) -> None:
    pygame.gfxdraw.filled_polygon(surface, points, color)
    ec = edge_color if edge_color else color
    pygame.gfxdraw.aapolygon(surface, points, ec)


# Tham khảo phép chiếu Oblique Cavalier: https://en.wikipedia.org/wiki/Oblique_projection
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
