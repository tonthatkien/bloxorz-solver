"""Hộp thoại chọn màn chơi (Level Selector Modal) cho Bloxorz."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import pygame

from game.level_loader import load_level
from gui.base_widgets import Button, draw_aa_round_rect


@dataclass
class LevelInfo:
    """Thông tin tóm tắt của một màn chơi."""
    name: str
    path: str
    rows: int
    cols: int


def discover_levels(levels_dir: str = "levels") -> List[LevelInfo]:
    """Quét thư mục và trả về danh sách các màn chơi hợp lệ."""
    levels: List[LevelInfo] = []
    p = Path(levels_dir)
    if not p.exists() or not p.is_dir():
        return levels

    for file_path in sorted(p.glob("*.json")):
        try:
            lvl = load_level(str(file_path))
            levels.append(LevelInfo(
                name=lvl.name,
                path=str(file_path),
                rows=lvl.rows,
                cols=lvl.cols
            ))
        except Exception:
            levels.append(LevelInfo(
                name=file_path.stem,
                path=str(file_path),
                rows=0,
                cols=0
            ))
    return levels


def get_next_level_path(current_path: str, levels_dir: str = "levels") -> Optional[str]:
    """Lấy đường dẫn màn chơi tiếp theo theo thứ tự danh sách."""
    levels = discover_levels(levels_dir)
    cur_p = Path(current_path).resolve()
    for i, lvl in enumerate(levels):
        if Path(lvl.path).resolve() == cur_p:
            if i + 1 < len(levels):
                return levels[i + 1].path
            break
    return None


class LevelSelectorModal:
    """Hộp thoại nổi (Modal) cho phép người chơi chọn màn chơi mới có thanh cuộn mượt mà."""

    def __init__(self,
                 window_size: Tuple[int, int],
                 font_title: pygame.font.Font,
                 font_item: pygame.font.Font,
                 font_sub: pygame.font.Font) -> None:
        self.window_size = window_size
        self.font_title = font_title
        self.font_item = font_item
        self.font_sub = font_sub

        self.is_open: bool = False
        self.current_path: str = ""
        self.levels: List[LevelInfo] = []
        self.modal_rect = pygame.Rect(0, 0, 540, 480)
        self.modal_rect.center = (window_size[0] // 2, window_size[1] // 2)

        # Nút đóng 'X' ở góc trên-phải của hộp thoại
        cx = self.modal_rect.right - 44
        cy = self.modal_rect.top + 16
        self.btn_close = Button(
            (cx, cy, 30, 30), "X", self.font_item,
            bg_color=(255, 255, 255),
            hover_color=(239, 68, 68),
            border_color=(30, 41, 59),
            border_color_hover=(15, 23, 42),
            text_color=(30, 41, 59),
            text_color_hover=(255, 255, 255),
            border_radius=8, border_width=2,
            shadow_offset=1
        )

        # Vùng cuộn (Viewport)
        view_x = self.modal_rect.x + 24
        view_y = self.modal_rect.top + 72
        view_w = self.modal_rect.w - 48
        view_h = self.modal_rect.h - 92
        self.view_rect = pygame.Rect(view_x, view_y, view_w, view_h)

        # Rãnh thanh cuộn (Track)
        track_w = 6
        track_x = self.modal_rect.right - 18
        track_y = view_y + 2
        track_h = view_h - 4
        self.track_rect = pygame.Rect(track_x, track_y, track_w, track_h)

        # Trạng thái cuộn & kéo
        self.scroll_y: float = 0.0
        self.is_dragging_scrollbar: bool = False
        self.drag_mouse_start_y: int = 0
        self.drag_scroll_start_y: float = 0.0

    @property
    def max_scroll(self) -> int:
        """Độ cuộn tối đa dựa trên tổng chiều cao danh sách màn chơi."""
        item_h, gap = 56, 12
        content_h = len(self.levels) * (item_h + gap) - gap if self.levels else 0
        return max(0, content_h - self.view_rect.h)

    def _get_thumb_rect(self) -> Optional[pygame.Rect]:
        """Tính toán hình chữ nhật con trượt (thumb) của thanh cuộn."""
        if self.max_scroll <= 0:
            return None
        item_h, gap = 56, 12
        content_h = len(self.levels) * (item_h + gap) - gap
        thumb_h = max(36, int(self.track_rect.h * (self.view_rect.h / float(content_h))))
        scroll_ratio = self.scroll_y / float(self.max_scroll)
        thumb_y = self.track_rect.y + int(scroll_ratio * (self.track_rect.h - thumb_h))
        return pygame.Rect(self.track_rect.x, thumb_y, self.track_rect.w, thumb_h)

    def _get_card_rect(self, idx: int) -> pygame.Rect:
        """Lấy hình chữ nhật hiển thị của thẻ màn chơi theo vị trí cuộn."""
        item_h, gap = 56, 12
        card_w = self.view_rect.w - self.track_rect.w - 12
        card_x = self.view_rect.x
        card_y = self.view_rect.y + idx * (item_h + gap) - int(self.scroll_y)
        return pygame.Rect(card_x, card_y, card_w, item_h)

    def open(self, current_path: str) -> None:
        """Mở hộp thoại, quét lại danh sách màn và cuộn tới màn hiện tại."""
        self.current_path = str(Path(current_path).resolve())
        self.levels = discover_levels("levels")
        self.is_open = True
        self.is_dragging_scrollbar = False

        # Tự động cuộn danh sách đến màn đang chơi
        self.scroll_y = 0.0
        active_idx = -1
        for i, lvl in enumerate(self.levels):
            if str(Path(lvl.path).resolve()) == self.current_path:
                active_idx = i
                break
        if active_idx != -1:
            item_h, gap = 56, 12
            target_scroll = active_idx * (item_h + gap) - (self.view_rect.h - item_h) // 2
            self.scroll_y = max(0.0, min(float(self.max_scroll), float(target_scroll)))

    def close(self) -> None:
        """Đóng hộp thoại."""
        self.is_open = False
        self.is_dragging_scrollbar = False

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Xử lý sự kiện bàn phím/chuột khi hộp thoại đang mở."""
        if not self.is_open:
            return None

        # Bấm ESC để đóng
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return None

        # Cuộn bằng con lăn chuột (Mouse Wheel)
        if event.type == pygame.MOUSEWHEEL and self.max_scroll > 0:
            self.scroll_y = max(0.0, min(float(self.max_scroll), self.scroll_y - event.y * 42))
            return None

        # Xử lý nhấn chuột
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Hỗ trợ chuột lăn dạng button 4/5
            if event.button == 4 and self.max_scroll > 0:
                self.scroll_y = max(0.0, min(float(self.max_scroll), self.scroll_y - 42))
                return None
            if event.button == 5 and self.max_scroll > 0:
                self.scroll_y = max(0.0, min(float(self.max_scroll), self.scroll_y + 42))
                return None

            if event.button == 1:
                # Click nút đóng
                if self.btn_close.is_clicked(event):
                    self.close()
                    return None

                # Click ra ngoài vùng modal
                if not self.modal_rect.collidepoint(event.pos):
                    self.close()
                    return None

                # Tương tác thanh cuộn
                if self.max_scroll > 0 and self.track_rect.collidepoint(event.pos):
                    thumb = self._get_thumb_rect()
                    if thumb and thumb.collidepoint(event.pos):
                        self.is_dragging_scrollbar = True
                        self.drag_mouse_start_y = event.pos[1]
                        self.drag_scroll_start_y = self.scroll_y
                    else:
                        # Click trên rãnh -> nhảy cuộn tới vị trí click
                        track_rel = (event.pos[1] - self.track_rect.y) / float(self.track_rect.h)
                        self.scroll_y = max(0.0, min(float(self.max_scroll), track_rel * self.max_scroll))
                        self.is_dragging_scrollbar = True
                        self.drag_mouse_start_y = event.pos[1]
                        self.drag_scroll_start_y = self.scroll_y
                    return None

                # Click vào thẻ màn chơi bên trong viewport
                if self.view_rect.collidepoint(event.pos):
                    for idx, lvl in enumerate(self.levels):
                        rect = self._get_card_rect(idx)
                        if rect.collidepoint(event.pos):
                            self.close()
                            return lvl.path

        # Nhả chuột kết thúc kéo thanh cuộn
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_scrollbar = False

        # Kéo thanh cuộn (Mouse Motion)
        elif event.type == pygame.MOUSEMOTION and self.is_dragging_scrollbar and self.max_scroll > 0:
            dy = event.pos[1] - self.drag_mouse_start_y
            thumb = self._get_thumb_rect()
            thumb_h = thumb.h if thumb else 36
            movable = self.track_rect.h - thumb_h
            if movable > 0:
                delta = (dy / float(movable)) * self.max_scroll
                self.scroll_y = max(0.0, min(float(self.max_scroll), self.drag_scroll_start_y + delta))
            return None

        return None

    def is_any_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có đang hover trên phần tử tương tác nào không."""
        if not self.is_open:
            return False
        if self.btn_close.is_hovered(mouse_pos):
            return True
        if self.max_scroll > 0 and self.track_rect.collidepoint(mouse_pos):
            return True
        if self.view_rect.collidepoint(mouse_pos):
            for idx in range(len(self.levels)):
                rect = self._get_card_rect(idx)
                if rect.collidepoint(mouse_pos):
                    return True
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ lớp phủ mờ tối, hộp thoại chọn màn và thanh cuộn."""
        if not self.is_open:
            return

        # 1. Lớp phủ mờ tối toàn màn hình (Dim overlay)
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 140))
        surface.blit(overlay, (0, 0))

        # 2. Khung hộp thoại chính
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                    self.modal_rect.w, self.modal_rect.h),
                           (255, 255, 255), border_radius=16,
                           border_color=(30, 41, 59), border_width=2,
                           shadow_offset=6, shadow_color=(15, 23, 42, 140))

        # 3. Tiêu đề hộp thoại
        title_surf = self.font_title.render("Select Level", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 24, self.modal_rect.y + 18))

        # Nút đóng
        self.btn_close.draw(surface, mouse_pos)

        # 4. Danh sách các thẻ màn chơi (giới hạn clip trong viewport)
        prev_clip = surface.get_clip()
        surface.set_clip(self.view_rect)

        try:
            for idx, lvl in enumerate(self.levels):
                card_rect = self._get_card_rect(idx)
                # Bỏ qua các thẻ nằm ngoài tầm nhìn viewport
                if card_rect.bottom < self.view_rect.top or card_rect.top > self.view_rect.bottom:
                    continue

                is_active = str(Path(lvl.path).resolve()) == self.current_path
                is_hover = card_rect.collidepoint(mouse_pos) and self.view_rect.collidepoint(mouse_pos)

                if is_active:
                    bg_col = (254, 240, 138)
                    border_col = (15, 23, 42)
                    b_w = 2
                elif is_hover:
                    bg_col = (241, 245, 249)
                    border_col = (15, 23, 42)
                    b_w = 2
                else:
                    bg_col = (255, 255, 255)
                    border_col = (203, 213, 225)
                    b_w = 1

                draw_aa_round_rect(surface, (card_rect.x, card_rect.y, card_rect.w, card_rect.h),
                                   bg_col, border_radius=10,
                                   border_color=border_col, border_width=b_w,
                                   shadow_offset=2 if (is_hover or is_active) else 0)

                # Tên màn chơi
                name_col = (15, 23, 42) if (is_active or is_hover) else (30, 41, 59)
                name_surf = self.font_item.render(lvl.name, True, name_col)
                surface.blit(name_surf, (card_rect.x + 16, card_rect.y + 10))

                # Thông số kích thước lưới (vd: 10x15)
                dim_txt = f"{lvl.rows} x {lvl.cols}" if lvl.rows > 0 else "Custom"
                dim_col = (71, 85, 105) if (is_active or is_hover) else (148, 163, 184)
                dim_surf = self.font_sub.render(dim_txt, True, dim_col)
                surface.blit(dim_surf, (card_rect.x + 16, card_rect.y + 32))

                # Huy hiệu "CURRENT" nếu là màn đang chơi
                if is_active:
                    badge_txt = self.font_sub.render("CURRENT", True, (15, 23, 42))
                    bw = badge_txt.get_width() + 16
                    bh = 24
                    bx = card_rect.right - bw - 14
                    by = card_rect.y + (card_rect.h - bh) // 2
                    draw_aa_round_rect(surface, (bx, by, bw, bh), (253, 224, 71),
                                       border_radius=8, border_color=(15, 23, 42), border_width=1)
                    surface.blit(badge_txt, (bx + 8, by + (bh - badge_txt.get_height()) // 2))

        finally:
            surface.set_clip(prev_clip)

        # 5. Thanh cuộn (Scrollbar)
        if self.max_scroll > 0:
            # Rãnh trượt (Track)
            draw_aa_round_rect(surface, (self.track_rect.x, self.track_rect.y,
                                        self.track_rect.w, self.track_rect.h),
                               (241, 245, 249), border_radius=self.track_rect.w // 2)

            # Con trượt (Thumb)
            thumb = self._get_thumb_rect()
            if thumb:
                is_thumb_hover = thumb.collidepoint(mouse_pos) or self.is_dragging_scrollbar
                thumb_color = (71, 85, 105) if is_thumb_hover else (148, 163, 184)
                draw_aa_round_rect(surface, (thumb.x, thumb.y, thumb.w, thumb.h),
                                   thumb_color, border_radius=thumb.w // 2)
