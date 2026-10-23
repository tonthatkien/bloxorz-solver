"""Unit test giao diện Game: initial_state, is_goal, get_successors (A1)."""
import unittest
from types import SimpleNamespace

from game.block import DOWN, HORIZ, RIGHT, STAND, VERT
from game.game import Game
from game.state import State

GRID = [
    "###..",
    "###..",
    "##G##",
    "..###",
]


def make_game(cost_fn=None):
    # Level giả tối thiểu, để test không phụ thuộc file JSON hay level_loader
    level = SimpleNamespace(start=(0, 0), grid=GRID, initial_bridge_mask=lambda: 0)
    return Game(level, cost_fn)


class TestInitialAndGoal(unittest.TestCase):
    def test_initial_state_is_standing_on_start(self):
        self.assertEqual(make_game().initial_state(), State(0, 0, STAND, 0, None))

    def test_standing_on_goal_is_goal(self):
        self.assertTrue(make_game().is_goal(State(2, 2, STAND, 0, None)))

    def test_lying_over_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(State(2, 1, HORIZ, 0, None)))

    def test_standing_off_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(make_game().initial_state()))


class TestSuccessors(unittest.TestCase):
    def test_invalid_moves_are_excluded_and_order_is_fixed(self):
        actions = [a for a, _, _ in make_game().get_successors(State(0, 0, STAND, 0, None))]
        self.assertEqual(actions, [DOWN, RIGHT])

    def test_successor_states_and_default_cost(self):
        result = make_game().get_successors(State(0, 0, STAND, 0, None))
        self.assertEqual(result[0], (DOWN, State(1, 0, VERT, 0, None), 1.0))
        self.assertEqual(result[1], (RIGHT, State(0, 1, HORIZ, 0, None), 1.0))

    def test_custom_cost_fn_is_used(self):
        game = make_game(cost_fn=lambda old, action, new: 5.0)
        costs = [c for _, _, c in game.get_successors(State(0, 0, STAND, 0, None))]
        self.assertEqual(costs, [5.0, 5.0])

    def test_get_successors_has_no_side_effects(self):
        game = make_game()
        state = State(0, 0, STAND, 0, None)
        self.assertEqual(game.get_successors(state), game.get_successors(state))
        self.assertEqual(state, State(0, 0, STAND, 0, None))


if __name__ == "__main__":
    unittest.main()