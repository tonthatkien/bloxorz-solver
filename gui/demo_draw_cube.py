"""Kịch bản kiểm thử độc lập cho Task D4 (Vẽ 2 cube khi tách & phím Space).

Chạy trực tiếp:
    python gui/demo_draw_cube.py

Tính năng trải nghiệm:
- Hiển thị 2 cube tách rời: Active (Gỗ Vàng Sáng) vs Inactive (Đá Xám Tro).
- Tam giác ngược nhấp nhô lơ lửng trên đỉnh cube active.
- Phong cách 3 (Minimalist Pure): Thuần khiết như Bloxorz nguyên bản.
- Phím SPACE: Đổi tức thì cube active (con đá thức tỉnh thành gỗ, con gỗ hóa đá).
- Phím Mũi Tên: Lăn cube active 90 độ mượt mà.
- Di chuyển 2 cube lại sát cạnh nhau: Tự động hút nam châm và ghép lại thành khối 1x1x2.
- Phím R: Đặt lại trạng thái tách 2 cube để thử lại.
"""
import math
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Thêm thư mục gốc của project vào sys.path để chạy trực tiếp không bị ModuleNotFoundError
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game.level_loader import Level
from game.state import HORIZ, STAND, State, VERT
from gui.draw import (
    calculate_iso_layout,
    draw_block,
    draw_sky_with_clouds,
    grid_to_iso,
    _draw_floor_tile,
    _draw_goal_tile,
)
from gui.draw_cube import draw_split_cubes
from gui.widgets import draw_aa_round_rect

WINDOW_SIZE = (1280, 720)
FPS = 60
ANIM_DURATION_MS = 140
MERGE_DURATION_MS = 100

_KEY_MAP = {
    pygame.K_UP: 'U',
    pygame.K_DOWN: 'D',
    pygame.K_LEFT: 'L',
    pygame.K_RIGHT: 'R',
}

_DIR_OFFSETS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}




def _create_demo_level() -> Level:
    """Tạo một bản đồ sàn đảo bay rộng rãi để test thoải mái."""
    grid = [
        "..........",
        "..######..",
        "..######..",
        "..######..",
        "..######..",
        "..######..",
        "....##G...",
        "..........",
    ]
    return Level(
        name="D4 Demo Split",
        grid=grid,
        start=(3, 3),
        goal=(6, 6),
        fragile=set(),
        bridges={},
        switches={},
    )


def run_demo() -> None:
    """Vòng lặp chính của demo D4."""
    pygame.init()
    pygame.display.set_caption("Bloxorz - D4 Split Cubes Demo")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    font_sys = pygame.font.SysFont("trebuchetms", 15, bold=True)
    font_hint = pygame.font.SysFont("trebuchetms", 15)
    font_val = pygame.font.SysFont("trebuchetms", 20, bold=True)

    level = _create_demo_level()
    tw, th, offset, skew = calculate_iso_layout(level.rows, level.cols, *WINDOW_SIZE)

    # Khởi tạo 2 cube tách rời ở 2 vị trí khác nhau
    initial_split: Tuple[Tuple[int, int], Tuple[int, int]] = ((3, 3), (3, 6))
    state = State(r=0, c=0, orient=STAND, bridges=0, split=initial_split)

    move_count = 0
    animating = False
    anim_start_r = 0
    anim_start_c = 0
    anim_action = 'D'
    anim_start_time = 0
    anim_next_state: Optional[State] = None

    merging = False
    merge_start_time = 0
    merged_final_state: Optional[State] = None
    merging_split: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

    def _ease(t: float) -> float:
        return t * t * (3.0 - 2.0 * t)

    def _step_cube(cur_state: State, action: str) -> Optional[State]:
        """Tính toán bước di chuyển tiếp theo cho cube active."""
        if cur_state.split is None:
            return None
        c_act, c_inact = cur_state.split
        dr, dc = _DIR_OFFSETS[action]
        nr, nc = c_act[0] + dr, c_act[1] + dc

        # Giới hạn trong sàn hợp lệ
        if not (0 <= nr < level.rows and 0 <= nc < level.cols):
            return None
        if level.grid[nr][nc] == '.':
            return None
        if (nr, nc) == c_inact:
            return None  # Không thể đè lên cube đang đứng

        # Kiểm tra kề cạnh để tự ghép lại (Merge)
        dist_r = abs(nr - c_inact[0])
        dist_c = abs(nc - c_inact[1])
        if dist_r + dist_c == 1:
            if dist_r == 0:  # Cùng hàng, cạnh cột -> Khối nằm ngang
                min_c = min(nc, c_inact[1])
                return State(r=nr, c=min_c, orient=HORIZ, bridges=cur_state.bridges, split=None)
            else:  # Cùng cột, cạnh hàng -> Khối đứng dọc
                min_r = min(nr, c_inact[0])
                return State(r=min_r, c=nc, orient=VERT, bridges=cur_state.bridges, split=None)

        return State(r=0, c=0, orient=STAND, bridges=cur_state.bridges, split=((nr, nc), c_inact))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)

                if event.key == pygame.K_r:
                    state = State(r=0, c=0, orient=STAND, bridges=0, split=initial_split)
                    animating, merging = False, False
                    move_count = 0

                # Bấm phím SPACE: Hoán đổi tức thì quyền điều khiển
                elif event.key == pygame.K_SPACE:
                    if state.split is not None and not animating and not merging:
                        c1, c2 = state.split
                        state = State(
                            r=0, c=0, orient=STAND, bridges=state.bridges, split=(c2, c1)
                        )

                # Bấm phím Mũi Tên: Di chuyển cube active
                elif event.key in _KEY_MAP and not animating and not merging:
                    action = _KEY_MAP[event.key]
                    if state.split is not None:
                        ns = _step_cube(state, action)
                        if ns is not None:
                            animating = True
                            anim_start_r, anim_start_c = state.split[0]
                            anim_action = action
                            anim_start_time = pygame.time.get_ticks()
                            anim_next_state = ns

        # Cập nhật animation lăn của cube active
        anim_progress = 0.0
        if animating:
            now = pygame.time.get_ticks()
            raw_t = (now - anim_start_time) / ANIM_DURATION_MS
            if raw_t >= 1.0:
                animating = False
                move_count += 1
                # Kiểm tra nếu bước vừa rồi dẫn đến tự ghép (Merge)
                if anim_next_state.split is None:
                    merging = True
                    merge_start_time = pygame.time.get_ticks()
                    merged_final_state = anim_next_state
                    dr, dc = _DIR_OFFSETS[anim_action]
                    c_act_new = (anim_start_r + dr, anim_start_c + dc)
                    merging_split = (c_act_new, state.split[1])
                else:
                    state = anim_next_state
            else:
                anim_progress = _ease(raw_t)

        # Cập nhật animation hút nam châm khi Merge
        merge_progress = 0.0
        if merging:
            now = pygame.time.get_ticks()
            raw_m = (now - merge_start_time) / MERGE_DURATION_MS
            if raw_m >= 1.0:
                merging = False
                state = merged_final_state
            else:
                merge_progress = _ease(raw_m)

        # 1. Vẽ bầu trời và sàn đảo bay
        draw_sky_with_clouds(screen, *WINDOW_SIZE)
        for r in range(level.rows):
            for c in range(level.cols):
                ch = level.grid[r][c]
                if ch == '.':
                    continue
                x, y = grid_to_iso(r, c, tw, th, offset, skew)
                if ch == 'G':
                    _draw_goal_tile(screen, level, r, c, x, y, tw, th, skew)
                else:
                    _draw_floor_tile(screen, level, r, c, x, y, tw, th, skew)

        # 2. Vẽ khối gỗ hoặc 2 cube
        if merging and merging_split is not None:
            draw_split_cubes(
                screen, merging_split, tw, th, offset, skew,
                merge_progress=merge_progress
            )
        elif state.split is not None:
            anim_info = (
                (anim_start_r, anim_start_c, anim_action, anim_progress)
                if animating else None
            )
            draw_split_cubes(
                screen, state.split, tw, th, offset, skew, anim_info=anim_info
            )
        else:
            draw_block(screen, state, tw, th, offset, skew)

        # 3. Vẽ HUD thông tin
        # Pill Level
        lvl_lbl = font_sys.render("LEVEL", True, (138, 90, 50))
        lvl_val = font_val.render(f"{level.name}", True, (185, 28, 28))
        draw_aa_round_rect(screen, (24, 20, 190, 38), (254, 250, 235, 235),
                           border_radius=14, border_color=(180, 130, 85, 180), border_width=2)
        screen.blit(lvl_lbl, (40, 31))
        screen.blit(lvl_val, (95, 27))

        # Pill Moves
        mov_lbl = font_sys.render("MOVES", True, (138, 90, 50))
        mov_val = font_val.render(f"{move_count}", True, (180, 83, 9))
        draw_aa_round_rect(screen, (226, 20, 130, 38), (254, 250, 235, 235),
                           border_radius=14, border_color=(180, 130, 85, 180), border_width=2)
        screen.blit(mov_lbl, (242, 31))
        screen.blit(mov_val, (300, 27))

        # Pill Status (Hiển thị quy ước màu tối giản)
        st_lbl = font_sys.render("ACTIVE CUBE", True, (138, 90, 50))
        if state.split is not None:
            st_val_str = "Wood (Golden)"
            st_val_col = (180, 83, 9)
        else:
            st_val_str = "Merged (1x1x2)"
            st_val_col = (22, 101, 52)
        st_val = font_val.render(st_val_str, True, st_val_col)
        pill_w = st_val.get_width() + 145
        draw_aa_round_rect(screen, (368, 20, pill_w, 38), (254, 250, 235, 235),
                           border_radius=14, border_color=(180, 130, 85, 180), border_width=2)
        screen.blit(st_lbl, (382, 31))
        screen.blit(st_val, (490, 27))

        # 4. Vẽ thanh Hint điều khiển ở đáy màn hình
        if state.split is not None:
            hint_str = "Arrows: Move Active Cube   •   SPACE: Switch Active Cube (Wood <-> Stone)   •   R: Reset   •   ESC: Exit"
        else:
            hint_str = "Cubes Merged!   •   Arrows: Move   •   R: Reset Cubes   •   ESC: Exit"

        hint_txt = font_hint.render(hint_str, True, (90, 60, 35))
        hw, hh = hint_txt.get_width() + 36, 34
        hx = (WINDOW_SIZE[0] - hw) // 2
        hy = WINDOW_SIZE[1] - 46
        draw_aa_round_rect(screen, (hx, hy, hw, hh), (254, 250, 235, 230),
                           border_radius=12, border_color=(180, 130, 85, 150), border_width=1)
        screen.blit(hint_txt, (hx + 18, hy + 8))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    run_demo()
