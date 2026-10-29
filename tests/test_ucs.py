"""Test UCS."""

import unittest
from pathlib import Path

from game.dummy_game import DummyGame
from game.game import Game
from game.level_loader import load_level
from game.state import State
from solvers.base import LimitReached, Limits
from solvers.ucs import solve
from solvers.metrics import verify_path


class GraphGame:
    """Đồ thị có hướng nhỏ, cung cấp giao diện game cho các bài kiểm thử UCS."""

    def __init__(
        self,
        edges: dict[State, list[tuple[str, State, float]]],
        goal: State,
    ) -> None:
        self.edges = edges
        self.start = State(0, 0)
        self.goal = goal

    def initial_state(self) -> State:
        """Trả về trạng thái bắt đầu của đồ thị."""
        return self.start

    def is_goal(self, state: State) -> bool:
        """Kiểm tra trạng thái có phải đích hay không."""
        return state == self.goal

    def get_successors(self, state: State) -> list[tuple[str, State, float]]:
        """Trả về các cung đi ra cùng hành động và chi phí."""
        return self.edges.get(state, [])


def _replay_path(game: GraphGame, actions: list[str]) -> tuple[State, float]:
    """Phát lại đường đi qua giao diện game và tính tổng chi phí."""
    state = game.initial_state()
    total_cost = 0.0
    for action in actions:
        successor = next(
            ((next_state, cost) for candidate, next_state, cost in game.get_successors(state)
             if candidate == action),
            None,
        )
        if successor is None:
            raise AssertionError(f"Hành động {action!r} không hợp lệ tại {state!r}.")
        state, step_cost = successor
        total_cost += step_cost
    return state, total_cost


class TestUniformCostSearch(unittest.TestCase):
    """Kiểm tra UCS tối ưu tổng chi phí và đếm nút theo quy ước chung."""

    def test_updates_parent_when_a_cheaper_route_reaches_same_state(self) -> None:
        """UCS thay cha khi tìm được đường rẻ hơn tới cùng trạng thái."""
        start, merge, cheap, goal = (State(0, col) for col in range(4))
        game = GraphGame(
            {
                start: [("expensive", merge, 10.0), ("detour", cheap, 1.0)],
                cheap: [("cheaper", merge, 1.0)],
                merge: [("finish", goal, 20.0)],
            },
            goal,
        )

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.path, ["detour", "cheaper", "finish"])
        self.assertEqual(result.cost, 22.0)
        self.assertEqual(result.length, 3)
        self.assertEqual(result.expanded_nodes, 4)
        final_state, replayed_cost = _replay_path(game, result.path)
        self.assertTrue(game.is_goal(final_state))
        self.assertEqual(replayed_cost, result.cost)

    def test_equal_cost_entries_do_not_compare_states(self) -> None:
        """Bộ đếm phá hòa cho phép heap xử lý nhiều trạng thái cùng chi phí."""
        start, first, second, goal = (State(0, col) for col in range(4))
        game = GraphGame(
            {
                start: [("first", first, 1.0), ("second", second, 1.0)],
                first: [("finish_first", goal, 1.0)],
                second: [("finish_second", goal, 1.0)],
            },
            goal,
        )

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.cost, 2.0)
        self.assertEqual(result.length, 2)

    def test_start_at_goal_returns_empty_path(self) -> None:
        """Trạng thái đầu là đích thì trả đường đi rỗng với chi phí bằng không."""
        game = GraphGame({}, State(0, 0))

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.path, [])
        self.assertEqual(result.cost, 0.0)
        self.assertEqual(result.expanded_nodes, 1)

    def test_unreachable_goal_returns_unsolved_result(self) -> None:
        """Đồ thị không có đường tới đích thì kết quả không được đánh dấu solved."""
        game = GraphGame({}, State(0, 1))

        result = solve(game)

        self.assertFalse(result.solved)
        self.assertEqual(result.expanded_nodes, 1)

    def test_node_limit_is_checked_when_a_current_entry_is_popped(self) -> None:
        """Giới hạn nút được kiểm tra khi lấy một mục hợp lệ ra khỏi heap."""
        game = GraphGame({}, State(0, 1))

        with self.assertRaisesRegex(LimitReached, "node_limit"):
            solve(game, Limits(max_nodes=0))

    def test_invalid_transition_cost_is_rejected(self) -> None:
        """Từ chối chi phí không hữu hạn hoặc âm để bảo toàn tính tối ưu của UCS."""
        start, goal = State(0, 0), State(0, 1)
        for invalid_cost in (float("nan"), -1.0):
            with self.subTest(cost=invalid_cost):
                game = GraphGame({start: [("go", goal, invalid_cost)]}, goal)

                with self.assertRaises(ValueError):
                    solve(game)

    def test_prefers_cheaper_longer_path_in_dummy_game(self) -> None:
        """UCS chọn mười bước R giá 10 thay cho năm bước D giá 15."""
        result = solve(DummyGame(10))

        self.assertTrue(result.solved)
        self.assertEqual(result.path, ["R"] * 10)
        self.assertEqual(result.length, 10)
        self.assertEqual(result.cost, 10.0)

    def test_solves_real_level_and_verify_path_accepts_result(self) -> None:
        level_path = Path(__file__).resolve().parents[1] / "levels" / "g1_basic_01.json"
        game = Game(load_level(str(level_path)))

        result = solve(game)

        self.assertTrue(result.solved)
        is_valid, replayed_cost = verify_path(game, result.path)
        self.assertTrue(is_valid)
        self.assertEqual(result.length, len(result.path))
        self.assertAlmostEqual(result.cost, replayed_cost)


if __name__ == "__main__":
    unittest.main()
