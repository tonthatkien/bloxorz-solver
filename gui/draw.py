import math
from typing import Optional, Tuple
import pygame

from game.block import Block
from game.level_loader import Level
from game.state import HORIZ, STAND, State, VERT, cells
from gui.draw_tiles import (
    draw_bridge_tile,
    draw_fragile_tile,
    draw_shattering_fragile_tile,
    draw_switch,
    terrain_view,
)

# Re-export các module con để giữ khả năng tương thích 100% với code gọi bên ngoài
from gui.sky import draw_sky_with_clouds
from gui.render_board import (
    C,
    TILE_DEPTH,
    grid_to_iso,
    calculate_iso_layout,
    _draw_floor_tile,
    _draw_goal_tile,
    _tile_quad,
    _draw_goal_garland,
)
from gui.render_block import (
    draw_block,
    draw_animated_block,
    draw_spawn_block,
)
from gui.effects import (
    VOID_FALL_GRAVITY,
    draw_goal_dissolve_block,
    draw_shatter_block,
    draw_void_fall_block,
    draw_void_tip_block,
    generate_shatter_pieces,
)
from gui.draw_cube import (
    draw_active_indicator,
    draw_animated_single_cube,
    draw_single_cube,
    draw_split_cubes,
)


# Thời gian (giây) để cả màn rớt hết khỏi màn hình;
# nên bằng FALL_VOID_DURATION_MS / 1000 trong app.py
VOID_FALL_SECONDS = 0.9


def draw_scene(surface: pygame.Surface,
               level: Level,
               state: Optional[State],
               tw: int, th: int,
               off: Tuple[int, int],
               skew: int,
               anim_state: Optional[tuple] = None,
               fall_state: Optional[tuple] = None,
               spawn_state: Optional[Tuple[int, int, int, float]] = None,
               *, bridge_mask: Optional[int] = None) -> None:
    """Vẽ địa hình trước khối và các hiệu ứng D1.

    Truyền bridge_mask runtime khi state=None trong animation hoặc khi ẩn khối.
    Nếu không có snapshot, khung cảnh ban đầu dùng mask được khai báo trong level.
    """
    is_shatter = (fall_state is not None and fall_state[0] == 'shatter')
    is_goal = (fall_state is not None and fall_state[0] == 'goal')
    is_void = (fall_state is not None and fall_state[0] == 'void')
    is_void_split = (fall_state is not None and fall_state[0] == 'void_split')

    scr_h = surface.get_height()

    # Giữ mask runtime cả khi khối được vẽ riêng trong animation (state=None).
    if bridge_mask is None:
        bridge_mask = state.bridges if state is not None else level.initial_bridge_mask()
    terrain = terrain_view(level, bridge_mask)
    bridge_positions = {bridge.pos for bridge in level.bridges.values()}

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
    center_r, center_c = 0.0, 0.0
    is_fragile_fall = False
    if is_void_split:
        _, vr, vc, vaction, vt, sp = fall_state
        c1, c2 = sp
        dr, dc = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}.get(vaction, (0, 0))
        target_r, target_c = c1[0] + dr, c1[1] + dc
        center_r, center_c = target_r + 0.5, target_c + 0.5
        split_row = target_r
        void_ordered = True
        is_void = True

        if vt < 0.20:
            decay = 1.0 - vt / 0.20
            shake_x = int(round(2.0 * decay * math.sin(vt * 40.0)))
            shake_y = int(round(1.5 * decay * math.cos(vt * 30.0)))
            off = (off[0] + shake_x, off[1] + shake_y)
    elif is_void:
        _, vr, vc, vorient, vaction, vt = fall_state
        rolled = Block(vr, vc, vorient).roll(vaction)
        is_fragile_fall = (rolled.orient == STAND and (rolled.r, rolled.c) in level.fragile)
        # Tâm chấn chấn động tại vị trí khối lăn hụt (hoặc vị trí ô sàn dễ vỡ)
        center_r = rolled.r + (1.0 if rolled.orient == VERT else 0.5)
        center_c = rolled.c + (1.0 if rolled.orient == HORIZ else 0.5)
        # Dùng terrain (theo mask cầu) để cầu đóng được coi là ô trống, giống luật game.
        void_floor = [
            0 <= rr < level.rows and 0 <= cc < level.cols and terrain.grid[rr][cc] != '.'
            for rr, cc in cells(State(rolled.r, rolled.c, rolled.orient))
        ]
        if not any(void_floor):
            void_mode = 'free'
        elif not all(void_floor):
            void_mode = 'tip'
        # Rơi ra mép sau (U): khối nằm sau map, vẽ sau cùng để thấy rõ nó tụt xuống.
        void_ordered = (
            void_mode == 'tip' or void_mode == 'ride'
            or (void_mode == 'free' and vaction != 'U')
        )
        # Khối rơi tự do xen kẽ với sàn: các hàng phía trước che khối khi rớt xuống.
        split_row = rolled.r + (2 if rolled.orient == VERT else 1) - 1
        if is_fragile_fall:
            split_row = rolled.r - 1

        # Rung nhẹ màn hình khi sụp sàn
        if vt < 0.20:
            decay = 1.0 - vt / 0.20
            shake_x = int(round(2.0 * decay * math.sin(vt * 40.0)))
            shake_y = int(round(1.5 * decay * math.cos(vt * 30.0)))
            off = (off[0] + shake_x, off[1] + shake_y)

    def draw_void_block() -> None:
        if is_void_split:
            drop_z = -0.5 * VOID_FALL_GRAVITY * vt * vt
            dist2 = math.hypot(c2[0] - center_r, c2[1] - center_c)
            t_eff2 = vt - max(0.0, dist2 * 0.045)
            drop_y2 = int(scr_h * (t_eff2 / 0.45) ** 2) if t_eff2 > 0 else 0
            off_inact = (off[0], off[1] + drop_y2)

            depth_act = target_r * 1000 + target_c
            depth_inact = c2[0] * 1000 + c2[1]

            def _draw_act():
                draw_single_cube(surface, target_r, target_c, True, tw, th, off, skew,
                                 drop_z=drop_z, shadow=False)

            def _draw_inact():
                draw_single_cube(surface, c2[0], c2[1], False, tw, th, off_inact, skew,
                                 shadow=(drop_y2 == 0))

            if depth_act < depth_inact:
                _draw_act()
                _draw_inact()
            else:
                _draw_inact()
                _draw_act()
        elif void_mode == 'free':
            draw_void_fall_block(surface, vr, vc, vorient, vaction, vt, tw, th, off, skew)
        elif void_mode == 'tip':
            draw_void_tip_block(surface, rolled.r, rolled.c, rolled.orient,
                                not void_floor[0], vt, tw, th, off, skew)
        else:
            # void_mode == 'ride' (ví dụ đứng lên ô dễ vỡ): rơi thẳng đứng xuyên qua sàn
            drop = (0.0, 0.0, -0.5 * 38.0 * vt * vt)
            draw_animated_block(surface, rolled.r, rolled.c, rolled.orient, 'D', 0.0,
                                tw, th, off, skew, drop=drop, shadow=False)

    if is_void and void_ordered and split_row < 0:
        draw_void_block()
        void_drawn = True

    # Vẽ từng hàng sàn theo trục Y (từ sau ra trước)
    for r in range(level.rows):
        for c in range(level.cols):
            ch = terrain.grid[r][c]
            if ch == '.':
                continue

            orig_x, orig_y = grid_to_iso(r, c, tw, th, off, skew)
            x, y = orig_x, orig_y
            if is_void:
                # Ô dễ vỡ nứt tách thành nhiều mảnh và sụp xuống tại tâm chấn
                if is_fragile_fall and (r, c) == (rolled.r, rolled.c):
                    draw_shattering_fragile_tile(surface, orig_x, orig_y, tw, th, skew, vt)
                    continue
                # Tính khoảng cách từ ô (r, c) tới tâm chấn
                dist = math.hypot(r - center_r, c - center_c)
                # Jitter giả ngẫu nhiên cố định theo tọa độ để mép vỡ so le tự nhiên
                jitter = (((r * 37 + c * 19) % 11) / 11.0 - 0.5) * 0.08
                delay = max(0.0, dist * 0.045 + jitter)
                t_eff = vt - delay
                if t_eff > 0:
                    # Ô sàn rơi gia tốc tự do: sau ~0.45s rơi khỏi màn hình
                    tile_drop_y = int(scr_h * (t_eff / 0.45) ** 2)
                    y += tile_drop_y
                    if dist > 0.1:
                        # Tản nhẹ sang hai bên theo hướng lan truyền sóng
                        drift_x = (t_eff / 0.45) * 14.0
                        x += int(((c - center_c) / dist) * drift_x)
                    if y > scr_h + 120:
                        continue

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
        if is_void and void_ordered and not void_drawn and r >= split_row:
            draw_void_block()
            void_drawn = True

    # Vẽ vòng hoa quanh miệng hố đích sau khi toàn bộ địa hình sàn đã hoàn tất
    # (Đảm bảo vòng hoa luôn trọn vẹn 100% không bao giờ bị các ô hàng trước che mất)
    for gr in range(level.rows):
        for gc in range(level.cols):
            if terrain.grid[gr][gc] == 'G':
                gx, gy = grid_to_iso(gr, gc, tw, th, off, skew)
                _draw_goal_garland(surface, _tile_quad(gx, gy, tw, th, skew), tw, th)

    # Hiệu ứng Vỡ Vụn (Shatter): Các mảnh voxel nổ tung văng ra không gian
    if is_shatter:
        _, s_pieces, s_t, s_alpha = fall_state
        draw_shatter_block(surface, s_pieces, s_t, s_alpha, tw, th, off, skew)

    # 3. Rơi vào hố Goal: Khối chìm dần xuống hố và tan biến hoàn hảo
    if is_goal:
        _, gr, gc, g_orient, g_alpha = fall_state
        gt = 1.0 - max(0.0, min(255, g_alpha)) / 255.0     # tiến độ 0 -> 1
        lz = 2 if g_orient == STAND else 1
        sink = (lz + 0.1) * (gt ** 1.3)
        h = max(0.0, lz - sink)
        eff_alpha = int(255 * min(1.0, h / 0.25))
        draw_goal_dissolve_block(surface, gr, gc, g_orient, eff_alpha, tw, th, off, skew, sink=sink)
    # Các trường hợp còn lại (khối vẽ sau cùng, khối rơi 'free'/'tip' đã vẽ xen kẽ ở trên)
    if is_void and not void_drawn:
        draw_void_block()

    # 4. Khối đang spawn rơi từ trên trời xuống, đang lăn hoặc khối tĩnh
    if spawn_state is not None:
        sr, sc, sorient, sz = spawn_state
        draw_spawn_block(surface, sr, sc, sorient, sz, tw, th, off, skew)
    elif anim_state is not None:
        # Nếu là anim lăn khối bình thường (5 phần tử: r, c, orient, action, progress)
        if len(anim_state) == 5:
            ar, ac, aorient, aaction, aprogress = anim_state
            draw_animated_block(
                surface, ar, ac, aorient, aaction, aprogress, tw, th, off, skew
            )
        # Nếu là anim split cube (6 phần tử: 'split', active_r, active_c, action, progress, sp)
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
