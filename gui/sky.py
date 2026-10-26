from typing import Optional, Tuple
import pygame

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
