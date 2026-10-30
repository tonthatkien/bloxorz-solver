"""Các thành phần giao diện (UI widgets) cho Bloxorz: Nút bấm và Hộp thoại chọn màn."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import pygame

from game.level_loader import load_level


def draw_aa_round_rect(surface: pygame.Surface,
                       rect: Tuple[int, int, int, int],
                       color: Tuple[int, ...],
                       border_radius: int = 0,
                       border_color: Optional[Tuple[int, ...]] = None,
                       border_width: int = 1,
                       shadow_offset: int = 0,
                       shadow_color: Optional[Tuple[int, ...]] = (15, 23, 42, 110)) -> None:
    """Vẽ hình chữ nhật bo góc sắc nét chuẩn 1:1 pixel kèm đổ bóng xúc giác (Solid Arcade)."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return

    # 1. Đổ bóng xúc giác nếu có yêu cầu (Solid Arcade drop shadow)
    if shadow_offset > 0 and shadow_color:
        s_rect = (x, y + shadow_offset, w, h)
        if len(shadow_color) == 4 and shadow_color[3] < 255:
            s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s_surf, shadow_color, (0, 0, w, h), border_radius=border_radius)
            surface.blit(s_surf, (x, y + shadow_offset))
        else:
            pygame.draw.rect(surface, shadow_color, s_rect, border_radius=border_radius)

    # 2. Vẽ hình chữ nhật chính (1:1 không smoothscale -> nét phẳng lỳ, không vỡ pixel)
    if len(color) == 4 and color[3] < 255:
        sub = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sub, color, (0, 0, w, h), border_radius=border_radius)
        if border_color and border_width > 0:
            pygame.draw.rect(sub, border_color, (0, 0, w, h),
                             width=border_width, border_radius=border_radius)
        surface.blit(sub, (x, y))
    else:
        pygame.draw.rect(surface, color, (x, y, w, h), border_radius=border_radius)
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, (x, y, w, h),
                             width=border_width, border_radius=border_radius)


class Button:
    """Nút bấm phong cách Neo-Brutalism/Arcade: viền đậm dứt khoát và bóng đổ nổi khối."""

    def __init__(self,
                 rect: Tuple[int, int, int, int],
                 text: str,
                 font: pygame.font.Font,
                 bg_color: Tuple[int, ...] = (255, 255, 255),
                 hover_color: Tuple[int, ...] = (254, 240, 138),
                 border_color: Optional[Tuple[int, ...]] = (30, 41, 59),
                 border_color_hover: Optional[Tuple[int, ...]] = (15, 23, 42),
                 text_color: Tuple[int, ...] = (30, 41, 59),
                 text_color_hover: Tuple[int, ...] = (15, 23, 42),
                 border_radius: int = 10,
                 border_width: int = 2,
                 enabled: bool = True,
                 shadow_offset: int = 2) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_color_hover = border_color_hover
        self.text_color = text_color
        self.text_color_hover = text_color_hover
        self.border_radius = border_radius
        self.border_width = border_width
        self.enabled = enabled
        self.shadow_offset = shadow_offset

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có đang rê qua nút không."""
        return self.enabled and self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Kiểm tra sự kiện click chuột trái vào nút."""
        if self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ nút lên bề mặt với hiệu ứng viền đậm và bóng nổi khối."""
        if not self.enabled:
            bg = (241, 245, 249)
            border = (148, 163, 184)
            txt_color = (148, 163, 184)
            draw_aa_round_rect(surface, (self.rect.x, self.rect.y, self.rect.w, self.rect.h),
                               bg, border_radius=self.border_radius,
                               border_color=border, border_width=self.border_width,
                               shadow_offset=0)
        else:
            hover = self.is_hovered(mouse_pos)
            bg = self.hover_color if hover else self.bg_color
            border = self.border_color_hover if hover else self.border_color
            txt_color = self.text_color_hover if hover else self.text_color
            draw_aa_round_rect(surface, (self.rect.x, self.rect.y, self.rect.w, self.rect.h),
                               bg, border_radius=self.border_radius,
                               border_color=border, border_width=self.border_width,
                               shadow_offset=self.shadow_offset)

        text_surf = self.font.render(self.text, True, txt_color)
        tx = self.rect.x + (self.rect.w - text_surf.get_width()) // 2
        ty = self.rect.y + (self.rect.h - text_surf.get_height()) // 2
        surface.blit(text_surf, (tx, ty))


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

        # 1. Lớp phủ mờ nền
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 175))
        surface.blit(overlay, (0, 0))

        # 2. Khung modal chính
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                     self.modal_rect.w, self.modal_rect.h),
                           (255, 255, 255), border_radius=16,
                           border_color=(30, 41, 59), border_width=3,
                           shadow_offset=6)

        # Tiêu đề & phụ đề số lượng màn
        title_surf = self.font_title.render("SELECT LEVEL", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 28, self.modal_rect.top + 20))
        sub_title = f"{len(self.levels)} levels available"
        sub_surf = self.font_sub.render(sub_title, True, (71, 85, 105))
        surface.blit(sub_surf, (self.modal_rect.x + 30, self.modal_rect.top + 46))

        # Nút đóng
        self.btn_close.draw(surface, mouse_pos)

        # 3. Danh sách các thẻ màn chơi (được cắt gọn trong view_rect)
        old_clip = surface.get_clip()
        surface.set_clip(self.view_rect)

        for idx, lvl in enumerate(self.levels):
            rect = self._get_card_rect(idx)
            # Tối ưu: bỏ qua các thẻ hoàn toàn nằm ngoài khung nhìn
            if rect.bottom < self.view_rect.top or rect.top > self.view_rect.bottom:
                continue

            is_hover = self.view_rect.collidepoint(mouse_pos) and rect.collidepoint(mouse_pos)
            is_active = (str(Path(lvl.path).resolve()) == self.current_path)

            if is_active:
                bg_col = (220, 252, 231)
                border_col = (22, 101, 52)
                border_w = 2
            elif is_hover:
                bg_col = (254, 240, 138)
                border_col = (30, 41, 59)
                border_w = 2
            else:
                bg_col = (248, 250, 252)
                border_col = (148, 163, 184)
                border_w = 2

            draw_aa_round_rect(surface, (rect.x, rect.y, rect.w, rect.h),
                               bg_col, border_radius=10,
                               border_color=border_col, border_width=border_w,
                               shadow_offset=2 if is_hover else 1)

            # Tên màn chơi
            if is_active:
                name_color = (20, 83, 45)
            elif is_hover:
                name_color = (15, 23, 42)
            else:
                name_color = (30, 41, 59)
            name_surf = self.font_item.render(lvl.name, True, name_color)
            surface.blit(name_surf, (rect.x + 16, rect.y + 10))

            # Thông số kích thước lưới (rows x cols)
            size_text = f"Size: {lvl.rows}x{lvl.cols}" if lvl.rows > 0 else ""
            size_surf = self.font_sub.render(size_text, True, (100, 116, 139))
            surface.blit(size_surf, (rect.x + 16, rect.y + 32))

            # Nhãn badge [PLAYING] hoặc [Play]
            if is_active:
                badge_surf = self.font_sub.render("PLAYING", True, (22, 101, 52))
                bx = rect.right - badge_surf.get_width() - 16
                by = rect.y + (rect.h - badge_surf.get_height()) // 2
                surface.blit(badge_surf, (bx, by))
            elif is_hover:
                play_surf = self.font_sub.render("Play", True, (15, 23, 42))
                bx = rect.right - play_surf.get_width() - 16
                by = rect.y + (rect.h - play_surf.get_height()) // 2
                surface.blit(play_surf, (bx, by))

        surface.set_clip(old_clip)

        # 4. Thanh cuộn bên phải (Scrollbar)
        if self.max_scroll > 0:
            # Rãnh cuộn (Track)
            track_bg = (226, 232, 240)
            draw_aa_round_rect(surface, (self.track_rect.x, self.track_rect.y,
                                         self.track_rect.w, self.track_rect.h),
                               track_bg, border_radius=self.track_rect.w // 2)

            # Con trượt (Thumb)
            thumb = self._get_thumb_rect()
            if thumb:
                is_thumb_hover = thumb.collidepoint(mouse_pos) or self.is_dragging_scrollbar
                thumb_color = (71, 85, 105) if is_thumb_hover else (148, 163, 184)
                draw_aa_round_rect(surface, (thumb.x, thumb.y, thumb.w, thumb.h),
                                   thumb_color, border_radius=thumb.w // 2)


class HelpModal:
    """How to Play and Game Rules dialog with Keyboard Controls and Advanced Tiles."""

    def __init__(self,
                 window_size: Tuple[int, int],
                 font_title: pygame.font.Font,
                 font_section: pygame.font.Font,
                 font_bold: pygame.font.Font,
                 font_text: pygame.font.Font) -> None:
        self.window_size = window_size
        self.font_title = font_title
        self.font_section = font_section
        self.font_bold = font_bold
        self.font_text = font_text

        self.is_open: bool = False
        self.modal_rect = pygame.Rect(0, 0, 840, 540)
        self.modal_rect.center = (window_size[0] // 2, window_size[1] // 2)

        # Close button 'X' at top-right
        cx = self.modal_rect.right - 44
        cy = self.modal_rect.top + 16
        self.btn_close = Button(
            (cx, cy, 30, 30), "X", self.font_bold,
            bg_color=(255, 255, 255),
            hover_color=(239, 68, 68),
            border_color=(30, 41, 59),
            border_color_hover=(15, 23, 42),
            text_color=(30, 41, 59),
            text_color_hover=(255, 255, 255),
            border_radius=8, border_width=2,
            shadow_offset=1
        )

        # 'Got It!' button at bottom
        btn_w, btn_h = 160, 38
        bx = self.modal_rect.centerx - btn_w // 2
        by = self.modal_rect.bottom - 52
        self.btn_got_it = Button(
            (bx, by, btn_w, btn_h), "Got It!", self.font_bold,
            bg_color=(187, 247, 208),
            hover_color=(134, 239, 172),
            border_color=(30, 41, 59),
            border_color_hover=(15, 23, 42),
            text_color=(20, 83, 45),
            text_color_hover=(15, 23, 42),
            border_radius=12, border_width=2,
            shadow_offset=2
        )

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_h, pygame.K_SPACE, pygame.K_RETURN):
                self.close()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.is_clicked(event) or self.btn_got_it.is_clicked(event):
                self.close()
                return True
            if not self.modal_rect.collidepoint(event.pos):
                self.close()
                return True

        return True

    def is_any_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        if not self.is_open:
            return False
        return self.btn_close.is_hovered(mouse_pos) or self.btn_got_it.is_hovered(mouse_pos)

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        if not self.is_open:
            return

        # 1. Dim overlay
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 175))
        surface.blit(overlay, (0, 0))

        # 2. Modal card
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                     self.modal_rect.w, self.modal_rect.h),
                           (255, 255, 255), border_radius=16,
                           border_color=(30, 41, 59), border_width=3,
                           shadow_offset=6)

        # 3. Header title
        title_surf = self.font_title.render("HOW TO PLAY AND RULES", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 28, self.modal_rect.top + 18))

        self.btn_close.draw(surface, mouse_pos)

        # Horizontal divider below title
        pygame.draw.line(surface, (203, 213, 225),
                         (self.modal_rect.x + 24, self.modal_rect.top + 54),
                         (self.modal_rect.right - 24, self.modal_rect.top + 54), 2)

        # Vertical divider between columns
        col_w = (self.modal_rect.w - 80) // 2
        mid_x = self.modal_rect.x + 28 + col_w + 12
        pygame.draw.line(surface, (203, 213, 225),
                         (mid_x, self.modal_rect.top + 66),
                         (mid_x, self.modal_rect.bottom - 64), 2)

        # COLUMN 1 (LEFT): KEYBOARD CONTROLS & OBJECTIVE
        c1_x = self.modal_rect.x + 28
        curr_y = self.modal_rect.top + 66

        hdr_ctrl = self.font_section.render("KEYBOARD CONTROLS", True, (29, 78, 216))
        surface.blit(hdr_ctrl, (c1_x, curr_y))
        curr_y += 26

        controls_data = [
            ("Arrow Keys", "Roll the block (Up, Down, Left, Right)"),
            ("SPACEBAR", "Switch active cube (when split into two)"),
            ("R Key", "Quick restart current level"),
            ("ESC", "Exit application"),
            ("H or [?]", "Open this guide dialog"),
        ]
        for key_t, desc_t in controls_data:
            k_s = self.font_bold.render(key_t, True, (15, 23, 42))
            d_s = self.font_text.render(desc_t, True, (51, 65, 85))
            surface.blit(k_s, (c1_x, curr_y))
            surface.blit(d_s, (c1_x + 12, curr_y + 17))
            curr_y += 38

        curr_y += 8
        hdr_goal = self.font_section.render("VICTORY OBJECTIVE", True, (22, 101, 52))
        surface.blit(hdr_goal, (c1_x, curr_y))
        curr_y += 24
        g_lines = [
            "• The 1x1x2 block must stand upright on the Goal hole.",
            "• Lying horizontally/vertically over the goal does not win.",
            "• Single 1x1x1 cubes cannot complete the level alone.",
        ]
        for line in g_lines:
            gl_s = self.font_text.render(line, True, (30, 41, 59))
            surface.blit(gl_s, (c1_x, curr_y))
            curr_y += 18

        # COLUMN 2 (RIGHT): ADVANCED TILES & MECHANICS
        c2_x = mid_x + 18
        curr_y = self.modal_rect.top + 66

        hdr_tiles = self.font_section.render("ADVANCED TILES AND SWITCHES", True, (180, 83, 9))
        surface.blit(hdr_tiles, (c2_x, curr_y))
        curr_y += 26

        tiles_data = [
            ("Fragile Tiles (Orange)", "Safe ONLY when lying down. Standing upright breaks the tile and drops into the void."),
            ("Soft Switch (Cyan Circle)", "Activates when pressed by any part of the block (standing, lying, or single cube)."),
            ("Heavy Switch (Yellow X)", "Activates ONLY when the full block STANDS upright on it. Lying down will not trigger it."),
            ("Split Switch (Purple Brackets)", "Activates when standing upright; teleports and splits the block into two 1x1x1 cubes."),
            ("Bridges and Planks", "Controlled by switches. Closed bridge = void hole; Open bridge = solid walkable floor (Toggle / Permanent)."),
        ]
        for title_t, desc_t in tiles_data:
            t_s = self.font_bold.render(title_t, True, (15, 23, 42))
            surface.blit(t_s, (c2_x, curr_y))
            curr_y += 18
            words = desc_t.split()
            line1, line2 = "", ""
            for w in words:
                test_l = (line1 + " " + w).strip()
                if self.font_text.render(test_l, True, (0, 0, 0)).get_width() <= col_w - 8:
                    line1 = test_l
                else:
                    line2 = (line2 + " " + w).strip()
            s1 = self.font_text.render(line1, True, (51, 65, 85))
            surface.blit(s1, (c2_x + 8, curr_y))
            curr_y += 17
            if line2:
                s2 = self.font_text.render(line2, True, (51, 65, 85))
                surface.blit(s2, (c2_x + 8, curr_y))
                curr_y += 17
            curr_y += 8

        # 'Got It!' button
        self.btn_got_it.draw(surface, mouse_pos)
