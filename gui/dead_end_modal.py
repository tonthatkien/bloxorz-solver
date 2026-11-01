"""Hộp thoại thông báo ngõ cụt (Dead End Modal) khi không tìm thấy lời giải từ trạng thái hiện tại."""
from typing import Optional, Tuple
import pygame

from gui.base_widgets import Button, draw_aa_round_rect


class DeadEndModal:
    """Hộp thoại hiển thị thông báo khi vị trí hiện tại không thể về đích."""

    def __init__(self,
                 window_size: Tuple[int, int],
                 font_title: pygame.font.Font,
                 font_btn: pygame.font.Font,
                 font_desc: Optional[pygame.font.Font] = None,
                 font_badge: Optional[pygame.font.Font] = None) -> None:
        self.window_size = window_size
        self.font_title = font_title
        self.font_btn = font_btn

        if font_desc is not None and font_desc.get_height() <= 22:
            self.font_desc = font_desc
        else:
            sys_fonts = pygame.font.get_fonts()
            fam = 'trebuchetms' if 'trebuchetms' in sys_fonts else ('verdana' if 'verdana' in sys_fonts else 'arial')
            self.font_desc = pygame.font.SysFont(fam, 14)

        if font_badge is not None:
            self.font_badge = font_badge
        else:
            sys_fonts = pygame.font.get_fonts()
            fam = 'trebuchetms' if 'trebuchetms' in sys_fonts else ('verdana' if 'verdana' in sys_fonts else 'arial')
            self.font_badge = pygame.font.SysFont(fam, 12, bold=True)

        self.is_open: bool = False
        self.algo_name: str = ""
        self.reason: str = ""

        # Kích thước modal: rộng 560px để thoải mái không gian cho chữ và các nút
        modal_w, modal_h = 560, 270
        mx = (window_size[0] - modal_w) // 2
        my = (window_size[1] - modal_h) // 2
        self.modal_rect = pygame.Rect(mx, my, modal_w, modal_h)

        # Nút đóng 'X'
        self.btn_close = Button(
            (self.modal_rect.right - 44, self.modal_rect.top + 16, 28, 28),
            "X", font_btn,
            bg_color=(241, 245, 249), hover_color=(226, 232, 240),
            text_color=(100, 116, 139), border_radius=8, border_width=1,
            border_color=(203, 213, 225)
        )

        # 3 nút hành động chính ở chân modal
        btn_y = self.modal_rect.bottom - 56
        btn_h = 40
        b_kw = dict(border_color=(30, 41, 59), border_width=2, shadow_offset=2, border_radius=10)

        # Nút 1: Restart & Solve (170px)
        self.btn_solve_start = Button(
            (self.modal_rect.x + 24, btn_y, 170, btn_h),
            "Restart & Solve", font_btn,
            bg_color=(59, 130, 246), hover_color=(37, 99, 235),
            text_color=(255, 255, 255), **b_kw
        )

        # Nút 2: Restart Level (150px)
        self.btn_restart = Button(
            (self.modal_rect.x + 208, btn_y, 150, btn_h),
            "Restart Level", font_btn,
            bg_color=(241, 245, 249), hover_color=(226, 232, 240),
            text_color=(30, 41, 59), **b_kw
        )

        # Nút 3: Keep Trying / Cancel (154px)
        self.btn_cancel = Button(
            (self.modal_rect.x + 372, btn_y, 164, btn_h),
            "Keep Trying", font_btn,
            bg_color=(255, 255, 255), hover_color=(248, 250, 252),
            text_color=(71, 85, 105), **b_kw
        )

    def open(self, algo_name: str = "", reason: str = "") -> None:
        """Mở hộp thoại với thông tin thuật toán và nguyên nhân (nếu có)."""
        self.is_open = True
        self.algo_name = algo_name
        self.reason = reason

    def close(self) -> None:
        """Đóng hộp thoại."""
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Xử lý sự kiện bàn phím/chuột.

        Trả về 'restart_and_solve', 'restart_level', 'cancel', hoặc None.
        """
        if not self.is_open:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return "cancel"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.close()
                return "restart_and_solve"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_solve_start.is_clicked(event):
                self.close()
                return "restart_and_solve"
            if self.btn_restart.is_clicked(event):
                self.close()
                return "restart_level"
            if self.btn_cancel.is_clicked(event) or self.btn_close.is_clicked(event):
                self.close()
                return "cancel"
            if not self.modal_rect.collidepoint(event.pos):
                self.close()
                return "cancel"
        return None

    def is_any_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có đang hover trên phần tử tương tác nào không."""
        if not self.is_open:
            return False
        return (self.btn_close.is_hovered(mouse_pos)
                or self.btn_solve_start.is_hovered(mouse_pos)
                or self.btn_restart.is_hovered(mouse_pos)
                or self.btn_cancel.is_hovered(mouse_pos))

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ lớp phủ mờ tối và hộp thoại thông báo."""
        if not self.is_open:
            return

        # 1. Lớp phủ làm tối màn hình (Dim overlay)
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 160))
        surface.blit(overlay, (0, 0))

        # 2. Khung thẻ hộp thoại chính
        draw_aa_round_rect(
            surface,
            (self.modal_rect.x, self.modal_rect.y, self.modal_rect.w, self.modal_rect.h),
            (255, 255, 255), border_radius=16,
            border_color=(30, 41, 59), border_width=2,
            shadow_offset=6, shadow_color=(15, 23, 42, 140)
        )

        # 3. Badge cảnh báo đỏ/cam
        b_txt = "DEAD END DETECTED"
        badge_surf = self.font_badge.render(b_txt, True, (185, 28, 28))
        badge_w = badge_surf.get_width() + 20
        badge_h = 24
        badge_rect = (self.modal_rect.x + 24, self.modal_rect.top + 20, badge_w, badge_h)
        draw_aa_round_rect(
            surface, badge_rect, (254, 226, 226), border_radius=6,
            border_color=(239, 68, 68), border_width=1
        )
        surface.blit(badge_surf, (
            self.modal_rect.x + 34,
            self.modal_rect.top + 20 + (badge_h - badge_surf.get_height()) // 2
        ))

        # Nút đóng 'X'
        self.btn_close.draw(surface, mouse_pos)

        # 4. Tiêu đề
        title_surf = self.font_title.render("No Solution From Current State", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 24, self.modal_rect.top + 56))

        # 5. Nội dung mô tả
        if self.reason == "timeout":
            desc_l1 = "The search timed out without reaching the goal."
            desc_l2 = "Would you like to restart from the beginning and solve?"
        elif self.reason == "node_limit":
            desc_l1 = "Search node limit was exceeded without reaching the goal."
            desc_l2 = "Would you like to restart from the beginning and solve?"
        else:
            desc_l1 = "No valid path to the goal exists from this position."
            desc_l2 = "A bridge or fragile tile may be permanently unreachable."

        s_l1 = self.font_desc.render(desc_l1, True, (71, 85, 105))
        s_l2 = self.font_desc.render(desc_l2, True, (100, 116, 139))
        surface.blit(s_l1, (self.modal_rect.x + 24, self.modal_rect.top + 96))
        surface.blit(s_l2, (self.modal_rect.x + 24, self.modal_rect.top + 120))

        # Đường kẻ phân cách
        pygame.draw.line(
            surface, (226, 232, 240),
            (self.modal_rect.x + 24, self.modal_rect.top + 158),
            (self.modal_rect.right - 24, self.modal_rect.top + 158), 1
        )

        # 6. Các nút hành động
        self.btn_solve_start.draw(surface, mouse_pos)
        self.btn_restart.draw(surface, mouse_pos)
        self.btn_cancel.draw(surface, mouse_pos)
