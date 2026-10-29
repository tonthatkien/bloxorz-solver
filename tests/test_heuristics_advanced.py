"""Test solvers/heuristics_advanced.py (task E2): admissible, consistent, giá trị tính tay.

Thước đo là brute-force trên toàn bộ không gian trạng thái: h*(s) tính bằng Dijkstra ngược,
rồi so với heuristic ở MỌI trạng thái và MỌI cạnh (xem tests/reference_game.py).
"""
import math
import random
import unittest
from pathlib import Path

from game.game import Game
from game.level_loader import load_level, parse_level
from game.state import STAND, State
from solvers import astar
from solvers import heuristics_advanced as ha
from solvers.heuristics_advanced import (HEURISTICS, get_heuristic, h_advanced, h_split_cubes,
                                         h_switch_aware)
from tests.reference_game import (ReferenceGame, explore, find_violations, random_level,
                                  true_costs)

LEVEL_DIR = Path(__file__).resolve().parent.parent / "levels"

# Cầu (2,3) đóng chắn đường tới goal (1,4); công tắc nặng (1,5) phải đứng lên mới mở.
BRIDGE_LEVEL = {
    "grid": ["######", "####G#", "######", "##.###"], "start": [3, 3], "goal": [1, 4],
    "bridges": [{"id": 0, "pos": [2, 3], "open": False}],
    "switches": [{"type": "heavy", "pos": [1, 5], "targets": [0], "mode": "toggle"}],
}
# Đứng lên công tắc split (1,3) -> hai cube ở (1,0) và (2,1), phải ghép lại rồi tới goal (1,2).
SPLIT_LEVEL = {
    "grid": [".####", "##G##", "##.##"], "start": [0, 4], "goal": [1, 2],
    "switches": [{"type": "split", "pos": [1, 3], "cubes": [[1, 0], [2, 1]]}],
}
ALL_NAMES = ("manhattan", "manhattan_orient", "relaxed_maze", "switch_aware", "split_cubes",
             "advanced")


class CacheCleaningTestCase(unittest.TestCase):
    def setUp(self):
        ha.clear_caches()

    def tearDown(self):
        ha.clear_caches()


class TestRegistry(unittest.TestCase):
    def test_registry_has_every_heuristic_and_all_are_callable(self):
        for name in ("zero",) + ALL_NAMES:
            self.assertTrue(callable(HEURISTICS[name]), name)

    def test_get_heuristic_by_name_or_function(self):
        self.assertIs(get_heuristic("switch_aware"), h_switch_aware)
        self.assertIs(get_heuristic(h_advanced), h_advanced)

    def test_unknown_name_is_rejected(self):
        with self.assertRaises(KeyError):
            get_heuristic("khong_ton_tai")


class TestPlainLevel(CacheCleaningTestCase):
    """Màn chỉ có sàn: đồ thị nới lỏng chính là đồ thị thật nên h chính xác (h = h*)."""

    def setUp(self):
        super().setUp()
        self.level = load_level(str(LEVEL_DIR / "g1_basic_01.json"))
        self.game = Game(self.level)
        self.edges = explore(self.game)
        self.star = true_costs(self.game, self.edges)

    def test_switch_aware_is_exact_with_unit_cost(self):
        for state, optimal in self.star.items():
            self.assertEqual(h_switch_aware(self.game, state), optimal, state)

    def test_advanced_equals_switch_aware_without_split(self):
        for state in self.edges:
            self.assertEqual(h_advanced(self.game, state), h_switch_aware(self.game, state))

    def test_no_violations_for_any_heuristic(self):
        for name in ALL_NAMES:
            with self.subTest(heuristic=name):
                self.assertEqual(find_violations(self.game, HEURISTICS[name], self.edges,
                                                 self.star), [])


class TestSwitchAware(CacheCleaningTestCase):
    def setUp(self):
        super().setUp()
        self.level = parse_level(BRIDGE_LEVEL)
        self.game = ReferenceGame(self.level)
        self.start = self.game.initial_state()
        self.edges = explore(self.game)
        self.star = true_costs(self.game, self.edges)

    def test_closed_bridge_forces_detour_to_the_switch(self):
        # Nếu coi cầu như đã mở thì chỉ cần 6 lần lăn; phải ghé công tắc nên cần 11.
        self.assertEqual(h_switch_aware(self.game, self.start), 11.0)
        self.assertEqual(self.star[self.start], 11.0)

    def test_open_bridge_removes_the_detour(self):
        opened = State(self.start.r, self.start.c, self.start.orient, 1, None)
        self.assertEqual(h_switch_aware(self.game, opened), 6.0)

    def test_no_violations_with_unit_and_weighted_costs(self):
        for weighted in (False, True):
            game = ReferenceGame(self.level, weighted)
            for name in ALL_NAMES:
                with self.subTest(heuristic=name, weighted=weighted):
                    self.assertEqual(find_violations(game, HEURISTICS[name]), [])


class TestSplitCubes(CacheCleaningTestCase):
    def setUp(self):
        super().setUp()
        self.level = parse_level(SPLIT_LEVEL)
        self.game = ReferenceGame(self.level)
        self.start = self.game.initial_state()
        self.edges = explore(self.game)
        self.star = true_costs(self.game, self.edges)
        self.split = State(0, 0, STAND, 0, ((1, 0), (2, 1)))

    def test_start_is_bounded_through_the_split_switch(self):
        self.assertEqual(h_advanced(self.game, self.start), 6.0)
        self.assertEqual(self.star[self.start], 9.0)

    def test_split_state_value_is_admissible_and_hand_checked(self):
        # Cube (2,1) lên (1,1) ghép với (1,0) thành khối nằm, rồi lăn phải: 1 + 1 = 2 bước.
        self.assertIn(self.split, self.edges)
        self.assertEqual(h_split_cubes(self.game, self.split), 2.0)
        self.assertEqual(self.star[self.split], 3.0)     # thật cần D (ghép), U, R

    def test_bound_does_not_depend_on_which_cube_is_active(self):
        swapped = State(0, 0, STAND, 0, ((2, 1), (1, 0)))
        self.assertEqual(h_split_cubes(self.game, swapped),
                         h_split_cubes(self.game, self.split))

    def test_unsplit_state_falls_back_and_switch_aware_gives_zero_when_split(self):
        self.assertEqual(h_split_cubes(self.game, self.start),
                         h_switch_aware(self.game, self.start))
        self.assertEqual(h_switch_aware(self.game, self.split), 0.0)

    def test_no_violations_with_unit_and_weighted_costs(self):
        for weighted in (False, True):
            game = ReferenceGame(self.level, weighted)
            for name in ALL_NAMES:
                with self.subTest(heuristic=name, weighted=weighted):
                    self.assertEqual(find_violations(game, HEURISTICS[name]), [])


class TestUnreachableGoal(CacheCleaningTestCase):
    def test_infinite_when_void_separates_start_and_goal(self):
        level = parse_level({"grid": ["#.G"], "start": [0, 0], "goal": [0, 2]})
        game = Game(level)
        for name in ("switch_aware", "advanced"):
            self.assertTrue(math.isinf(HEURISTICS[name](game, game.initial_state())), name)
        result = astar.solve_with(game, "advanced")
        self.assertFalse(result.solved)
        self.assertEqual(result.expanded_nodes, 0)


class TestRandomLevels(CacheCleaningTestCase):
    def test_no_violations_on_random_levels_with_every_feature(self):
        rng = random.Random(2026)
        for index in range(60):
            level = random_level(rng)
            for weighted in (False, True):
                game = ReferenceGame(level, weighted)
                edges = explore(game)
                star = true_costs(game, edges)
                for name in ALL_NAMES:
                    problems = find_violations(game, HEURISTICS[name], edges, star)
                    self.assertEqual(problems[:1], [], f"level {index}, {name}, "
                                                       f"weighted={weighted}")


class TestRealGameAdvancedLevels(unittest.TestCase):
    def test_no_violations_on_real_game_for_g2_g3_g4_levels(self):
        for path in sorted(LEVEL_DIR.glob("g[234]_*.json")):
            game = Game(load_level(str(path)))
            for name in ALL_NAMES:
                with self.subTest(level=path.name, heuristic=name):
                    self.assertEqual(find_violations(game, HEURISTICS[name]), [])


if __name__ == "__main__":
    unittest.main()
