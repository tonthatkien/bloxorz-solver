"""Bầu trời, mặt trời tỏa nắng, mây trôi và các hòn đảo lơ lửng."""
from functools import lru_cache
import math
from typing import Optional, Tuple
import pygame

# Dữ liệu đám mây gốc (giữ tương thích 100%)
CLOUDS_DATA = [
    (180,   90, 220, 56, 0.88),
    (980,   85, 250, 62, 0.85),
    (100,  360, 210, 52, 0.80),
    (1160, 350, 230, 56, 0.80),
    (260,  640, 260, 65, 0.80),
    (960,  630, 280, 70, 0.85),
]

# Cấu hình mây trôi mượt mà (trôi ngang ổn định, không giật dọc)
CLOUDS_DRIFT_DATA = [
    # (orig_x, orig_y, width, height, alpha, speed_px_s, is_far)
    ( 540, 150, 160, 38, 0.50, 12.0, True),
    ( 760, 420, 180, 44, 0.45, 10.0, True),
    ( 180,  90, 220, 56, 0.84, 18.0, False),
    ( 980,  85, 250, 62, 0.80, 22.0, False),
    ( 100, 360, 210, 52, 0.78, 16.0, False),
    (1160, 350, 230, 56, 0.78, 20.0, False),
    ( 260, 640, 260, 65, 0.80, 24.0, False),
    ( 960, 630, 280, 70, 0.84, 26.0, False),
]

# Cấu hình các hòn đảo lơ lửng phía xa (bố trí thoáng, thơ mộng)
ISLANDS_DATA = [
    # (rel_x, rel_y, iw, ih, variant)
    (0.08, 0.50, 115, 76, 0),   # Đảo trái trung tâm (có 2 cây cổ thụ Ghibli bồng bềnh)
    (0.91, 0.38,  95, 64, 1),   # Đảo phải (có ngọn thông thanh thoát & hoa dại)
    (0.85, 0.72,  75, 50, 2),   # Đảo nhỏ góc phải dưới (đồi cỏ & tảng đá rêu)
]


@lru_cache(maxsize=32)
def _make_cloud_stamp(cw: int, ch: int, alpha: int) -> pygame.Surface:
    """Tạo texture đám mây dạng vector bo tròn mềm mại và nướng sẵn alpha để không bị xung đột."""
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

    scaled = pygame.transform.smoothscale(c_surf, (sw // scale, sh // scale))
    scaled.set_alpha(max(0, min(255, alpha)))
    return scaled


@lru_cache(maxsize=16)
def _make_island_stamp(iw: int, ih: int, variant: int) -> pygame.Surface:
    """Tạo texture hòn đảo đá/cỏ mini lơ lửng phía xa (phong cách Ghibli bồng bềnh, thơ mộng)."""
    scale = 3
    sw = iw * scale
    sh = ih * scale
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx = sw // 2

    # 1. Đệm mây trắng ôm chân đảo (Cloud cradle cushion)
    c_w = int(sw * 0.76)
    c_h = int(sh * 0.28)
    c_x = cx - c_w // 2
    c_y = int(sh * 0.64)
    pygame.draw.ellipse(surf, (245, 250, 255, 180), (c_x, c_y, c_w, c_h))
    pygame.draw.ellipse(surf, (255, 255, 255, 220), (c_x + int(c_w * 0.12), c_y - int(c_h * 0.25), int(c_w * 0.44), int(c_h * 0.85)))
    pygame.draw.ellipse(surf, (255, 255, 255, 220), (c_x + int(c_w * 0.44), c_y - int(c_h * 0.20), int(c_w * 0.42), int(c_h * 0.80)))

    # 2. Thân đảo dạng đá phong hóa xếp tầng (Layered rock strata)
    # Tầng đá trên cùng
    poly_top = [
        (int(cx - sw * 0.44), int(sh * 0.35)),
        (int(cx + sw * 0.44), int(sh * 0.35)),
        (int(cx + sw * 0.36), int(sh * 0.54)),
        (int(cx - sw * 0.36), int(sh * 0.54)),
    ]
    pygame.draw.polygon(surf, (142, 105, 75), poly_top)
    pygame.draw.polygon(surf, (110, 80, 58), [poly_top[0], (cx, int(sh * 0.35)), (cx - int(sw * 0.05), int(sh * 0.54)), poly_top[3]])

    # Tầng đá giữa
    poly_mid = [
        (int(cx - sw * 0.34), int(sh * 0.53)),
        (int(cx + sw * 0.34), int(sh * 0.53)),
        (int(cx + sw * 0.20), int(sh * 0.72)),
        (int(cx - sw * 0.20), int(sh * 0.72)),
    ]
    pygame.draw.polygon(surf, (125, 90, 64), poly_mid)
    pygame.draw.polygon(surf, (95, 68, 48), [poly_mid[0], (cx, int(sh * 0.53)), (cx - int(sw * 0.04), int(sh * 0.72)), poly_mid[3]])

    # Mỏm đá dưới cùng thu nhọn tự nhiên
    poly_tip = [
        (int(cx - sw * 0.18), int(sh * 0.71)),
        (int(cx + sw * 0.18), int(sh * 0.71)),
        (int(cx + sw * 0.02), int(sh * 0.86)),
        (int(cx - sw * 0.06), int(sh * 0.86)),
    ]
    pygame.draw.polygon(surf, (105, 75, 52), poly_tip)
    pygame.draw.polygon(surf, (78, 55, 38), [poly_tip[0], (cx, int(sh * 0.71)), (int(cx - sw * 0.06), int(sh * 0.86))])

    # Dây leo xanh rủ từ mép đá
    pygame.draw.lines(surf, (75, 145, 55), False, [
        (int(cx - sw * 0.38), int(sh * 0.37)),
        (int(cx - sw * 0.37), int(sh * 0.48)),
        (int(cx - sw * 0.39), int(sh * 0.58)),
    ], 2)
    pygame.draw.lines(surf, (85, 160, 65), False, [
        (int(cx + sw * 0.28), int(sh * 0.37)),
        (int(cx + sw * 0.30), int(sh * 0.46)),
        (int(cx + sw * 0.27), int(sh * 0.55)),
    ], 2)

    # 3. Mặt thảm cỏ xanh mướt bo tròn bồng bềnh
    grass_w = int(sw * 0.92)
    grass_h = int(sh * 0.25)
    gx = cx - grass_w // 2
    gy = int(sh * 0.24)
    pygame.draw.ellipse(surf, (95, 155, 75), (gx, gy + 4, grass_w, grass_h))
    pygame.draw.ellipse(surf, (128, 198, 98), (gx, gy, grass_w, grass_h))
    pygame.draw.ellipse(surf, (162, 228, 126), (gx + int(grass_w * 0.15), gy + 2, int(grass_w * 0.70), int(grass_h * 0.65)))

    # 4. Cây cối & tiểu cảnh xinh xắn trên đỉnh đảo
    if variant == 0:
        # Cây cổ thụ tán tròn bồng bềnh phong cách Ghibli
        tx, ty = cx - 6, int(sh * 0.26)
        pygame.draw.polygon(surf, (110, 75, 48), [
            (tx - 3, ty), (tx + 3, ty), (tx + 2, ty - 22), (tx - 2, ty - 22)
        ])
        pygame.draw.circle(surf, (68, 140, 62), (tx - 10, ty - 28), 16)
        pygame.draw.circle(surf, (82, 165, 75), (tx + 8, ty - 30), 18)
        pygame.draw.circle(surf, (110, 195, 95), (tx - 4, ty - 38), 17)
        pygame.draw.circle(surf, (145, 230, 125), (tx - 2, ty - 41), 11)
        pygame.draw.circle(surf, (255, 235, 120), (tx - 6, ty - 32), 2)
        pygame.draw.circle(surf, (255, 160, 180), (tx + 6, ty - 34), 2)

        # Cây nhỏ thứ 2 bên cạnh
        tx2 = cx + 20
        pygame.draw.polygon(surf, (110, 75, 48), [
            (tx2 - 2, ty + 2), (tx2 + 2, ty + 2), (tx2 + 1, ty - 12), (tx2 - 1, ty - 12)
        ])
        pygame.draw.circle(surf, (82, 165, 75), (tx2, ty - 16), 11)
        pygame.draw.circle(surf, (130, 215, 115), (tx2, ty - 18), 7)

    elif variant == 1:
        # Ngọn thông cao thanh thoát & khóm hoa dại
        tx = cx + 8
        ty = int(sh * 0.27)
        pygame.draw.rect(surf, (105, 72, 45), (tx - 2, ty - 24, 4, 24))
        pygame.draw.polygon(surf, (65, 135, 68), [(tx, ty - 38), (tx - 15, ty - 20), (tx + 15, ty - 20)])
        pygame.draw.polygon(surf, (85, 165, 88), [(tx, ty - 34), (tx - 12, ty - 18), (tx + 12, ty - 18)])
        pygame.draw.polygon(surf, (115, 200, 110), [(tx, ty - 40), (tx - 9, ty - 26), (tx + 9, ty - 26)])
        pygame.draw.circle(surf, (255, 255, 245), (cx - 14, int(sh * 0.24)), 3)
        pygame.draw.circle(surf, (255, 215, 50), (cx - 8, int(sh * 0.25)), 3)
        pygame.draw.circle(surf, (255, 140, 180), (cx - 20, int(sh * 0.25)), 3)

    else:
        # Đồi cỏ hoa dại và tảng đá cuội mini
        rx = cx + 10
        ry = int(sh * 0.24)
        pygame.draw.ellipse(surf, (140, 145, 150), (rx - 8, ry - 6, 16, 10))
        pygame.draw.ellipse(surf, (175, 180, 185), (rx - 6, ry - 6, 12, 6))
        for ox, oy, col in [(-12, -2, (255, 255, 245)), (-4, 1, (255, 220, 60)), (2, -3, (255, 140, 170))]:
            pygame.draw.circle(surf, col, (cx + ox, int(sh * 0.24) + oy), 3)

    return pygame.transform.smoothscale(surf, (iw, ih))


_cached_sky_bg: Optional[Tuple[int, int, pygame.Surface]] = None


def _render_sky_background(win_w: int, win_h: int) -> pygame.Surface:
    """Vẽ nền trời gradient, vầng mặt trời vàng rực rỡ và hòn đảo cố định vững chãi."""
    surf = pygame.Surface((win_w, win_h))
    top_color = (68, 138, 212)
    bot_color = (135, 192, 242)

    # 1. Bầu trời chuyển sắc (Gradient Sky)
    for y in range(0, win_h, 2):
        t = y / win_h
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * t)
        pygame.draw.rect(surf, (r, g, b), (0, y, win_w, 2))

    scale_x = win_w / 1280.0
    scale_y = win_h / 720.0
    scale = min(scale_x, scale_y)

    sun_cx = int(980 * scale_x)
    sun_cy = int(95 * scale_y)

    # 2. Vẽ các hòn đảo mini lơ lửng phía xa cố định trong background
    for rel_x, rel_y, iw, ih, variant in ISLANDS_DATA:
        actual_iw = max(20, int(iw * scale))
        actual_ih = max(15, int(ih * scale))
        base_x = int(rel_x * win_w)
        base_y = int(rel_y * win_h)
        island_stamp = _make_island_stamp(actual_iw, actual_ih, variant)
        surf.blit(island_stamp, (base_x - island_stamp.get_width() // 2,
                                 int(base_y - island_stamp.get_height() * 0.5)))

    # 3. Vầng mặt trời vàng rực rỡ, tỏa nắng ấm áp (Radiant Warm Golden Sun)
    sun_surf = pygame.Surface((win_w, win_h), pygame.SRCALPHA)

    # A. Vầng hào quang tỏa rộng nhiều tầng (Warm Golden Aura)
    num_steps = 26
    max_radius = int(240 * scale)
    for i in range(num_steps, 0, -1):
        ratio = i / float(num_steps)
        rad = int(max_radius * (ratio ** 1.30))
        r_col = 255
        g_col = int(180 + 55 * ratio)
        b_col = int(30 + 100 * ratio)
        alpha = int(125 * ((1.0 - ratio) ** 1.6))
        if rad > 0 and alpha > 0:
            pygame.draw.circle(sun_surf, (r_col, g_col, b_col, alpha), (sun_cx, sun_cy), rad)

    # B. Vòng tia hào quang tỏa tròn (Sun Corona Rays / Starburst)
    num_rays = 12
    r_inner = 24 * scale
    r_outer = 48 * scale
    ray_width_angle = math.pi / 18.0
    for k in range(num_rays):
        angle = k * (2.0 * math.pi / num_rays)
        p_tip = (sun_cx + int(r_outer * math.cos(angle)),
                 sun_cy + int(r_outer * math.sin(angle)))
        p_b1 = (sun_cx + int(r_inner * math.cos(angle - ray_width_angle)),
                sun_cy + int(r_inner * math.sin(angle - ray_width_angle)))
        p_b2 = (sun_cx + int(r_inner * math.cos(angle + ray_width_angle)),
                sun_cy + int(r_inner * math.sin(angle + ray_width_angle)))
        pygame.draw.polygon(sun_surf, (255, 215, 65, 140), [p_tip, p_b1, p_b2])

    # C. Quầng sáng corona bao quanh đĩa mặt trời
    pygame.draw.circle(sun_surf, (255, 210, 50, 200), (sun_cx, sun_cy), max(18, int(30 * scale)))

    # D. Đĩa mặt trời màu vàng ấm rực rỡ (Golden Sun Core)
    pygame.draw.circle(sun_surf, (255, 228, 60, 255), (sun_cx, sun_cy), max(14, int(22 * scale)))
    # Tâm đĩa sáng bừng
    pygame.draw.circle(sun_surf, (255, 250, 160, 255), (sun_cx, sun_cy), max(9, int(14 * scale)))

    surf.blit(sun_surf, (0, 0))
    return surf


def draw_sky_with_clouds(surface: pygame.Surface, win_w: int, win_h: int) -> None:
    """Vẽ bầu trời, mặt trời tỏa nắng, hòn đảo xa và mây trôi ngang mượt mà."""
    global _cached_sky_bg
    if _cached_sky_bg is None or _cached_sky_bg[0] != win_w or _cached_sky_bg[1] != win_h:
        _cached_sky_bg = (win_w, win_h, _render_sky_background(win_w, win_h))

    # 1. Vẽ nền trời tĩnh (gồm nền gradient, hòn đảo xa, mặt trời tỏa nắng)
    surface.blit(_cached_sky_bg[2], (0, 0))

    scale_x = win_w / 1280.0
    scale_y = win_h / 720.0
    scale = min(scale_x, scale_y)

    ticks = pygame.time.get_ticks()
    t_sec = ticks / 1000.0

    # 2. Vẽ các đám mây xa (trôi êm dịu, không giật)
    for orig_x, orig_y, cw, ch, alpha_s, speed, is_far in CLOUDS_DRIFT_DATA:
        if not is_far:
            continue
        actual_cw = max(20, int(cw * scale))
        actual_ch = max(10, int(ch * scale))
        wrap_w = win_w + actual_cw * 2
        drift_x = (int(orig_x * scale_x) - speed * scale_x * t_sec) % wrap_w - actual_cw
        actual_y = int(orig_y * scale_y)

        stamp = _make_cloud_stamp(actual_cw, actual_ch, int(230 * alpha_s))
        surface.blit(stamp, (int(round(drift_x - stamp.get_width() // 2)),
                             int(round(actual_y - stamp.get_height() * 0.62))))

    # 3. Vẽ các đám mây chính bồng bềnh trôi ngang màn hình (Main puffy clouds)
    for orig_x, orig_y, cw, ch, alpha_s, speed, is_far in CLOUDS_DRIFT_DATA:
        if is_far:
            continue
        actual_cw = max(20, int(cw * scale))
        actual_ch = max(10, int(ch * scale))
        wrap_w = win_w + actual_cw * 2
        drift_x = (int(orig_x * scale_x) - speed * scale_x * t_sec) % wrap_w - actual_cw
        actual_y = int(orig_y * scale_y)

        stamp = _make_cloud_stamp(actual_cw, actual_ch, int(230 * alpha_s))
        surface.blit(stamp, (int(round(drift_x - stamp.get_width() // 2)),
                             int(round(actual_y - stamp.get_height() * 0.62))))
