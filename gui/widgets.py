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
                       border_width: int = 1) -> None:
    """Vẽ hình chữ nhật bo góc khử răng cưa (supersampling 2x)."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    scale = 2
    sw, sh = w * scale, h * scale
    sr = border_radius * scale
    sbw = border_width * scale
    sub = pygame.Surface((sw, sh), pygame.SRCALPHA)
    pygame.draw.rect(sub, color, (0, 0, sw, sh), border_radius=sr)
    if border_color and border_width > 0:
        pygame.draw.rect(sub, border_color, (0, 0, sw, sh), width=sbw, border_radius=sr)
    smooth = pygame.transform.smoothscale(sub, (w, h))
    surface.blit(smooth, (x, y))


class Button:
    """Nút bấm có hiệu ứng hover, bo góc và nhãn chữ căn giữa."""

    def __init__(self,
                 rect: Tuple[int, int, int, int],
                 text: str,
                 font: pygame.font.Font,
                 bg_color: Tuple[int, ...] = (254, 250, 235, 235),
                 hover_color: Tuple[int, ...] = (245, 230, 205, 255),
                 border_color: Optional[Tuple[int, ...]] = (180, 130, 85, 180),
                 border_color_hover: Optional[Tuple[int, ...]] = (150, 95, 45, 230),
                 text_color: Tuple[int, ...] = (110, 65, 35),
                 text_color_hover: Tuple[int, ...] = (75, 40, 15),
                 border_radius: int = 12,
                 border_width: int = 2) -> None:
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

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có đang rê qua nút không."""
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Kiểm tra sự kiện click chuột trái vào nút."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ nút lên bề mặt với màu tương ứng trạng thái hover."""
        hover = self.is_hovered(mouse_pos)
        bg = self.hover_color if hover else self.bg_color
        border = self.border_color_hover if hover else self.border_color
        txt_color = self.text_color_hover if hover else self.text_color

        draw_aa_round_rect(surface, (self.rect.x, self.rect.y, self.rect.w, self.rect.h),
                           bg, border_radius=self.border_radius,
                           border_color=border, border_width=self.border_width)

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
    """Hộp thoại nổi (Modal) cho phép người chơi chọn màn chơi mới."""

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
        self.modal_rect = pygame.Rect(0, 0, 520, 420)
        self.modal_rect.center = (window_size[0] // 2, window_size[1] // 2)

        # Nút đóng 'X' ở góc trên-phải của hộp thoại
        cx = self.modal_rect.right - 44
        cy = self.modal_rect.top + 14
        self.btn_close = Button(
            (cx, cy, 30, 30), "X", self.font_item,
            bg_color=(240, 235, 225, 200),
            hover_color=(230, 90, 75, 230),
            border_color=(180, 150, 130),
            border_color_hover=(190, 50, 40),
            text_color=(120, 80, 60),
            text_color_hover=(255, 255, 255),
            border_radius=8, border_width=1
        )
        self._items: List[Tuple[pygame.Rect, LevelInfo]] = []

    def open(self, current_path: str) -> None:
        """Mở hộp thoại và quét lại danh sách màn."""
        self.current_path = str(Path(current_path).resolve())
        self.levels = discover_levels("levels")
        self.is_open = True
        self._rebuild_layout()

    def close(self) -> None:
        """Đóng hộp thoại."""
        self.is_open = False

    def _rebuild_layout(self) -> None:
        """Tính toán vị trí của từng thẻ màn chơi trong danh sách."""
        self._items.clear()
        start_y = self.modal_rect.top + 70
        item_h = 56
        gap = 12
        card_w = self.modal_rect.w - 56
        card_x = self.modal_rect.x + 28

        for idx, lvl in enumerate(self.levels):
            iy = start_y + idx * (item_h + gap)
            rect = pygame.Rect(card_x, iy, card_w, item_h)
            self._items.append((rect, lvl))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Xử lý sự kiện bàn phím/chuột khi hộp thoại đang mở.

        Trả về đường dẫn file màn được chọn (str), hoặc None nếu chưa chọn.
        """
        if not self.is_open:
            return None

        # Bấm ESC để đóng
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return None

        # Xử lý click chuột
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click nút đóng
            if self.btn_close.is_clicked(event):
                self.close()
                return None

            # Click ra ngoài vùng modal
            if not self.modal_rect.collidepoint(event.pos):
                self.close()
                return None

            # Click vào từng màn chơi
            for rect, lvl in self._items:
                if rect.collidepoint(event.pos):
                    self.close()
                    return lvl.path

        return None

    def is_any_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra xem chuột có đang hover trên phần tử tương tác nào không."""
        if not self.is_open:
            return False
        if self.btn_close.is_hovered(mouse_pos):
            return True
        for rect, _ in self._items:
            if rect.collidepoint(mouse_pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ lớp phủ mờ tối và hộp thoại chọn màn."""
        if not self.is_open:
            return

        # 1. Lớp phủ mờ nền
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((20, 35, 45, 160))
        surface.blit(overlay, (0, 0))

        # 2. Khung modal chính
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                     self.modal_rect.w, self.modal_rect.h),
                           (253, 250, 243, 250), border_radius=18,
                           border_color=(175, 125, 80, 240), border_width=2)

        # Tiêu đề
        title_surf = self.font_title.render("SELECT LEVEL", True, (120, 65, 25))
        surface.blit(title_surf, (self.modal_rect.x + 28, self.modal_rect.top + 22))

        # Nút đóng
        self.btn_close.draw(surface, mouse_pos)

        # 3. Danh sách các thẻ màn chơi
        for rect, lvl in self._items:
            is_hover = rect.collidepoint(mouse_pos)
            is_active = (str(Path(lvl.path).resolve()) == self.current_path)

            if is_active:
                bg_col = (235, 248, 235, 250)
                border_col = (46, 160, 67, 230)
                border_w = 2
            elif is_hover:
                bg_col = (248, 238, 222, 250)
                border_col = (190, 120, 60, 220)
                border_w = 2
            else:
                bg_col = (255, 253, 248, 240)
                border_col = (210, 180, 150, 180)
                border_w = 1

            draw_aa_round_rect(surface, (rect.x, rect.y, rect.w, rect.h),
                               bg_col, border_radius=12,
                               border_color=border_col, border_width=border_w)

            # Tên màn chơi
            name_color = (35, 105, 45) if is_active else (80, 45, 20)
            name_surf = self.font_item.render(lvl.name, True, name_color)
            surface.blit(name_surf, (rect.x + 16, rect.y + 10))

            # Thông số kích thước lưới (rows x cols)
            size_text = f"Size: {lvl.rows}x{lvl.cols}" if lvl.rows > 0 else ""
            size_surf = self.font_sub.render(size_text, True, (140, 110, 85))
            surface.blit(size_surf, (rect.x + 16, rect.y + 32))

            # Nhãn badge [PLAYING] nếu là màn hiện tại
            if is_active:
                badge_surf = self.font_sub.render("PLAYING", True, (35, 135, 55))
                bx = rect.right - badge_surf.get_width() - 16
                by = rect.y + (rect.h - badge_surf.get_height()) // 2
                surface.blit(badge_surf, (bx, by))
            elif is_hover:
                play_surf = self.font_sub.render("Play", True, (180, 90, 30))
                bx = rect.right - play_surf.get_width() - 16
                by = rect.y + (rect.h - play_surf.get_height()) // 2
                surface.blit(play_surf, (bx, by))
