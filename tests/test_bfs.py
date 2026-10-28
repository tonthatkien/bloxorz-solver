"""Test BFS."""

import unittest

from game.dummy_game import DummyGame
from game.state import State
from solvers.base import LimitReached, Limits
from solvers.bfs import solve


class GraphGame:
    """Đồ thị có hướng nhỏ, cung cấp các phương thức Game mà solver sử dụng."""

    def __init__(self, edges: dict[State, list[tuple[str, State, float]]], goal: State):
        self.edges = edges
        self.start = State(0, 0)
        self.goal = goal

    def initial_state(self) -> State:
        return self.start

    def is_goal(self, state: State) -> bool:
        return state == self.goal

    def get_successors(self, state: State) -> list[tuple[str, State, float]]:
        return self.edges.get(state, [])


def _replay_path(game: GraphGame | DummyGame, actions: list[str]) -> tuple[State, float]:
    """Phát lại các hành động qua giao diện game, trả về trạng thái cuối và chi phí đường đi."""
    state = game.initial_state()
    total_cost = 0.0
    for action in actions:
        successor = next(
            ((next_state, cost) for candidate, next_state, cost in game.get_successors(state)
             if candidate == action),
            None,
        )
        if successor is None:
            raise AssertionError(f"Hành động {action!r} không hợp lệ tại trạng thái {state!r}.")
        state, step_cost = successor
        total_cost += step_cost
    return state, total_cost


class TestBreadthFirstSearch(unittest.TestCase):
    def test_finds_shortest_action_path_and_reports_its_cost(self) -> None:
        game = DummyGame(10)

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.length, 5)
        self.assertEqual(result.path, ["D"] * 5)
        self.assertEqual(result.cost, 15.0)
        self.assertEqual(result.length, len(result.path))
        final_state, replayed_cost = _replay_path(game, result.path)
        self.assertTrue(game.is_goal(final_state))
        self.assertEqual(replayed_cost, result.cost)

    def test_visited_on_enqueue_keeps_first_shortest_path_to_a_state(self) -> None:
        start, left, right, merge, goal = (State(0, col) for col in range(5))
        game = GraphGame(
            {
                start: [("SL", left, 5.0), ("SR", right, 1.0)],
                left: [("LM", merge, 5.0)],
                right: [("RM", merge, 1.0)],
                merge: [("MG", goal, 1.0)],
            },
            goal,
        )

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.path, ["SL", "LM", "MG"])
        self.assertEqual(result.cost, 11.0)
        self.assertEqual(result.expanded_nodes, 5)
        final_state, replayed_cost = _replay_path(game, result.path)
        self.assertTrue(game.is_goal(final_state))
        self.assertEqual(replayed_cost, result.cost)

    def test_start_at_goal_returns_empty_path(self) -> None:
        game = DummyGame(0)

        result = solve(game)

        self.assertTrue(result.solved)
        self.assertEqual(result.path, [])
        self.assertEqual(result.length, 0)
        self.assertEqual(result.cost, 0.0)
        self.assertEqual(result.expanded_nodes, 1)

    def test_unreachable_goal_returns_unsolved_result(self) -> None:
        game = GraphGame({}, State(0, 1))

        result = solve(game)

        self.assertFalse(result.solved)
        self.assertEqual(result.path, [])
        self.assertEqual(result.length, 0)
        self.assertEqual(result.cost, 0.0)
        self.assertEqual(result.expanded_nodes, 1)

    def test_node_limit_is_checked_when_a_state_is_popped(self) -> None:
        with self.assertRaisesRegex(LimitReached, "node_limit"):
            solve(DummyGame(1), Limits(max_nodes=0))

    def test_non_finite_transition_cost_is_rejected(self) -> None:
        start, goal = State(0, 0), State(0, 1)
        game = GraphGame({start: [("R", goal, float("nan"))]}, goal)

        with self.assertRaisesRegex(ValueError, "số hữu hạn"):
            solve(game)


if __name__ == "__main__":
    unittest.main()
