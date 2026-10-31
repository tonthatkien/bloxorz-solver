"""GUI chính của Bloxorz."""
from typing import Optional, Tuple
import pygame

from game.block import Block
from game.game import Game
from game.level_loader import Level, load_level
from game.state import STAND, State
from gui.animator import (
    ANIM_DURATION_MS, REPLAY_MERGE_PAUSE_MS, REPLAY_SPLIT_PAUSE_MS,
    REPLAY_STEP_DELAY_MS, REPLAY_SWAP_PAUSE_MS, AnimationManager, ease_roll,
)
from gui.draw import calculate_iso_layout, draw_scene, draw_sky_with_clouds
from gui.help_modal import HelpModal
from gui.hud import (
    DOCK_W, DOCK_X, DOCK_Y, draw_dock_bar, draw_hud_status, draw_loss_banner, draw_win_banner,
)
from gui.intro import IntroScreen
from gui.level_modal import LevelSelectorModal, get_next_level_path
from gui.solver_runner import SolverManager
from gui.theme import get_theme
from gui.transition import SPAWN_DELAY_MS, ScreenFader
from gui.widgets import Button

# Cấu hình cửa sổ
WINDOW_SIZE, FPS = (1280, 720), 60
_KEY_MAP = {pygame.K_UP: 'U', pygame.K_DOWN: 'D', pygame.K_LEFT: 'L', pygame.K_RIGHT: 'R'}


def _step(game: Game, cur_state: State, action: str) -> Tuple[Optional[State], bool]:
    """Thực hiện một bước đi thông qua Game Core."""
    for act, next_st, _ in game.get_successors(cur_state):
        if act == action:
            return next_st, False
    if action == 'S':
        return None, False
    if cur_state.split is not None:
        c1, c2 = cur_state.split
        dr, dc = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}.get(action, (0, 0))
        target_cell = (c1[0] + dr, c1[1] + dc)
        if target_cell == c2:
            return None, False
        return State(0, 0, STAND, cur_state.bridges, (target_cell, c2)), True

    rolled = Block(cur_state.r, cur_state.c, cur_state.orient).roll(action)
    return State(rolled.r, rolled.c, rolled.orient, cur_state.bridges, None), True


def run(level_path: str) -> None:
    """Khởi chạy vòng lặp giao diện Pygame cho Bloxorz."""
    pygame.init()
    pygame.display.set_caption('Bloxorz')
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock  = pygame.time.Clock()

    # Phông chữ
    sys_fonts = pygame.font.get_fonts()
    fam = 'trebuchetms' if 'trebuchetms' in sys_fonts else ('verdana' if 'verdana' in sys_fonts else 'arial')
    font_title, font_sub = pygame.font.SysFont(fam, 44, bold=True), pygame.font.SysFont(fam, 18)
    font_hud_lbl, font_btn = pygame.font.SysFont(fam, 15, bold=True), pygame.font.SysFont(fam, 15, bold=True)
    font_hud_val, font_dock_b = pygame.font.SysFont(fam, 20, bold=True), pygame.font.SysFont(fam, 14, bold=True)
    font_dock_sm = pygame.font.SysFont(fam, 13)

    # Game Core và bố cục isometric
    current_level_path = level_path
    level: Level = load_level(current_level_path)
    game: Game   = Game(level)
    tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

    state: State = game.initial_state()
    won, lost, move_count = False, False, 0

    # Quản lý hoạt ảnh, luồng giải, màn hình mở đầu và chuyển cảnh
    anim = AnimationManager()
    solver_mgr = SolverManager()
    intro = IntroScreen(WINDOW_SIZE, current_level_path)
    fader = ScreenFader(WINDOW_SIZE)
    showing_intro = True

    def load_level_and_reset(path: str, delay_ms: int = 0) -> None:
        """Tải màn chơi và thiết lập lại trạng thái."""
        nonlocal level, game, current_level_path, tw, th, offset, skew, state, won, lost, move_count
        solver_mgr.reset(reset_result=(path != current_level_path))
        current_level_path = path
        level = load_level(current_level_path)
        game = Game(level)
        tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)
        state, won, lost, move_count = game.initial_state(), False, False, 0
        anim.reset_for_level(pygame.time.get_ticks(), delay_ms=delay_ms)

    def _enter_game() -> None:
        nonlocal showing_intro
        showing_intro = False
        (load_level_and_reset(intro.selected_level_path, delay_ms=SPAWN_DELAY_MS)
         if intro.selected_level_path != current_level_path
         else anim.reset_for_level(pygame.time.get_ticks(), delay_ms=SPAWN_DELAY_MS))

    def _return_to_intro() -> None:
        nonlocal showing_intro
        intro.open(current_level_path)
        showing_intro = True

    def _reset_play_state() -> None:
        nonlocal state, won, lost, move_count
        state, won, lost, move_count = game.initial_state(), False, False, 0
        anim.reset_for_level(pygame.time.get_ticks())
        anim.spawning, anim.z_spawn = False, 0.0

    def _start_solve(name: str) -> None:
        """Chạy thuật toán tìm kiếm trên luồng nền."""
        if not solver_mgr.is_solving:
            _reset_play_state()
            solver_mgr.start_solve(name, level)

    def _start_replay() -> None:
        """Phát lại lời giải tìm được."""
        if solver_mgr.start_replay():
            _reset_play_state()

    # Nút thanh tiêu đề
    rx = WINDOW_SIZE[0] - 24
    btn_new_game = Button((rx - 120, 20, 120, 38), 'New Game', font_btn, border_radius=14)
    btn_restart = Button((rx - 242, 20, 110, 38), 'Restart', font_btn, border_radius=14)
    btn_help = Button((rx - 294, 20, 40, 38), '?', font_btn, border_radius=12)
    btn_home = Button((rx - 346, 20, 40, 38), '', font_btn, border_radius=12, icon='home')

    # Nút thanh dock
    btn_bfs = Button((DOCK_X + 14, DOCK_Y + 6, 52, 32), 'BFS', font_dock_b, border_radius=8)
    btn_dfs = Button((DOCK_X + 72, DOCK_Y + 6, 52, 32), 'DFS', font_dock_b, border_radius=8)
    btn_ucs = Button((DOCK_X + 130, DOCK_Y + 6, 52, 32), 'UCS', font_dock_b, border_radius=8)
    btn_astar = Button((DOCK_X + 188, DOCK_Y + 6, 52, 32), 'A*', font_dock_b, border_radius=8)
    btn_action = Button((DOCK_X + 250, DOCK_Y + 6, 126, 32), 'Replay Solution', font_dock_b, border_radius=8, enabled=False)
    btn_speed = Button((DOCK_X + 382, DOCK_Y + 6, 52, 32), '1.0x', font_dock_b, border_radius=8, enabled=True)
    dock_algo_btns = [(btn_bfs, 'BFS'), (btn_dfs, 'DFS'), (btn_ucs, 'UCS'), (btn_astar, 'A*')]
    stats_box_x = DOCK_X + 440
    stats_box_w = DOCK_W - (stats_box_x - DOCK_X) - 14

    # Nút banner thắng/thua
    banner_w, banner_h = 480, 220
    b_px, b_py = (WINDOW_SIZE[0] - banner_w) // 2, (WINDOW_SIZE[1] - banner_h) // 2
    b_kw = dict(border_color=(30, 41, 59), border_width=2, shadow_offset=2)
    win_kw = dict(bg_color=(187, 247, 208), hover_color=(134, 239, 172), text_color=(20, 83, 45), **b_kw)
    loss_kw = dict(bg_color=(254, 202, 202), hover_color=(252, 165, 165), text_color=(153, 27, 27), **b_kw)
    btn_win_restart  = Button((b_px + 20, b_py + 145, 130, 44), 'Play Again', font_btn, **win_kw)
    btn_win_new_game = Button((b_px + 165, b_py + 145, 130, 44), 'Levels', font_btn, **win_kw)
    btn_win_next     = Button((b_px + 310, b_py + 145, 150, 44), 'Next Level', font_btn, **win_kw)
    btn_loss_restart = Button((b_px + 45, b_py + 145, 180, 44), 'Try Again', font_btn, **loss_kw)
    btn_loss_new_game = Button((b_px + 255, b_py + 145, 180, 44), 'New Game', font_btn, **loss_kw)

    level_modal = LevelSelectorModal(WINDOW_SIZE, font_hud_val, font_btn, font_sub)
    help_modal  = HelpModal(WINDOW_SIZE, font_hud_val, font_dock_b, font_btn, font_dock_sm)
    level_pill_rect = pygame.Rect(24, 20, 160, 38)

    while True:
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # Kiểm tra kết quả luồng giải
        if solver_mgr.poll_queue():
            _start_replay()

        can_control = (not showing_intro and not won and not lost and not anim.falling_goal
                       and not anim.falling_void and not anim.spawning and not fader.is_fading
                       and not level_modal.is_open and not help_modal.is_open
                       and not solver_mgr.is_replaying and not solver_mgr.is_solving)

        # Cập nhật con trỏ chuột
        is_hovering = (
            intro.is_any_hovered(mouse_pos) if showing_intro else
            level_modal.is_any_hovered(mouse_pos) if level_modal.is_open else
            help_modal.is_any_hovered(mouse_pos) if help_modal.is_open else
            (level_pill_rect.collidepoint(mouse_pos) or
             any(b.is_hovered(mouse_pos) for b in (btn_home, btn_help, btn_restart, btn_new_game, btn_action, btn_speed)) or
             any(b.is_hovered(mouse_pos) for b, _ in dock_algo_btns) or
             (won and (btn_win_restart.is_hovered(mouse_pos) or btn_win_new_game.is_hovered(mouse_pos) or btn_win_next.is_hovered(mouse_pos))) or
             (lost and (btn_loss_restart.is_hovered(mouse_pos) or btn_loss_new_game.is_hovered(mouse_pos))))
        )
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if is_hovering else pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return

            if fader.is_fading:
                continue

            # Sự kiện màn hình mở đầu
            if showing_intro:
                action = intro.handle_event(event)
                if action == 'play':
                    fader.start(now, _enter_game)
                elif action == 'quit':
                    pygame.quit()
                    return
                continue

            if help_modal.is_open:
                help_modal.handle_event(event)
                continue

            if level_modal.is_open:
                selected_level = level_modal.handle_event(event)
                if selected_level is not None:
                    fader.start(now, lambda lvl=selected_level: load_level_and_reset(lvl, delay_ms=SPAWN_DELAY_MS))
                continue

            if event.type == pygame.KEYDOWN:
                if won and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    nxt = get_next_level_path(current_level_path)
                    (fader.start(now, lambda p=nxt: load_level_and_reset(p, delay_ms=SPAWN_DELAY_MS))
                     if nxt else level_modal.open(current_level_path))
                elif event.key == pygame.K_h:
                    help_modal.open()
                elif event.key == pygame.K_r:
                    load_level_and_reset(current_level_path)
                elif can_control and event.key == pygame.K_SPACE and not anim.animating:
                    ns, _ = _step(game, state, 'S')
                    if ns is not None:
                        state = ns
                elif can_control and event.key in _KEY_MAP:
                    action = _KEY_MAP[event.key]
                    if not anim.animating:
                        ns, is_void = _step(game, state, action)
                        if ns is not None:
                            anim.start_roll(state, action, ns, is_void, now)
                    elif not anim.anim_is_void:
                        elapsed = now - anim.anim_start_time
                        if elapsed / ANIM_DURATION_MS > 0.35:
                            anim.buffered_action = action

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if level_pill_rect.collidepoint(event.pos) or btn_new_game.is_clicked(event):
                    level_modal.open(current_level_path)
                elif btn_home.is_clicked(event):
                    if solver_mgr.is_replaying:
                        solver_mgr.stop_replay()
                    fader.start(now, _return_to_intro)
                elif btn_help.is_clicked(event):
                    help_modal.open()
                elif btn_restart.is_clicked(event):
                    load_level_and_reset(current_level_path)
                elif btn_action.is_clicked(event):
                    if solver_mgr.is_replaying:
                        solver_mgr.stop_replay()
                    else:
                        _start_replay()
                elif btn_speed.is_clicked(event):
                    new_sp = solver_mgr.cycle_speed()
                    btn_speed.text = f"{new_sp}x"
                elif won and btn_win_next.is_clicked(event):
                    nxt = get_next_level_path(current_level_path)
                    (fader.start(now, lambda p=nxt: load_level_and_reset(p, delay_ms=SPAWN_DELAY_MS))
                     if nxt else level_modal.open(current_level_path))
                elif (won and btn_win_restart.is_clicked(event)) or (lost and btn_loss_restart.is_clicked(event)):
                    load_level_and_reset(current_level_path)
                elif (won and btn_win_new_game.is_clicked(event)) or (lost and btn_loss_new_game.is_clicked(event)):
                    level_modal.open(current_level_path)
                else:
                    for b, algo in dock_algo_btns:
                        if b.is_clicked(event):
                            _start_solve(algo)
                            break

        # Vẽ màn hình mở đầu
        if showing_intro:
            intro.draw(screen, mouse_pos, now)
            fader.update(now)
            fader.draw(screen, now)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # Replay lời giải
        if (solver_mgr.is_replaying and not anim.animating and not anim.falling_goal
                and not anim.falling_void and not anim.spawning):
            can_step = (now >= solver_mgr.replay_last_time)
            act = solver_mgr.get_next_replay_action(now, can_step)
            if act is not None:
                cur_anim_dur = int(ANIM_DURATION_MS / solver_mgr.replay_speed)
                cur_step_delay = int(REPLAY_STEP_DELAY_MS / solver_mgr.replay_speed)
                if act == 'S':
                    ns, _ = _step(game, state, 'S')
                    if ns is not None:
                        state = ns
                        anim.anim_is_split = True
                        anim.anim_split_tuple = state.split
                        solver_mgr.replay_last_time = now + int(REPLAY_SWAP_PAUSE_MS / solver_mgr.replay_speed)
                else:
                    ns, is_void = _step(game, state, act)
                    if ns is not None:
                        anim.start_roll(state, act, ns, is_void, now)
                        solver_mgr.replay_last_time = now + cur_anim_dur + cur_step_delay

        # Hoạt ảnh khối xuất hiện
        anim.update_spawn(now)

        # Hoạt ảnh lăn khối
        if anim.animating:
            cur_speed = solver_mgr.replay_speed if solver_mgr.is_replaying else 1.0
            cur_anim_dur = int(ANIM_DURATION_MS / cur_speed)
            raw_t = (now - anim.anim_start_time) / cur_anim_dur
            if raw_t >= 1.0:
                anim.animating = False
                move_count += 1
                if anim.anim_is_void:
                    anim.start_fall_void(now)
                    solver_mgr.stop_replay()
                else:
                    was_split = (state.split is not None)
                    state = anim.anim_next_state
                    is_split = (state.split is not None)
                    if solver_mgr.is_replaying:
                        if not was_split and is_split:
                            solver_mgr.replay_last_time = max(
                                solver_mgr.replay_last_time,
                                now + int(REPLAY_SPLIT_PAUSE_MS / solver_mgr.replay_speed)
                            )
                        elif was_split and not is_split:
                            solver_mgr.replay_last_time = max(
                                solver_mgr.replay_last_time,
                                now + int(REPLAY_MERGE_PAUSE_MS / solver_mgr.replay_speed)
                            )

                    if game.is_goal(state):
                        anim.start_fall_goal(state, now)
                        solver_mgr.stop_replay()
                    elif anim.buffered_action is not None:
                        b_act = anim.buffered_action
                        anim.buffered_action = None
                        ns, is_void = _step(game, state, b_act)
                        if ns is not None:
                            anim.start_roll(state, b_act, ns, is_void, now)
            else:
                anim.anim_progress = ease_roll(raw_t)

        # Tiến trình rơi
        fall_tuple, goal_event, void_event = anim.get_fall_tuple(now)
        if goal_event:
            won = True
        elif void_event:
            lost = True

        # Vẽ khung cảnh
        current_theme = get_theme(level.name)
        draw_sky_with_clouds(screen, *WINDOW_SIZE, theme=current_theme)

        sc_kw = dict(bridge_mask=state.bridges, theme=current_theme)
        if anim.spawning:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       spawn_state=(state.r, state.c, state.orient, anim.z_spawn), **sc_kw)
        elif anim.animating:
            draw_scene(screen, level, None, tw, th, offset, skew, anim_state=anim.get_anim_tuple(), **sc_kw)
        elif anim.falling_goal or anim.falling_void:
            draw_scene(screen, level, None, tw, th, offset, skew, fall_state=fall_tuple, **sc_kw)
        elif not lost:
            draw_scene(screen, level, state, tw, th, offset, skew, **sc_kw)

        # Vẽ giao diện và HUD
        is_lvl_hover = (level_pill_rect.collidepoint(mouse_pos)
                        and not level_modal.is_open and not help_modal.is_open)
        level_pill_rect = draw_hud_status(screen, level.name, move_count, is_lvl_hover,
                                          font_hud_lbl, font_hud_val)

        for b in (btn_home, btn_help, btn_restart, btn_new_game):
            b.draw(screen, mouse_pos)

        draw_dock_bar(screen, mouse_pos,
                      solver_mgr.is_solving, solver_mgr.solving_name,
                      solver_mgr.last_solver_name, solver_mgr.last_result,
                      solver_mgr.is_replaying, solver_mgr.replay_speed,
                      btn_bfs, btn_dfs, btn_ucs, btn_astar,
                      btn_action, btn_speed,
                      stats_box_x, stats_box_w,
                      font_dock_b, font_dock_sm)

        if won:
            draw_win_banner(screen, mouse_pos, b_px, b_py, banner_w, banner_h,
                            move_count, font_title, font_sub,
                            btn_win_restart, btn_win_new_game, btn_win_next)
        if lost:
            draw_loss_banner(screen, mouse_pos, b_px, b_py, banner_w, banner_h,
                             move_count, font_title, font_sub,
                             btn_loss_restart, btn_loss_new_game)

        if level_modal.is_open:
            level_modal.draw(screen, mouse_pos)
        if help_modal.is_open:
            help_modal.draw(screen, mouse_pos)

        fader.update(now)
        fader.draw(screen, now)
        pygame.display.flip()
        clock.tick(FPS)
