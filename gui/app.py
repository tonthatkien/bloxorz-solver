"""Main GUI for Bloxorz (Task D1/D2/D4/D5) - Centered Layout with Help Modal."""
import math
import threading
from typing import List, Optional, Tuple
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
    HelpModal,
    LevelSelectorModal,
    draw_aa_round_rect,
)
from solvers import astar, bfs, dfs, ucs
from solvers.base import Limits, SearchResult, run_measured

# Window configuration
WINDOW_SIZE = (1280, 720)
FPS         = 60
BG_COLOR    = (82, 115, 135)

_KEY_MAP = {
    pygame.K_UP:    'U',
    pygame.K_DOWN:  'D',
    pygame.K_LEFT:  'L',
    pygame.K_RIGHT: 'R',
}

SOLVER_MODULES = {
    'BFS': bfs,
    'DFS': dfs,
    'UCS': ucs,
    'A*': astar,
}

# Bottom Dock Geometry
DOCK_W = 868
DOCK_H = 44
DOCK_X = (WINDOW_SIZE[0] - DOCK_W) // 2
DOCK_Y = WINDOW_SIZE[1] - DOCK_H - 18


def _draw_hud_pill(surf: pygame.Surface, x: int, y: int,
                   lbl_s: pygame.Surface, val_s: pygame.Surface,
                   bg_col=(255, 255, 255),
                   border_col=(30, 41, 59)) -> int:
    """Draw a rounded status pill for Level or Moves count."""
    pad_x, gap, h = 16, 8, 38
    w = pad_x * 2 + lbl_s.get_width() + gap + val_s.get_width()
    draw_aa_round_rect(surf, (x, y, w, h), bg_col, border_radius=12,
                       border_color=border_col, border_width=2,
                       shadow_offset=2)

    ly = y + (h - lbl_s.get_height()) // 2
    vy = y + (h - val_s.get_height()) // 2
    surf.blit(lbl_s, (x + pad_x, ly))
    surf.blit(val_s, (x + pad_x + lbl_s.get_width() + gap, vy))
    return w


def _draw_dock_stats(surf: pygame.Surface, x: int, y: int, w: int, h: int,
                     is_solving: bool, solving_name: str,
                     last_solver_name: str, last_result: Optional[SearchResult],
                     font_bold: pygame.font.Font, font_sm: pygame.font.Font) -> None:
    """Draw the solver performance stats inside the bottom dock bar."""
    draw_aa_round_rect(surf, (x, y, w, h), (241, 245, 249),
                       border_radius=8, border_color=(30, 41, 59), border_width=1)

    prev_clip = surf.get_clip()
    surf.set_clip(pygame.Rect(x + 4, y, w - 8, h))

    try:
        if is_solving:
            dots = "." * (((pygame.time.get_ticks() // 280) % 4))
            txt = font_bold.render(f"Solving with {solving_name}{dots}", True, (29, 78, 216))
            tx = x + (w - txt.get_width()) // 2
            ty = y + (h - txt.get_height()) // 2
            surf.blit(txt, (tx, ty))
        elif last_result is not None:
            if last_result.solved:
                tag_surf = font_bold.render(f"[{last_solver_name}]", True, (22, 101, 52))
                t_ms = last_result.time_sec * 1000.0
                time_str = f"{t_ms:.1f}ms" if t_ms < 1000.0 else f"{last_result.time_sec:.2f}s"
                mem_kb = last_result.peak_memory_kb
                mem_str = f"{mem_kb:.0f}KB" if mem_kb < 1024.0 else f"{mem_kb / 1024.0:.1f}MB"
                nodes_str = f"{last_result.expanded_nodes:,} nodes"
                len_str = f"{last_result.length} moves"
                info_str = f"{time_str}   •   {mem_str}   •   {nodes_str}   •   {len_str}"
                info_surf = font_bold.render(info_str, True, (15, 23, 42))

                total_w = tag_surf.get_width() + 10 + info_surf.get_width()
                cur_x = x + max(10, (w - total_w) // 2)
                surf.blit(tag_surf, (cur_x, y + (h - tag_surf.get_height()) // 2))
                ix = cur_x + tag_surf.get_width() + 10
                surf.blit(info_surf, (ix, y + (h - info_surf.get_height()) // 2))
            else:
                tag_surf = font_bold.render(f"[{last_solver_name}]", True, (185, 28, 28))
                note = last_result.note if last_result.note else "No solution"
                msg_surf = font_bold.render(f"No solution ({note})", True, (185, 28, 28))
                total_w = tag_surf.get_width() + 8 + msg_surf.get_width()
                cur_x = x + max(10, (w - total_w) // 2)
                surf.blit(tag_surf, (cur_x, y + (h - tag_surf.get_height()) // 2))
                mx = cur_x + tag_surf.get_width() + 8
                surf.blit(msg_surf, (mx, y + (h - msg_surf.get_height()) // 2))
        else:
            hint_txt = "Select BFS, DFS, UCS or A* to solve level"
            hint_surf = font_sm.render(hint_txt, True, (71, 85, 105))
            tx = x + (w - hint_surf.get_width()) // 2
            ty = y + (h - hint_surf.get_height()) // 2
            surf.blit(hint_surf, (tx, ty))
    finally:
        surf.set_clip(prev_clip)


def run(level_path: str) -> None:
    """Launch the main Pygame GUI loop for Bloxorz."""
    pygame.init()
    pygame.display.set_caption('Bloxorz')
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock  = pygame.time.Clock()

    # Fonts
    sys_fonts = pygame.font.get_fonts()
    font_family = ('trebuchetms' if 'trebuchetms' in sys_fonts
                   else ('verdana' if 'verdana' in sys_fonts else 'arial'))
    font_title   = pygame.font.SysFont(font_family, 44, bold=True)
    font_hud_lbl = pygame.font.SysFont(font_family, 15, bold=True)
    font_hud_val = pygame.font.SysFont(font_family, 20, bold=True)
    font_btn     = pygame.font.SysFont(font_family, 15, bold=True)
    font_dock_b  = pygame.font.SysFont(font_family, 14, bold=True)
    font_dock_sm = pygame.font.SysFont(font_family, 13)
    font_sub     = pygame.font.SysFont(font_family, 18)

    # Core Game & Board Layout (Centered in window)
    current_level_path = level_path
    level: Level = load_level(current_level_path)
    game: Game   = Game(level)
    tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

    state: State = game.initial_state()
    won: bool    = False
    lost: bool   = False
    move_count: int = 0

    # Animation configuration
    ANIM_DURATION_MS = 140
    FALL_GOAL_DURATION_MS = 600
    FALL_VOID_DURATION_MS = 900
    SPAWN_DURATION_MS = 460
    SPAWN_HEIGHT = 8.5
    REPLAY_STEP_DELAY_MS = 70
    REPLAY_SPLIT_PAUSE_MS = 650
    REPLAY_SWAP_PAUSE_MS = 380
    REPLAY_MERGE_PAUSE_MS = 480
    replay_speed = 1.0

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
    anim_is_split = False
    anim_split_tuple: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

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

    # Solver & Replay management
    is_solving = False
    solving_name = ''
    new_result_ready = False
    last_result: Optional[SearchResult] = None
    last_solver_name = ''

    is_replaying = False
    replay_actions: List[str] = []
    replay_index = 0
    replay_last_time = 0

    def _step(cur_state: State, action: str) -> Tuple[Optional[State], bool]:
        """Execute a step via Game Core (game.get_successors)."""
        for act, next_st, _ in game.get_successors(cur_state):
            if act == action:
                return next_st, False

        # Nếu đang ở trạng thái split mà Game Core chưa có successors hoặc đi vào ô cấm
        if cur_state.split is not None:
            return None, False

        # Không nằm trong successors -> khối lăn ra ngoài sàn rơi vực
        rolled = Block(cur_state.r, cur_state.c, cur_state.orient).roll(action)
        phantom_state = State(rolled.r, rolled.c, rolled.orient, cur_state.bridges, None)
        return phantom_state, True

    def load_level_and_reset(path: str) -> None:
        """Load a new level or restart and reset all animation states."""
        nonlocal level, game, current_level_path, tw, th, offset, skew
        nonlocal state, won, lost, move_count, animating
        nonlocal falling_goal, falling_void, buffered_action
        nonlocal fall_shatter_pieces, spawning, spawn_start_time
        nonlocal spawn_r, spawn_c, spawn_orient, z_spawn
        nonlocal is_replaying, last_result, last_solver_name
        nonlocal anim_is_split, anim_split_tuple

        is_replaying = False
        anim_is_split = False
        anim_split_tuple = None
        if path != current_level_path:
            last_result = None
            last_solver_name = ''

        current_level_path = path
        level = load_level(current_level_path)
        game = Game(level)
        tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

        state = game.initial_state()
        won, lost, move_count = False, False, 0
        animating = False
        anim_is_split = False
        anim_split_tuple = None
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

    def _start_solve(name: str) -> None:
        """Start solver on a background thread without freezing the UI."""
        nonlocal is_solving, solving_name, new_result_ready, is_replaying
        nonlocal state, won, lost, move_count, animating, falling_goal, falling_void
        nonlocal buffered_action, fall_shatter_pieces

        if is_solving:
            return

        is_replaying = False

        state = game.initial_state()
        won, lost, move_count = False, False, 0
        animating = False
        falling_goal = False
        falling_void = False
        buffered_action = None
        fall_shatter_pieces = []

        is_solving = True
        solving_name = name
        new_result_ready = False

        def _worker(solver_fn, game_level, s_name):
            nonlocal is_solving, last_result, last_solver_name, new_result_ready
            try:
                solver_game = Game(game_level)
                limits = Limits(max_nodes=2_000_000, timeout_sec=60.0)
                res = run_measured(solver_fn, solver_game, limits=limits, repeats=1)
            except Exception as exc:
                res = SearchResult(solved=False, note=str(exc))
            last_result = res
            last_solver_name = s_name
            is_solving = False
            new_result_ready = True

        solver_mod = SOLVER_MODULES[name]
        thread = threading.Thread(target=_worker, args=(solver_mod.solve, level, name), daemon=True)
        thread.start()

    def _start_replay() -> None:
        """Start animated replay of the solved path."""
        nonlocal is_replaying, replay_actions, replay_index, replay_last_time
        nonlocal state, won, lost, move_count, animating, falling_goal, falling_void
        nonlocal buffered_action

        if not last_result or not last_result.solved or not last_result.path:
            return

        state = game.initial_state()
        won, lost, move_count = False, False, 0
        animating = False
        falling_goal = False
        falling_void = False
        buffered_action = None

        is_replaying = True
        replay_actions = list(last_result.path)
        replay_index = 0
        replay_last_time = pygame.time.get_ticks() + int(200 / replay_speed)

    # Top-right header buttons
    btn_help     = Button((WINDOW_SIZE[0] - 24 - 120 - 12 - 110 - 12 - 40, 20, 40, 38),
                          '?', font_btn, border_radius=12)
    btn_restart  = Button((WINDOW_SIZE[0] - 24 - 120 - 12 - 110, 20, 110, 38),
                          'Restart', font_btn, border_radius=14)
    btn_new_game = Button((WINDOW_SIZE[0] - 24 - 120, 20, 120, 38),
                          'New Game', font_btn, border_radius=14)

    # Bottom Dock buttons (Centered)
    btn_bfs = Button((DOCK_X + 14, DOCK_Y + 6, 52, 32),
                     'BFS', font_dock_b, border_radius=8)
    btn_dfs = Button((DOCK_X + 14 + 58, DOCK_Y + 6, 52, 32),
                     'DFS', font_dock_b, border_radius=8)
    btn_ucs = Button((DOCK_X + 14 + 116, DOCK_Y + 6, 52, 32),
                     'UCS', font_dock_b, border_radius=8)
    btn_astar = Button((DOCK_X + 14 + 174, DOCK_Y + 6, 52, 32),
                       'A*', font_dock_b, border_radius=8)
    btn_action = Button((DOCK_X + 14 + 236, DOCK_Y + 6, 126, 32),
                        'Replay Solution', font_dock_b, border_radius=8, enabled=False)
    btn_speed  = Button((DOCK_X + 14 + 236 + 132, DOCK_Y + 6, 52, 32),
                        '1.0x', font_dock_b, border_radius=8, enabled=True)

    stats_box_x = DOCK_X + 14 + 236 + 132 + 58
    stats_box_w = DOCK_W - (stats_box_x - DOCK_X) - 14

    # Win / Loss Banner Buttons
    banner_w, banner_h = 460, 220
    b_px = (WINDOW_SIZE[0] - banner_w) // 2
    b_py = (WINDOW_SIZE[1] - banner_h) // 2
    btn_win_restart   = Button((b_px + 35, b_py + 145, 180, 44), 'Play Again', font_btn,
                               bg_color=(187, 247, 208), hover_color=(134, 239, 172),
                               border_color=(30, 41, 59), text_color=(20, 83, 45),
                               border_width=2, shadow_offset=2)
    btn_win_new_game  = Button((b_px + 245, b_py + 145, 180, 44), 'New Game', font_btn,
                               bg_color=(187, 247, 208), hover_color=(134, 239, 172),
                               border_color=(30, 41, 59), text_color=(20, 83, 45),
                               border_width=2, shadow_offset=2)
    btn_loss_restart  = Button((b_px + 35, b_py + 145, 180, 44), 'Try Again', font_btn,
                               bg_color=(254, 202, 202), hover_color=(252, 165, 165),
                               border_color=(30, 41, 59), text_color=(153, 27, 27),
                               border_width=2, shadow_offset=2)
    btn_loss_new_game = Button((b_px + 245, b_py + 145, 180, 44), 'New Game', font_btn,
                               bg_color=(254, 202, 202), hover_color=(252, 165, 165),
                               border_color=(30, 41, 59), text_color=(153, 27, 27),
                               border_width=2, shadow_offset=2)

    # Dialog Modals
    level_modal = LevelSelectorModal(WINDOW_SIZE, font_hud_val, font_btn, font_sub)
    help_modal  = HelpModal(WINDOW_SIZE, font_hud_val, font_dock_b, font_btn, font_dock_sm)
    level_pill_rect = pygame.Rect(24, 20, 160, 38)

    while True:
        if new_result_ready:
            new_result_ready = False
            if last_result and last_result.solved and last_result.path:
                _start_replay()

        can_control = (not won and not lost and not falling_goal
                       and not falling_void and not spawning
                       and not level_modal.is_open and not help_modal.is_open
                       and not is_replaying and not is_solving)
        mouse_pos = pygame.mouse.get_pos()

        # Update cursor hover state
        if level_modal.is_open:
            is_hovering = level_modal.is_any_hovered(mouse_pos)
        elif help_modal.is_open:
            is_hovering = help_modal.is_any_hovered(mouse_pos)
        else:
            is_hovering = (
                level_pill_rect.collidepoint(mouse_pos) or
                btn_help.is_hovered(mouse_pos) or
                btn_restart.is_hovered(mouse_pos) or
                btn_new_game.is_hovered(mouse_pos) or
                btn_bfs.is_hovered(mouse_pos) or
                btn_dfs.is_hovered(mouse_pos) or
                btn_ucs.is_hovered(mouse_pos) or
                btn_astar.is_hovered(mouse_pos) or
                btn_action.is_hovered(mouse_pos) or
                btn_speed.is_hovered(mouse_pos) or
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

        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # Priority 1: Help Modal
            if help_modal.is_open:
                help_modal.handle_event(event)
                continue

            # Priority 2: Level Selector Modal
            if level_modal.is_open:
                selected_level = level_modal.handle_event(event)
                if selected_level is not None:
                    load_level_and_reset(selected_level)
                continue

            # Keyboard Events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if event.key == pygame.K_h:
                    help_modal.open()

                elif event.key == pygame.K_r:
                    load_level_and_reset(current_level_path)

                # Bấm phím SPACE để đổi quyền điều khiển khi ở trạng thái tách 2 cube (Task D4)
                elif can_control and event.key == pygame.K_SPACE:
                    if state.split is not None and not animating:
                        c1, c2 = state.split
                        state = State(
                            r=0, c=0, orient=STAND, bridges=state.bridges, split=(c2, c1)
                        )

                elif can_control and event.key in _KEY_MAP:
                    action = _KEY_MAP[event.key]
                    if not animating:
                        ns, anim_is_void = _step(state, action)
                        if ns is not None:
                            animating = True
                            if state.split is not None:
                                anim_is_split = True
                                anim_start_r, anim_start_c = state.split[0]
                                anim_start_orient = STAND
                                anim_split_tuple = state.split
                            else:
                                anim_is_split = False
                                anim_start_r = state.r
                                anim_start_c = state.c
                                anim_start_orient = state.orient
                                anim_split_tuple = None
                            anim_action = action
                            anim_next_state = ns
                            anim_start_time = pygame.time.get_ticks()
                            buffered_action = None
                    else:
                        if not anim_is_void:
                            elapsed = pygame.time.get_ticks() - anim_start_time
                            if elapsed / ANIM_DURATION_MS > 0.35:
                                buffered_action = action

            # Mouse Click Events
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if level_pill_rect.collidepoint(event.pos) or btn_new_game.is_clicked(event):
                    level_modal.open(current_level_path)
                elif btn_help.is_clicked(event):
                    help_modal.open()
                elif btn_restart.is_clicked(event):
                    load_level_and_reset(current_level_path)
                elif btn_bfs.is_clicked(event):
                    _start_solve('BFS')
                elif btn_dfs.is_clicked(event):
                    _start_solve('DFS')
                elif btn_ucs.is_clicked(event):
                    _start_solve('UCS')
                elif btn_astar.is_clicked(event):
                    _start_solve('A*')
                elif btn_action.is_clicked(event):
                    if is_replaying:
                        is_replaying = False
                    else:
                        _start_replay()
                elif btn_speed.is_clicked(event):
                    if replay_speed == 0.5:
                        replay_speed = 1.0
                    elif replay_speed == 1.0:
                        replay_speed = 2.0
                    else:
                        replay_speed = 0.5
                    btn_speed.text = f"{replay_speed}x"
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

        # Replay Progression
        if is_replaying and not animating and not falling_goal and not falling_void and not spawning:
            now = pygame.time.get_ticks()
            if now >= replay_last_time:
                if replay_index < len(replay_actions):
                    act = replay_actions[replay_index]
                    replay_index += 1

                    cur_anim_dur = int(ANIM_DURATION_MS / replay_speed)
                    cur_step_delay = int(REPLAY_STEP_DELAY_MS / replay_speed)

                    if act == 'S':
                        # Hành động Space Swap: đổi cube đang điều khiển tức thì
                        ns, _ = _step(state, 'S')
                        if ns is not None:
                            state = ns
                            move_count += 1
                            anim_is_split = True
                            anim_split_tuple = state.split
                            # Tạm dừng nhẹ để người xem thấy rõ khối active vừa đổi chất liệu
                            replay_last_time = now + int(REPLAY_SWAP_PAUSE_MS / replay_speed)
                    else:
                        ns, anim_is_void = _step(state, act)
                        if ns is not None:
                            animating = True
                            if state.split is not None:
                                anim_is_split = True
                                anim_start_r, anim_start_c = state.split[0]
                                anim_start_orient = STAND
                                anim_split_tuple = state.split
                            else:
                                anim_is_split = False
                                anim_start_r = state.r
                                anim_start_c = state.c
                                anim_start_orient = state.orient
                                anim_split_tuple = None

                            anim_action = act
                            anim_next_state = ns
                            anim_start_time = now
                            buffered_action = None
                            replay_last_time = now + cur_anim_dur + cur_step_delay
                else:
                    is_replaying = False

        # Spawn Animation
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

        # Block Roll Animation
        anim_progress = 0.0
        if animating:
            now = pygame.time.get_ticks()
            cur_anim_dur = int(ANIM_DURATION_MS / (replay_speed if is_replaying else 1.0))
            raw_t = (now - anim_start_time) / cur_anim_dur
            if raw_t >= 1.0:
                animating = False
                move_count += 1

                if anim_is_void:
                    falling_void = True
                    fall_start_time = pygame.time.get_ticks()
                    buffered_action = None
                    is_replaying = False
                else:
                    was_split = (state.split is not None)
                    state = anim_next_state
                    is_split = (state.split is not None)

                    # Dramatic Pause khi phát hiện sự kiện Tách hoặc Ghép trong Replay
                    if is_replaying:
                        if not was_split and is_split:
                            # Vừa đứng lên Split Switch: Tách đôi thành công!
                            replay_last_time = max(
                                replay_last_time,
                                now + int(REPLAY_SPLIT_PAUSE_MS / replay_speed)
                            )
                        elif was_split and not is_split:
                            # Hai cube vừa kề cạnh và tự ghép (Merge) thành khối 1x1x2!
                            replay_last_time = max(
                                replay_last_time,
                                now + int(REPLAY_MERGE_PAUSE_MS / replay_speed)
                            )

                    if game.is_goal(state):
                        falling_goal = True
                        fall_start_time = pygame.time.get_ticks()
                        fall_r = float(state.r)
                        fall_c = float(state.c)
                        fall_orient = state.orient
                        buffered_action = None
                        is_replaying = False
                    elif buffered_action is not None:
                        b_act = buffered_action
                        buffered_action = None
                        ns, anim_is_void = _step(state, b_act)
                        if ns is not None:
                            animating = True
                            if state.split is not None:
                                anim_is_split = True
                                anim_start_r, anim_start_c = state.split[0]
                                anim_start_orient = STAND
                                anim_split_tuple = state.split
                            else:
                                anim_is_split = False
                                anim_start_r = state.r
                                anim_start_c = state.c
                                anim_start_orient = state.orient
                                anim_split_tuple = None
                            anim_action = b_act
                            anim_next_state = ns
                            anim_start_time = pygame.time.get_ticks()
            else:
                anim_progress = _ease(raw_t)

        # Fall Progression
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
                fall_tuple = ('void', anim_start_r, anim_start_c,
                              anim_start_orient, anim_action, t)

        # 1. Draw Sky and Isometric Scene (Centered)
        draw_sky_with_clouds(screen, *WINDOW_SIZE)
        if spawning:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       spawn_state=(spawn_r, spawn_c, spawn_orient, z_spawn),
                       bridge_mask=state.bridges)
        elif animating:
            if anim_is_split and anim_split_tuple is not None:
                anim_tuple = ('split', anim_start_r, anim_start_c, anim_action,
                              anim_progress, anim_split_tuple)
            else:
                anim_tuple = (anim_start_r, anim_start_c, anim_start_orient,
                              anim_action, anim_progress)
            draw_scene(screen, level, None, tw, th, offset, skew,
                       anim_state=anim_tuple, bridge_mask=state.bridges)
        elif falling_goal or falling_void:
            draw_scene(screen, level, None, tw, th, offset, skew,
                       fall_state=fall_tuple, bridge_mask=state.bridges)
        elif not lost:
            draw_scene(screen, level, state, tw, th, offset, skew,
                       bridge_mask=state.bridges)

        # 2. Top-left Status Pills (LEVEL & MOVES)
        lvl_lbl = font_hud_lbl.render('LEVEL', True, (71, 85, 105))
        lvl_val = font_hud_val.render(f'{level.name}', True, (15, 23, 42))

        is_lvl_hover = (level_pill_rect.collidepoint(mouse_pos)
                        and not level_modal.is_open and not help_modal.is_open)
        lvl_bg = (254, 240, 138) if is_lvl_hover else (255, 255, 255)
        lvl_border = (15, 23, 42) if is_lvl_hover else (30, 41, 59)

        w_lvl = _draw_hud_pill(screen, 24, 20, lvl_lbl, lvl_val,
                               bg_col=lvl_bg, border_col=lvl_border)
        level_pill_rect = pygame.Rect(24, 20, w_lvl, 38)

        mov_lbl = font_hud_lbl.render('MOVES', True, (71, 85, 105))
        mov_val = font_hud_val.render(f'{move_count}', True, (217, 119, 6))
        _draw_hud_pill(screen, 24 + w_lvl + 12, 20, mov_lbl, mov_val)

        # 3. Top-right Header Buttons (?, Restart, New Game)
        btn_help.draw(screen, mouse_pos)
        btn_restart.draw(screen, mouse_pos)
        btn_new_game.draw(screen, mouse_pos)

        # 4. Bottom AI Solver Dock Bar (Centered)
        draw_aa_round_rect(screen, (DOCK_X, DOCK_Y, DOCK_W, DOCK_H),
                           (255, 255, 255), border_radius=14,
                           border_color=(30, 41, 59), border_width=2,
                           shadow_offset=3)

        # Solver buttons
        solver_btns = [(btn_bfs, 'BFS'), (btn_dfs, 'DFS'), (btn_ucs, 'UCS'), (btn_astar, 'A*')]
        for btn, s_name in solver_btns:
            btn.enabled = not is_solving
            if is_solving and solving_name == s_name:
                btn.bg_color = (59, 130, 246)
                btn.border_color = (30, 41, 59)
                btn.text_color = (255, 255, 255)
            else:
                btn.bg_color = (248, 250, 252)
                btn.border_color = (30, 41, 59)
                btn.text_color = (30, 41, 59)
            btn.draw(screen, mouse_pos)

        # Replay / Stop Action Button
        if is_replaying:
            btn_action.text = 'Stop Replay'
            btn_action.enabled = True
            btn_action.bg_color = (254, 202, 202)
            btn_action.hover_color = (252, 165, 165)
            btn_action.border_color = (30, 41, 59)
            btn_action.border_color_hover = (15, 23, 42)
            btn_action.text_color = (153, 27, 27)
            btn_action.text_color_hover = (127, 29, 29)
        else:
            btn_action.text = 'Replay Solution'
            can_replay = bool(last_result and last_result.solved
                              and last_result.path and not is_solving)
            btn_action.enabled = can_replay
            btn_action.bg_color = (187, 247, 208)
            btn_action.hover_color = (134, 239, 172)
            btn_action.border_color = (30, 41, 59)
            btn_action.border_color_hover = (15, 23, 42)
            btn_action.text_color = (20, 83, 45)
            btn_action.text_color_hover = (15, 23, 42)
        btn_action.draw(screen, mouse_pos)

        # Speed Button (0.5x, 1.0x, 2.0x)
        if replay_speed == 0.5:
            btn_speed.bg_color = (254, 243, 199)
            btn_speed.text_color = (180, 83, 9)
        elif replay_speed == 2.0:
            btn_speed.bg_color = (224, 231, 255)
            btn_speed.text_color = (67, 56, 202)
        else:
            btn_speed.bg_color = (248, 250, 252)
            btn_speed.text_color = (30, 41, 59)
        btn_speed.text = f"{replay_speed}x"
        btn_speed.draw(screen, mouse_pos)

        # Dock Stats Pill
        _draw_dock_stats(screen, stats_box_x, DOCK_Y + 6, stats_box_w, 32,
                         is_solving, solving_name, last_solver_name, last_result,
                         font_dock_b, font_dock_sm)

        # 5. Victory Banner (YOU WIN!)
        if won:
            draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (255, 255, 255),
                               border_radius=16, border_color=(22, 163, 74), border_width=3,
                               shadow_offset=5)
            msg = font_title.render('YOU WIN!', True, (22, 163, 74))
            sub = font_sub.render(f'Completed in {move_count} moves', True, (20, 83, 45))
            screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
            screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
            btn_win_restart.draw(screen, mouse_pos)
            btn_win_new_game.draw(screen, mouse_pos)

        # 6. Defeat Banner (GAME OVER)
        if lost:
            draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (255, 255, 255),
                               border_radius=16, border_color=(220, 38, 38), border_width=3,
                               shadow_offset=5)
            msg = font_title.render('GAME OVER', True, (220, 38, 38))
            sub = font_sub.render(f'You fell into the void ({move_count} moves)',
                                  True, (51, 65, 85))
            screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
            screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
            btn_loss_restart.draw(screen, mouse_pos)
            btn_loss_new_game.draw(screen, mouse_pos)

        # 7. Modals
        if level_modal.is_open:
            level_modal.draw(screen, mouse_pos)

        if help_modal.is_open:
            help_modal.draw(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(FPS)
