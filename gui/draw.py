from typing import Optional, Tuple
import pygame

from game.block import Block
from game.level_loader import Level
from game.state import STAND, State, VERT, cells

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
    draw_void_fall_block,
    draw_void_tip_block,
    generate_shatter_pieces,
)


# Thời gian (giây) để cả màn rớt hết khỏi màn hình; nên bằng FALL_VOID_DURATION_MS / 1000 trong app.py
VOID_FALL_SECONDS = 0.9


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
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')
    is_void = (fall_state is not None and fall_state[0] == 'void')

    # Rơi khỏi sàn: cả màn (sàn + khối) cùng rớt xuống. Quãng rơi tăng theo t^2 và vừa đủ
    # để ra khỏi màn hình lúc kết thúc.
    # Hiệu ứng riêng của khối (so với sàn) tùy vào số ô còn gác trên sàn sau khi lăn hụt:
    # - 'free': khối nằm hoàn toàn ngoài sàn -> lật thêm quanh mép và rơi nhanh hơn sàn.
    # - 'tip' : một ô gác sàn, một ô treo trên hố -> chúi xuống phía hố quanh mép sàn rồi rơi.
    void_mode = 'ride'
    void_floor = []
    void_ordered = False   # True: vẽ khối xen kẽ với các hàng sàn (hàng phía trước che khối)
    split_row = -1
    void_drawn = False
    if is_void:
        _, vr, vc, vorient, vaction, vt = fall_state
        drop_px = int(surface.get_height() * (vt / VOID_FALL_SECONDS) ** 2)
        off = (off[0], off[1] + drop_px)
        rolled = Block(vr, vc, vorient).roll(vaction)
        void_floor = [0 <= rr < level.rows and 0 <= cc < level.cols and level.grid[rr][cc] != '.'
                      for rr, cc in cells(State(rolled.r, rolled.c, rolled.orient))]
        if not any(void_floor):
            void_mode = 'free'
        elif not all(void_floor):
            void_mode = 'tip'
        # Rơi ra mép sau (bấm U): khối nằm sau lưng map, nếu xen kẽ thì sàn che mất nên nhìn không rõ.
        # Vì vậy trường hợp này vẽ khối đè lên sàn (vẽ sau cùng) để thấy rõ nó tụt xuống.
        void_ordered = void_mode == 'tip' or (void_mode == 'free' and vaction != 'U')
        # Khối rơi tự do phải xen kẽ với sàn: các hàng phía trước (gần camera) che khối khi nó rớt xuống.
        split_row = rolled.r + (2 if rolled.orient == VERT else 1) - 1

    def draw_void_block() -> None:
        if void_mode == 'free':
            draw_void_fall_block(surface, vr, vc, vorient, vaction, vt, tw, th, off, skew)
        elif void_mode == 'tip':
            draw_void_tip_block(surface, rolled.r, rolled.c, rolled.orient,
                                not void_floor[0], vt, tw, th, off, skew)
        else:
            draw_animated_block(surface, vr, vc, vorient, vaction, 1.0, tw, th, off, skew)

    if is_void and void_ordered and split_row < 0:
        draw_void_block()
        void_drawn = True

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
        if is_void and void_ordered and not void_drawn and r >= split_row:
            draw_void_block()
            void_drawn = True

    # Hiệu ứng Vỡ Vụn (Shatter): Các mảnh voxel nổ tung văng ra không gian
    if is_shatter:
        _, s_pieces, s_t, s_alpha = fall_state
        draw_shatter_block(surface, s_pieces, s_t, s_alpha, tw, th, off, skew)

    # 3. Rơi vào hố Goal: khối trượt thẳng xuống hố, bị mép hố che dần
    if is_goal:
        _, gr, gc, g_orient, g_alpha = fall_state
        gt = 1.0 - max(0.0, min(255, g_alpha)) / 255.0     # tiến độ 0 -> 1 (app.py truyền alpha 255 -> 0)
        lz = 2 if g_orient == STAND else 1
        ly = 2 if g_orient == VERT else 1
        sink = (lz + 1.0) * gt * gt                        # chìm sâu hơn chiều cao khối để biến mất hẳn
        y_front = off[1] + (gr + ly) * th                  # mép trước của hố: phần khối thấp hơn mép bị che
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(0, 0, surface.get_width(), max(0, y_front)))
        draw_animated_block(surface, gr, gc, g_orient, 'D', 0.0, tw, th, off, skew,
                            drop=(0.0, 0.0, -sink), shadow=False)
        surface.set_clip(old_clip)

    # Các trường hợp còn lại (khối vẽ sau cùng, khối rơi 'free'/'tip' đã vẽ xen kẽ ở trên)
    if is_void and not void_drawn:
        draw_void_block()

    # 4. Khối đang spawn rơi từ trên trời xuống, đang lăn hoặc khối tĩnh
    if spawn_state is not None:
        sr, sc, sorient, sz = spawn_state
        draw_spawn_block(surface, sr, sc, sorient, sz, tw, th, off, skew)
    elif anim_state is not None:
        ar, ac, aorient, aaction, aprogress = anim_state
        draw_animated_block(surface, ar, ac, aorient, aaction, aprogress, tw, th, off, skew)
    elif state is not None and fall_state is None:
        draw_block(surface, state, tw, th, off, skew)