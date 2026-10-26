"""T2 level contracts and replay proofs; advanced integration is explicitly gated."""
import json
from dataclasses import replace
from pathlib import Path
import unittest

from game.game import Game
from game.level_loader import Level, load_level
from game.state import HORIZ, STAND, State, cells
from tests.level_verifier import TileRules, VerificationGame, replay, solve

CATALOG = json.loads((Path(__file__).with_name("t2_solutions.json")).read_text())


def _level(name: str) -> Level:
    return load_level(str(Path("levels", name + ".json")))


def _advance(game: VerificationGame, actions: str) -> list[State]:
    states = [game.initial_state()]
    for action in actions:
        options = {key: state for key, state, _ in game.get_successors(states[-1])}
        if action not in options:
            raise AssertionError(f"Invalid probe action {action}")
        states.append(options[action])
    return states


def _core_handles_switches() -> bool:
    # Capability probe: main currently lacks B2; do not declare Game integration verified.
    return any(action == "R" and state.bridges == 1 << 2
               for action, state, _ in Game(_level("g3_switch_01")).get_successors(State()))


class TestT2Catalog(unittest.TestCase):
    """Validate data independently of whether B2 is present in the checkout."""

    def test_six_levels_have_expected_groups_and_metadata(self) -> None:
        self.assertEqual(len(CATALOG), 6)
        for name, record in CATALOG.items():
            with self.subTest(level=name):
                level = _level(name)
                self.assertEqual(level.name, name)
                self.assertTrue(name.startswith(f'g{record["group"]}_'))
                self.assertEqual(record["length"], len(record["path"]))
                self.assertEqual(record["fragile"], len(level.fragile))
                self.assertEqual(record["bridges"], len(level.bridges))
                self.assertEqual(record["switches"], len(level.switches))
                self.assertEqual(record["floor_cells"],
                                 sum(ch in "#G" for row in level.grid for ch in row))
                self.assertNotIn(level.start, level.fragile)
                self.assertFalse(any(s.type == "split" for s in level.switches.values()))
                if record["group"] == 2:
                    self.assertTrue(level.fragile)
                    self.assertFalse(level.bridges or level.switches)
                else:
                    self.assertTrue(level.bridges and level.switches)
                    self.assertEqual(level.initial_bridge_mask(), 0)

    def test_relative_difficulty_has_increasing_verified_lengths_and_expansions(self) -> None:
        for group in (2, 3):
            records = [r for name, r in sorted(CATALOG.items()) if r["group"] == group]
            for metric in ("length", "expanded"):
                values = [r[metric] for r in records]
                self.assertTrue(all(a < b for a, b in zip(values, values[1:])))

    def test_existing_switch_demo_remains_separate_from_t2_benchmarks(self) -> None:
        demo = load_level("levels/g3_switch_demo.json")
        self.assertTrue(any(s.type == "split" for s in demo.switches.values()))
        self.assertNotIn(demo.name, CATALOG)


class _SolutionChecks:
    def check_solution(self, name: str) -> list[State]:
        level = _level(name)
        game = VerificationGame(level)
        result = solve(game)
        self.assertIsNotNone(result)
        self.assertEqual(result, solve(game))
        record = CATALOG[name]
        self.assertEqual(len(result.path), record["length"])
        states = replay(game, tuple(record["path"]))
        replay(game, result.path)
        for state in states:
            self.assertIsNone(state.split)
            if state.orient == STAND:
                self.assertNotIn((state.r, state.c), level.fragile)
            for r, c in cells(state):
                self.assertTrue(0 <= r < level.rows and 0 <= c < level.cols)
                self.assertIn(level.grid[r][c], "#G")
                for bridge in level.bridges.values():
                    if bridge.pos == (r, c):
                        self.assertTrue(state.bridges & (1 << bridge.id))
        return states


class TestT2FragileSolvability(_SolutionChecks, unittest.TestCase):
    """B1 fragile safety can be verified even before B2 is merged."""

    def test_easy_level_rejects_a_reachable_upright_shortcut(self) -> None:
        game = VerificationGame(_level("g2_fragile_01"))
        state = _advance(game, "RD")[-1]
        core_moves = {a: s for a, s, _ in game.core.get_successors(state)}
        self.assertEqual(core_moves["R"], State(1, 3))
        self.assertNotIn("R", {a for a, _, _ in game.get_successors(state)})

    def test_three_fragile_levels_have_optimal_replayable_solutions(self) -> None:
        for name, record in CATALOG.items():
            if record["group"] != 2:
                continue
            with self.subTest(level=name):
                states = self.check_solution(name)
                level = _level(name)
                self.assertTrue(any(set(cells(s)) & level.fragile for s in states))
                relaxed = solve(VerificationGame(replace(level, fragile=set())))
                self.assertEqual(len(relaxed.path), record["length_without_fragile"])
                if name != "g2_fragile_01":
                    self.assertLess(len(relaxed.path), record["length"])
                    rejected = 0
                    game = VerificationGame(level)
                    for state in states:
                        valid = {a for a, _, _ in game.get_successors(state)}
                        for action, pose, _ in game.core.get_successors(state):
                            if pose.orient == STAND and (pose.r, pose.c) in level.fragile:
                                self.assertNotIn(action, valid)
                                rejected += 1
                    self.assertGreater(rejected, 0)


@unittest.skipIf(TileRules is None, "Pending B2: game.tiles.TileRules is not on main")
class TestT2BridgeSolvability(_SolutionChecks, unittest.TestCase):
    """Run with the actual B2 helper on its dependency snapshot or once it reaches main."""

    def test_soft_level_has_solution(self) -> None:
        self.check_solution("g3_switch_01")

    def test_heavy_level_has_solution(self) -> None:
        self.check_solution("g3_switch_02")

    def test_mixed_level_has_solution(self) -> None:
        self.check_solution("g3_switch_03")

    def test_switch_effects_are_necessary_and_disabled_replay_is_illegal(self) -> None:
        for name, record in CATALOG.items():
            if record["group"] == 3:
                with self.subTest(level=name):
                    disabled = VerificationGame(_level(name), disable_switches=True)
                    self.assertIsNone(solve(disabled))
                    with self.assertRaises(AssertionError):
                        replay(disabled, tuple(record["path"]))

    def test_reachable_lying_contact_does_not_press_heavy_but_standing_does(self) -> None:
        game = VerificationGame(_level("g3_switch_02"))
        states = _advance(game, "RDDDLURD")
        self.assertEqual(states[4].orient, HORIZ)
        self.assertIn((3, 1), cells(states[4]))
        self.assertEqual(states[4].bridges, 0)
        self.assertEqual(states[-1], State(3, 1, bridges=(1 << 2) | (1 << 7)))

    def test_soft_toggle_reentry_and_permanent_open_reentry(self) -> None:
        toggled = _advance(VerificationGame(_level("g3_switch_01")), "RLR")
        self.assertEqual(toggled[1].bridges, 1 << 2)
        self.assertEqual(toggled[-1].bridges, 0)
        permanent = _advance(VerificationGame(_level("g3_switch_03")), "RDU")
        self.assertEqual(permanent[1], permanent[-1])
        self.assertEqual(permanent[-1].bridges, (1 << 2) | (1 << 7))

    def test_both_mixed_switches_are_necessary(self) -> None:
        level = _level("g3_switch_03")
        for switch in level.switches.values():
            game = VerificationGame(level)
            game.rules = replace(game.rules, switches=tuple(
                event for event in game.rules.switches if event.pos != switch.pos))
            with self.subTest(disabled=switch.pos):
                self.assertIsNone(solve(game))


@unittest.skipUnless(_core_handles_switches(), "Pending advanced-tile integration in Game")
class TestT2ProductionGame(unittest.TestCase):
    """Keep the final production API check visible until Game actually implements B2."""

    def test_all_solutions_replay_through_integrated_game(self) -> None:
        for name, record in CATALOG.items():
            with self.subTest(level=name):
                game = Game(_level(name))
                result = solve(game)
                self.assertIsNotNone(result)
                self.assertEqual(len(result.path), record["length"])
                replay(game, tuple(record["path"]))


if __name__ == "__main__":
    unittest.main()
