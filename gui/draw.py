from typing import Optional, Tuple
import pygame

from game.level_loader import Level
from game.state import State

# Re-export các module con để giữ khả năng tương thích 100% với code gọi bên ngoài
from gui.sky import draw_sky_with_clouds
from gui.board import (
    C,
    TILE_DEPTH,
    grid_to_iso,
    calculate_iso_layout,
    _draw_floor_tile,
    _draw_goal_tile,
)
from gui.block import (
    draw_block,
    draw_animated_block,
    draw_spawn_block,
)
from gui.effects import (
    draw_goal_dissolve_block,
    draw_void_fall_block,
    draw_shatter_block,
    generate_shatter_pieces,
)


def draw_scene(surface: pygame.Surface,
               level: Level,
               state: Optional[State],
               tw: int, th: int,
               off: Tuple[int, int],
               skew: int,
               anim_state: Optional[Tuple[int, int, int, str, float]] = None,
               fall_state: Optional[tuple] = None,
               spawn_state: Optional[Tuple[int, int, int, float]] = None) -> None:
    """Vẽ toàn bộ khung cảnh: Sàn đảo bay và Khối gỗ (tĩnh, lăn animation, rơi xuất phát, vỡ vụn hoặc mờ dần)."""
    is_void = (fall_state is not None and fall_state[0] == 'void')
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')

    # Xếp lớp chiều sâu khi khối rơi vực:
    if is_void:
        _, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc, v_scale, v_alpha = fall_state
        ly = 1 if v_orient != VERT else 2
        cut_row = vr + ly - 1

    # Vẽ từng hàng sàn theo trục Y (từ sau ra trước)
    for r in range(level.rows):
        for c in range(level.cols):
            ch = level.grid[r][c]
            if ch == '.':
                continue

            x, y = grid_to_iso(r, c, tw, th, off, skew)
            if ch == 'G':
                _draw_goal_tile(surface, level, r, c, x, y, tw, th, skew)
            else:
                _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)

        # Chèn khối rơi void cũ sau khi đã vẽ xong hàng cut_row
        if is_void and r == cut_row and v_alpha > 0:
            draw_void_fall_block(surface, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc,
                                 tw, th, off, skew, scale=v_scale, alpha=v_alpha)

    # Nếu rơi ở hàng cuối cùng của đảo, vẽ khối sau khi vẽ toàn bộ sàn
    if is_void and cut_row >= level.rows and v_alpha > 0:
        draw_void_fall_block(surface, vr, vc, v_orient, v_act, v_angle, v_dz, v_dr, v_dc,
                             tw, th, off, skew, scale=v_scale, alpha=v_alpha)

    # Hiệu ứng Vỡ Vụn (Shatter): Các mảnh voxel nổ tung văng ra không gian
    if is_shatter:
        _, s_pieces, s_t, s_alpha = fall_state
        draw_shatter_block(surface, s_pieces, s_t, s_alpha, tw, th, off, skew)

    # 3. Rơi vào hố Goal: Khối mờ dần tự nhiên, đứng nguyên tại ô
    if is_goal:
        _, gr, gc, g_orient, g_alpha = fall_state
        draw_goal_dissolve_block(surface, gr, gc, g_orient, g_alpha, tw, th, off, skew)

    # 4. Khối đang spawn rơi từ trên trời xuống, đang lăn hoặc khối tĩnh
    if spawn_state is not None:
        sr, sc, sorient, sz = spawn_state
        draw_spawn_block(surface, sr, sc, sorient, sz, tw, th, off, skew)
    elif anim_state is not None:
        ar, ac, aorient, aaction, aprogress = anim_state
        draw_animated_block(surface, ar, ac, aorient, aaction, aprogress, tw, th, off, skew)
    elif state is not None and fall_state is None:
        draw_block(surface, state, tw, th, off, skew)
