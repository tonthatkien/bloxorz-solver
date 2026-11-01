"""Thành phần giao diện nền tảng: Button và draw_aa_round_rect."""
from typing import Optional, Tuple
import pygame


def draw_aa_round_rect(surface: pygame.Surface,
                       rect: Tuple[int, int, int, int],
                       color: Tuple[int, ...],
                       border_radius: int = 0,
                       border_color: Optional[Tuple[int, ...]] = None,
                       border_width: int = 1,
                       shadow_offset: int = 0,
                       shadow_color: Optional[Tuple[int, ...]] = (15, 23, 42, 110)) -> None:
    """Vẽ hình chữ nhật kèm đổ bóng."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return

    # 1. Đổ bóng xúc giác (Solid Arcade drop shadow)
    if shadow_offset > 0 and shadow_color:
        s_rect = (x, y + shadow_offset, w, h)
        if len(shadow_color) == 4 and shadow_color[3] < 255:
            s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s_surf, shadow_color, (0, 0, w, h), border_radius=border_radius)
            surface.blit(s_surf, (x, y + shadow_offset))
        else:
            pygame.draw.rect(surface, shadow_color, s_rect, border_radius=border_radius)

    # 2. Vẽ hình chữ nhật chính
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
    """Nút bấm"""

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
                 shadow_offset: int = 2,
                 icon: Optional[str] = None) -> None:
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
        self.icon = icon

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Kiểm tra chuột có đang rê qua nút không."""
        return self.enabled and self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Kiểm tra sự kiện click chuột trái vào nút."""
        if self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Vẽ nút lên bề mặt."""
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

        if self.icon == 'home':
            cx = self.rect.x + self.rect.w // 2
            cy = self.rect.y + self.rect.h // 2
            pygame.draw.polygon(surface, txt_color, [(cx, cy - 8), (cx + 9, cy), (cx - 9, cy)])
            pygame.draw.rect(surface, txt_color, (cx - 6, cy, 13, 8))
            door_col = bg[:3] if len(bg) >= 3 else bg
            pygame.draw.rect(surface, door_col, (cx - 2, cy + 3, 5, 5))
        elif self.text:
            text_surf = self.font.render(self.text, True, txt_color)
            tx = self.rect.x + (self.rect.w - text_surf.get_width()) // 2
            ty = self.rect.y + (self.rect.h - text_surf.get_height()) // 2
            surface.blit(text_surf, (tx, ty))
