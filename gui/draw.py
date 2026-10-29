from typing import Optional, Tuple
import pygame

from game.level_loader import Level
from game.state import State
from gui.draw_tiles import draw_bridge_tile, draw_fragile_tile, draw_switch, terrain_view

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


def draw_scene(surface: pygame.Surface,
               level: Level,
               state: Optional[State],
               tw: int, th: int,
               off: Tuple[int, int],
               skew: int,
               anim_state: Optional[Tuple[int, int, int, str, float]] = None,
               fall_state: Optional[tuple] = None,
               spawn_state: Optional[Tuple[int, int, int, float]] = None,
               *, bridge_mask: Optional[int] = None) -> None:
    """Vẽ địa hình trước khối và các hiệu ứng D1.

    Truyền bridge_mask runtime khi state=None trong animation hoặc khi ẩn khối.
    Nếu không có snapshot, khung cảnh ban đầu dùng mask được khai báo trong level.
    """
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')

    # Giữ mask runtime cả khi khối được vẽ riêng trong animation (state=None).
    if bridge_mask is None:
        bridge_mask = state.bridges if state is not None else level.initial_bridge_mask()
    terrain = terrain_view(level, bridge_mask)
    bridge_positions = {bridge.pos for bridge in level.bridges.values()}

    # Vẽ từng hàng sàn theo trục Y (từ sau ra trước)
    for r in range(level.rows):
        for c in range(level.cols):
            ch = terrain.grid[r][c]
            if ch == '.':
                continue

            x, y = grid_to_iso(r, c, tw, th, off, skew)
            if (r, c) in level.fragile:
                draw_fragile_tile(surface, terrain, r, c, x, y, tw, th, skew)
            elif (r, c) in bridge_positions:
                draw_bridge_tile(surface, terrain, r, c, x, y, tw, th, skew)
            elif ch == 'G':
                _draw_goal_tile(surface, terrain, r, c, x, y, tw, th, skew)
            else:
                _draw_floor_tile(surface, terrain, r, c, x, y, tw, th, skew)
            switch = level.switches.get((r, c))
            if switch is not None:
                draw_switch(surface, switch.type, x, y, tw, th, skew)

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
