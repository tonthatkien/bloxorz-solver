"""GUI chính của Bloxorz"""
from typing import Optional, Tuple
import math
import pygame

from game.game import Game
from game.level_loader import Level, load_level
from game.state import State, STAND, HORIZ, VERT, cells
from gui.draw import (
    calculate_iso_layout,
    draw_scene,
    draw_sky_with_clouds,
    generate_shatter_pieces,
)

# Cấu hình cửa sổ và màu sắc
WINDOW_SIZE = (1280, 720)
FPS         = 60
BG_COLOR    = (82, 115, 135)

# Bảng chuyển đổi hướng
_TRANS = {
    (STAND, 'U'): (VERT,   -2,  0),
    (STAND, 'D'): (VERT,    1,  0),
    (STAND, 'L'): (HORIZ,   0, -2),
    (STAND, 'R'): (HORIZ,   0,  1),
    (HORIZ, 'U'): (HORIZ,  -1,  0),
    (HORIZ, 'D'): (HORIZ,   1,  0),
    (HORIZ, 'L'): (STAND,   0, -1),
    (HORIZ, 'R'): (STAND,   0,  2),
    (VERT,  'U'): (STAND,  -1,  0),
    (VERT,  'D'): (STAND,   2,  0),
    (VERT,  'L'): (VERT,    0, -1),
    (VERT,  'R'): (VERT,    0,  1),
}

_KEY_MAP = {
    pygame.K_UP:    'U',
    pygame.K_DOWN:  'D',
    pygame.K_LEFT:  'L',
    pygame.K_RIGHT: 'R',
}


def _step(state: State, action: str) -> Optional[State]:
    """Tính trạng thái kế tiếp khi lăn (chưa xét sàn)"""
    if state.split is not None:
        return None
    key = (state.orient, action)
    if key not in _TRANS:
        return None
    new_orient, dr, dc = _TRANS[key]
    return State(state.r + dr, state.c + dc, new_orient, state.bridges, None)


def _is_walkable(state: State, level: Level) -> bool:
    """Kiểm tra khối có nằm trọn vẹn trên các ô sàn hợp lệ hay không"""
    for r, c in cells(state):
        if not (0 <= r < level.rows and 0 <= c < level.cols):
            return False
        if level.grid[r][c] == '.':
            return False
    return True


def _is_goal(state: State, level: Level) -> bool:
    return (state.orient == STAND
            and state.split is None
            and level.grid[state.r][state.c] == 'G')


def run(level_path: str) -> None:
    pygame.init()
    pygame.display.set_caption('Bloxorz')
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock  = pygame.time.Clock()

    # Phông chữ và Giao diện
    sys_fonts = pygame.font.get_fonts()
    font_family = 'trebuchetms' if 'trebuchetms' in sys_fonts else ('verdana' if 'verdana' in sys_fonts else 'arial')
    font_title   = pygame.font.SysFont(font_family, 48, bold=True)
    font_hud_lbl = pygame.font.SysFont(font_family, 15, bold=True)
    font_hud_val = pygame.font.SysFont(font_family, 20, bold=True)
    font_sub     = pygame.font.SysFont(font_family, 18)
    font_hint    = pygame.font.SysFont(font_family, 15)

    def draw_aa_round_rect(surface: pygame.Surface,
                           rect: Tuple[int, int, int, int],
                           color: Tuple[int, ...],
                           border_radius: int = 0,
                           border_color: Optional[Tuple[int, ...]] = None,
                           border_width: int = 1) -> None:
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return
        scale = 2
        sw, sh = w * scale, h * scale
        sr = border_radius * scale
        sbw = border_width * scale
        sub = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(sub, color, (0, 0, sw, sh), border_radius=sr)
        if border_color and border_width > 0:
            pygame.draw.rect(sub, border_color, (0, 0, sw, sh), width=sbw, border_radius=sr)
        smooth = pygame.transform.smoothscale(sub, (w, h))
        surface.blit(smooth, (x, y))

    def _draw_hud_pill(surf: pygame.Surface, x: int, y: int,
                       lbl_s: pygame.Surface, val_s: pygame.Surface,
                       bg_col=(254, 250, 235, 235),
                       border_col=(180, 130, 85, 180)) -> int:
        pad_x, gap, h = 16, 8, 38
        w = pad_x * 2 + lbl_s.get_width() + gap + val_s.get_width()
        draw_aa_round_rect(surf, (x, y, w, h), bg_col, border_radius=14, border_color=border_col, border_width=2)

        ly = y + (h - lbl_s.get_height()) // 2
        vy = y + (h - val_s.get_height()) // 2
        surf.blit(lbl_s, (x + pad_x, ly))
        surf.blit(val_s, (x + pad_x + lbl_s.get_width() + gap, vy))
        return w

    level  = load_level(level_path)
    game   = Game(level)
    tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

    def reset() -> State:
        return game.initial_state()

    state: State = reset()
    won: bool    = False
    lost: bool   = False
    move_count: int = 0

    # Cấu hình và trạng thái Animation toán học
    ANIM_DURATION_MS = 140      # Lăn 140ms
    FALL_GOAL_DURATION_MS = 600 # Khối mờ dần trên ô Goal 600ms
    FALL_VOID_DURATION_MS = 600 # Khối vỡ vụn thành các voxel 3D tản mác vào không gian 600ms
    SPAWN_DURATION_MS = 460     # Khối từ trên trời rơi xuống và nảy nhẹ tiếp đất 460ms

    def _ease(t: float) -> float:
        return t * t * (3.0 - 2.0 * t)

    animating = False
    anim_start_r = 0
    anim_start_c = 0
    anim_start_orient = STAND
    anim_action = 'D'
    anim_next_state: Optional[State] = None
    anim_is_void = False
    anim_start_time = 0
    buffered_action: Optional[str] = None

    # Trạng thái rơi
    falling_goal = False
    falling_void = False
    fall_start_time = 0
    fall_r, fall_c, fall_orient = 0.0, 0.0, STAND
    fall_shatter_pieces: list = []

    # Trạng thái Spawn Drop (rơi từ trên trời khi khởi đầu và restart)
    spawning = True
    spawn_start_time = pygame.time.get_ticks()
    spawn_r = state.r
    spawn_c = state.c
    spawn_orient = state.orient
    z_spawn = 8.5

    while True:
        can_control = not won and not lost and not falling_goal and not falling_void and not spawning

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if event.key == pygame.K_r:
                    state, won, lost, move_count = reset(), False, False, 0
                    animating = False
                    falling_goal = False
                    falling_void = False
                    buffered_action = None
                    fall_shatter_pieces = []
                    spawning = True
                    spawn_start_time = pygame.time.get_ticks()
                    spawn_r = state.r
                    spawn_c = state.c
                    spawn_orient = state.orient
                    z_spawn = 8.5

                elif can_control and event.key in _KEY_MAP:
                    action = _KEY_MAP[event.key]
                    if not animating:
                        ns = _step(state, action)
                        if ns is not None:
                            animating = True
                            anim_start_r = state.r
                            anim_start_c = state.c
                            anim_start_orient = state.orient
                            anim_action = action
                            anim_next_state = ns
                            anim_is_void = not _is_walkable(ns, level)
                            anim_start_time = pygame.time.get_ticks()
                            buffered_action = None
                    else:
                        # Đệm phím nếu đang lăn trên sàn và đã đi hơn 35% chặng đường
                        if not anim_is_void:
                            elapsed = pygame.time.get_ticks() - anim_start_time
                            if elapsed / ANIM_DURATION_MS > 0.35:
                                buffered_action = action

        # Cập nhật tiến độ Spawn Drop (khối rơi từ mây xuống khi bắt đầu / nhấn R)
        if spawning:
            now = pygame.time.get_ticks()
            elapsed = now - spawn_start_time
            if elapsed >= SPAWN_DURATION_MS:
                spawning = False
                z_spawn = 0.0
            else:
                t = elapsed / float(SPAWN_DURATION_MS)
                if t <= 0.78:
                    # Rơi nhanh dần theo gia tốc trọng lực từ Z = 8.5
                    tf = t / 0.78
                    z_spawn = 8.5 * (1.0 - tf * tf)
                else:
                    # Nảy nhẹ đàn hồi 1 nhịp khi tiếp đất
                    tb = (t - 0.78) / 0.22
                    z_spawn = 0.22 * math.sin(tb * math.pi) * (1.0 - tb * 0.5)

        # Cập nhật tiến độ animation lăn khối
        anim_progress = 0.0
        if animating:
            now = pygame.time.get_ticks()
            raw_t = (now - anim_start_time) / ANIM_DURATION_MS
            if raw_t >= 1.0:
                animating = False
                move_count += 1

                if anim_is_void:
                    # Lăn hụt mép sàn -> khối vỡ vụn thành các voxel 3D tản mác ra không gian
                    falling_void = True
                    fall_start_time = pygame.time.get_ticks()
                    fall_shatter_pieces = generate_shatter_pieces(anim_start_r, anim_start_c, anim_start_orient, anim_action)
                    buffered_action = None
                else:
                    state = anim_next_state
                    if _is_goal(state, level):
                        # Đứng đúng ô Goal -> rơi chìm vào lòng hố
                        falling_goal = True
                        fall_start_time = pygame.time.get_ticks()
                        fall_r = float(state.r)
                        fall_c = float(state.c)
                        fall_orient = state.orient
                        buffered_action = None
                    elif buffered_action is not None:
                        # Kích hoạt ngay lệnh đệm
                        b_act = buffered_action
                        buffered_action = None
                        ns = _step(state, b_act)
                        if ns is not None:
                            animating = True
                            anim_start_r = state.r
                            anim_start_c = state.c
                            anim_start_orient = state.orient
                            anim_action = b_act
                            anim_next_state = ns
                            anim_is_void = not _is_walkable(ns, level)
                            anim_start_time = pygame.time.get_ticks()
            else:
                anim_progress = _ease(raw_t)

        # Cập nhật tiến độ rơi (Goal Fall & Void Fall)
        fall_tuple = None
        if falling_goal:
            now = pygame.time.get_ticks()
            gt = (now - fall_start_time) / FALL_GOAL_DURATION_MS
            if gt >= 1.0:
                falling_goal = False
                won = True
            else:
                # Khối đứng nguyên tại ô Goal và mờ dần tự nhiên
                alpha = int(255 * max(0.0, 1.0 - gt))
                fall_tuple = ('goal', fall_r, fall_c, fall_orient, alpha)

        elif falling_void:
            now = pygame.time.get_ticks()
            elapsed_ms = now - fall_start_time
            t = elapsed_ms / 1000.0
            if elapsed_ms >= FALL_VOID_DURATION_MS:
                falling_void = False
                lost = True
            else:
                # Giữ nét trong ~190ms đầu (t < 0.32s), sau đó mờ dần khi rơi sâu vào mây
                if t < 0.32:
                    alpha = 255
                elif t < 0.60:
                    alpha = int(255 * max(0.0, 1.0 - (t - 0.32) / 0.28))
                else:
                    alpha = 0

                fall_tuple = ('shatter', fall_shatter_pieces, t, alpha)

        # Vẽ bầu trời mây và hòn đảo
        draw_sky_with_clouds(screen, *WINDOW_SIZE)
        if spawning:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       spawn_state=(spawn_r, spawn_c, spawn_orient, z_spawn))
        elif animating:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       anim_state=(anim_start_r, anim_start_c, anim_start_orient, anim_action, anim_progress))
        elif falling_goal or falling_void:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       fall_state=fall_tuple)
        else:
            # Khi đã thua (rơi xong), ẩn khối khỏi màn hình
            draw_scene(screen, level, None if lost else state, tw, th, offset, skew)

        lvl_lbl = font_hud_lbl.render("LEVEL", True, (138, 90, 50))
        lvl_val = font_hud_val.render(f"{level.name}", True, (185, 28, 28))
        w_lvl = _draw_hud_pill(screen, 24, 20, lvl_lbl, lvl_val)

        mov_lbl = font_hud_lbl.render("MOVES", True, (138, 90, 50))
        mov_val = font_hud_val.render(f"{move_count}", True, (180, 83, 9))
        _draw_hud_pill(screen, 24 + w_lvl + 12, 20, mov_lbl, mov_val)

        # Controls Hint
        hint_str = "Arrow Keys: Move   •   R: Restart   •   ESC: Exit"
        hint_txt = font_hint.render(hint_str, True, (90, 60, 35))
        hw, hh = hint_txt.get_width() + 32, 34
        hx = (WINDOW_SIZE[0] - hw) // 2
        hy = WINDOW_SIZE[1] - 46
        draw_aa_round_rect(screen, (hx, hy, hw, hh), (254, 250, 235, 225),
                           border_radius=12, border_color=(180, 130, 85, 150), border_width=1)
        screen.blit(hint_txt, ((WINDOW_SIZE[0] - hint_txt.get_width()) // 2, WINDOW_SIZE[1] - 38))

        # Banner chiến thắng (YOU WIN!)
        if won:
            pw, ph = 460, 180
            px = (WINDOW_SIZE[0] - pw) // 2
            py = (WINDOW_SIZE[1] - ph) // 2
            draw_aa_round_rect(screen, (px, py, pw, ph), (250, 254, 250, 250),
                               border_radius=16, border_color=(34, 197, 94), border_width=2)

            msg = font_title.render('YOU WIN!', True, (22, 163, 74))
            sub = font_sub.render(f'Completed in {move_count} moves', True, (21, 128, 61))
            restart_hint = font_hint.render('Press R to play again', True, (74, 140, 90))

            screen.blit(msg, (px + (pw - msg.get_width()) // 2, py + 24))
            screen.blit(sub, (px + (pw - sub.get_width()) // 2, py + 95))
            screen.blit(restart_hint, (px + (pw - restart_hint.get_width()) // 2, py + 130))

        # Banner thất bại (GAME OVER)
        if lost:
            pw, ph = 460, 180
            px = (WINDOW_SIZE[0] - pw) // 2
            py = (WINDOW_SIZE[1] - ph) // 2
            draw_aa_round_rect(screen, (px, py, pw, ph), (255, 248, 246, 250),
                               border_radius=16, border_color=(220, 75, 60), border_width=2)

            msg = font_title.render('GAME OVER', True, (185, 28, 28))
            sub = font_sub.render(f'You fell into the void ({move_count} moves)', True, (110, 65, 55))
            restart_hint = font_hint.render('Press R to try again', True, (140, 80, 70))

            screen.blit(msg, (px + (pw - msg.get_width()) // 2, py + 24))
            screen.blit(sub, (px + (pw - sub.get_width()) // 2, py + 95))
            screen.blit(restart_hint, (px + (pw - restart_hint.get_width()) // 2, py + 130))

        pygame.display.flip()
        clock.tick(FPS)
