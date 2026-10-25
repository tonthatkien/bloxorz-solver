"""Real-roll integration tests: B2 tile rules driven by A1's actual Block.roll."""
import unittest
from typing import Optional

from game.block import Block
from game.level_loader import parse_level
from game.state import HORIZ, State
from game.tiles import TileRules


def resolve_roll(rules: TileRules, old: State, action: str) -> Optional[State]:
    """Adapt A1's rolled pose to B2 without implementing or modifying Game."""
    block = Block(old.r, old.c, old.orient).roll(action)
    return rules.resolve_landing(old, State(block.r, block.c, block.orient))


class TestA1TileIntegration(unittest.TestCase):
    """Use the actual A1 roll table instead of duplicating movement rules in B2."""

    def test_standing_rolls_to_lying_across_fragile(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5],
                "fragile": [[0, 1], [0, 2]]}
        rules = TileRules.from_level(parse_level(data))
        result = resolve_roll(rules, State(0, 0), "R")
        self.assertEqual((result.r, result.c, result.orient), (0, 1, HORIZ))

    def test_lying_rolls_to_standing_on_fragile_and_falls(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5],
                "fragile": [[0, 3]]}
        rules = TileRules.from_level(parse_level(data))
        lying = resolve_roll(rules, State(0, 0), "R")
        self.assertIsNone(resolve_roll(rules, lying, "R"))

    def test_soft_switch_at_second_cell_opens_bridge_before_next_roll(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5],
                "bridges": [{"id": 7, "pos": [0, 3]}],
                "switches": [{"type": "soft", "pos": [0, 2], "targets": [7]}]}
        rules = TileRules.from_level(parse_level(data))
        lying = resolve_roll(rules, State(0, 0), "R")
        self.assertEqual(lying.bridges, 1 << 7)
        crossed = resolve_roll(rules, lying, "R")
        self.assertEqual(crossed, State(0, 3, bridges=1 << 7))
        self.assertIsNone(resolve_roll(rules, State(0, 1, HORIZ), "R"))

    def test_heavy_ignores_lying_contact_then_activates_on_upright_landing(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5],
                "bridges": [{"id": 7, "pos": [0, 4]}],
                "switches": [{"type": "heavy", "pos": [0, 2], "targets": [7]},
                             {"type": "heavy", "pos": [0, 3], "targets": [7]}]}
        rules = TileRules.from_level(parse_level(data))
        lying = resolve_roll(rules, State(0, 0), "R")
        self.assertEqual(lying.bridges, 0)
        upright = resolve_roll(rules, lying, "R")
        self.assertEqual(upright, State(0, 3, bridges=1 << 7))

    def test_real_roll_closing_bridge_under_second_cell_falls(self):
        data = {"grid": ["######", "#####G"], "start": [0, 0], "goal": [1, 5],
                "bridges": [{"id": 2, "pos": [1, 2], "open": True}],
                "switches": [{"type": "soft", "pos": [1, 1], "targets": [2]}]}
        rules = TileRules.from_level(parse_level(data))
        lying = resolve_roll(rules, State(0, 0, bridges=1 << 2), "R")
        self.assertIsNone(resolve_roll(rules, lying, "D"))
        self.assertEqual(lying.bridges, 1 << 2)

    def test_real_roll_leaves_and_reenters_toggle_switch(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5],
                "bridges": [{"id": 7, "pos": [0, 4]}],
                "switches": [{"type": "soft", "pos": [0, 1], "targets": [7]}]}
        rules = TileRules.from_level(parse_level(data))
        first = resolve_roll(rules, State(0, 0), "R")
        self.assertEqual(first.bridges, 1 << 7)
        left = resolve_roll(rules, first, "L")
        self.assertEqual(left, State(0, 0, bridges=1 << 7))
        second = resolve_roll(rules, left, "R")
        self.assertEqual(second.bridges, 0)

    def test_real_roll_outside_board_is_not_a_valid_landing(self):
        data = {"grid": ["#####G"], "start": [0, 0], "goal": [0, 5]}
        rules = TileRules.from_level(parse_level(data))
        self.assertIsNone(resolve_roll(rules, State(0, 0), "L"))
        self.assertIsNone(resolve_roll(rules, State(0, 0), "U"))


if __name__ == "__main__":
    unittest.main()
