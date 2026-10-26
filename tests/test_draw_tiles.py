"""Headless rendering regressions for D3 and the shared D1 scene pipeline."""
import copy
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.level_loader import parse_level
from game.state import State
from gui.draw import calculate_iso_layout, draw_scene
from gui.draw_tiles import (
    BRIDGE_TOP, FRAGILE_TOP, draw_bridge_tile, draw_heavy_switch,
    draw_soft_switch, draw_split_switch, terrain_view,
)
from gui.render_board import C, grid_to_iso


def advanced_scene() -> dict:
    """Return separated special tiles and sparse bridge IDs, including bit 63."""
    return {
        "grid": ["########"] * 3 + ["#######G"], "start": [0, 0], "goal": [3, 7],
        "fragile": [[1, 1]],
        "bridges": [{"id": 2, "pos": [1, 3]}, {"id": 63, "pos": [1, 5], "open": True}],
        "switches": [{"type": "soft", "pos": [2, 1], "targets": [2]},
                     {"type": "heavy", "pos": [2, 3], "targets": [63]},
                     {"type": "split", "pos": [2, 5], "cubes": [[0, 2], [0, 5]]}],
    }


class TestAdvancedRendering(unittest.TestCase):
    """Pixels, draw order, animation masks and input immutability are observable contracts."""

    def setUp(self) -> None:
        self.level = parse_level(advanced_scene())
        self.surface = pygame.Surface((900, 500))
        self.background = (30, 50, 80)
        self.off = (60, 100)
        self.tw, self.th, self.skew = 68, 38, 22

    def render(self, mask: int, state: State | None = None, **effects) -> None:
        """Render a clean frame with an explicit display mask."""
        self.surface.fill(self.background)
        draw_scene(self.surface, self.level, state, self.tw, self.th, self.off,
                   self.skew, bridge_mask=mask, **effects)

    def pixel(self, r: int, c: int, u: float = 0.5, v: float = 0.5) -> tuple:
        """Sample a point on the existing oblique tile geometry."""
        x, y = grid_to_iso(r, c, self.tw, self.th, self.off, self.skew)
        return tuple(self.surface.get_at((round(x + u * self.tw + v * self.skew),
                                          round(y + v * self.th))))[:3]

    def test_fragile_has_orange_surface(self) -> None:
        self.render(0)
        self.assertEqual(self.pixel(1, 1, 0.2), FRAGILE_TOP)

    def test_runtime_mask_overrides_json_and_supports_sparse_ids(self) -> None:
        self.render(1 << 2)
        self.assertEqual(self.pixel(1, 3), BRIDGE_TOP)
        self.assertEqual(self.pixel(1, 5), self.background)
        self.render(1 << 63)
        self.assertEqual(self.pixel(1, 3), self.background)
        self.assertEqual(self.pixel(1, 5), BRIDGE_TOP)

    def test_scene_uses_state_mask_when_no_override_is_passed(self) -> None:
        self.surface.fill(self.background)
        draw_scene(self.surface, self.level, State(0, 0, bridges=1 << 2),
                   self.tw, self.th, self.off, self.skew)
        self.assertEqual(self.pixel(1, 3), BRIDGE_TOP)
        self.assertEqual(self.pixel(1, 5), self.background)

    def test_state_none_uses_initial_mask_before_any_runtime_snapshot(self) -> None:
        self.surface.fill(self.background)
        draw_scene(self.surface, self.level, None, self.tw, self.th, self.off, self.skew)
        self.assertEqual(self.pixel(1, 3), self.background)
        self.assertEqual(self.pixel(1, 5), BRIDGE_TOP)

    def test_animation_without_static_state_preserves_runtime_bridge_mask(self) -> None:
        for effects in ({"spawn_state": (0, 0, 0, 1.0)},
                        {"anim_state": (0, 0, 0, "R", 0.5)},
                        {"fall_state": ("goal", 3, 7, 0, 120)},
                        {"fall_state": ("shatter", [], 0.2, 200)}):
            with self.subTest(effects=effects):
                self.render(1 << 2, **effects)
                self.assertEqual(self.pixel(1, 3), BRIDGE_TOP)
                self.assertEqual(self.pixel(1, 5), self.background)

    def test_closed_bridge_draws_no_surface(self) -> None:
        self.surface.fill(self.background)
        before = pygame.image.tostring(self.surface, "RGB")
        draw_bridge_tile(self.surface, self.level, 1, 3, 100, 100,
                         self.tw, self.th, self.skew, opened=False)
        self.assertEqual(pygame.image.tostring(self.surface, "RGB"), before)

    def test_closed_bridge_exposes_neighbor_cliff_geometry(self) -> None:
        self.render(0)
        x, y = grid_to_iso(0, 3, self.tw, self.th, self.off, self.skew)
        sample = (x + self.skew + self.tw // 2, y + self.th + 7)
        self.assertEqual(tuple(self.surface.get_at(sample))[:3], C["soil_front"])
        self.render(1 << 2)
        self.assertNotEqual(tuple(self.surface.get_at(sample))[:3], C["soil_front"])

    def test_switch_shapes_are_distinct_at_normal_and_small_sizes(self) -> None:
        for tw, th, skew in ((68, 38, 22), (25, 14, 8), (10, 6, 3)):
            images = []
            for draw in (draw_soft_switch, draw_heavy_switch, draw_split_switch):
                surface = pygame.Surface((120, 80))
                surface.fill(self.background)
                draw(surface, 20, 20, tw, th, skew)
                images.append(pygame.image.tostring(surface, "RGB"))
            with self.subTest(size=(tw, th)):
                self.assertEqual(len(set(images)), 3)

    def test_terrain_markers_are_drawn_before_the_block(self) -> None:
        def block_on_top(*args) -> None:
            self.assertEqual(self.pixel(1, 1, 0.2), FRAGILE_TOP)
        with patch("gui.draw.draw_block", side_effect=block_on_top) as block:
            self.render(0, State(0, 0))
            block.assert_called_once()

    def test_render_does_not_mutate_level_or_state(self) -> None:
        level_before = copy.deepcopy(self.level)
        state = State(0, 0, bridges=1 << 2)
        self.render(state.bridges, state)
        self.assertEqual(self.level, level_before)
        self.assertEqual(state, State(0, 0, bridges=1 << 2))
        self.assertEqual(terrain_view(self.level, 0).grid[1][3], ".")
        self.assertEqual(self.level.grid[1][3], "#")

    def test_small_and_large_boards_use_the_shared_scaled_layout(self) -> None:
        for rows, cols in ((2, 3), (18, 26)):
            with self.subTest(size=(rows, cols)):
                grid = ["#" * cols for _ in range(rows)]
                grid[-1] = "#" * (cols - 1) + "G"
                level = parse_level({"grid": grid, "start": [0, 0],
                                     "goal": [rows - 1, cols - 1], "fragile": [[0, 1]]})
                tw, th, off, skew = calculate_iso_layout(rows, cols, 900, 500)
                draw_scene(self.surface, level, None, tw, th, off, skew)

    def test_restart_repaints_initial_bridge_state(self) -> None:
        self.render(1 << 2)
        self.render(self.level.initial_bridge_mask())
        self.assertEqual(self.pixel(1, 3), self.background)
        self.assertEqual(self.pixel(1, 5), BRIDGE_TOP)


if __name__ == "__main__":
    unittest.main()
