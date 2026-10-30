"""Bầu trời, mặt trời, tia nắng, mây trôi và các hòn đảo lơ lửng."""
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

# Cấu hình chuyển động mây trôi và dập dềnh
CLOUDS_DRIFT_DATA = [
    # (orig_x, orig_y, width, height, alpha, speed_px_s, bob_amp, phase, is_far)
    ( 540, 150, 160, 38, 0.55,  8.0, 2.5, 1.2, True),
    ( 760, 420, 180, 44, 0.50,  6.5, 2.0, 3.4, True),
    ( 180,  90, 220, 56, 0.86, 12.0, 3.0, 0.5, False),
    ( 980,  85, 250, 62, 0.82, 15.0, 3.5, 2.1, False),
    ( 100, 360, 210, 52, 0.78, 10.0, 3.0, 4.3, False),
    (1160, 350, 230, 56, 0.78, 14.0, 3.2, 5.7, False),
    ( 260, 640, 260, 65, 0.80, 17.0, 4.0, 1.9, False),
    ( 960, 630, 280, 70, 0.85, 19.0, 4.5, 3.8, False),
]

# Cấu hình các hòn đảo lơ lửng phía xa (bố trí thoáng, không vướng sàn chơi)
ISLANDS_DATA = [
    # (rel_x, rel_y, iw, ih, variant, bob_speed, bob_amp, phase)
    (0.08, 0.52, 105, 68, 0, 1.1, 4.0, 0.0),   # Đảo trái trung tâm
    (0.91, 0.35,  88, 56, 1, 1.3, 3.5, 2.1),   # Đảo phải trên
    (0.85, 0.20,  64, 42, 2, 0.9, 2.5, 4.2),   # Đảo nhỏ xa xăm góc trên phải
]


@lru_cache(maxsize=32)
def _make_cloud_stamp(cw: int, ch: int) -> pygame.Surface:
    """Tạo texture đám mây dạng vector bo tròn mềm mại."""
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


@lru_cache(maxsize=16)
def _make_island_stamp(iw: int, ih: int, variant: int) -> pygame.Surface:
    """Tạo texture hòn đảo đá/cỏ mini lơ lửng phía xa."""
    scale = 3
    sw = iw * scale
    sh = ih * scale
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx = sw // 2

    # 1. Đáy đá nhọn treo lơ lửng (Rocky inverted cone)
    crag_tip = (int(cx - sw * 0.04), int(sh * 0.84))
    left_edge = (int(cx - sw * 0.42), int(sh * 0.38))
    right_edge = (int(cx + sw * 0.42), int(sh * 0.38))
    mid_top = (cx, int(sh * 0.38))

    # Mặt vách đá tối (bên trái)
    pts_left = [left_edge, (int(cx - sw * 0.22), int(sh * 0.62)), crag_tip, mid_top]
    pygame.draw.polygon(surf, (82, 62, 50), pts_left)

    # Mặt vách đá sáng (bên phải đón nắng)
    pts_right = [mid_top, crag_tip, (int(cx + sw * 0.22), int(sh * 0.60)), right_edge]
    pygame.draw.polygon(surf, (115, 88, 70), pts_right)

    # Viên đá nhỏ rời lơ lửng dưới đáy đảo
    pygame.draw.polygon(surf, (95, 75, 60), [
        (int(cx - sw * 0.05), int(sh * 0.89)),
        (int(cx + sw * 0.02), int(sh * 0.88)),
        (int(cx - sw * 0.01), int(sh * 0.94)),
    ])

    # 2. Mặt thảm cỏ xanh phẳng trên đỉnh đảo
    grass_rect = (int(cx - sw * 0.44), int(sh * 0.26), int(sw * 0.88), int(sh * 0.24))
    pygame.draw.ellipse(surf, (108, 162, 98), (grass_rect[0], grass_rect[1] + 4, grass_rect[2], grass_rect[3]))
    pygame.draw.ellipse(surf, (132, 185, 120), grass_rect)
    pygame.draw.ellipse(surf, (155, 208, 142), (int(cx - sw * 0.36), int(sh * 0.27), int(sw * 0.72), int(sh * 0.16)))

    # 3. Cây cối / tiểu cảnh nhỏ trên đảo
    if variant == 0:
        # Cây thông/bonsai nhỏ
        tx, ty = cx - 8, int(sh * 0.28)
        pygame.draw.rect(surf, (95, 65, 42), (tx - 2, ty - 22, 5, 22))
        pygame.draw.circle(surf, (82, 148, 75), (tx - 8, ty - 26), 14)
        pygame.draw.circle(surf, (105, 175, 95), (tx + 6, ty - 28), 16)
        pygame.draw.circle(surf, (125, 195, 110), (tx, ty - 34), 13)
    elif variant == 1:
        # 2 khóm cây lùn
        tx1, ty1 = cx - 18, int(sh * 0.30)
        pygame.draw.rect(surf, (95, 65, 42), (tx1 - 2, ty1 - 16, 4, 16))
        pygame.draw.circle(surf, (95, 165, 88), (tx1, ty1 - 18), 12)
        tx2, ty2 = cx + 14, int(sh * 0.31)
        pygame.draw.rect(surf, (95, 65, 42), (tx2 - 2, ty2 - 12, 4, 12))
        pygame.draw.circle(surf, (115, 185, 102), (tx2, ty2 - 14), 10)
    else:
        # Đồi cỏ nhỏ với cụm hoa trắng
        pygame.draw.ellipse(surf, (142, 198, 128), (cx - 16, int(sh * 0.22), 32, 14))
        pygame.draw.circle(surf, (255, 255, 245), (cx - 8, int(sh * 0.24)), 3)
        pygame.draw.circle(surf, (255, 255, 245), (cx + 6, int(sh * 0.25)), 3)

    # 4. Vạt mây quấn quanh chân đảo
    cloud_w = int(sw * 0.46)
    cloud_h = int(sh * 0.16)
    cloud_surf = pygame.Surface((cloud_w, cloud_h), pygame.SRCALPHA)
    pygame.draw.ellipse(cloud_surf, (245, 250, 255, 165), (0, 0, cloud_w, cloud_h))
    surf.blit(cloud_surf, (int(cx - sw * 0.24), int(sh * 0.50)))

    return pygame.transform.smoothscale(surf, (iw, ih))


_cached_sky_bg: Optional[Tuple[int, int, pygame.Surface]] = None


def _render_sky_background(win_w: int, win_h: int) -> pygame.Surface:
    """Vẽ nền trời gradient, vầng mặt trời ấm áp và các tia nắng xiên."""
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

    # Đặt mặt trời ở góc cao bên trái (thoáng, không bị khối che lấp)
    sun_cx = int(210 * scale_x)
    sun_cy = int(78 * scale_y)

    sun_surf = pygame.Surface((win_w, win_h), pygame.SRCALPHA)

    # 2. Vầng hào quang mặt trời tỏa tròn đa lớp mịn màng (Smooth Radial Glow)
    num_steps = 22
    max_radius = int(210 * scale)
    for i in range(num_steps, 0, -1):
        ratio = i / float(num_steps)
        rad = int(max_radius * (ratio ** 1.35))
        alpha = int(110 * ((1.0 - ratio) ** 1.7))
        if rad > 0 and alpha > 0:
            pygame.draw.circle(sun_surf, (255, 230, 150, alpha), (sun_cx, sun_cy), rad)

    # Lõi mặt trời sáng ấm
    pygame.draw.circle(sun_surf, (255, 255, 245, 255), (sun_cx, sun_cy), max(12, int(18 * scale)))

    # 3. Tia nắng xiên (God rays / Sunbeams)
    # Kéo dài xuyên suốt màn hình (length = 2200) để không tạo vệt cắt ngang bất thường
    ray_length = 2200 * scale
    rays = [
        # (angle_deg, spread_deg, alpha)
        (25.0, 5.0, 20),
        (33.0, 6.5, 26),
        (42.0, 6.0, 22),
        (51.0, 4.5, 18),
    ]

    for angle, spread, alpha in rays:
        a1 = math.radians(angle - spread * 0.5)
        a2 = math.radians(angle + spread * 0.5)
        r_start = 20 * scale
        p0 = (sun_cx + int(r_start * math.cos(a1)), sun_cy + int(r_start * math.sin(a1)))
        p1 = (sun_cx + int(r_start * math.cos(a2)), sun_cy + int(r_start * math.sin(a2)))
        p2 = (sun_cx + int(ray_length * math.cos(a2)), sun_cy + int(ray_length * math.sin(a2)))
        p3 = (sun_cx + int(ray_length * math.cos(a1)), sun_cy + int(ray_length * math.sin(a1)))

        pygame.draw.polygon(sun_surf, (255, 248, 212, alpha), [p0, p1, p2, p3])

    surf.blit(sun_surf, (0, 0))
    return surf


def draw_sky_with_clouds(surface: pygame.Surface, win_w: int, win_h: int) -> None:
    """Vẽ bầu trời, mặt trời, tia nắng xiên, mây trôi động và đảo lơ lửng."""
    global _cached_sky_bg
    if _cached_sky_bg is None or _cached_sky_bg[0] != win_w or _cached_sky_bg[1] != win_h:
        _cached_sky_bg = (win_w, win_h, _render_sky_background(win_w, win_h))

    # 1. Vẽ nền trời tĩnh (đã gồm mặt trời + tia nắng xiên được cache)
    surface.blit(_cached_sky_bg[2], (0, 0))

    scale_x = win_w / 1280.0
    scale_y = win_h / 720.0
    scale = min(scale_x, scale_y)

    ticks = pygame.time.get_ticks()
    t_sec = ticks / 1000.0

    # 2. Vẽ các đám mây xa (Far whisper clouds)
    for orig_x, orig_y, cw, ch, alpha_s, speed, bob_amp, phase, is_far in CLOUDS_DRIFT_DATA:
        if not is_far:
            continue
        actual_cw = max(20, int(cw * scale))
        actual_ch = max(10, int(ch * scale))
        wrap_w = win_w + actual_cw * 2
        drift_x = (int(orig_x * scale_x) + speed * scale_x * t_sec) % wrap_w - actual_cw
        bob_y = int(orig_y * scale_y) + math.sin(t_sec * 0.9 + phase) * (bob_amp * scale_y)

        stamp = _make_cloud_stamp(actual_cw, actual_ch)
        stamp.set_alpha(int(230 * alpha_s))
        surface.blit(stamp, (int(drift_x - stamp.get_width() // 2),
                             int(bob_y - stamp.get_height() * 0.62)))

    # 3. Vẽ các hòn đảo mini lơ lửng phía xa (với chuyển động dập dềnh nhẹ nhàng)
    for rel_x, rel_y, iw, ih, variant, bob_speed, bob_amp, phase in ISLANDS_DATA:
        actual_iw = max(20, int(iw * scale))
        actual_ih = max(15, int(ih * scale))
        base_x = int(rel_x * win_w)
        base_y = int(rel_y * win_h) + math.sin(t_sec * bob_speed + phase) * (bob_amp * scale_y)

        island_stamp = _make_island_stamp(actual_iw, actual_ih, variant)
        surface.blit(island_stamp, (base_x - island_stamp.get_width() // 2,
                                    int(base_y - island_stamp.get_height() * 0.5)))

    # 4. Vẽ các đám mây chính bồng bềnh trôi ngang màn hình (Main puffy clouds)
    for orig_x, orig_y, cw, ch, alpha_s, speed, bob_amp, phase, is_far in CLOUDS_DRIFT_DATA:
        if is_far:
            continue
        actual_cw = max(20, int(cw * scale))
        actual_ch = max(10, int(ch * scale))
        wrap_w = win_w + actual_cw * 2
        drift_x = (int(orig_x * scale_x) + speed * scale_x * t_sec) % wrap_w - actual_cw
        bob_y = int(orig_y * scale_y) + math.sin(t_sec * 1.1 + phase) * (bob_amp * scale_y)

        stamp = _make_cloud_stamp(actual_cw, actual_ch)
        stamp.set_alpha(int(230 * alpha_s))
        surface.blit(stamp, (int(drift_x - stamp.get_width() // 2),
                             int(bob_y - stamp.get_height() * 0.62)))
