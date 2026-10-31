"""Quản lý hiển thị cây tìm kiếm và đường nghiệm tối ưu (Solution Route)."""
from typing import List, Optional, Set, Tuple
import pygame

from game.game import Game
from game.state import Cell, State, cells
from gui.render_board import _tile_quad
from gui.theme import Theme
from solvers.base import SearchResult

# Thời gian diễn hoạt từng bước vẽ đường đi ở tốc độ 1.0x (ms)
BASE_STEP_ANIM_MS: int = 320

# Bảng màu Dynamic theo từng Theme
THEME_PALETTES = {
    'garden': {'path': (245, 158, 11),  'glow': (186, 230, 253)},
    'sunset': {'path': (6, 182, 212),   'glow': (216, 180, 254)},
    'dusk':   {'path': (250, 204, 21),  'glow': (110, 231, 183)},
    'storm':  {'path': (56, 189, 248),  'glow': (147, 197, 253)},
}
DEFAULT_PALETTE = {'path': (245, 158, 11), 'glow': (186, 230, 253)}


class RouteTracer:
    """Điều khiển diễn hoạt và vẽ vết duyệt cây tìm kiếm cùng đường đi nghiệm."""

    def __init__(self) -> None:
        self.is_visible: bool = False
        self.is_review_mode: bool = False
        self.anim_start_time: int = 0
        self.path_states: List[State] = []
        self.path_cells: Set[Cell] = set()
        self.visited_cells: Set[Cell] = set()
        self._overlay_surf: Optional[pygame.Surface] = None

    def toggle(self, game: Game, result: Optional[SearchResult], now_ms: int,
               current_state: Optional[State] = None) -> bool:
        """Bật/tắt hiển thị đường đi. Trả về trạng thái hiển thị mới."""
        if self.is_visible:
            self.hide()
            return False
        if result and result.solved and result.path:
            self.load(game, result, now_ms, current_state=current_state)
            return True
        return False

    def hide(self) -> None:
        """Ẩn đường đi và xóa dữ liệu diễn hoạt."""
        self.is_visible = False
        self.is_review_mode = False
        self.path_states.clear()
        self.path_cells.clear()
        self.visited_cells.clear()

    def load(self, game: Game, result: SearchResult, now_ms: int,
             current_state: Optional[State] = None) -> None:
        """Nạp dữ liệu nghiệm và cây duyệt để bắt đầu diễn hoạt."""
        self.is_visible = True
        self.anim_start_time = now_ms
        self.visited_cells = {c for s in result.expanded_order for c in cells(s)}

        st = game.initial_state()
        self.path_states = [st]
        self.path_cells = set(cells(st))
        for act in result.path:
            for a, nxt, _ in game.get_successors(st):
                if a == act:
                    st = nxt
                    self.path_states.append(st)
                    self.path_cells.update(cells(st))
                    break

        # Kích hoạt Review toàn cảnh nếu người dùng bấm Path khi khối gỗ đã ở đích
        goal_state = self.path_states[-1] if self.path_states else None
        self.is_review_mode = bool(current_state is not None and current_state == goal_state)

    def draw(self, surface: pygame.Surface, tw: int, th: int,
             off: Tuple[int, int], skew: int, theme: Theme, now_ms: int,
             speed: float = 1.0, active_state: Optional[State] = None) -> None:
        """Vẽ lớp phủ cây tìm kiếm và đường nghiệm tối ưu lên màn hình."""
        if not self.is_visible or not self.path_states:
            return

        w, h = surface.get_size()
        if self._overlay_surf is None or self._overlay_surf.get_size() != (w, h):
            self._overlay_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        else:
            self._overlay_surf.fill((0, 0, 0, 0))

        pal = THEME_PALETTES.get(theme.name.lower(), DEFAULT_PALETTE)
        path_c = pal['path']
        glow_c = pal['glow']

        # 1. Quầng sáng lưới trên mặt sàn các ô đã duyệt
        for r, c in self.visited_cells:
            x = off[0] + c * tw + r * skew
            y = off[1] + r * th
            quad = _tile_quad(x, y, tw, th, skew)
            alpha = 100 if (r, c) not in self.path_cells else 35
            pygame.draw.polygon(self._overlay_surf, (*glow_c, alpha), quad)
            pygame.draw.polygon(self._overlay_surf, (*glow_c, 215), quad, 2)

        def _tile_center(r: int, c: int) -> Tuple[float, float]:
            return (off[0] + (c + 0.5) * tw + (r + 0.5) * skew,
                    off[1] + (r + 0.5) * th)

        # 2. Tọa độ trung tâm từng trạng thái trên đường đi
        centroids: List[Tuple[float, float]] = []
        for st in self.path_states:
            pts = [_tile_center(r, c) for r, c in cells(st)]
            mid = ((pts[0][0] + pts[-1][0]) / 2.0, (pts[0][1] + pts[-1][1]) / 2.0)
            centroids.append(mid)

        num_states = len(self.path_states)
        num_segments = max(0, num_states - 1)

        if self.is_review_mode:
            # CHẾ ĐỘ REVIEW TOÀN CẢNH (KHI BẤM PATH SAU KHI ĐÃ Ở ĐÍCH)
            step_anim_ms = max(50, int(BASE_STEP_ANIM_MS / max(0.1, speed)))
            elapsed = max(0, now_ms - self.anim_start_time)
            progress = elapsed / step_anim_ms if step_anim_ms > 0 else float(num_segments)
            curr_seg = int(progress)

            completed_segs = min(curr_seg, num_segments)
            for i in range(completed_segs):
                p1, p2 = centroids[i], centroids[i + 1]
                pygame.draw.line(self._overlay_surf, (*path_c, 75), p1, p2, 6)
                pygame.draw.line(self._overlay_surf, (*path_c, 255), p1, p2, 3)
                pygame.draw.line(self._overlay_surf, (255, 255, 255, 220), p1, p2, 1)

            if curr_seg < num_segments:
                seg_t = progress - curr_seg
                p1 = centroids[curr_seg]
                p2 = centroids[curr_seg + 1]
                tip = (p1[0] + (p2[0] - p1[0]) * seg_t, p1[1] + (p2[1] - p1[1]) * seg_t)
                pygame.draw.line(self._overlay_surf, (*path_c, 75), p1, tip, 6)
                pygame.draw.line(self._overlay_surf, (*path_c, 255), p1, tip, 3)
                pygame.draw.line(self._overlay_surf, (255, 255, 255, 220), p1, tip, 1)

                tip_int = (int(tip[0]), int(tip[1]))
                pygame.draw.circle(self._overlay_surf, (*path_c, 110), tip_int, 7)
                pygame.draw.circle(self._overlay_surf, (*path_c, 230), tip_int, 4)
                pygame.draw.circle(self._overlay_surf, (255, 255, 255, 255), tip_int, 2)

            vis_footprints = min(num_states, curr_seg + 1)
            for i in range(vis_footprints):
                st = self.path_states[i]
                c_list = [_tile_center(r, c) for r, c in cells(st)]
                is_start = (i == 0)
                is_goal = (i == num_states - 1)

                if len(c_list) == 2:
                    pA, pB = c_list[0], c_list[1]
                    pygame.draw.line(self._overlay_surf, (*path_c, 90), pA, pB, 14)
                    pygame.draw.circle(self._overlay_surf, (*path_c, 90), (int(pA[0]), int(pA[1])), 7)
                    pygame.draw.circle(self._overlay_surf, (*path_c, 90), (int(pB[0]), int(pB[1])), 7)
                    pygame.draw.line(self._overlay_surf, (255, 255, 255, 180), pA, pB, 2)

                for p in c_list:
                    px, py = int(p[0]), int(p[1])
                    if is_start:
                        pygame.draw.circle(self._overlay_surf, (34, 197, 94, 255), (px, py), 6)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, 255), (px, py), 3)
                    elif is_goal:
                        pygame.draw.circle(self._overlay_surf, (239, 68, 68, 255), (px, py), 7)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, 255), (px, py), 3)
                    else:
                        pygame.draw.circle(self._overlay_surf, (15, 23, 42, 220), (px, py), 4)
                        pygame.draw.circle(self._overlay_surf, (*path_c, 255), (px, py), 3)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, 255), (px, py), 1)

            if curr_seg >= num_segments and num_states > 0:
                goal_time = elapsed - num_segments * step_anim_ms
                pulse_phase = (goal_time % 900) / 900.0
                pulse_r = int(7 + pulse_phase * 12)
                pulse_a = max(0, int(220 * (1.0 - pulse_phase)))
                for r, c in cells(self.path_states[-1]):
                    gx, gy = _tile_center(r, c)
                    pygame.draw.circle(self._overlay_surf, (239, 68, 68, pulse_a),
                                       (int(gx), int(gy)), pulse_r, 2)
                    pygame.draw.circle(self._overlay_surf, (255, 255, 255, max(0, pulse_a - 40)),
                                       (int(gx), int(gy)), max(1, pulse_r - 4), 1)

        else:
            # CHẾ ĐỘ SOI ĐƯỜNG 1 BƯỚC (BÁM SÁT THEO KHỐI GỖ)
            cur_idx = 0
            if active_state is not None:
                for idx, st in enumerate(self.path_states):
                    if st == active_state:
                        cur_idx = idx
                        break

            completed_segs = min(cur_idx, num_segments)
            for i in range(completed_segs):
                p1, p2 = centroids[i], centroids[i + 1]
                pygame.draw.line(self._overlay_surf, (*path_c, 75), p1, p2, 6)
                pygame.draw.line(self._overlay_surf, (*path_c, 255), p1, p2, 3)
                pygame.draw.line(self._overlay_surf, (255, 255, 255, 220), p1, p2, 1)

            # Phóng trước đúng 1 bước (chỉ khi chưa ở đích)
            if cur_idx < num_segments:
                p1, p2 = centroids[cur_idx], centroids[cur_idx + 1]
                pygame.draw.line(self._overlay_surf, (*path_c, 75), p1, p2, 6)
                pygame.draw.line(self._overlay_surf, (*path_c, 255), p1, p2, 3)
                pygame.draw.line(self._overlay_surf, (255, 255, 255, 220), p1, p2, 1)

                pulse_phase = ((now_ms // 15) % 60) / 60.0
                spark_r = int(5 + pulse_phase * 6)
                spark_a = max(0, int(220 * (1.0 - pulse_phase)))
                p2_int = (int(p2[0]), int(p2[1]))
                pygame.draw.circle(self._overlay_surf, (*path_c, spark_a), p2_int, spark_r, 2)
                pygame.draw.circle(self._overlay_surf, (*path_c, 220), p2_int, 4)
                pygame.draw.circle(self._overlay_surf, (255, 255, 255, 255), p2_int, 2)

            vis_footprints = min(num_states, cur_idx + 2 if cur_idx < num_segments else num_states)
            for i in range(vis_footprints):
                st = self.path_states[i]
                c_list = [_tile_center(r, c) for r, c in cells(st)]
                is_start = (i == 0)
                is_goal = (i == num_states - 1)
                is_preview = (i == cur_idx + 1 and cur_idx < num_segments)
                alpha_mul = 0.55 if is_preview else 1.0

                if len(c_list) == 2:
                    pA, pB = c_list[0], c_list[1]
                    pygame.draw.line(self._overlay_surf, (*path_c, int(90 * alpha_mul)), pA, pB, 14)
                    pygame.draw.circle(self._overlay_surf, (*path_c, int(90 * alpha_mul)), (int(pA[0]), int(pA[1])), 7)
                    pygame.draw.circle(self._overlay_surf, (*path_c, int(90 * alpha_mul)), (int(pB[0]), int(pB[1])), 7)
                    pygame.draw.line(self._overlay_surf, (255, 255, 255, int(180 * alpha_mul)), pA, pB, 2)

                for p in c_list:
                    px, py = int(p[0]), int(p[1])
                    if is_start:
                        pygame.draw.circle(self._overlay_surf, (34, 197, 94, int(255 * alpha_mul)), (px, py), 6)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, int(255 * alpha_mul)), (px, py), 3)
                    elif is_goal:
                        pygame.draw.circle(self._overlay_surf, (239, 68, 68, int(255 * alpha_mul)), (px, py), 7)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, int(255 * alpha_mul)), (px, py), 3)
                    else:
                        pygame.draw.circle(self._overlay_surf, (15, 23, 42, int(220 * alpha_mul)), (px, py), 4)
                        pygame.draw.circle(self._overlay_surf, (*path_c, int(255 * alpha_mul)), (px, py), 3)
                        pygame.draw.circle(self._overlay_surf, (255, 255, 255, int(255 * alpha_mul)), (px, py), 1)

            # Sóng lan tỏa khi khối gỗ đã ở đích
            if cur_idx >= num_segments and num_states > 0:
                pulse_phase = ((now_ms // 15) % 60) / 60.0
                pulse_r = int(7 + pulse_phase * 12)
                pulse_a = max(0, int(220 * (1.0 - pulse_phase)))
                for r, c in cells(self.path_states[-1]):
                    gx, gy = _tile_center(r, c)
                    pygame.draw.circle(self._overlay_surf, (239, 68, 68, pulse_a), (int(gx), int(gy)), pulse_r, 2)
                    pygame.draw.circle(self._overlay_surf, (255, 255, 255, max(0, pulse_a - 40)),
                                       (int(gx), int(gy)), max(1, pulse_r - 4), 1)

        surface.blit(self._overlay_surf, (0, 0))
