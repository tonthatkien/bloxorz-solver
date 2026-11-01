"""Hộp thoại hướng dẫn luật chơi và phím điều khiển (Help Modal) cho Bloxorz."""
from typing import Tuple
import pygame
import pygame.gfxdraw

from gui.base_widgets import Button, draw_aa_round_rect
from gui.draw_tiles import (
    BRIDGE_EDGE, BRIDGE_TOP, FRAGILE_EDGE, FRAGILE_TOP, HEAVY_INK,
    MARKER_EDGE, SOFT_TOP, SOIL_FRONT, SOIL_LEFT, SPLIT_INK,
    _disc, _point, _smooth_lines,
)
from gui.render_board import _poly_aa, _tile_quad


def _draw_mini_tile(surf: pygame.Surface, kind: str, bx: int, by: int,
                    bw: int = 56, bh: int = 40) -> None:
    """Vẽ ô isometric 3D thu nhỏ làm icon minh họa trực quan."""
    # Khung badge chứa icon
    draw_aa_round_rect(surf, (bx, by, bw, bh), (248, 250, 252), border_radius=8,
                       border_color=(203, 213, 225), border_width=1)
    tw, th, skew, d = 32, 16, 9, 6
    tx = bx + (bw - (tw + skew)) // 2
    ty = by + (bh - (th + d)) // 2
    quad = _tile_quad(tx, ty, tw, th, skew)
    tl, tr, br, bl = quad
    front_face = [bl, br, (br[0], br[1] + d), (bl[0], bl[1] + d)]
    left_face = [tl, bl, (bl[0], bl[1] + d), (tl[0], tl[1] + d)]

    if kind == "fragile":
        # Ô đất cam dễ vỡ kèm vết nứt
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        _poly_aa(surf, FRAGILE_TOP, quad, FRAGILE_EDGE)
        crack = [_point(tx, ty, tw, th, skew, u, v)
                 for u, v in ((0.55, 0.12), (0.43, 0.40), (0.60, 0.55), (0.46, 0.85))]
        _smooth_lines(surf, FRAGILE_EDGE, crack, 2)
    elif kind == "bridge":
        # Ô cầu ván gỗ nan ngang
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        _poly_aa(surf, BRIDGE_TOP, quad, BRIDGE_EDGE)
        for v in (0.3, 0.6):
            p1 = _point(tx, ty, tw, th, skew, 0.08, v)
            p2 = _point(tx, ty, tw, th, skew, 0.92, v)
            _smooth_lines(surf, BRIDGE_EDGE, [p1, p2], 1)
    elif kind == "soft":
        # Công tắc nhẹ đĩa tròn lục lam (cyan)
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        _poly_aa(surf, (142, 198, 92), quad, (98, 150, 54))
        _disc(surf, SOFT_TOP, tx, ty, tw, th, skew)
    elif kind == "heavy":
        # Công tắc nặng đĩa xám có dấu chữ X vàng
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        _poly_aa(surf, (142, 198, 92), quad, (98, 150, 54))
        _disc(surf, MARKER_EDGE, tx, ty, tw, th, skew)
        for start, end in (((0.33, 0.29), (0.67, 0.71)),
                           ((0.33, 0.71), (0.67, 0.29))):
            _smooth_lines(surf, HEAVY_INK,
                          [_point(tx, ty, tw, th, skew, *start),
                           _point(tx, ty, tw, th, skew, *end)], 2)
    elif kind == "split":
        # Công tắc phân tách hai dấu ngoặc tím đối xứng
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        _poly_aa(surf, (142, 198, 92), quad, (98, 150, 54))
        _disc(surf, MARKER_EDGE, tx, ty, tw, th, skew)
        for mirror in (False, True):
            points = [_point(tx, ty, tw, th, skew, 1 - u if mirror else u, v)
                      for u, v in ((0.42, 0.29), (0.33, 0.39), (0.30, 0.50),
                                   (0.33, 0.61), (0.42, 0.71))]
            _smooth_lines(surf, SPLIT_INK, points, 2)
    elif kind == "goal":
        # Lỗ mục tiêu 3D xuyên sàn nhìn sâu xuống vực
        _poly_aa(surf, SOIL_FRONT, front_face)
        _poly_aa(surf, SOIL_LEFT, left_face)
        t_d = d / float(th)
        dx_d = int(t_d * skew)
        p1 = (tl[0] + dx_d, tl[1] + d)
        p2 = (tr[0], tr[1] + d)
        p3 = (br[0] - dx_d, br[1])
        p4 = bl
        _poly_aa(surf, (115, 175, 235), [p1, p2, p3, p4])
        _poly_aa(surf, (95, 65, 42), [tl, tr, p2, p1])
        _poly_aa(surf, (115, 80, 52), [tr, br, p3, p2])
        _poly_aa(surf, (60, 38, 22), [tr, p2, (p2[0] - 3, p2[1]), (tr[0] - 3, tr[1])])
        pygame.gfxdraw.polygon(surf, quad, (55, 90, 35))
        pygame.gfxdraw.aapolygon(surf, quad, (55, 90, 35))


class HelpModal:
    """Hộp thoại hướng dẫn luật chơi, phím điều khiển và các ô đặc biệt."""

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
        self.modal_rect = pygame.Rect(0, 0, 860, 560)
        self.modal_rect.center = (window_size[0] // 2, window_size[1] // 2)

        # Nút đóng 'X'
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

        # Nút xác nhận 'Got It!'
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

        # 1. Lớp phủ làm tối màn hình nền
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 175))
        surface.blit(overlay, (0, 0))

        # 2. Khung thẻ hộp thoại và tiêu đề
        draw_aa_round_rect(surface, (self.modal_rect.x, self.modal_rect.y,
                                     self.modal_rect.w, self.modal_rect.h),
                           (255, 255, 255), border_radius=16,
                           border_color=(30, 41, 59), border_width=3,
                           shadow_offset=6)

        title_surf = self.font_title.render("HOW TO PLAY AND RULES", True, (15, 23, 42))
        surface.blit(title_surf, (self.modal_rect.x + 28, self.modal_rect.top + 18))
        self.btn_close.draw(surface, mouse_pos)

        # Đường kẻ phân cách
        pygame.draw.line(surface, (203, 213, 225),
                         (self.modal_rect.x + 24, self.modal_rect.top + 54),
                         (self.modal_rect.right - 24, self.modal_rect.top + 54), 2)

        col_w = (self.modal_rect.w - 80) // 2
        mid_x = self.modal_rect.x + 28 + col_w + 12
        pygame.draw.line(surface, (203, 213, 225),
                         (mid_x, self.modal_rect.top + 66),
                         (mid_x, self.modal_rect.bottom - 64), 2)

        # 3. Cột 1 (Trái): Phím điều khiển và điều kiện chiến thắng
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

        curr_y += 6
        hdr_goal = self.font_section.render("VICTORY OBJECTIVE", True, (22, 101, 52))
        surface.blit(hdr_goal, (c1_x, curr_y))
        curr_y += 24

        _draw_mini_tile(surface, "goal", c1_x, curr_y, bw=56, bh=40)
        g_lines = [
            ("Goal Hole (Drop Zone)", self.font_bold, (22, 101, 52)),
            ("Block must STAND upright into the hole.", self.font_text, (51, 65, 85)),
            ("Lying across does not win; single cubes cannot finish.", self.font_text, (71, 85, 105)),
        ]
        gy = curr_y
        for text_item, fnt, col in g_lines:
            surface.blit(fnt.render(text_item, True, col), (c1_x + 66, gy))
            gy += 16

        # 4. Cột 2 (Phải): Các ô nâng cao & công tắc kèm icon minh họa
        c2_x = mid_x + 18
        curr_y = self.modal_rect.top + 66

        hdr_tiles = self.font_section.render("ADVANCED TILES AND SWITCHES", True, (180, 83, 9))
        surface.blit(hdr_tiles, (c2_x, curr_y))
        curr_y += 26

        tiles_data = [
            ("fragile", "Fragile Tile (Orange)",
             "Safe ONLY when lying down.",
             "Standing breaks the tile and drops into void."),
            ("soft", "Soft Switch (Cyan Circle)",
             "Triggered by ANY part of the block.",
             "Works for standing, lying, or single 1x1 cube."),
            ("heavy", "Heavy Switch (Yellow X)",
             "Triggered ONLY when full block STANDS on it.",
             "Lying down or single cube will not activate."),
            ("split", "Split Switch (Purple Brackets)",
             "Triggered when full block STANDS upright.",
             "Splits and teleports into two 1x1 cubes."),
            ("bridge", "Bridges and Planks",
             "Controlled by switches (Toggle / Permanent).",
             "Closed bridge = void hole; Open = solid floor."),
        ]

        for kind, title, line1, line2 in tiles_data:
            _draw_mini_tile(surface, kind, c2_x, curr_y, bw=56, bh=40)
            surface.blit(self.font_bold.render(title, True, (15, 23, 42)), (c2_x + 66, curr_y))
            surface.blit(self.font_text.render(line1, True, (51, 65, 85)), (c2_x + 66, curr_y + 16))
            surface.blit(self.font_text.render(line2, True, (100, 116, 139)), (c2_x + 66, curr_y + 30))
            curr_y += 56

        # Nút hoàn tất
        self.btn_got_it.draw(surface, mouse_pos)
