"""Unit test cho module gui/draw_cube.py (Task D4)."""
import os
import unittest
import pygame

from gui.draw_cube import (
    _wood_face_color,
    _stone_face_color,
    _proj,
    draw_active_indicator,
    draw_single_cube,
    draw_animated_single_cube,
    draw_split_cubes,
)


class TestDrawCube(unittest.TestCase):
    """Kiểm thử hình học, bóng đổ và hàm vẽ của hai cube tách rời."""

    @classmethod
    def setUpClass(cls) -> None:
        """Khởi tạo Pygame headless để kiểm thử vẽ không cần màn hình thật."""
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        cls.surface = pygame.Surface((800, 600))
        cls.layout = (68, 38, (400, 200), 22)

    def test_face_colors_valid_rgb(self) -> None:
        """Đảm bảo các hàm tính màu mặt trả về bộ 3 giá trị RGB hợp lệ (0-255)."""
        normals = [
            (0.0, 0.0, 1.0),
            (0.0, 0.0, -1.0),
            (0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0),
            (1.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
        ]
        for normal in normals:
            wood_col = _wood_face_color(normal)
            stone_col = _stone_face_color(normal)

            self.assertEqual(len(wood_col), 3)
            self.assertEqual(len(stone_col), 3)
            for ch in wood_col:
                self.assertTrue(0 <= ch <= 255)
            for ch in stone_col:
                self.assertTrue(0 <= ch <= 255)

            # Khối active (gỗ) phải ấm hơn/sáng hơn hoặc khác biệt rõ rệt khối đá (inactive)
            self.assertNotEqual(wood_col, stone_col)

    def test_isometric_projection(self) -> None:
        """Kiểm tra phép chiếu 3D sang 2D isometric trả về tọa độ chính xác."""
        tw, th, off, skew = self.layout
        px, py = _proj((2.0, 3.0, 1.0), tw, th, off, skew, cube_h=60)
        expected_x = off[0] + 2.0 * tw + 3.0 * skew
        expected_y = off[1] + 3.0 * th - 1.0 * 60
        self.assertAlmostEqual(px, expected_x)
        self.assertAlmostEqual(py, expected_y)

    def test_draw_single_cube_active_and_inactive(self) -> None:
        """Kiểm tra vẽ cube đơn tĩnh không gây lỗi (active và inactive)."""
        tw, th, off, skew = self.layout
        draw_single_cube(self.surface, 1, 2, True, tw, th, off, skew)
        draw_single_cube(self.surface, 3, 4, False, tw, th, off, skew)

    def test_draw_active_indicator(self) -> None:
        """Kiểm tra vẽ tam giác ngược và bóng đổ hoạt động bình thường."""
        tw, th, off, skew = self.layout
        draw_active_indicator(self.surface, 1, 2, tw, th, off, skew, now_ms=1000)

    def test_draw_animated_single_cube(self) -> None:
        """Kiểm tra hoạt ảnh lăn 90 độ cho cả 4 hướng U, D, L, R."""
        tw, th, off, skew = self.layout
        for action in ("U", "D", "L", "R"):
            draw_animated_single_cube(
                self.surface, 2, 2, action, 0.5, True, tw, th, off, skew
            )

    def test_draw_split_cubes_integration(self) -> None:
        """Kiểm tra hàm tổng hợp draw_split_cubes với cả chế độ tĩnh, lăn và hút (merge)."""
        tw, th, off, skew = self.layout
        split = ((2, 3), (4, 5))

        # 1. Trạng thái tĩnh
        draw_split_cubes(self.surface, split, tw, th, off, skew)

        # 2. Trạng thái active đang lăn
        draw_split_cubes(
            self.surface, split, tw, th, off, skew, anim_info=(2, 3, "R", 0.4)
        )

        # 3. Trạng thái đang hút vào nhau (Merge)
        draw_split_cubes(
            self.surface, split, tw, th, off, skew, merge_progress=0.75
        )


if __name__ == "__main__":
    unittest.main()
