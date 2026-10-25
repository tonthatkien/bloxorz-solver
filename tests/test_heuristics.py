"""Unit tests cho solvers/heuristics.py
"""
import math
import unittest
from unittest.mock import MagicMock

from game.game import Game
from game.level_loader import Level, load_level
from game.state import HORIZ, STAND, VERT, State
from solvers.heuristics import (
    COST_FRAGILE,
    COST_MIN,
    COST_NORMAL,
    COST_SWAP,
    COST_SWITCH,
    h_manhattan,
    h_manhattan_orient,
    h_relaxed_maze,
    h_zero,
    make_cost_fn,
    step_cost,
)



# Helpers
def _make_game(level_path: str):
    """Tạo đối tượng game giả (chỉ cần game.level) từ file JSON."""
    level = load_level(level_path)
    game = MagicMock()
    game.level = level
    return game



# Tests cho hàm chi phí step_cost
class TestStepCost(unittest.TestCase):

    def setUp(self) -> None:
        self.game = _make_game("levels/g3_switch_demo.json")

    def test_swap_action_returns_cost_swap(self) -> None:
        """Hành động 'S' phải trả về COST_SWAP bất kể trạng thái."""
        old = State(1, 1, STAND)
        new = State(1, 1, STAND, split=((1, 1), (2, 2)))
        self.assertAlmostEqual(step_cost(self.game, old, "S", new), COST_SWAP)

    def test_normal_move_returns_cost_normal(self) -> None:
        """Bước lăn thông thường trên ô sàn không có công tắc/ô dễ vỡ."""
        # g1_basic_01: toàn ô sàn thường, không có công tắc/fragile
        game = _make_game("levels/g1_basic_01.json")
        old = State(0, 0, STAND)
        new = State(0, 0, HORIZ)   # STAND→HORIZ khi lăn phải
        self.assertAlmostEqual(step_cost(game, old, "R", new), COST_NORMAL)

    def test_fragile_cell_returns_cost_fragile(self) -> None:
        """Bước lăn đặt khối lên ô dễ vỡ phải trả COST_FRAGILE."""
        # g2_fragile_01: fragile tại (1,3) và (2,4)
        game = _make_game("levels/g2_fragile_01.json")
        # Khối nằm ngang tại (1,2)–(1,3): ô (1,3) là fragile
        old = State(1, 1, STAND, bridges=0)
        new = State(1, 2, HORIZ, bridges=0)  # chiếm (1,2) và (1,3)
        self.assertAlmostEqual(step_cost(game, old, "R", new), COST_FRAGILE)

    def test_switch_activation_returns_cost_switch(self) -> None:
        """Bước kích hoạt công tắc (bridges thay đổi) phải trả COST_SWITCH."""
        game = _make_game("levels/g3_switch_demo.json")
        old = State(1, 1, STAND, bridges=0)
        # Sau khi kích hoạt công tắc soft tại (1,1): bridge 0 mở → bridges=1
        new = State(1, 1, STAND, bridges=1)
        self.assertAlmostEqual(step_cost(game, old, "R", new), COST_SWITCH)

    def test_cost_callback_matches_game_signature(self) -> None:
        """Factory trả callback ba tham số mà Game.step_cost có thể gọi."""
        level = load_level("levels/g1_basic_01.json")
        game = Game(level, cost_fn=make_cost_fn(level))
        old = State(0, 0, STAND)
        new = State(0, 0, HORIZ)
        self.assertAlmostEqual(game.step_cost(old, "R", new), COST_NORMAL)

    def test_cost_min_is_positive(self) -> None:
        """Chi phí tối thiểu phải dương để UCS/A* hội tụ."""
        self.assertGreater(COST_MIN, 0.0)

    def test_all_costs_positive(self) -> None:
        """Mọi hằng số chi phí phải dương."""
        for c in [COST_NORMAL, COST_FRAGILE, COST_SWITCH, COST_SWAP]:
            self.assertGreater(c, 0.0, msg=f"Chi phí {c} phải > 0")

class TestHZero(unittest.TestCase):

    def setUp(self) -> None:
        self.game = _make_game("levels/g1_basic_01.json")

    def test_always_zero(self) -> None:
        for orient in (STAND, HORIZ, VERT):
            self.assertEqual(h_zero(self.game, State(0, 0, orient)), 0.0)

    def test_zero_at_goal(self) -> None:
        goal = self.game.level.goal
        self.assertEqual(h_zero(self.game, State(*goal, STAND)), 0.0)


class TestHManhattan(unittest.TestCase):

    def setUp(self) -> None:
        self.game = _make_game("levels/g1_basic_01.json")
        self.goal = self.game.level.goal  # (2, 5)

    def test_non_negative(self) -> None:
        """h_manhattan phải ≥ 0 với mọi trạng thái."""
        for r in range(5):
            for c in range(10):
                for orient in (STAND, HORIZ, VERT):
                    val = h_manhattan(self.game, State(r, c, orient))
                    self.assertGreaterEqual(val, 0.0)

    def test_zero_at_goal_stand(self) -> None:
        """h_manhattan tại goal + STAND phải = 0."""
        gr, gc = self.goal
        val = h_manhattan(self.game, State(gr, gc, STAND))
        self.assertAlmostEqual(val, 0.0)

    def test_stand_far_from_goal(self) -> None:
        """Khối tại (0,0) STAND: Manhattan đến goal (2,5) = 7, ⌈7/2⌉×1 = 4."""
        expected = math.ceil(7 / 2.0) * COST_MIN
        val = h_manhattan(self.game, State(0, 0, STAND))
        self.assertAlmostEqual(val, expected)

    def test_horiz_centroid_used(self) -> None:
        """Khối HORIZ tại (r,c)–(r,c+1): centroid = (r, c+0.5)."""
        gr, gc = self.goal
        r, c = 0, 0
        centroid_c = c + 0.5
        d = abs(r - gr) + abs(centroid_c - gc)
        expected = math.ceil(d / 2.0) * COST_MIN
        val = h_manhattan(self.game, State(r, c, HORIZ))
        self.assertAlmostEqual(val, expected)


class TestHManhattanOrient(unittest.TestCase):

    def setUp(self) -> None:
        self.game = _make_game("levels/g1_basic_01.json")
        self.goal = self.game.level.goal  # (2, 5)

    def test_no_penalty_when_stand(self) -> None:
        """Khối STAND không bị phạt tư thế."""
        s = State(self.goal[0], self.goal[1] - 1, STAND)
        self.assertAlmostEqual(
            h_manhattan_orient(self.game, s),
            h_manhattan(self.game, s),
        )

    def test_one_roll_can_stand_on_goal_without_extra_penalty(self) -> None:
        """HORIZ có thể tới goal và đứng lên trong cùng một lần lăn."""
        gr, gc = self.goal
        # HORIZ tại c=gc-2 lăn phải thành STAND tại goal; D tâm = 1.5.
        s = State(gr, gc - 2, HORIZ)
        self.assertAlmostEqual(h_manhattan_orient(self.game, s), COST_MIN)

    def test_orientation_bound_uses_maximum_centroid_motion(self) -> None:
        """Một lần lăn dịch tâm tối đa 1.5 ô, nên h dùng ceil(D / 1.5)."""
        s = State(0, 0, HORIZ)
        rc, cc = 0.0, 0.5
        gr, gc = self.goal
        distance = abs(rc - gr) + abs(cc - gc)
        expected = math.ceil(distance / 1.5) * COST_MIN
        self.assertAlmostEqual(h_manhattan_orient(self.game, s), expected)

    def test_orient_ge_manhattan(self) -> None:
        """h_manhattan_orient ≥ h_manhattan với mọi trạng thái."""
        for r in range(5):
            for c in range(10):
                for orient in (STAND, HORIZ, VERT):
                    s = State(r, c, orient)
                    self.assertGreaterEqual(
                        h_manhattan_orient(self.game, s),
                        h_manhattan(self.game, s),
                    )

    def test_split_switch_level_uses_zero_heuristic(self) -> None:
        """Teleport do split switch làm mất hiệu lực của cận hình học."""
        split_game = _make_game("levels/g3_switch_demo.json")
        state = State(0, 0, STAND)
        self.assertEqual(h_manhattan(split_game, state), 0.0)
        self.assertEqual(h_manhattan_orient(split_game, state), 0.0)
        self.assertEqual(h_relaxed_maze(split_game, state), 0.0)

    def test_split_state_uses_zero_heuristic(self) -> None:
        """Đổi cube active với S có thể làm cận dựa trên một cube mất consistency."""
        goal = self.goal
        state = State(0, 0, STAND, split=((0, 0), goal))
        self.assertEqual(h_manhattan(self.game, state), 0.0)
        self.assertEqual(h_manhattan_orient(self.game, state), 0.0)
        self.assertEqual(h_relaxed_maze(self.game, state), 0.0)


class TestHRelaxedMaze(unittest.TestCase):

    def setUp(self) -> None:
        self.game = _make_game("levels/g1_basic_01.json")
        self.goal = self.game.level.goal  # (2, 5)

    def test_non_negative(self) -> None:
        for r in range(5):
            for c in range(10):
                val = h_relaxed_maze(self.game, State(r, c, STAND))
                self.assertGreaterEqual(val, 0.0)

    def test_zero_at_goal(self) -> None:
        """h_relaxed_maze phải trả 0 tại ô goal."""
        gr, gc = self.goal
        val = h_relaxed_maze(self.game, State(gr, gc, STAND))
        self.assertAlmostEqual(val, 0.0)

    def test_relaxed_can_be_less_than_centroid_manhattan(self) -> None:
        """BFS tới ô gần goal nhất có thể nhỏ hơn Manhattan đo từ tâm khối."""
        state = State(2, 2, HORIZ)
        self.assertLess(h_relaxed_maze(self.game, state), h_manhattan(self.game, state))

    def test_non_negative_for_all_grid_coordinates(self) -> None:
        """Heuristic BFS không âm trên toàn bộ tọa độ lưới."""
        for r in range(5):
            for c in range(10):
                s = State(r, c, STAND)
                self.assertGreaterEqual(h_relaxed_maze(self.game, s), 0.0)

    def test_cache_consistent(self) -> None:
        """Gọi nhiều lần với cùng game phải trả kết quả giống nhau."""
        s = State(0, 0, STAND)
        v1 = h_relaxed_maze(self.game, s)
        v2 = h_relaxed_maze(self.game, s)
        self.assertAlmostEqual(v1, v2)

    def test_split_state_uses_zero_heuristic(self) -> None:
        """Không dùng vị trí cube active vì hành động S có thể đổi cube với giá thấp."""
        gr, gc = self.goal
        s = State(0, 0, STAND, split=((0, 0), (gr, gc)))
        self.assertAlmostEqual(h_relaxed_maze(self.game, s), 0.0)

    def test_split_switch_level_uses_zero_heuristic(self) -> None:
        """Heuristic BFS trả 0 cả trước khi split switch dịch chuyển cube."""
        split_game = _make_game("levels/g3_switch_demo.json")
        state = State(0, 0, STAND)
        self.assertEqual(h_relaxed_maze(split_game, state), 0.0)

    def test_unreachable_relaxed_cell_returns_infinity(self) -> None:
        """Không có đường trên lưới nới lỏng thì h_relaxed trả math.inf."""
        level = Level(
            name="disconnected",
            grid=["#..", "...", "..G"],
            start=(0, 0),
            goal=(2, 2),
            fragile=set(),
            bridges={},
            switches={},
        )
        game = MagicMock()
        game.level = level
        self.assertTrue(math.isinf(h_relaxed_maze(game, State(0, 0, STAND))))


if __name__ == "__main__":
    unittest.main()
