from typing import List, Tuple
import math
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


def _draw_hanging_vines(surface: pygame.Surface, p_start: Tuple[int, int], p_end: Tuple[int, int],
                        depth: int, seed: int) -> None:
    """Vẽ dây leo xanh tự nhiên buông rủ từ mép vách đất xuống không trung."""
    if (seed % 100) >= 50:
        return

    num_vines = 2 if (seed % 100) < 18 else 1
    for i in range(num_vines):
        sub_seed = (seed + i * 7919) & 0xFFFF
        t = 0.20 + ((sub_seed % 60) / 100.0)
        rx = int(p_start[0] + t * (p_end[0] - p_start[0]))
        ry = int(p_start[1] + t * (p_end[1] - p_start[1]))

        # Chiều dài dây leo buông rủ xuống quá đáy vách đất
        hang_extra = 4 + ((sub_seed >> 4) % 12)
        total_len = depth + hang_extra

        # Các điểm uốn lượn tự nhiên
        wiggle = 2 if (sub_seed % 2 == 0) else -2
        pts = [
            (rx, ry),
            (rx + wiggle, ry + int(depth * 0.45)),
            (rx - wiggle, ry + depth),
            (rx + (wiggle // 2), ry + total_len),
        ]
        pygame.draw.lines(surface, (62, 118, 40), False, pts, 2)

        # Các chiếc lá nhỏ mọc dọc thân dây leo
        leaf_col_1 = (105, 178, 58)
        leaf_col_2 = (128, 198, 72)
        pygame.draw.circle(surface, leaf_col_1, (rx + wiggle - 2, ry + int(depth * 0.35)), 2)
        pygame.draw.circle(surface, leaf_col_2, (rx - wiggle + 2, ry + int(depth * 0.85)), 2)
        pygame.draw.circle(surface, leaf_col_1, (rx + (wiggle // 2), ry + total_len - 1), 2)


def _draw_tile_vegetation(surface: pygame.Surface, quad: List[Tuple[int, int]],
                          tw: int, th: int, skew: int, seed: int) -> None:
    """Vẽ hoa dại hoặc khóm cỏ non trên mặt thảm cỏ theo phân bố tự nhiên."""
    h_val = seed % 100
    if h_val >= 46:
        return

    tl, tr, _, bl = quad
    u = 0.28 + (((seed >> 4) % 44) / 100.0)
    v = 0.28 + (((seed >> 9) % 44) / 100.0)
    px = int(tl[0] + u * (tr[0] - tl[0]) + v * (bl[0] - tl[0]))
    py = int(tl[1] + u * (tr[1] - tl[1]) + v * (bl[1] - tl[1]))

    r_petal = max(2, tw // 32)

    if h_val < 16:
        # Hoa cúc dại (Cánh trắng, nhụy vàng)
        p_col = (252, 252, 245)
        for dx, dy in [(-r_petal, 0), (r_petal, 0), (0, -r_petal), (0, r_petal), (0, 0)]:
            pygame.draw.circle(surface, p_col, (px + dx, py + dy), r_petal)
        pygame.draw.circle(surface, (255, 215, 35), (px, py), max(1, r_petal - 1))

    elif h_val < 32:
        # Hoa lưu ly / tím oải hương hoặc hoa hồng phấn
        p_col = (210, 145, 235) if (seed % 2 == 0) else (248, 138, 162)
        for dx, dy in [(-r_petal, -1), (r_petal, -1), (-1, r_petal), (1, r_petal)]:
            pygame.draw.circle(surface, p_col, (px + dx, py + dy), r_petal)
        pygame.draw.circle(surface, (255, 245, 140), (px, py), max(1, r_petal - 1))

    else:
        # Khóm cỏ non (2-3 cọng cỏ xanh tươi vươn lên)
        g_col1 = (175, 230, 85)
        g_col2 = (148, 212, 68)
        pygame.draw.line(surface, g_col1, (px, py), (px - 3, py - 6), 1)
        pygame.draw.line(surface, g_col2, (px, py), (px + 2, py - 7), 1)
        if seed % 3 == 0:
            pygame.draw.line(surface, g_col1, (px, py), (px, py - 5), 1)


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
        # Dây leo rủ xuống mép vực trước
        _draw_hanging_vines(surface, bl, br, d, ((r * 48271) ^ (c * 99991)) & 0xFFFF)

    # Vách mép vực trái
    if c - 1 < 0 or level.grid[r][c - 1] == '.':
        left_face = [tl, bl, (bl[0], bl[1] + d), (tl[0], tl[1] + d)]
        _poly_aa(surface, C['soil_left'], left_face)
        grass_rim_l = [tl, bl, (bl[0], bl[1] + 3), (tl[0], tl[1] + 3)]
        _poly_aa(surface, C['grass_rim_l'], grass_rim_l)
        # Dây leo rủ xuống mép vực trái
        _draw_hanging_vines(surface, tl, bl, d, ((r * 65537) ^ (c * 179424673)) & 0xFFFF)

    # Mặt trên thảm cỏ
    top_c = C['grass_light'] if (r + c) % 2 == 0 else C['grass_dark']
    line_c = C['grass_line']

    _poly_aa(surface, top_c, quad, line_c)

    # Điểm xuyết hoa dại và khóm cỏ non (chỉ trên ô cỏ thường)
    is_bridge = any(b.pos == (r, c) for b in level.bridges.values())
    if (not is_bridge and
        (r, c) not in level.fragile and
        (r, c) not in level.switches and
        level.grid[r][c] not in ('.', 'G')):
        h = ((r * 73856093) ^ (c * 19349663)) & 0xFFFFFFFF
        _draw_tile_vegetation(surface, quad, tw, th, skew, h)


def _draw_goal_garland(surface: pygame.Surface, quad: List[Tuple[int, int]],
                       tw: int, th: int) -> None:
    """Vẽ vòng hoa kết từ cành lá và hoa dại quanh miệng hố đích (không có hào quang)."""
    tl, tr, br, bl = quad

    # 4 cạnh của miệng hố: (điểm đầu, điểm cuối, vector dời nhẹ ra ngoài)
    edges = [
        (tl, tr, (0, -2)),      # Cạnh sau
        (tr, br, (2, 0)),       # Cạnh phải
        (br, bl, (0, 2)),       # Cạnh trước
        (bl, tl, (-2, 0)),      # Cạnh trái
    ]

    r_leaf = max(2, tw // 30)
    r_flower = max(2, tw // 28)

    # 1. Vẽ dây leo xanh viền quanh 4 cạnh
    garland_col = (65, 128, 42)
    leaf_col_light = (118, 192, 70)
    leaf_col_dark = (82, 155, 48)

    for p1, p2, off in edges:
        pts = [
            (p1[0] + off[0], p1[1] + off[1]),
            (int(p1[0] * 0.6 + p2[0] * 0.4) + off[0], int(p1[1] * 0.6 + p2[1] * 0.4) + off[1]),
            (int(p1[0] * 0.4 + p2[0] * 0.6) + off[0], int(p1[1] * 0.4 + p2[1] * 0.6) + off[1]),
            (p2[0] + off[0], p2[1] + off[1]),
        ]
        pygame.draw.lines(surface, garland_col, False, pts, max(2, tw // 32))

        # Cụm lá nhỏ so le dọc cạnh
        for t in (0.22, 0.50, 0.78):
            lx = int(p1[0] + t * (p2[0] - p1[0])) + off[0]
            ly = int(p1[1] + t * (p2[1] - p1[1])) + off[1]
            pygame.draw.circle(surface, leaf_col_light, (lx - 1, ly - 1), r_leaf)
            pygame.draw.circle(surface, leaf_col_dark, (lx + 2, ly + 1), r_leaf)

    # 2. Các bông hoa điểm xuyết quanh vòng hoa
    palette = [
        ((255, 138, 162), (255, 230,  90)),   # Hoa hồng đào
        ((255, 255, 245), (255, 210,  35)),   # Hoa cúc trắng
        ((255, 222,  55), (238, 135,  30)),   # Hoa vàng rực rỡ
        ((208, 145, 240), (255, 245, 140)),   # Hoa tím oải hương
    ]

    def _draw_garland_flower(fx: int, fy: int, col_idx: int, is_corner: bool = False) -> None:
        p_col, c_col = palette[col_idx % len(palette)]
        rf = r_flower + (1 if is_corner else 0)
        # 5 cánh hoa tròn
        angles = [0.0, 1.256, 2.513, 3.770, 5.026]  # 2*pi / 5
        d_petal = int(rf * 0.85)
        for a in angles:
            px = fx + int(d_petal * math.cos(a))
            py = fy + int(d_petal * math.sin(a))
            pygame.draw.circle(surface, p_col, (px, py), rf)
        # Nhụy hoa
        pygame.draw.circle(surface, c_col, (fx, fy), max(1, rf - 1))

    # Hoa ở 4 góc nổi bật
    _draw_garland_flower(tl[0] - 1, tl[1] - 2, 0, is_corner=True)
    _draw_garland_flower(tr[0] + 1, tr[1] - 2, 1, is_corner=True)
    _draw_garland_flower(br[0] + 1, br[1] + 2, 2, is_corner=True)
    _draw_garland_flower(bl[0] - 1, bl[1] + 2, 3, is_corner=True)

    # Hoa nhỏ nằm giữa các cạnh
    for i, (p1, p2, off) in enumerate(edges):
        for j, t in enumerate((0.36, 0.68)):
            fx = int(p1[0] + t * (p2[0] - p1[0])) + off[0]
            fy = int(p1[1] + t * (p2[1] - p1[1])) + off[1]
            _draw_garland_flower(fx, fy, (i * 2 + j + 1), is_corner=False)


def _draw_goal_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                    x: int, y: int, tw: int, th: int, skew: int) -> None:
    """Vẽ hố đích kèm vòng hoa trang trí (không có hào quang)."""
    quad = _tile_quad(x, y, tw, th, skew)
    tl, tr, br, bl = quad
    d = TILE_DEPTH

    # Mép vực ngoài nếu hố nằm ở rìa ngoài cùng
    if r + 1 >= level.rows or level.grid[r + 1][c] == '.':
        _poly_aa(surface, C['soil_front'], [bl, br, (br[0], br[1] + d), (bl[0], bl[1] + d)])
        _draw_hanging_vines(surface, bl, br, d, ((r * 48271) ^ (c * 99991)) & 0xFFFF)
    if c - 1 < 0 or level.grid[r][c - 1] == '.':
        _poly_aa(surface, C['soil_left'], [tl, bl, (bl[0], bl[1] + d), (tl[0], tl[1] + d)])
        _draw_hanging_vines(surface, tl, bl, d, ((r * 65537) ^ (c * 179424673)) & 0xFFFF)

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
