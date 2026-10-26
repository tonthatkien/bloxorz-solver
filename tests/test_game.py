"""Unit test giao diện Game: initial_state, is_goal, get_successors (A2)."""
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
# Lưới 5x5 toàn sàn: từ (2,2) đứng thì cả 4 hướng đều hợp lệ.
OPEN_GRID = ["#####"] * 5
LEVEL_PATH = Path(__file__).resolve().parent.parent / "levels" / "g1_basic_01.json"


def make_game(cost_fn=None, grid=GRID):
    # Level giả tối thiểu, để test không phụ thuộc file JSON hay level_loader
    level = SimpleNamespace(start=(0, 0), grid=grid, initial_bridge_mask=lambda: 0)
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
    def test_moves_off_the_grid_are_excluded(self):
        actions = [a for a, _, _ in make_game().get_successors(State(0, 0, STAND, 0, None))]
        self.assertEqual(actions, [DOWN, RIGHT])

    def test_whole_block_over_void_is_excluded(self):
        # HORIZ ở (0,1): R lăn thành STAND ở (0,3) là ô '.', U ra ngoài lưới.
        actions = [a for a, _, _ in make_game().get_successors(State(0, 1, HORIZ, 0, None))]
        self.assertEqual(actions, [DOWN, LEFT])

    def test_half_block_over_void_is_excluded(self):
        # STAND ở (1,1): D để nửa khối ở (3,1) là '.', R để nửa khối ở (1,3) là '.',
        # U và L ra ngoài lưới -> không còn nước đi nào.
        self.assertEqual(make_game().get_successors(State(1, 1, STAND, 0, None)), [])

    def test_successor_order_with_all_four_directions(self):
        actions = [a for a, _, _ in
                   make_game(grid=OPEN_GRID).get_successors(State(2, 2, STAND, 0, None))]
        self.assertEqual(actions, [UP, DOWN, LEFT, RIGHT])

    def test_successor_order_skips_invalid_direction(self):
        # Từ ô đích: D ra ngoài lưới nên chỉ còn U, L, R (vẫn đúng thứ tự).
        actions = [a for a, _, _ in make_game().get_successors(State(2, 2, STAND, 0, None))]
        self.assertEqual(actions, [UP, LEFT, RIGHT])

    def test_successor_states_and_default_cost(self):
        result = make_game().get_successors(State(0, 0, STAND, 0, None))
        self.assertEqual(result[0], (DOWN, State(1, 0, VERT, 0, None), 1.0))
        self.assertEqual(result[1], (RIGHT, State(0, 1, HORIZ, 0, None), 1.0))

    def test_successors_preserve_bridges_mask(self):
        # TODO [B]: khi công tắc đổi mask thì test này phải cập nhật theo.
        # TODO [C]: khi có tách/ghép, thêm test giữ split khác None.
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
        successors = game.get_successors(start)
        self.assertTrue(successors)
        for _, new, cost in successors:
            self.assertEqual(cost, 1.0)
            self.assertEqual(new.bridges, start.bridges)


if __name__ == "__main__":
    unittest.main()