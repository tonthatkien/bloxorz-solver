"""Tests for C2 split-switch activation and Game integration."""
import unittest

from game.game import Game
from game.level_loader import Bridge, Level, Switch
from game.split import activate_split_switch
from game.state import HORIZ, STAND, State, VERT


def make_level(start=(2, 1), cubes=((0, 4), (4, 0))):
    grid = ["#####", "#####", "#####", "#####", "####G"]
    switch = Switch(type="split", pos=(2, 2), cubes=list(cubes))
    return Level(
        name="split-test",
        grid=grid,
        start=start,
        goal=(4, 4),
        fragile=set(),
        bridges={},
        switches={(2, 2): switch},
    )


class TestSplitSwitchHelper(unittest.TestCase):
    def test_standing_on_split_switch_uses_configured_positions(self):
        level = make_level()
        old = State(2, 1, STAND)
        landed = State(2, 2, STAND, bridges=3)

        result = activate_split_switch(old, landed, level)

        self.assertEqual(result, State(bridges=3, split=((0, 4), (4, 0))))

    def test_laying_on_split_switch_does_not_activate(self):
        level = make_level()
        old = State(2, 1, STAND)
        landed = State(2, 2, HORIZ)

        self.assertIsNone(activate_split_switch(old, landed, level))

    def test_must_be_a_split_switch(self):
        level = make_level()
        level.switches[(2, 2)] = Switch(type="soft", pos=(2, 2))
        self.assertIsNone(
            activate_split_switch(State(2, 1), State(2, 2), level)
        )

    def test_standing_on_same_switch_does_not_retrigger(self):
        level = make_level()
        state = State(2, 2, STAND)
        self.assertIsNone(activate_split_switch(state, state, level))

    def test_adjacent_configured_cubes_are_normalized_to_full_block(self):
        level = make_level(cubes=((1, 1), (1, 2)))
        result = activate_split_switch(
            State(2, 1), State(2, 2), level
        )
        self.assertEqual(result, State(1, 1, HORIZ))

    # --- Bổ sung cho C2 ---

    def test_split_state_never_retriggers(self):
        """Một state đã split không bao giờ kích hoạt split switch lần nữa."""
        level = make_level()
        old = State(split=((0, 4), (4, 0)))
        landed = State(split=((1, 4), (4, 0)))  # cube active vừa vào switch
        # landed.split != None -> không kích hoạt dù orient/r/c bị ép STAND/0/0
        self.assertIsNone(activate_split_switch(old, landed, level))

    def test_split_switch_without_cubes_is_ignored(self):
        level = make_level()
        level.switches[(2, 2)] = Switch(type="split", pos=(2, 2), cubes=None)
        self.assertIsNone(
            activate_split_switch(State(2, 1), State(2, 2), level)
        )


class TestSplitSwitchGameIntegration(unittest.TestCase):
    def test_game_splits_when_standing_on_switch(self):
        game = Game(make_level())
        # Khối nằm ngang lăn sang trái, đứng thẳng tại (2, 2).
        state = State(2, 3, HORIZ)

        successors = game.get_successors(state)
        by_action = {action: next_state for action, next_state, _ in successors}

        self.assertEqual(
            by_action["L"],
            State(split=((0, 4), (4, 0))),
        )

    def test_split_cube_does_not_win_on_goal(self):
        game = Game(make_level(cubes=((4, 4), (0, 4))))
        self.assertFalse(game.is_goal(State(split=((4, 4), (0, 4)))))

    def test_split_cube_activates_soft_but_not_heavy_switch(self):
        for switch_type, expected_mask in (("soft", 1), ("heavy", 0)):
            with self.subTest(switch_type=switch_type):
                level = make_level()
                level.bridges = {0: Bridge(id=0, pos=(3, 3), open=False)}
                level.switches = {
                    (1, 2): Switch(type=switch_type, pos=(1, 2), targets=[0])
                }
                game = Game(level)
                state = State(split=((1, 1), (4, 0)))

                successors = game.get_successors(state)
                moved = next(next_state for action, next_state, _ in successors
                             if action == "R")

                self.assertEqual(moved.bridges, expected_mask)

    def test_split_successors_keep_fixed_action_order(self):
        game = Game(make_level())
        state = State(split=((1, 1), (3, 3)))
        actions = [action for action, _, _ in game.get_successors(state)]
        self.assertEqual(actions, sorted(actions, key=("U", "D", "L", "R", "S").index))

    # --- Bổ sung cho C2 ---

    def test_swap_control_action_s_is_generated(self):
        game = Game(make_level())
        state = State(split=((1, 1), (3, 3)))
        actions = [action for action, _, _ in game.get_successors(state)]
        self.assertIn("S", actions)

    def test_swap_control_swaps_cube_order(self):
        game = Game(make_level())
        state = State(split=((1, 1), (3, 3)))
        by_action = {a: ns for a, ns, _ in game.get_successors(state)}
        self.assertEqual(by_action["S"], State(split=((3, 3), (1, 1))))

    def test_cube_move_without_merge_keeps_split(self):
        game = Game(make_level())
        state = State(split=((1, 1), (3, 3)))
        by_action = {a: ns for a, ns, _ in game.get_successors(state)}
        self.assertEqual(by_action["R"], State(split=((1, 2), (3, 3))))

    def test_adjacent_cubes_merge_on_move(self):
        game = Game(make_level())
        # (1,1) và (1,3): active "R" -> (1,2), kề (1,3) -> merge HORIZ tại (1,2).
        state = State(split=((1, 1), (1, 3)))
        by_action = {a: ns for a, ns, _ in game.get_successors(state)}
        self.assertEqual(by_action["R"], State(1, 2, HORIZ))

    def test_cube_cannot_move_into_other_cube(self):
        game = Game(make_level())
        state = State(split=((1, 1), (1, 2)))  # đã kề -> không hợp lệ
        # move_cube raise ValueError -> get_successors nuốt lỗi, trả rỗng
        self.assertEqual(game.get_successors(state), [])


if __name__ == "__main__":
    unittest.main()