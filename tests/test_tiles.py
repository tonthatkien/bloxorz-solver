"""B2 bridge support, switch events and landing integration with the B1 loader."""
import copy
import unittest
from dataclasses import FrozenInstanceError, replace
from typing import Optional

from game.game import Game
from game.level_loader import Level, parse_level
from game.state import HORIZ, STAND, VERT, State
from game.tiles import TileRules
from tests.test_level_validation import advanced_level, basic_level


def switch_level(kind: str = "soft", mode: str = "toggle",
                 setting: Optional[str] = None) -> Level:
    """Build two independent bridges and a configurable switch at (1, 1)."""
    data = basic_level()
    data["bridges"] = [{"id": 7, "pos": [2, 4]}, {"id": 2, "pos": [2, 3]}]
    data["switches"] = [{"type": kind, "pos": [1, 1], "targets": [7], "mode": mode}]
    if setting is not None:
        data["switches"][0]["set"] = setting
    return parse_level(data)


class TestTileSupport(unittest.TestCase):
    """All terrain checks use the complete footprint and the runtime mask."""

    def test_basic_terrain_goal_and_void_follow_json_symbols(self):
        data = basic_level()
        data["grid"][0] = "#.####"
        rules = TileRules.from_level(parse_level(data))
        self.assertTrue(rules.is_supported(State(0, 0)))
        self.assertTrue(rules.is_supported(State(1, 5)))
        self.assertFalse(rules.is_supported(State(0, 1)))

    def test_entire_horizontal_and_vertical_footprints_must_stay_inside(self):
        rules = TileRules.from_level(parse_level(basic_level()))
        for state in (State(-1, 0), State(0, -1), State(4, 0), State(0, 6),
                      State(0, 5, HORIZ), State(3, 0, VERT)):
            with self.subTest(state=state):
                self.assertFalse(rules.is_supported(state))

    def test_void_under_second_horizontal_or_vertical_cell_fails(self):
        data = basic_level()
        data["grid"][1] = "#.###G"
        rules = TileRules.from_level(parse_level(data))
        self.assertFalse(rules.is_supported(State(1, 0, HORIZ)))
        self.assertFalse(rules.is_supported(State(0, 1, VERT)))

    def test_stand_on_fragile_fails_but_both_lying_orientations_pass(self):
        data = dict(basic_level(), fragile=[[1, 1], [1, 2], [2, 1]])
        rules = TileRules.from_level(parse_level(data))
        self.assertFalse(rules.is_supported(State(1, 1)))
        self.assertTrue(rules.is_supported(State(1, 1, HORIZ)))
        self.assertTrue(rules.is_supported(State(1, 1, VERT)))

    def test_lying_on_fragile_still_requires_support_under_other_cell(self):
        data = dict(basic_level(), fragile=[[1, 1]])
        data["grid"][1] = "##.##G"
        rules = TileRules.from_level(parse_level(data))
        self.assertFalse(rules.is_supported(State(1, 1, HORIZ)))

    def test_closed_and_open_bridge_use_runtime_mask(self):
        level = switch_level()
        rules = TileRules.from_level(level)
        self.assertFalse(rules.is_supported(State(2, 4, bridges=0)))
        self.assertTrue(rules.is_supported(State(2, 4, bridges=1 << 7)))
        level.bridges[7].open = True
        self.assertFalse(rules.is_supported(State(2, 4, bridges=0)))

    def test_initial_open_bridge_can_be_closed_by_runtime_mask(self):
        level = parse_level(advanced_level())
        rules = TileRules.from_level(level)
        self.assertTrue(rules.is_supported(State(2, 2, bridges=level.initial_bridge_mask())))
        self.assertFalse(rules.is_supported(State(2, 2, bridges=0)))

    def test_two_footprint_bridges_are_independent_by_sparse_id(self):
        rules = TileRules.from_level(switch_level())
        state = State(2, 3, HORIZ)
        for mask in (0, 1 << 2, 1 << 7):
            self.assertFalse(rules.is_supported(replace(state, bridges=mask)))
        self.assertTrue(rules.is_supported(replace(state, bridges=(1 << 2) | (1 << 7))))

    def test_bridge_coordinate_lookup_distinguishes_floor_and_id_zero(self):
        data = basic_level()
        data["bridges"] = [{"id": 0, "pos": [2, 2]}]
        rules = TileRules.from_level(parse_level(data))
        self.assertTrue(rules.is_bridge_open((2, 2), 1))
        self.assertFalse(rules.is_bridge_open((2, 2), 0))
        self.assertFalse(rules.is_bridge_open((0, 0), 1))
        self.assertFalse(rules.is_bridge_open((-1, 0), 1))

    def test_fragile_and_bridge_overlap_compose_instead_of_losing_weight_rule(self):
        data = basic_level()
        data["bridges"] = [{"id": 0, "pos": [1, 1]}]
        data["fragile"] = [[1, 1]]
        rules = TileRules.from_level(parse_level(data))
        self.assertFalse(rules.is_supported(State(1, 1, bridges=1)))
        self.assertTrue(rules.is_supported(State(1, 1, HORIZ, bridges=1)))
        self.assertFalse(rules.is_supported(State(1, 1, HORIZ, bridges=0)))

    def test_invalid_orientation_is_not_supported(self):
        rules = TileRules.from_level(switch_level())
        self.assertFalse(rules.is_supported(State(0, 0, orient=9)))

    def test_invalid_masks_are_rejected_instead_of_opening_all_bridges(self):
        rules = TileRules.from_level(switch_level())
        for mask in (-1, True, 1.0, "1"):
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "bridges"):
                rules.is_supported(State(0, 0, bridges=mask))
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "bridges"):
                rules.is_bridge_open((2, 4), mask)


class TestSwitchEvents(unittest.TestCase):
    """Switch activation is an entry event, using pressed state rather than anchor only."""

    def test_soft_switch_activates_for_stand_horizontal_and_vertical(self):
        rules = TileRules.from_level(switch_level())
        for pose in (STAND, HORIZ, VERT):
            with self.subTest(pose=pose):
                events = rules.detect_triggered_switches(State(0, 0), State(1, 1, pose))
                self.assertEqual([event.pos for event in events], [(1, 1)])

    def test_soft_switch_detected_at_second_footprint_cell(self):
        rules = TileRules.from_level(switch_level())
        for state in (State(1, 0, HORIZ), State(0, 1, VERT)):
            self.assertEqual(len(rules.detect_triggered_switches(State(0, 0), state)), 1)

    def test_no_contact_does_not_activate_switch(self):
        rules = TileRules.from_level(switch_level())
        self.assertEqual(rules.detect_triggered_switches(State(0, 0), State(0, 2)), ())

    def test_contact_pose_comparisons_do_not_retrigger(self):
        rules = TileRules.from_level(switch_level())
        # Synthetic pose comparisons test the event API; A1 tests check legal rolls.
        # Sustained contact also occurs when the other split cube moves or control swaps.
        for old, landed in ((State(1, 1), State(1, 1, HORIZ)),
                            (State(1, 0, HORIZ), State(1, 1, VERT)),
                            (State(1, 1, VERT), State(1, 0, HORIZ))):
            self.assertEqual(rules.detect_triggered_switches(old, landed), ())

    def test_leave_and_reenter_create_separate_activation_events(self):
        rules = TileRules.from_level(switch_level())
        off, on = State(0, 0), State(1, 1)
        self.assertEqual(len(rules.detect_triggered_switches(off, on)), 1)
        self.assertEqual(rules.detect_triggered_switches(on, off), ())
        self.assertEqual(len(rules.detect_triggered_switches(off, on)), 1)

    def test_heavy_switch_requires_full_block_standing(self):
        rules = TileRules.from_level(switch_level("heavy"))
        self.assertEqual(len(rules.detect_triggered_switches(State(0, 0), State(1, 1))), 1)
        for state in (State(1, 1, HORIZ), State(1, 1, VERT),
                      State(1, 0, HORIZ), State(0, 1, VERT)):
            self.assertEqual(rules.detect_triggered_switches(State(0, 0), state), ())

    def test_lying_contact_to_standing_enters_heavy_activation_region(self):
        rules = TileRules.from_level(switch_level("heavy"))
        for old in (State(1, 1, HORIZ), State(1, 1, VERT)):
            self.assertEqual(len(rules.detect_triggered_switches(old, State(1, 1))), 1)

    def test_heavy_contact_persists_then_reenters_after_leaving(self):
        rules = TileRules.from_level(switch_level("heavy"))
        on, off = State(1, 1), State(1, 2, HORIZ)
        self.assertEqual(rules.detect_triggered_switches(on, on), ())
        self.assertEqual(rules.detect_triggered_switches(on, off), ())
        self.assertEqual(len(rules.detect_triggered_switches(off, on)), 1)

    def test_single_cube_can_press_soft_but_never_heavy(self):
        split = State(split=((3, 3), (1, 1)))
        soft = TileRules.from_level(switch_level("soft"))
        heavy = TileRules.from_level(switch_level("heavy"))
        self.assertEqual(len(soft.detect_triggered_switches(State(0, 0), split)), 1)
        self.assertEqual(heavy.detect_triggered_switches(State(0, 0), split), ())

    def test_swapping_control_keeps_contact_and_does_not_retrigger(self):
        rules = TileRules.from_level(switch_level())
        old = State(split=((1, 1), (3, 3)))
        swapped = replace(old, split=tuple(reversed(old.split)))
        self.assertEqual(rules.detect_triggered_switches(old, swapped), ())

    def test_split_switch_metadata_does_not_execute_split_gameplay(self):
        rules = TileRules.from_level(parse_level(advanced_level()))
        old, landed = State(0, 0), State(0, 2)
        self.assertEqual(rules.detect_triggered_switches(old, landed), ())
        self.assertEqual(rules.resolve_landing(old, landed), landed)
        self.assertIsNone(rules.resolve_landing(old, landed).split)


class TestSwitchEffects(unittest.TestCase):
    """Effects preserve unrelated bits and compose deterministically."""

    def test_toggle_opens_then_closes_without_changing_other_bits(self):
        rules = TileRules.from_level(switch_level())
        events = rules.detect_triggered_switches(State(0, 0), State(1, 1))
        mask = (1 << 2) | (1 << 12)
        opened = rules.apply_switch_effects(mask, events)
        self.assertEqual(opened, mask | (1 << 7))
        self.assertEqual(rules.apply_switch_effects(opened, events), mask)

    def test_permanent_open_and_close_are_idempotent_and_preserve_unrelated_bits(self):
        for setting in ("open", "close"):
            rules = TileRules.from_level(switch_level(mode="permanent", setting=setting))
            events = rules.detect_triggered_switches(State(0, 0), State(1, 1))
            for mask in (1 << 2, (1 << 2) | (1 << 7)):
                result = rules.apply_switch_effects(mask, events)
                expected = (mask | (1 << 7)) if setting == "open" else (mask & ~(1 << 7))
                self.assertEqual(result, expected)
                self.assertEqual(rules.apply_switch_effects(result, events), expected)

    def test_toggle_multiple_sparse_targets_does_not_use_json_order(self):
        level = switch_level()
        level.switches[(1, 1)].targets = [2, 7]
        rules = TileRules.from_level(level)
        events = rules.detect_triggered_switches(State(0, 0), State(1, 1))
        self.assertEqual(rules.apply_switch_effects(0, events), (1 << 2) | (1 << 7))

    def test_permanent_multiple_targets(self):
        for setting in ("open", "close"):
            level = switch_level(mode="permanent", setting=setting)
            level.switches[(1, 1)].targets = [2, 7]
            rules = TileRules.from_level(level)
            events = rules.detect_triggered_switches(State(0, 0), State(1, 1))
            all_targets = (1 << 2) | (1 << 7)
            start, expected = (0, all_targets) if setting == "open" else (all_targets, 0)
            self.assertEqual(rules.apply_switch_effects(start, events), expected)

    def test_no_events_preserves_mask(self):
        rules = TileRules.from_level(switch_level())
        self.assertEqual(rules.apply_switch_effects(1 << 7, ()), 1 << 7)

    def test_simultaneous_toggles_same_target_cancel(self):
        data = basic_level()
        data["bridges"] = [{"id": 7, "pos": [3, 3]}]
        data["switches"] = [
            {"type": "soft", "pos": [1, 1], "targets": [7]},
            {"type": "soft", "pos": [1, 2], "targets": [7]}]
        rules = TileRules.from_level(parse_level(data))
        events = rules.detect_triggered_switches(State(0, 0), State(1, 1, HORIZ))
        self.assertEqual(len(events), 2)
        self.assertEqual(rules.apply_switch_effects(0, events), 0)

    def test_mixed_simultaneous_effects_use_coordinate_order_regardless_of_json_order(self):
        data = basic_level()
        data["bridges"] = [{"id": 7, "pos": [3, 3]}]
        data["switches"] = [
            {"type": "soft", "pos": [1, 2], "targets": [7]},
            {"type": "soft", "pos": [1, 1], "targets": [7],
             "mode": "permanent", "set": "open"}]
        first = TileRules.from_level(parse_level(data))
        data["switches"].reverse()
        second = TileRules.from_level(parse_level(data))
        for rules in (first, second):
            events = rules.detect_triggered_switches(State(0, 0), State(1, 1, HORIZ))
            self.assertEqual([event.pos for event in events], [(1, 1), (1, 2)])
            self.assertEqual(rules.apply_switch_effects(0, reversed(events)), 0)

    def test_switch_without_targets_is_harmless(self):
        level = switch_level()
        level.switches[(1, 1)].targets = []
        rules = TileRules.from_level(level)
        events = rules.detect_triggered_switches(State(0, 0), State(1, 1))
        self.assertEqual(rules.apply_switch_effects(17, events), 17)


class TestLandingIntegration(unittest.TestCase):
    """Resolve caller-provided poses without implementing A1 rolling or Game successors."""

    def test_landing_on_soft_switch_creates_new_immutable_state(self):
        rules = TileRules.from_level(switch_level())
        old, landed = State(0, 0), State(1, 1)
        result = rules.resolve_landing(old, landed)
        self.assertEqual(result, State(1, 1, bridges=1 << 7))
        self.assertEqual((old.bridges, landed.bridges), (0, 0))
        self.assertIsNot(result, landed)
        with self.assertRaises(FrozenInstanceError):
            result.bridges = 0

    def test_old_mask_is_authoritative_over_candidate_mask(self):
        rules = TileRules.from_level(switch_level())
        self.assertIsNone(rules.resolve_landing(State(0, 0), State(2, 4, bridges=1 << 7)))
        old = State(0, 0, bridges=1 << 7)
        self.assertEqual(rules.resolve_landing(old, State(2, 4)), State(2, 4, bridges=1 << 7))

    def test_open_bridge_can_be_crossed_after_prior_switch_activation(self):
        rules = TileRules.from_level(switch_level())
        pressed = rules.resolve_landing(State(0, 0), State(1, 1))
        crossed = rules.resolve_landing(pressed, State(2, 4))
        self.assertEqual(crossed, State(2, 4, bridges=1 << 7))

    def test_pre_effect_support_prevents_opening_bridge_under_falling_block(self):
        level = switch_level()
        level.switches[(1, 1)].pos = (2, 3)
        level.switches = {(2, 3): level.switches[(1, 1)]}
        rules = TileRules.from_level(level)
        # Candidate covers both closed bridges, even though one cell carries a switch.
        self.assertIsNone(rules.resolve_landing(State(0, 0), State(2, 3, HORIZ)))

    def test_switch_closing_occupied_bridge_rejects_landing_after_effect(self):
        data = basic_level()
        data["bridges"] = [{"id": 7, "pos": [1, 2], "open": True}]
        data["switches"] = [{"type": "soft", "pos": [1, 1], "targets": [7]}]
        rules = TileRules.from_level(parse_level(data))
        old = State(0, 1, HORIZ, bridges=1 << 7)
        landed = State(1, 1, HORIZ)
        self.assertIsNone(rules.resolve_landing(old, landed))
        self.assertEqual(old.bridges, 1 << 7)
        self.assertTrue(rules.is_bridge_open((1, 2), old.bridges))

    def test_switch_on_bridge_that_closes_itself_rejects_landing(self):
        data = basic_level()
        data["bridges"] = [{"id": 0, "pos": [1, 1], "open": True}]
        data["switches"] = [{"type": "heavy", "pos": [1, 1], "targets": [0],
                             "mode": "permanent", "set": "close"}]
        rules = TileRules.from_level(parse_level(data))
        self.assertIsNone(rules.resolve_landing(State(0, 0, bridges=1), State(1, 1)))

    def test_lying_to_standing_fragile_fails_before_switch_effects(self):
        data = basic_level()
        data["fragile"] = [[1, 3]]
        data["bridges"] = [{"id": 2, "pos": [3, 3]}]
        data["switches"] = [{"type": "soft", "pos": [1, 3], "targets": [2]}]
        rules = TileRules.from_level(parse_level(data))
        self.assertIsNone(rules.resolve_landing(State(1, 1, HORIZ), State(1, 3)))

    def test_standing_to_lying_on_fragile_succeeds(self):
        data = dict(basic_level(), fragile=[[1, 2], [1, 3]])
        rules = TileRules.from_level(parse_level(data))
        self.assertEqual(rules.resolve_landing(State(1, 1), State(1, 2, HORIZ)),
                         State(1, 2, HORIZ))

    def test_toggle_reentry_toggles_again_while_sustained_contact_does_not(self):
        rules = TileRules.from_level(switch_level())
        first = rules.resolve_landing(State(1, 0), State(1, 1))
        sustained = rules.resolve_landing(first, State(1, 1, HORIZ))
        self.assertEqual(sustained.bridges, 1 << 7)
        left = rules.resolve_landing(sustained, State(0, 0))
        returned = rules.resolve_landing(left, State(1, 1))
        self.assertEqual(returned.bridges, 0)

    def test_level_and_runtime_snapshot_remain_unchanged_after_success_and_failure(self):
        level = switch_level()
        before = copy.deepcopy(level)
        rules = TileRules.from_level(level)
        for _ in range(2):
            self.assertEqual(rules.resolve_landing(State(0, 0), State(1, 1)).bridges, 1 << 7)
            self.assertIsNone(rules.resolve_landing(State(0, 0), State(2, 4)))
        self.assertEqual(level, before)
        with self.assertRaises(TypeError):
            rules.bridges[(2, 4)] = 2
        with self.assertRaises(FrozenInstanceError):
            rules.switches[0].mode = "permanent"

    def test_snapshot_is_detached_from_later_mutations_of_public_level(self):
        level = switch_level()
        rules = TileRules.from_level(level)
        level.grid[0] = "......"
        level.fragile.add((0, 0))
        level.bridges[7].pos = (0, 0)
        level.switches[(1, 1)].targets.append(2)
        self.assertTrue(rules.is_supported(State(0, 0)))
        self.assertEqual(rules.resolve_landing(State(0, 0), State(1, 1)).bridges, 1 << 7)

    def test_same_state_and_landing_are_deterministic_and_hashable(self):
        rules = TileRules.from_level(switch_level())
        old, pose = State(0, 0), State(1, 1, HORIZ)
        results = [rules.resolve_landing(old, pose) for _ in range(4)]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(set(results)), 1)
        self.assertNotEqual(results[0], replace(results[0], bridges=0))
        self.assertEqual(len({results[0], replace(results[0], bridges=0)}), 2)

    def test_split_fields_survive_bridge_updates_without_split_gameplay(self):
        rules = TileRules.from_level(switch_level())
        pose = State(split=((1, 1), (3, 3)))
        result = rules.resolve_landing(State(0, 0), pose)
        self.assertEqual(result.split, pose.split)
        self.assertEqual((result.r, result.c, result.orient), (0, 0, STAND))
        self.assertEqual(result.bridges, 1 << 7)
        self.assertEqual(pose.bridges, 0)

    def test_initial_state_and_restart_recover_initial_bridge_mask(self):
        level = parse_level(advanced_level())
        game = Game(level)
        initial = game.initial_state()
        self.assertEqual(initial.bridges, 1 << 7)
        _ = TileRules.from_level(level).resolve_landing(initial, State(1, 1))
        self.assertEqual(game.initial_state(), initial)
        self.assertEqual(game.initial_state().bridges, 1 << 7)


if __name__ == "__main__":
    unittest.main()
