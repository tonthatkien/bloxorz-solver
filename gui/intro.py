"""Màn hình giới thiệu (Intro Screen) cho Bloxorz."""
import math
from typing import Optional, Tuple
import pygame

from gui.base_widgets import Button
from gui.help_modal import HelpModal
from gui.level_modal import LevelSelectorModal
from gui.sky import draw_sky_with_clouds
from gui.theme import get_theme


class IntroScreen:
    """Quản lý hiển thị và tương tác màn hình mở đầu."""

    def __init__(self, window_size: Tuple[int, int], current_level_path: str = "levels/g1_basic_01.json") -> None:
        self.window_size = window_size
        self.selected_level_path: str = current_level_path

        # Phông chữ
        sys_fonts = pygame.font.get_fonts()
        font_family = ('trebuchetms' if 'trebuchetms' in sys_fonts
                       else ('verdana' if 'verdana' in sys_fonts else 'arial'))
        self.font_logo = pygame.font.SysFont(font_family, 68, bold=True)
        self.font_btn = pygame.font.SysFont(font_family, 15, bold=True)
        self.font_hint = pygame.font.SysFont(font_family, 15, bold=True)
        font_hud_val = pygame.font.SysFont(font_family, 20, bold=True)
        font_dock_b = pygame.font.SysFont(font_family, 14, bold=True)
        font_dock_sm = pygame.font.SysFont(font_family, 13)
        font_sub = pygame.font.SysFont(font_family, 18)

        # Hộp thoại chọn màn và hướng dẫn
        self.help_modal = HelpModal(window_size, font_hud_val, font_dock_b, self.font_btn, font_dock_sm)
        self.level_modal = LevelSelectorModal(window_size, font_hud_val, self.font_btn, font_sub)

        cx = window_size[0] // 2
        btn_w, btn_h = 220, 46
        bx = cx - btn_w // 2
        btn_start_y = 350
        gap_y = 58

        # 3 nút điều hướng dọc
        self.btn_play = Button(
            (bx, btn_start_y, btn_w, btn_h), "PLAY NOW", self.font_btn,
            bg_color=(187, 247, 208), hover_color=(134, 239, 172),
            border_color=(30, 41, 59), border_color_hover=(15, 23, 42),
            text_color=(20, 83, 45), text_color_hover=(15, 23, 42),
            border_radius=14, border_width=2, shadow_offset=3
        )
        self.btn_levels = Button(
            (bx, btn_start_y + gap_y, btn_w, btn_h), "SELECT LEVEL", self.font_btn,
            bg_color=(191, 219, 254), hover_color=(147, 197, 253),
            border_color=(30, 41, 59), border_color_hover=(15, 23, 42),
            text_color=(30, 58, 138), text_color_hover=(15, 23, 42),
            border_radius=14, border_width=2, shadow_offset=3
        )
        self.btn_help = Button(
            (bx, btn_start_y + gap_y * 2, btn_w, btn_h), "HOW TO PLAY", self.font_btn,
            bg_color=(255, 255, 255), hover_color=(241, 245, 249),
            border_color=(30, 41, 59), border_color_hover=(15, 23, 42),
            text_color=(30, 41, 59), text_color_hover=(15, 23, 42),
            border_radius=14, border_width=2, shadow_offset=3
        )

    def open(self, current_level_path: str = "") -> None:
        """Kích hoạt lại màn hình giới thiệu và đặt lại hộp thoại."""
        if current_level_path:
            self.selected_level_path = current_level_path
        self.help_modal.close()
        self.level_modal.close()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Xử lý sự kiện bàn phím và chuột."""
        # Xử lý modal chọn màn
        if self.level_modal.is_open:
            selected = self.level_modal.handle_event(event)
            if selected is not None:
                self.selected_level_path = selected
                return 'play'
            return None

        # Xử lý modal hướng dẫn
        if self.help_modal.is_open:
            self.help_modal.handle_event(event)
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                return 'play'
            elif event.key == pygame.K_l:
                self.level_modal.open(self.selected_level_path)
            elif event.key == pygame.K_h:
                self.help_modal.open()
            elif event.key == pygame.K_ESCAPE:
                return 'quit'

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_play.is_clicked(event):
                return 'play'
            elif self.btn_levels.is_clicked(event):
                self.level_modal.open(self.selected_level_path)
            elif self.btn_help.is_clicked(event):
                self.help_modal.open()

        return None

    def is_any_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có trỏ vào nút nào không."""
        if self.level_modal.is_open:
            return self.level_modal.is_any_hovered(mouse_pos)
        if self.help_modal.is_open:
            return self.help_modal.is_any_hovered(mouse_pos)
        return (self.btn_play.is_hovered(mouse_pos)
                or self.btn_levels.is_hovered(mouse_pos)
                or self.btn_help.is_hovered(mouse_pos))

    def _draw_floating_block(self, surface: pygame.Surface, cx: int, cy: int, bob: float) -> None:
        """Vẽ khối gỗ 3D lơ lửng."""
        bx = cx
        by = int(cy + bob)

        # Bóng đổ dưới đáy
        sw = int(72 - bob * 1.5)
        sh = int(24 - bob * 0.5)
        s_surf = pygame.Surface((sw * 2, sh * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s_surf, (15, 23, 42, 55), (0, 0, sw * 2, sh * 2))
        surface.blit(s_surf, (cx - sw, cy + 50))

        tw, th, h = 40, 21, 52
        p_top = (bx, by - h)
        p_right = (bx + tw, by - h + th // 2)
        p_bot = (bx, by - h + th)
        p_left = (bx - tw, by - h + th // 2)

        # Mặt trên và hai mặt bên
        pygame.draw.polygon(surface, (230, 160, 95), [p_top, p_right, p_bot, p_left])
        pygame.draw.polygon(surface, (110, 65, 35), [p_top, p_right, p_bot, p_left], 2)

        p_bot_l = (bx - tw, by + th // 2)
        p_bot_c = (bx, by + th)
        pygame.draw.polygon(surface, (170, 105, 55), [p_left, p_bot, p_bot_c, p_bot_l])
        pygame.draw.polygon(surface, (110, 65, 35), [p_left, p_bot, p_bot_c, p_bot_l], 2)

        p_bot_r = (bx + tw, by + th // 2)
        pygame.draw.polygon(surface, (195, 125, 70), [p_bot, p_right, p_bot_r, p_bot_c])
        pygame.draw.polygon(surface, (110, 65, 35), [p_bot, p_right, p_bot_r, p_bot_c], 2)

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], now_ms: int) -> None:
        """Vẽ toàn bộ giao diện màn hình giới thiệu."""
        # Nền bầu trời
        theme = get_theme('g1_basic_01')
        draw_sky_with_clouds(surface, *self.window_size, theme=theme)

        cx = self.window_size[0] // 2

        # Khối gỗ nhấp nhô theo sóng sine
        bob = math.sin(now_ms * 0.0032) * 7.0
        self._draw_floating_block(surface, cx, 140, bob)

        # Tiêu đề BLOXORZ
        title_txt = "BLOXORZ"
        title_y = 240

        shadow_s = self.font_logo.render(title_txt, True, (30, 41, 59))
        for dx, dy in ((2, 3), (3, 4), (4, 6)):
            surface.blit(shadow_s, (cx - shadow_s.get_width() // 2 + dx, title_y + dy))

        logo_s = self.font_logo.render(title_txt, True, (254, 240, 138))
        surface.blit(logo_s, (cx - logo_s.get_width() // 2, title_y))

        border_s = self.font_logo.render(title_txt, True, (120, 53, 15))
        surface.blit(border_s, (cx - border_s.get_width() // 2 + 1, title_y + 1))

        # 3 nút bấm
        self.btn_play.draw(surface, mouse_pos)
        self.btn_levels.draw(surface, mouse_pos)
        self.btn_help.draw(surface, mouse_pos)

        # Nhắc phím tắt
        pulse = int(170 + 85 * math.sin(now_ms * 0.005))
        hint_surf = pygame.Surface(self.window_size, pygame.SRCALPHA)
        hint_txt = self.font_hint.render("PRESS [SPACE] OR [ENTER] TO START", True, (15, 23, 42, pulse))
        hint_surf.blit(hint_txt, (cx - hint_txt.get_width() // 2, 545))
        surface.blit(hint_surf, (0, 0))

        # Modal
        if self.help_modal.is_open:
            self.help_modal.draw(surface, mouse_pos)
        elif self.level_modal.is_open:
            self.level_modal.draw(surface, mouse_pos)
