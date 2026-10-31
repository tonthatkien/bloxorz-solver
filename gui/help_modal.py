"""Hộp thoại hướng dẫn luật chơi và phím điều khiển (Help Modal) cho Bloxorz."""
from typing import Tuple
import pygame

from gui.base_widgets import Button, draw_aa_round_rect


class HelpModal:
    """Hộp thoại hướng dẫn luật chơi, phím điều khiển và cơ chế các ô đặc biệt."""

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

        # Nút đóng 'X' ở góc trên bên phải
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

        # Nút xác nhận 'Got It!' ở cạnh dưới
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
        """Mở hộp thoại hướng dẫn."""
        self.is_open = True

    def close(self) -> None:
        """Đóng hộp thoại hướng dẫn."""
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Xử lý sự kiện bàn phím và chuột khi hộp thoại đang mở."""
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
        """Kiểm tra con trỏ chuột có đang hover vào nút bấm nào trong modal không."""
        if not self.is_open:
            return False
        return self.btn_close.is_hovered(mouse_pos) or self.btn_got_it.is_hovered(mouse_pos)

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ hộp thoại hướng dẫn lên màn hình."""
        if not self.is_open:
            return

        # 1. Lớp phủ làm tối màn hình nền (Dim overlay)
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 175))
        surface.blit(overlay, (0, 0))

        # 2. Khung thẻ hộp thoại (Modal card)
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                     self.modal_rect.w, self.modal_rect.h),
                           (255, 255, 255), border_radius=16,
                           border_color=(30, 41, 59), border_width=3,
                           shadow_offset=6)

        # 3. Tiêu đề hộp thoại
        title_surf = self.font_title.render("HOW TO PLAY AND RULES", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 28, self.modal_rect.top + 18))

        self.btn_close.draw(surface, mouse_pos)

        # Đường kẻ ngang phân cách tiêu đề
        pygame.draw.line(surface, (203, 213, 225),
                         (self.modal_rect.x + 24, self.modal_rect.top + 54),
                         (self.modal_rect.right - 24, self.modal_rect.top + 54), 2)

        # Đường kẻ dọc phân cách giữa hai cột nội dung
        col_w = (self.modal_rect.w - 80) // 2
        mid_x = self.modal_rect.x + 28 + col_w + 12
        pygame.draw.line(surface, (203, 213, 225),
                         (mid_x, self.modal_rect.top + 66),
                         (mid_x, self.modal_rect.bottom - 64), 2)

        # CỘT 1 (TRÁI): BÀN PHÍM ĐIỀU KHIỂN & MỤC TIÊU CHIẾN THẮNG
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

        # CỘT 2 (PHẢI): CÁC Ô ĐẶC BIỆT & CƠ CHẾ CÔNG TẮC
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

        # Nút 'Got It!'
        self.btn_got_it.draw(surface, mouse_pos)
