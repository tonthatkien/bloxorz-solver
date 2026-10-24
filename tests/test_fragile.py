"""B1 fragile checks using post-movement footprints without modifying A1 or Game."""
import unittest
from dataclasses import FrozenInstanceError, replace

from game.fragile import is_fragile_safe
from game.state import HORIZ, STAND, VERT, State, cells


class TestFragile(unittest.TestCase):
    """Verify weight rules and the unchanged shared State contract."""

    def test_standing_on_fragile_fails(self):
        self.assertFalse(is_fragile_safe(State(1, 1), {(1, 1)}))

    def test_horizontal_and_vertical_across_multiple_fragile_are_safe(self):
        for orientation in (HORIZ, VERT):
            state = State(1, 1, orientation)
            self.assertTrue(is_fragile_safe(state, set(cells(state))))

    def test_standing_on_normal_floor_or_goal_is_fragile_safe(self):
        self.assertTrue(is_fragile_safe(State(1, 1), {(1, 2)}))
        self.assertTrue(is_fragile_safe(State(1, 1), set()))

    def test_lying_to_standing_checks_destination(self):
        old = State(1, 1, HORIZ)
        landed = State(1, 3, STAND)
        self.assertTrue(is_fragile_safe(old, {(1, 3)}))
        self.assertFalse(is_fragile_safe(landed, {(1, 3)}))

    def test_standing_to_lying_does_not_destroy_tiles(self):
        fragile = {(1, 2), (1, 3)}
        old = State(1, 1)
        landed = State(1, 2, HORIZ)
        self.assertTrue(is_fragile_safe(old, fragile))
        self.assertTrue(is_fragile_safe(landed, fragile))
        self.assertEqual(fragile, {(1, 2), (1, 3)})

    def test_state_bridge_masks_are_distinct_visited_keys(self):
        closed = State(1, 1, HORIZ, bridges=0)
        opened = replace(closed, bridges=1 << 7)
        self.assertNotEqual(closed, opened)
        self.assertEqual(len({closed, opened}), 2)
        self.assertEqual({closed: "closed", opened: "open"}[opened], "open")
        self.assertEqual(hash(opened), hash(replace(opened)))
        self.assertEqual(closed.bridges, 0)

    def test_state_immutable_and_split_fields_preserved_when_replacing_mask(self):
        state = State(split=((1, 1), (3, 3)))
        with self.assertRaises(FrozenInstanceError):
            state.bridges = 1
        updated = replace(state, bridges=1 << 2)
        self.assertEqual(updated.split, state.split)
        self.assertEqual(updated.orient, STAND)
        self.assertEqual(state.bridges, 0)
        self.assertTrue(is_fragile_safe(updated, {(1, 1), (3, 3)}))


if __name__ == "__main__":
    unittest.main()
