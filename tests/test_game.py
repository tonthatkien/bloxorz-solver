"""Unit test giao diện Game: initial_state, is_goal, get_successors (A1)."""
import unittest
from pathlib import Path
from types import SimpleNamespace

from game.block import DOWN, LEFT, RIGHT, UP
from game.game import Game
from game.level_loader import load_level
from game.state import HORIZ, STAND, VERT, State

GRID = [
    "###..",
    "###..",
    "##G##",
    "..###",
]
LEVEL_PATH = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"


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

    def test_vertical_over_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(State(2, 2, VERT, 0, None)))

    def test_split_state_is_never_goal(self):
        # Phòng thủ: state chuẩn hóa không dựng ra tổ hợp này, nhưng is_goal vẫn phải từ chối.
        self.assertFalse(make_game().is_goal(State(2, 2, STAND, 0, ((0, 0), (0, 1)))))

    def test_standing_off_goal_is_not_goal(self):
        self.assertFalse(make_game().is_goal(make_game().initial_state()))


class TestSuccessors(unittest.TestCase):
    def test_invalid_moves_are_excluded(self):
        actions = [a for a, _, _ in make_game().get_successors(State(0, 0, STAND, 0, None))]
        self.assertEqual(actions, [DOWN, RIGHT])

    def test_successor_order_is_u_d_l_r(self):
        # Từ ô đích: U, L, R hợp lệ; D ra ngoài lưới nên bị loại.
        actions = [a for a, _, _ in make_game().get_successors(State(2, 2, STAND, 0, None))]
        self.assertEqual(actions, [UP, LEFT, RIGHT])

    def test_successor_states_and_default_cost(self):
        result = make_game().get_successors(State(0, 0, STAND, 0, None))
        self.assertEqual(result[0], (DOWN, State(1, 0, VERT, 0, None), 1.0))
        self.assertEqual(result[1], (RIGHT, State(0, 1, HORIZ, 0, None), 1.0))

    def test_successors_preserve_bridges_and_split(self):
        # TODO [B]: khi công tắc đổi mask thì test này phải cập nhật theo.
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
        # Bắt lỗi khi Level thật đổi tên trường mà level giả ở trên không biết.
        level = load_level(str(LEVEL_PATH))
        game = Game(level)
        start = game.initial_state()
        self.assertEqual((start.r, start.c), level.start)
        self.assertEqual(start.bridges, level.initial_bridge_mask())
        for _, new, cost in game.get_successors(start):
            self.assertEqual(cost, 1.0)
            self.assertEqual(new.bridges, start.bridges)


if __name__ == "__main__":
    unittest.main()