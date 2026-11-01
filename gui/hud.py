"""Các thành phần hiển thị HUD, Dock điều khiển và Banner kết quả cho Bloxorz."""
from typing import Optional, Tuple
import pygame

from gui.base_widgets import Button, draw_aa_round_rect
from solvers.base import SearchResult

WINDOW_SIZE = (1280, 720)

# Bottom Dock Geometry
DOCK_W = 950
DOCK_H = 44
DOCK_X = (WINDOW_SIZE[0] - DOCK_W) // 2
DOCK_Y = WINDOW_SIZE[1] - DOCK_H - 18


def draw_hud_pill(surf: pygame.Surface, x: int, y: int,
                  lbl_s: pygame.Surface, val_s: pygame.Surface,
                  bg_col=(255, 255, 255),
                  border_col=(30, 41, 59)) -> int:
    """Vẽ pill hiển thị thông tin (Level hoặc Moves count)."""
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


def draw_dock_stats(surf: pygame.Surface, x: int, y: int, w: int, h: int,
                    is_solving: bool, solving_name: str,
                    last_solver_name: str, last_result: Optional[SearchResult],
                    font_bold: pygame.font.Font, font_sm: pygame.font.Font) -> None:
    """Vẽ thông số hiệu năng của thuật toán tìm kiếm bên trong thanh dock."""
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

                # Định dạng số node
                nodes = last_result.expanded_nodes
                if nodes >= 1_000_000:
                    nodes_str = f"{nodes / 1_000_000:.2f}M nodes"
                elif nodes >= 100_000:
                    nodes_str = f"{nodes / 1_000:.0f}k nodes"
                elif nodes >= 10_000:
                    nodes_str = f"{nodes / 1_000:.1f}k nodes"
                else:
                    nodes_str = f"{nodes:,} nodes"

                len_str = f"{last_result.length} moves"

                info_str = f"{time_str} • {mem_str} • {nodes_str} • {len_str}"
                render_font = font_bold
                info_surf = render_font.render(info_str, True, (15, 23, 42))
                total_w = tag_surf.get_width() + 8 + info_surf.get_width()

                # Tự động chuyển font_sm nếu dữ liệu quá dài
                if total_w > w - 16:
                    render_font = font_sm
                    info_surf = render_font.render(info_str, True, (15, 23, 42))
                    total_w = tag_surf.get_width() + 8 + info_surf.get_width()

                cur_x = x + max(8, (w - total_w) // 2)
                surf.blit(tag_surf, (cur_x, y + (h - tag_surf.get_height()) // 2))
                ix = cur_x + tag_surf.get_width() + 8
                surf.blit(info_surf, (ix, y + (h - info_surf.get_height()) // 2))
            else:
                tag_surf = font_bold.render(f"[{last_solver_name}]", True, (185, 28, 28))
                note = last_result.note if last_result.note else "No solution"
                msg_surf = font_bold.render(f"No solution ({note})", True, (185, 28, 28))
                total_w = tag_surf.get_width() + 8 + msg_surf.get_width()
                if total_w > w - 16:
                    msg_surf = font_sm.render(f"No solution ({note})", True, (185, 28, 28))
                    total_w = tag_surf.get_width() + 8 + msg_surf.get_width()
                cur_x = x + max(8, (w - total_w) // 2)
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


def draw_hud_status(screen: pygame.Surface, level_name: str, move_count: int,
                    is_lvl_hover: bool,
                    font_hud_lbl: pygame.font.Font,
                    font_hud_val: pygame.font.Font) -> pygame.Rect:
    """Vẽ 2 pill trạng thái ở góc trên bên trái: LEVEL và MOVES."""
    lvl_lbl = font_hud_lbl.render('LEVEL', True, (71, 85, 105))
    lvl_val = font_hud_val.render(f'{level_name}', True, (15, 23, 42))

    lvl_bg = (254, 240, 138) if is_lvl_hover else (255, 255, 255)
    lvl_border = (15, 23, 42) if is_lvl_hover else (30, 41, 59)

    w_lvl = draw_hud_pill(screen, 24, 20, lvl_lbl, lvl_val,
                          bg_col=lvl_bg, border_col=lvl_border)

    mov_lbl = font_hud_lbl.render('MOVES', True, (71, 85, 105))
    mov_val = font_hud_val.render(f'{move_count}', True, (217, 119, 6))
    draw_hud_pill(screen, 24 + w_lvl + 12, 20, mov_lbl, mov_val)

    return pygame.Rect(24, 20, w_lvl, 38)


def draw_dock_bar(screen: pygame.Surface, mouse_pos: Tuple[int, int],
                  is_solving: bool, solving_name: str,
                  last_solver_name: str, last_result: Optional[SearchResult],
                  is_replaying: bool, replay_speed: float,
                  btn_bfs: Button, btn_dfs: Button, btn_ucs: Button, btn_astar: Button,
                  btn_action: Button, btn_speed: Button,
                  stats_box_x: int, stats_box_w: int,
                  font_dock_b: pygame.font.Font, font_dock_sm: pygame.font.Font,
                  btn_path: Optional[Button] = None, is_path_visible: bool = False) -> None:
    """Vẽ thanh dock điều khiển giải thuật toán và replay ở cạnh dưới màn hình."""
    # Nền Dock
    draw_aa_round_rect(screen, (DOCK_X, DOCK_Y, DOCK_W, DOCK_H),
                       (255, 255, 255), border_radius=14,
                       border_color=(30, 41, 59), border_width=2,
                       shadow_offset=3)

    # Các nút chọn thuật toán
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

    # Nút Replay / Stop
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

    # Nút tốc độ Speed (0.5x, 1.0x, 1.5x, 2.0x)
    if replay_speed == 0.5:
        btn_speed.bg_color = (254, 243, 199)
        btn_speed.text_color = (180, 83, 9)
    elif replay_speed == 2.0:
        btn_speed.bg_color = (224, 231, 255)
        btn_speed.text_color = (67, 56, 202)
    elif replay_speed == 1.5:
        btn_speed.bg_color = (220, 252, 231)
        btn_speed.text_color = (22, 101, 52)
    else:
        btn_speed.bg_color = (248, 250, 252)
        btn_speed.text_color = (30, 41, 59)
    btn_speed.text = f"{replay_speed}x"
    btn_speed.draw(screen, mouse_pos)

    # Nút Path / Hide Path
    if btn_path is not None:
        can_path = not is_solving and bool(last_result and last_result.solved)
        btn_path.enabled = can_path
        if is_path_visible and can_path:
            btn_path.text = 'Hide Path'
            btn_path.bg_color = (254, 240, 138)
            btn_path.hover_color = (253, 224, 71)
            btn_path.border_color = (180, 83, 9)
            btn_path.text_color = (133, 77, 14)
        else:
            btn_path.text = 'Path'
            btn_path.bg_color = (248, 250, 252)
            btn_path.hover_color = (226, 232, 240)
            btn_path.border_color = (30, 41, 59)
            btn_path.text_color = (30, 41, 59)
        btn_path.draw(screen, mouse_pos)

    # Hộp hiển thị thống kê
    draw_dock_stats(screen, stats_box_x, DOCK_Y + 6, stats_box_w, 32,
                    is_solving, solving_name, last_solver_name, last_result,
                    font_dock_b, font_dock_sm)


def draw_win_banner(screen: pygame.Surface, mouse_pos: Tuple[int, int],
                    b_px: int, b_py: int, banner_w: int, banner_h: int,
                    move_count: int,
                    font_title: pygame.font.Font, font_sub: pygame.font.Font,
                    btn_restart: Button, btn_new_game: Button,
                    btn_next: Optional[Button] = None) -> None:
    """Vẽ banner chiến thắng khi hoàn thành màn chơi."""
    draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (255, 255, 255),
                       border_radius=16, border_color=(22, 163, 74), border_width=3,
                       shadow_offset=5)
    msg = font_title.render('YOU WIN!', True, (22, 163, 74))
    sub = font_sub.render(f'Completed in {move_count} moves', True, (20, 83, 45))
    screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
    screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
    btn_restart.draw(screen, mouse_pos)
    btn_new_game.draw(screen, mouse_pos)
    if btn_next is not None:
        btn_next.draw(screen, mouse_pos)


def draw_loss_banner(screen: pygame.Surface, mouse_pos: Tuple[int, int],
                     b_px: int, b_py: int, banner_w: int, banner_h: int,
                     move_count: int,
                     font_title: pygame.font.Font, font_sub: pygame.font.Font,
                     btn_restart: Button, btn_new_game: Button) -> None:
    """Vẽ banner thất bại khi khối lăn rơi vào khoảng không."""
    draw_aa_round_rect(screen, (b_px, b_py, banner_w, banner_h), (255, 255, 255),
                       border_radius=16, border_color=(220, 38, 38), border_width=3,
                       shadow_offset=5)
    msg = font_title.render('GAME OVER', True, (220, 38, 38))
    sub = font_sub.render(f'You fell into the void ({move_count} moves)', True, (51, 65, 85))
    screen.blit(msg, (b_px + (banner_w - msg.get_width()) // 2, b_py + 24))
    screen.blit(sub, (b_px + (banner_w - sub.get_width()) // 2, b_py + 88))
    btn_restart.draw(screen, mouse_pos)
    btn_new_game.draw(screen, mouse_pos)
