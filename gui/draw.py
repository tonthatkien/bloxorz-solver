from typing import Optional, Tuple
import pygame

from game.level_loader import Level
from game.state import State

# Re-export các module con để giữ khả năng tương thích 100% với code gọi bên ngoài
from gui.sky import draw_sky_with_clouds
from gui.render_board import (
    C,
    TILE_DEPTH,
    grid_to_iso,
    calculate_iso_layout,
    _draw_floor_tile,
    _draw_goal_tile,
)
from gui.render_block import (
    draw_block,
    draw_animated_block,
    draw_spawn_block,
)
from gui.effects import (
    draw_goal_dissolve_block,
    draw_shatter_block,
    generate_shatter_pieces,
)
from gui.draw_cube import (
    draw_active_indicator,
    draw_animated_single_cube,
    draw_single_cube,
    draw_split_cubes,
)


def draw_scene(surface: pygame.Surface,
               level: Level,
               state: Optional[State],
               tw: int, th: int,
               off: Tuple[int, int],
               skew: int,
               anim_state: Optional[tuple] = None,
               fall_state: Optional[tuple] = None,
               spawn_state: Optional[Tuple[int, int, int, float]] = None) -> None:
    """Vẽ toàn bộ khung cảnh: Sàn đảo bay và Khối gỗ / Hai cube tách rời."""
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')

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
        # Nếu là anim lăn khối bình thường (5 phần tử: r, c, orient, action, progress)
        if len(anim_state) == 5:
            ar, ac, aorient, aaction, aprogress = anim_state
            draw_animated_block(surface, ar, ac, aorient, aaction, aprogress, tw, th, off, skew)
        # Nếu là anim split cube (6 phần tử: 'split', active_r, active_c, action, progress, split_tuple)
        elif len(anim_state) == 6 and anim_state[0] == 'split':
            _, ar, ac, aaction, aprogress, sp = anim_state
            draw_split_cubes(
                surface, sp, tw, th, off, skew, anim_info=(ar, ac, aaction, aprogress)
            )
    elif state is not None and fall_state is None:
        if state.split is not None:
            draw_split_cubes(surface, state.split, tw, th, off, skew)
        else:
            draw_block(surface, state, tw, th, off, skew)
