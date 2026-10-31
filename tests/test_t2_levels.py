"""T2 level contracts and replay proofs through the integrated production Game."""
import json
from dataclasses import replace
from pathlib import Path
import unittest

from game.block import Block
from game.game import Game
from game.level_loader import Level, load_level
from game.state import HORIZ, STAND, State, cells
from solvers import bfs
from solvers.base import Limits
from tests.level_verifier import VerificationGame, replay, solve

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


class TestT2Catalog(unittest.TestCase):
    """Validate the level data and stored proof metadata."""

    def test_seven_levels_have_expected_groups_and_metadata(self) -> None:
        self.assertEqual(len(CATALOG), 7)
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


class _SolutionChecks:
    def check_solution(self, name: str) -> list[State]:
        level = _level(name)
        game = VerificationGame(level)
        result = solve(game)
        self.assertIsNotNone(result)
        self.assertEqual(result, solve(game))
        record = CATALOG[name]
        self.assertEqual(len(result.path), record["length"])
        self.assertEqual(result.expanded, record["expanded"])
        self.assertEqual(result.discovered, record["discovered"])
        states = replay(game, tuple(record["path"]))
        self.assertEqual(sum(a.orient != b.orient for a, b in zip(states, states[1:])),
                         record["orientation_changes"])
        self.assertEqual(sum(a.bridges != b.bridges for a, b in zip(states, states[1:])),
                         record["mask_changes"])
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
    """Verify fragile safety and compare against geometric rolls without that restriction."""

    def test_easy_level_rejects_a_reachable_upright_shortcut(self) -> None:
        game = VerificationGame(_level("g2_fragile_01"))
        state = _advance(game, "RD")[-1]
        rolled = Block(state.r, state.c, state.orient).roll("R")
        self.assertEqual((rolled.r, rolled.c, rolled.orient), (1, 3, STAND))
        self.assertNotIn("R", {a for a, _, _ in game.get_successors(state)})

    def test_fragile_levels_have_optimal_replayable_solutions(self) -> None:
        for name, record in CATALOG.items():
            if record["group"] != 2:
                continue
            with self.subTest(level=name):
                states = self.check_solution(name)
                level = _level(name)
                self.assertTrue(any(set(cells(s)) & level.fragile for s in states))
                relaxed = solve(VerificationGame(replace(level, fragile=set())))
                self.assertEqual(len(relaxed.path), record["length_without_fragile"])
                if name in ("g2_fragile_02", "g2_fragile_03"):
                    self.assertLess(len(relaxed.path), record["length"])
                if name == "g2_fragile_04":
                    self.assertEqual(relaxed.expanded, record["expanded_without_fragile"])
                    self.assertLess(solve(VerificationGame(level)).expanded,
                                    relaxed.expanded)
                if name != "g2_fragile_01":
                    rejected = 0
                    game = VerificationGame(level)
                    for state in states:
                        valid = {a for a, _, _ in game.get_successors(state)}
                        block = Block(state.r, state.c, state.orient)
                        for action, pose in game.core.board.valid_moves(block):
                            if pose.orient == STAND and (pose.r, pose.c) in level.fragile:
                                self.assertNotIn(action, valid)
                                rejected += 1
                    self.assertGreater(rejected, 0)


class TestT2BridgeSolvability(_SolutionChecks, unittest.TestCase):
    """Verify bridges and switches through the real production transitions."""

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
            without_switch = replace(level, switches={
                pos: item for pos, item in level.switches.items() if pos != switch.pos})
            game = VerificationGame(without_switch)
            with self.subTest(disabled=switch.pos):
                self.assertIsNone(solve(game))


class TestT2ProductionGame(unittest.TestCase):
    """Require production replay and keep the verification adapter aligned with Game."""

    def test_adapter_matches_production_successors_on_every_recorded_path(self) -> None:
        for name, record in CATALOG.items():
            with self.subTest(level=name):
                level = _level(name)
                game, adapter = Game(level), VerificationGame(level)
                for state in replay(game, tuple(record["path"])):
                    self.assertEqual(adapter.get_successors(state), game.get_successors(state))

    def test_all_solutions_replay_through_integrated_game(self) -> None:
        for name, record in CATALOG.items():
            with self.subTest(level=name):
                game = Game(_level(name))
                result = bfs.solve(game, Limits(max_nodes=20000))
                self.assertTrue(result.solved)
                self.assertEqual(result.length, record["length"])
                replay(game, tuple(result.path))
                replay(game, tuple(record["path"]))


if __name__ == "__main__":
    unittest.main()
