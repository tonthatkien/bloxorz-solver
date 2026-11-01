"""Unit test giao diện Game: initial_state, is_goal, get_successors (A2)."""
import unittest
from pathlib import Path
from types import SimpleNamespace

from game.block import DOWN, LEFT, RIGHT, UP
from game.game import Game
from game.state import HORIZ, STAND, VERT, State
from game.level_loader import Level, load_level

GRID = [
    "###..",
    "###..",
    "##G##",
    "..###",
]
OPEN_GRID = ["#####"] * 5
LEVEL_PATH = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"


def make_game(cost_fn=None, grid=GRID):
    level = Level(
        name="test",
        grid=grid,
        start=(0, 0),
        goal=(2, 2),
        fragile=set(),
        bridges={},
        switches={},
    )
    return Game(level, cost_fn)


class TestInitialAndGoal(unittest.TestCase):
    def test_initial_state_is_standing_on_start(self):
        self.assertEqual(make_game().initial_state(), State(0, 0, STAND, 0, None))

    def test_standing_on_goal_is_goal(self):
        self.assertTrue(make_game().is_goal(State(2, 2, STAND, 0, None)))

    def test_lying_over_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(State(2, 1, HORIZ, 0, None)))

    def test_vertical_over_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(State(2, 2, VERT, 0, None)))

    def test_split_state_is_never_goal(self):
        self.assertFalse(make_game().is_goal(State(2, 2, STAND, 0, ((0, 0), (0, 1)))))

    def test_standing_off_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(make_game().initial_state()))


class TestSuccessors(unittest.TestCase):
    def test_moves_off_the_grid_are_excluded(self):
        actions = [a for a, _, _ in make_game().get_successors(State(0, 0, STAND, 0, None))]
        self.assertEqual(actions, [DOWN, RIGHT])

    def test_whole_block_over_void_is_excluded(self):
        actions = [a for a, _, _ in make_game().get_successors(State(0, 1, HORIZ, 0, None))]
        self.assertEqual(actions, [DOWN, LEFT])

    def test_half_block_over_void_is_excluded(self):
        self.assertEqual(make_game().get_successors(State(1, 1, STAND, 0, None)), [])

    def test_successor_order_with_all_four_directions(self):
        actions = [a for a, _, _ in
                   make_game(grid=OPEN_GRID).get_successors(State(2, 2, STAND, 0, None))]
        self.assertEqual(actions, [UP, DOWN, LEFT, RIGHT])

    def test_successor_order_skips_invalid_direction(self):
        actions = [a for a, _, _ in make_game().get_successors(State(2, 2, STAND, 0, None))]
        self.assertEqual(actions, [UP, LEFT, RIGHT])

    def test_successor_states_and_default_cost(self):
        result = make_game().get_successors(State(0, 0, STAND, 0, None))
        self.assertEqual(result[0], (DOWN, State(1, 0, VERT, 0, None), 1.0))
        self.assertEqual(result[1], (RIGHT, State(0, 1, HORIZ, 0, None), 1.0))

    def test_successors_preserve_bridges_mask(self):
        successors = make_game().get_successors(State(0, 0, STAND, 5, None))
        self.assertTrue(successors)
        for _, new, _ in successors:
            self.assertEqual(new.bridges, 5)
            self.assertIsNone(new.split)

    def test_custom_cost_fn_is_used(self):
        calls = []
        game = make_game(cost_fn=lambda old, action, new: calls.append((old, action, new)) or 5.0)
        start = State(0, 0, STAND, 0, None)
        costs = [c for _, _, c in game.get_successors(start)]
        self.assertEqual(costs, [5.0, 5.0])
        self.assertEqual(calls, [
            (start, DOWN, State(1, 0, VERT, 0, None)),
            (start, RIGHT, State(0, 1, HORIZ, 0, None)),
        ])

    def test_get_successors_has_no_side_effects(self):
        game = make_game()
        state = State(0, 0, STAND, 0, None)
        self.assertEqual(game.get_successors(state), game.get_successors(state))
        self.assertEqual(state, State(0, 0, STAND, 0, None))


class TestWithRealLevel(unittest.TestCase):
    def test_game_works_on_loaded_level(self):
        level = load_level(str(LEVEL_PATH))
        game = Game(level)
        start = game.initial_state()
        self.assertEqual((start.r, start.c), level.start)
        self.assertEqual(start.bridges, level.initial_bridge_mask())
        successors = game.get_successors(start)
        self.assertTrue(successors)
        for _, new, cost in successors:
            self.assertEqual(cost, 1.0)
            self.assertEqual(new.bridges, start.bridges)


if __name__ == "__main__":
    unittest.main()