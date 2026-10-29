"""GUI chính của Bloxorz (Task D1/D2)."""
import math
from typing import Optional, Tuple
import pygame

from game.block import Block
from game.game import Game
from game.level_loader import Level, load_level
from game.state import STAND, State
from gui.draw import (
    calculate_iso_layout,
    draw_scene,
    draw_sky_with_clouds,
)
from gui.widgets import (
    Button,
    LevelSelectorModal,
    draw_aa_round_rect,
)

# Cấu hình cửa sổ và màu sắc
WINDOW_SIZE = (1280, 720)
FPS         = 60
BG_COLOR    = (82, 115, 135)

_KEY_MAP = {
    pygame.K_UP:    'U',
    pygame.K_DOWN:  'D',
    pygame.K_LEFT:  'L',
    pygame.K_RIGHT: 'R',
}


def _draw_hud_pill(surf: pygame.Surface, x: int, y: int,
                   lbl_s: pygame.Surface, val_s: pygame.Surface,
                   bg_col=(254, 250, 235, 235),
                   border_col=(180, 130, 85, 180)) -> int:
    """Vẽ viên thuốc (pill) hiển thị thông số trên thanh trạng thái."""
    pad_x, gap, h = 16, 8, 38
    w = pad_x * 2 + lbl_s.get_width() + gap + val_s.get_width()
    draw_aa_round_rect(surf, (x, y, w, h), bg_col, border_radius=14,
                       border_color=border_col, border_width=2)

    ly = y + (h - lbl_s.get_height()) // 2
    vy = y + (h - val_s.get_height()) // 2
    surf.blit(lbl_s, (x + pad_x, ly))
    surf.blit(val_s, (x + pad_x + lbl_s.get_width() + gap, vy))
    return w


def run(level_path: str) -> None:
    """Khởi chạy vòng lặp giao diện Pygame cho game Bloxorz."""
    pygame.init()
    pygame.display.set_caption('Bloxorz')
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock  = pygame.time.Clock()

    # Phông chữ giao diện
    sys_fonts = pygame.font.get_fonts()
    font_family = ('trebuchetms' if 'trebuchetms' in sys_fonts
                   else ('verdana' if 'verdana' in sys_fonts else 'arial'))
    font_title   = pygame.font.SysFont(font_family, 44, bold=True)
    font_hud_lbl = pygame.font.SysFont(font_family, 15, bold=True)
    font_hud_val = pygame.font.SysFont(font_family, 20, bold=True)
    font_btn     = pygame.font.SysFont(font_family, 16, bold=True)
    font_sub     = pygame.font.SysFont(font_family, 18)
    font_hint    = pygame.font.SysFont(font_family, 15)

    # Quản lý màn chơi và Game Core
    current_level_path = level_path
    level: Level = load_level(current_level_path)
    game: Game   = Game(level)
    tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

    state: State = game.initial_state()
    won: bool    = False
    lost: bool   = False
    move_count: int = 0

    # Cấu hình thời gian và thông số Animation
    ANIM_DURATION_MS = 140
    FALL_GOAL_DURATION_MS = 600
    FALL_VOID_DURATION_MS = 900
    SPAWN_DURATION_MS = 460
    SPAWN_HEIGHT = 8.5

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

    falling_goal = False
    falling_void = False
    fall_start_time = 0
    fall_r, fall_c, fall_orient = 0.0, 0.0, STAND
    fall_shatter_pieces: list = []

    spawning = True
    spawn_start_time = pygame.time.get_ticks()
    spawn_r = state.r
    spawn_c = state.c
    spawn_orient = state.orient
    z_spawn = SPAWN_HEIGHT

    def _step(cur_state: State, action: str) -> Tuple[Optional[State], bool]:
        """Thực hiện một nước đi bằng cách truy vấn Game Core (game.get_successors).

        Trả về (state_tiếp_theo, có_rơi_không).
        - Nếu action nằm trong successors: nước đi hợp lệ -> (next_state, False).
        - Nếu action không nằm trong successors: nước đi rơi (thua) -> (phantom_state, True).
        """
        if cur_state.split is not None:
            return None, False

        # Kiểm tra tính hợp lệ qua Game Core
        for act, next_st, _ in game.get_successors(cur_state):
            if act == action:
                return next_st, False

        # Không nằm trong successors -> khối lăn ra ngoài sàn rơi vực
        rolled = Block(cur_state.r, cur_state.c, cur_state.orient).roll(action)
        phantom_state = State(rolled.r, rolled.c, rolled.orient, cur_state.bridges, None)
        return phantom_state, True

    def load_level_and_reset(path: str) -> None:
        """Nạp màn chơi mới hoặc khởi động lại và reset toàn bộ trạng thái animation."""
        nonlocal level, game, current_level_path, tw, th, offset, skew
        nonlocal state, won, lost, move_count, animating
        nonlocal falling_goal, falling_void, buffered_action
        nonlocal fall_shatter_pieces, spawning, spawn_start_time
        nonlocal spawn_r, spawn_c, spawn_orient, z_spawn

        current_level_path = path
        level = load_level(current_level_path)
        game = Game(level)
        tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

        state = game.initial_state()
        won, lost, move_count = False, False, 0
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
        z_spawn = SPAWN_HEIGHT

    # Nút bấm HUD góc trên-phải
    btn_restart  = Button((WINDOW_SIZE[0] - 24 - 120 - 12 - 110, 20, 110, 38),
                          "Restart", font_btn, border_radius=14)
    btn_new_game = Button((WINDOW_SIZE[0] - 24 - 120, 20, 120, 38),
                          "New Game", font_btn, border_radius=14)

    # Nút bấm trên Banner Thắng / Thua
    banner_w, banner_h = 460, 220
    b_px = (WINDOW_SIZE[0] - banner_w) // 2
    b_py = (WINDOW_SIZE[1] - banner_h) // 2
    btn_win_restart   = Button((b_px + 35, b_py + 145, 180, 44), "Play Again", font_btn,
                               bg_color=(235, 252, 238), hover_color=(215, 245, 220),
                               border_color=(34, 197, 94), text_color=(20, 120, 50))
    btn_win_new_game  = Button((b_px + 245, b_py + 145, 180, 44), "New Game", font_btn,
                               border_color=(34, 197, 94), text_color=(20, 120, 50))
    btn_loss_restart  = Button((b_px + 35, b_py + 145, 180, 44), "Try Again", font_btn,
                               bg_color=(255, 240, 238), hover_color=(255, 225, 220),
                               border_color=(220, 75, 60), text_color=(185, 28, 28))
    btn_loss_new_game = Button((b_px + 245, b_py + 145, 180, 44), "New Game", font_btn,
                               border_color=(220, 75, 60), text_color=(185, 28, 28))

    # Hộp thoại chọn màn
    level_modal = LevelSelectorModal(WINDOW_SIZE, font_hud_val, font_btn, font_sub)
    level_pill_rect = pygame.Rect(24, 20, 160, 38)

    while True:
        can_control = (not won and not lost and not falling_goal
                       and not falling_void and not spawning and not level_modal.is_open)
        mouse_pos = pygame.mouse.get_pos()

        # Cập nhật con trỏ chuột tương tác (Hand Pointer khi hover nút)
        if level_modal.is_open:
            is_hovering = level_modal.is_any_hovered(mouse_pos)
        else:
            is_hovering = (
                level_pill_rect.collidepoint(mouse_pos) or
                btn_restart.is_hovered(mouse_pos) or
                btn_new_game.is_hovered(mouse_pos) or
                (won and (btn_win_restart.is_hovered(mouse_pos) or
                          btn_win_new_game.is_hovered(mouse_pos))) or
                (lost and (btn_loss_restart.is_hovered(mouse_pos) or
                           btn_loss_new_game.is_hovered(mouse_pos)))
            )
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if is_hovering
                                    else pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

        # Xử lý sự kiện (Event Loop)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # Ưu tiên tương tác với modal chọn màn nếu đang mở
            if level_modal.is_open:
                selected_level = level_modal.handle_event(event)
                if selected_level is not None:
                    load_level_and_reset(selected_level)
                continue

            # Xử lý phím bấm
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if event.key == pygame.K_r:
                    load_level_and_reset(current_level_path)

                elif can_control and event.key in _KEY_MAP:
                    action = _KEY_MAP[event.key]
                    if not animating:
                        ns, anim_is_void = _step(state, action)
                        if ns is not None:
                            animating = True
                            anim_start_r = state.r
                            anim_start_c = state.c
                            anim_start_orient = state.orient
                            anim_action = action
                            anim_next_state = ns
                            anim_start_time = pygame.time.get_ticks()
                            buffered_action = None
                    else:
                        if not anim_is_void:
                            elapsed = pygame.time.get_ticks() - anim_start_time
                            if elapsed / ANIM_DURATION_MS > 0.35:
                                buffered_action = action

            # Xử lý click chuột vào nút bấm
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if level_pill_rect.collidepoint(event.pos) or btn_new_game.is_clicked(event):
                    level_modal.open(current_level_path)
                elif btn_restart.is_clicked(event):
                    load_level_and_reset(current_level_path)
                elif won:
                    if btn_win_restart.is_clicked(event):
                        load_level_and_reset(current_level_path)
                    elif btn_win_new_game.is_clicked(event):
                        level_modal.open(current_level_path)
                elif lost:
                    if btn_loss_restart.is_clicked(event):
                        load_level_and_reset(current_level_path)
                    elif btn_loss_new_game.is_clicked(event):
                        level_modal.open(current_level_path)

        # Cập nhật tiến độ Spawn Drop
        if spawning:
            now = pygame.time.get_ticks()
            elapsed = now - spawn_start_time
            if elapsed >= SPAWN_DURATION_MS:
                spawning = False
                z_spawn = 0.0
            else:
                t = elapsed / float(SPAWN_DURATION_MS)
                if t <= 0.78:
                    tf = t / 0.78
                    z_spawn = SPAWN_HEIGHT * (1.0 - tf * tf)
                else:
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
                    falling_void = True
                    fall_start_time = pygame.time.get_ticks()
                    buffered_action = None
                else:
                    state = anim_next_state
                    if game.is_goal(state):
                        falling_goal = True
                        fall_start_time = pygame.time.get_ticks()
                        fall_r = float(state.r)
                        fall_c = float(state.c)
                        fall_orient = state.orient
                        buffered_action = None
                    elif buffered_action is not None:
                        b_act = buffered_action
                        buffered_action = None
                        ns, anim_is_void = _step(state, b_act)
                        if ns is not None:
                            animating = True
                            anim_start_r = state.r
                            anim_start_c = state.c
                            anim_start_orient = state.orient
                            anim_action = b_act
                            anim_next_state = ns
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
                # Cả màn rớt xuống cùng khối (xem draw_scene, nhánh 'void')
                fall_tuple = ('void', anim_start_r, anim_start_c,
                              anim_start_orient, anim_action, t)

        # 1. Vẽ bầu trời và khung cảnh sàn
        draw_sky_with_clouds(screen, *WINDOW_SIZE)
        if spawning:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       spawn_state=(spawn_r, spawn_c, spawn_orient, z_spawn))
        elif animating:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       anim_state=(anim_start_r, anim_start_c, anim_start_orient,
                                   anim_action, anim_progress))
        elif falling_goal or falling_void:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       fall_state=fall_tuple)
        elif not lost:
            # Thua do rơi khỏi sàn: cả màn đã rớt mất, chỉ còn bầu trời phía sau banner GAME OVER
            draw_scene(screen, level, state, tw, th, offset, skew)

        # 2. Vẽ thanh trạng thái (HUD) góc trên-trái
        lvl_lbl = font_hud_lbl.render("LEVEL", True, (138, 90, 50))
        lvl_val = font_hud_val.render(f"{level.name}", True, (185, 28, 28))

        is_lvl_hover = (level_pill_rect.collidepoint(mouse_pos)
                        and not level_modal.is_open)
        lvl_bg = (245, 230, 205, 255) if is_lvl_hover else (254, 250, 235, 235)
        lvl_border = (150, 95, 45, 230) if is_lvl_hover else (180, 130, 85, 180)

        w_lvl = _draw_hud_pill(screen, 24, 20, lvl_lbl, lvl_val,
                               bg_col=lvl_bg, border_col=lvl_border)
        level_pill_rect = pygame.Rect(24, 20, w_lvl, 38)

        mov_lbl = font_hud_lbl.render("MOVES", True, (138, 90, 50))
        mov_val = font_hud_val.render(f"{move_count}", True, (180, 83, 9))
        _draw_hud_pill(screen, 24 + w_lvl + 12, 20, mov_lbl, mov_val)

        # 3. Vẽ nút bấm HUD góc trên-phải
        btn_restart.draw(screen, mouse_pos)
        btn_new_game.draw(screen, mouse_pos)

        # 4. Hướng dẫn phím điều khiển ở đáy màn hình
        hint_str = "Arrow Keys: Move   •   R: Restart   •   ESC: Exit"
        hint_txt = font_hint.render(hint_str, True, (90, 60, 35))
        hw, hh = hint_txt.get_width() + 32, 34
        hx = (WINDOW_SIZE[0] - hw) // 2
        hy = WINDOW_SIZE[1] - 46
        draw_aa_round_rect(screen, (hx, hy, hw, hh), (254, 250, 235, 225),
                           border_radius=12, border_color=(180, 130, 85, 150), border_width=1)
        screen.blit(hint_txt, ((WINDOW_SIZE[0] - hint_txt.get_width()) // 2, WINDOW_SIZE[1] - 38))

        # 5. Banner chiến thắng (YOU WIN!)
        if won:
            draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (250, 254, 250, 250),
                               border_radius=16, border_color=(34, 197, 94), border_width=2)
            msg = font_title.render('YOU WIN!', True, (22, 163, 74))
            sub = font_sub.render(f'Completed in {move_count} moves', True, (21, 128, 61))
            screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
            screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
            btn_win_restart.draw(screen, mouse_pos)
            btn_win_new_game.draw(screen, mouse_pos)

        # 6. Banner thất bại (GAME OVER)
        if lost:
            draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (255, 248, 246, 250),
                               border_radius=16, border_color=(220, 75, 60), border_width=2)
            msg = font_title.render('GAME OVER', True, (185, 28, 28))
            sub = font_sub.render(f'You fell into the void ({move_count} moves)',
                                  True, (110, 65, 55))
            screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
            screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
            btn_loss_restart.draw(screen, mouse_pos)
            btn_loss_new_game.draw(screen, mouse_pos)

        # 7. Vẽ Hộp thoại chọn màn (nếu đang mở)
        if level_modal.is_open:
            level_modal.draw(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(FPS)