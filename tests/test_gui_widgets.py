"""Unit test cho các widget và tiện ích giao diện GUI (Task D2)."""
import os
import unittest

# Sử dụng dummy video driver để test chạy headless không cần màn hình đồ họa
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()

from gui.widgets import (
    Button,
    LevelSelectorModal,
    discover_levels,
    draw_aa_round_rect,
)


class TestDiscoverLevels(unittest.TestCase):
    """Kiểm tra chức năng quét và phát hiện file màn chơi trong thư mục levels."""

    def test_discover_default_levels(self):
        levels = discover_levels("levels")
        self.assertGreaterEqual(len(levels), 3)
        names = [lvl.name for lvl in levels]
        self.assertIn("g1_basic_01", names)
        self.assertIn("g2_fragile_01", names)
        self.assertIn("g3_switch_demo", names)

    def test_discover_nonexistent_directory_returns_empty(self):
        levels = discover_levels("levels_non_existent_folder")
        self.assertEqual(levels, [])


class TestButton(unittest.TestCase):
    """Kiểm tra hoạt động của lớp Button: hover, click và vẽ."""

    def setUp(self):
        self.font = pygame.font.SysFont("arial", 14)
        self.btn = Button((50, 50, 100, 40), "Test", self.font)

    def test_hover_inside_bounds(self):
        self.assertTrue(self.btn.is_hovered((60, 60)))
        self.assertTrue(self.btn.is_hovered((50, 50)))
        self.assertTrue(self.btn.is_hovered((149, 89)))

    def test_hover_outside_bounds(self):
        self.assertFalse(self.btn.is_hovered((40, 50)))
        self.assertFalse(self.btn.is_hovered((160, 60)))
        self.assertFalse(self.btn.is_hovered((60, 100)))

    def test_click_mouse_button_1_inside(self):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (70, 70)})
        self.assertTrue(self.btn.is_clicked(event))

    def test_click_mouse_button_1_outside(self):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (200, 200)})
        self.assertFalse(self.btn.is_clicked(event))

    def test_click_other_mouse_button(self):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (70, 70)})
        self.assertFalse(self.btn.is_clicked(event))

    def test_draw_does_not_crash(self):
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        self.btn.draw(surf, (70, 70))
        self.btn.draw(surf, (0, 0))


class TestLevelSelectorModal(unittest.TestCase):
    """Kiểm tra hoạt động của hộp thoại chọn màn: đóng mở và xử lý sự kiện."""

    def setUp(self):
        self.font = pygame.font.SysFont("arial", 14)
        self.modal = LevelSelectorModal((1280, 720), self.font, self.font, self.font)

    def test_initial_state_is_closed(self):
        self.assertFalse(self.modal.is_open)

    def test_open_and_close(self):
        self.modal.open("levels/g1_basic_01.json")
        self.assertTrue(self.modal.is_open)
        self.assertGreaterEqual(len(self.modal.levels), 3)

        self.modal.close()
        self.assertFalse(self.modal.is_open)

    def test_escape_key_closes_modal(self):
        self.modal.open("levels/g1_basic_01.json")
        esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        result = self.modal.handle_event(esc_event)
        self.assertIsNone(result)
        self.assertFalse(self.modal.is_open)

    def test_click_outside_closes_modal(self):
        self.modal.open("levels/g1_basic_01.json")
        click_outside = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)})
        result = self.modal.handle_event(click_outside)
        self.assertIsNone(result)
        self.assertFalse(self.modal.is_open)

    def test_click_level_item_selects_level(self):
        self.modal.open("levels/g1_basic_01.json")
        self.assertGreater(len(self.modal._items), 0)
        first_rect, first_lvl = self.modal._items[0]

        click_first = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (first_rect.centerx, first_rect.centery)}
        )
        selected = self.modal.handle_event(click_first)
        self.assertEqual(selected, first_lvl.path)
        self.assertFalse(self.modal.is_open)

    def test_draw_modal(self):
        surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        self.modal.open("levels/g1_basic_01.json")
        self.modal.draw(surf, (100, 100))


class TestDrawAARoundRect(unittest.TestCase):
    """Kiểm tra hàm vẽ hình chữ nhật bo góc khử răng cưa."""

    def test_draw_normal_rect(self):
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        draw_aa_round_rect(surf, (10, 10, 80, 50), (255, 0, 0), border_radius=8,
                           border_color=(0, 255, 0), border_width=2)

    def test_draw_zero_size_rect(self):
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        # Không được ném ngoại lệ khi kích thước <= 0
        draw_aa_round_rect(surf, (10, 10, 0, 50), (255, 0, 0))
        draw_aa_round_rect(surf, (10, 10, 50, 0), (255, 0, 0))


if __name__ == "__main__":
    unittest.main()
