"""Happy, edge, classic and expected-loss cases complement the solvable T2 benchmarks."""
import json
from pathlib import Path
import unittest

from game.game import Game
from game.level_loader import load_level
from game.state import HORIZ, STAND, State, cells
from tests.level_verifier import VerificationGame, replay, solve

FIXTURES = Path(__file__).parent / "fixtures" / "t2"


class TestT2Scenarios(unittest.TestCase):
    """Keep negative rule fixtures out of the advertised solvable benchmark catalog."""

    def game(self, name: str) -> VerificationGame:
        """Read a scenario with the same loader used by production."""
        return VerificationGame(load_level(str(FIXTURES / (name + ".json"))))

    def test_happy_path_has_no_obstacles_and_four_basic_rolls(self) -> None:
        game = self.game("happy_path")
        self.assertFalse(game.level.fragile or game.level.bridges or game.level.switches)
        result = solve(game)
        self.assertIsNotNone(result)
        self.assertEqual(result.path, tuple("RRRR"))
        self.assertEqual(solve(Game(game.level)).path, result.path)
        replay(game, result.path)

    def test_narrow_corridor_requires_two_right_angle_turns(self) -> None:
        game = self.game("edge_narrow_turns")
        result = solve(game)
        self.assertEqual(result.path, tuple("RRDDRR"))
        states = replay(game, result.path)
        self.assertEqual(states[2], State(0, 3))
        self.assertEqual(states[4], State(3, 3))
        # Turning before the corner would put the footprint across void cells.
        self.assertNotIn("D", {a for a, _, _ in game.get_successors(states[1])})
        self.assertNotIn("R", {a for a, _, _ in game.get_successors(states[2])})

    def test_tiny_map_has_adjacent_start_goal_but_lying_is_not_a_win(self) -> None:
        game = self.game("edge_adjacent_goal")
        start, goal = game.level.start, game.level.goal
        self.assertEqual(abs(start[0] - goal[0]) + abs(start[1] - goal[1]), 1)
        result = solve(game)
        self.assertEqual(len(result.path), 3)
        replay(game, result.path)
        self.assertFalse(game.is_goal(State(0, 1, HORIZ)))
        for state in (State(0, 0), State(0, 1, HORIZ)):
            for action, pose, _ in game.get_successors(state):
                with self.subTest(action=action, state=state):
                    self.assertTrue(all(0 <= r < 3 and 0 <= c < 3 for r, c in cells(pose)))

    def test_forced_fragile_standing_is_an_expected_loss_not_a_solved_benchmark(self) -> None:
        game = self.game("rule_forced_fragile_loss")
        initial = game.initial_state()
        lying = next(s for a, s, _ in game.get_successors(initial) if a == "R")
        core_moves = {a: s for a, s, _ in game.core.get_successors(lying)}
        self.assertEqual(core_moves["R"], State(0, 3, STAND))
        self.assertNotIn("R", {a for a, _, _ in game.get_successors(lying)})
        self.assertIsNone(solve(game))
        catalog = json.loads((Path(__file__).with_name("t2_solutions.json")).read_text())
        self.assertNotIn(game.level.name, catalog)

    def test_classic_map_uses_multiple_areas_and_a_longer_solution(self) -> None:
        level = load_level("levels/g2_fragile_04.json")
        game = VerificationGame(level)
        result = solve(game)
        self.assertGreater(sum(ch in "#G" for row in level.grid for ch in row), 250)
        self.assertGreaterEqual(len(result.path), 25)
        self.assertGreater(result.expanded, 500)
        replay(game, result.path)


if __name__ == "__main__":
    unittest.main()
