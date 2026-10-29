"""C3 integration through the production Game API, loader, and search solvers."""
import copy
import unittest

from game.game import ACTIONS, Game
from game.level_loader import Level, parse_level
from game.state import HORIZ, STAND, VERT, State, cells
from solvers import astar, bfs, ucs
from solvers.base import Limits


def open_level(**changes: object) -> Level:
    """Build validated terrain; each test selects its interacting rules explicitly."""
    data = {
        "grid": ["#########"] * 6 + ["########G"],
        "start": [3, 0], "goal": [6, 8],
    }
    data.update(changes)
    return parse_level(data)


def mixed_level() -> Level:
    """Include fragile, void, two sparse bridge IDs, and all three switch types."""
    return open_level(
        grid=["########."] + ["#########"] * 5 + ["########G"],
        fragile=[[2, 2]],
        bridges=[{"id": 2, "pos": [3, 4]},
                 {"id": 63, "pos": [5, 4], "open": True}],
        switches=[{"type": "soft", "pos": [1, 2], "targets": [2]},
                  {"type": "heavy", "pos": [3, 2], "targets": [63],
                   "mode": "permanent", "set": "close"},
                  {"type": "split", "pos": [3, 3], "cubes": [[1, 0], [5, 6]]}],
    )


def forced_split_level() -> Level:
    """The initial cube is blocked until S selects the cube that can open a bridge."""
    return parse_level({
        "grid": ["####....", "........", "..#####G"],
        "start": [0, 0], "goal": [2, 7],
        "bridges": [{"id": 2, "pos": [2, 3]}],
        "switches": [{"type": "split", "pos": [0, 3], "cubes": [[2, 2], [2, 5]]},
                     {"type": "soft", "pos": [2, 4], "targets": [2]}],
    })


class TestIntegratedTransitions(unittest.TestCase):
    """Transitions combine movement, terrain, effects and final-state costs."""

    def advance(self, game: Game, state: State, action: str) -> State:
        """Require the requested action to exist in the real successor list."""
        matches = [(new, cost) for act, new, cost in game.get_successors(state) if act == action]
        self.assertEqual(len(matches), 1, (state, action))
        new, cost = matches[0]
        self.assertEqual(cost, 1.0)
        self.assertTrue(game.tile_rules.is_supported(new))
        return new

    def test_split_switch_requires_standing_and_preserves_runtime_mask(self) -> None:
        game = Game(mixed_level())
        start = game.initial_state()
        lying = self.advance(game, start, "R")
        self.assertIsNone(lying.split)
        split = self.advance(game, lying, "R")
        self.assertEqual(split, State(bridges=1 << 63, split=((1, 0), (5, 6))))
        self.assertEqual(game.initial_state(), start)

    def test_cube_actions_move_one_cell_then_swap_only_active_order(self) -> None:
        game = Game(open_level())
        old = State(bridges=1 << 63, split=((2, 2), (5, 6)))
        expected = [((1, 2), (5, 6)), ((3, 2), (5, 6)),
                    ((2, 1), (5, 6)), ((2, 3), (5, 6)), ((5, 6), (2, 2))]
        successors = game.get_successors(old)
        self.assertEqual([action for action, _, _ in successors], list(ACTIONS))
        for (_, new, cost), positions in zip(successors, expected):
            self.assertEqual(new, State(bridges=1 << 63, split=positions))
            self.assertEqual(cost, 1.0)
        swapped = successors[-1][1]
        self.assertEqual(self.advance(game, swapped, "S"), old)

    def test_adjacent_split_has_no_successors(self) -> None:
        game = Game(open_level())
        for positions in (((2, 2), (2, 3)), ((2, 3), (2, 2)),
                          ((2, 2), (3, 2)), ((3, 2), (2, 2))):
            with self.subTest(positions=positions):
                self.assertEqual(game.get_successors(State(split=positions)), [])

    def test_split_switch_can_place_cube_on_fragile(self) -> None:
        level = open_level(switches=[
            {"type": "split", "pos": [2, 1], "cubes": [[2, 2], [5, 6]]}])
        # Runtime-only Level fixture: the JSON contract forbids fragile split targets.
        level.fragile.add((2, 2))
        game = Game(level)
        # Roll left from a lying block to stand on the switch at (2, 1).
        split = self.advance(game, State(2, 2, HORIZ), "L")
        self.assertEqual(split, State(split=((2, 2), (5, 6))))
        self.assertIn((2, 2), game.tile_rules.fragile)
        self.assertTrue(game.tile_rules.is_supported(split))

    def test_all_four_merge_directions_normalize_and_resume_block_rolls(self) -> None:
        game = Game(open_level())
        cases = [(State(split=((2, 2), (2, 4))), "R", State(2, 3, HORIZ)),
                 (State(split=((2, 4), (2, 2))), "L", State(2, 2, HORIZ)),
                 (State(split=((2, 2), (4, 2))), "D", State(3, 2, VERT)),
                 (State(split=((4, 2), (2, 2))), "U", State(2, 2, VERT))]
        for old, action, expected in cases:
            with self.subTest(action=action):
                merged = self.advance(game, old, action)
                self.assertEqual(merged, expected)
                self.assertNotIn("S", [act for act, _, _ in game.get_successors(merged)])
                self.assertTrue(game.get_successors(merged))

    def test_merge_over_split_switch_does_not_immediately_split_again(self) -> None:
        game = Game(open_level(switches=[
            {"type": "split", "pos": [2, 2], "cubes": [[0, 0], [0, 4]]}]))
        merged = self.advance(game, State(split=((2, 1), (2, 3))), "R")
        self.assertEqual(merged, State(2, 2, HORIZ))
        self.assertIsNone(self.advance(game, merged, "R").split)

    def test_cube_can_cross_fragile_but_upright_full_block_cannot(self) -> None:
        game = Game(open_level(fragile=[[2, 2]]))
        full = State(2, 0, HORIZ)
        self.assertNotIn("R", [a for a, _, _ in game.get_successors(full)])
        cube = State(split=((2, 1), (5, 6)))
        self.assertEqual(self.advance(game, cube, "R").split, ((2, 2), (5, 6)))
        self.assertEqual(self.advance(game, State(2, 0), "R"), State(2, 1, HORIZ))

    def test_closed_bridge_rejects_partial_block_and_single_cube_support(self) -> None:
        game = Game(open_level(bridges=[{"id": 2, "pos": [3, 2]}]))
        for old in (State(3, 0), State(split=((3, 1), (5, 6)))):
            with self.subTest(old=old):
                self.assertNotIn("R", [a for a, _, _ in game.get_successors(old)])
        opened = State(3, 0, bridges=1 << 2)
        self.assertEqual(self.advance(game, opened, "R"), State(3, 1, HORIZ, bridges=1 << 2))

    def test_switch_cannot_rescue_a_landing_on_an_already_closed_bridge(self) -> None:
        game = Game(open_level(
            bridges=[{"id": 2, "pos": [3, 2]}],
            switches=[{"type": "soft", "pos": [3, 1], "targets": [2]}]))
        self.assertNotIn("R", [a for a, _, _ in game.get_successors(game.initial_state())])

    def test_closing_bridge_beneath_full_block_or_inactive_cube_rejects_move(self) -> None:
        for cube in (False, True):
            with self.subTest(cube=cube):
                bridge = [5, 6] if cube else [3, 2]
                game = Game(open_level(
                    bridges=[{"id": 2, "pos": bridge, "open": True}],
                    switches=[{"type": "soft", "pos": [3, 1], "targets": [2]}]))
                old = (State(bridges=1 << 2, split=((3, 0), (5, 6))) if cube
                       else game.initial_state())
                self.assertNotIn("R", [a for a, _, _ in game.get_successors(old)])

    def test_held_soft_switch_does_not_retrigger_on_swap_or_other_cube_move(self) -> None:
        game = Game(open_level(
            bridges=[{"id": 63, "pos": [0, 8]}],
            switches=[{"type": "soft", "pos": [2, 2], "targets": [63]}]))
        state = State(split=((2, 1), (5, 6)))
        pressed = self.advance(game, state, "R")
        swapped = self.advance(game, pressed, "S")
        moved = self.advance(game, swapped, "L")
        self.assertEqual([s.bridges for s in (pressed, swapped, moved)], [1 << 63] * 3)

    def test_soft_toggle_retriggers_only_after_cube_leaves_and_returns(self) -> None:
        game = Game(open_level(
            bridges=[{"id": 2, "pos": [0, 8]}],
            switches=[{"type": "soft", "pos": [2, 2], "targets": [2]}]))
        old = State(split=((2, 1), (5, 6)))
        pressed = self.advance(game, old, "R")
        left = self.advance(game, pressed, "L")
        again = self.advance(game, left, "R")
        self.assertEqual([s.bridges for s in (pressed, left, again)], [4, 4, 0])

    def test_permanent_soft_switch_stays_idempotent_after_reentry(self) -> None:
        for setting, initially_open, expected in (("open", False, 4), ("close", True, 0)):
            with self.subTest(setting=setting):
                game = Game(open_level(
                    bridges=[{"id": 2, "pos": [0, 8], "open": initially_open}],
                    switches=[{"type": "soft", "pos": [2, 2], "targets": [2],
                               "mode": "permanent", "set": setting}]))
                old = State(bridges=game.initial_state().bridges, split=((2, 1), (5, 6)))
                pressed = self.advance(game, old, "R")
                returned = self.advance(game, self.advance(game, pressed, "L"), "R")
                self.assertEqual(pressed.bridges, expected)
                self.assertEqual(returned.bridges, expected)

    def test_single_cube_does_not_activate_heavy_or_split_switch(self) -> None:
        for kind in ("heavy", "split"):
            with self.subTest(kind=kind):
                switch = {"type": kind, "pos": [2, 2]}
                switch.update({"cubes": [[0, 0], [0, 4]]} if kind == "split"
                              else {"targets": [2]})
                game = Game(open_level(bridges=[{"id": 2, "pos": [0, 8]}], switches=[switch]))
                moved = self.advance(game, State(split=((2, 1), (5, 6))), "R")
                self.assertEqual(moved, State(split=((2, 2), (5, 6))))

    def test_two_soft_effects_use_coordinate_order_independent_of_json_order(self) -> None:
        switches = [{"type": "soft", "pos": [3, 1], "targets": [2],
                     "mode": "permanent", "set": "open"},
                    {"type": "soft", "pos": [3, 2], "targets": [2]}]
        for order in (switches, list(reversed(switches))):
            with self.subTest(order=order):
                game = Game(open_level(bridges=[{"id": 2, "pos": [0, 8]}], switches=order))
                self.assertEqual(self.advance(game, game.initial_state(), "R").bridges, 0)

    def test_cost_callback_receives_final_states_once_for_split_merge_and_swap(self) -> None:
        calls = []
        game = Game(mixed_level(), lambda old, action, new: calls.append((old, action, new)) or 7)
        for old in (State(3, 1, HORIZ, bridges=1 << 63),
                    State(bridges=1 << 63, split=((2, 1), (5, 6))),
                    State(bridges=1 << 63, split=((1, 1), (1, 3)))):
            calls.clear()
            successors = game.get_successors(old)
            self.assertEqual(calls, [(old, action, new) for action, new, _ in successors])
            self.assertTrue(all(cost == 7 for _, _, cost in successors))
        calls.clear()
        game.get_successors(State(3, 3, bridges=1 << 63))
        self.assertNotIn("R", [action for _, action, _ in calls])  # closed bridge at (3, 4)

    def test_split_destinations_without_support_are_not_returned(self) -> None:
        # Level's public dataclass also permits direct construction/mutation outside the loader.
        for destination in ((0, 8), (99, 0), (3, 4)):
            with self.subTest(destination=destination):
                level = mixed_level()
                level.switches[(3, 3)].cubes[0] = destination
                game = Game(level)
                old = State(3, 1, HORIZ, bridges=1 << 63)
                self.assertNotIn("R", [a for a, _, _ in game.get_successors(old)])

    def test_repeat_calls_preserve_level_states_and_branch_independence(self) -> None:
        level = mixed_level()
        before = copy.deepcopy(level)
        game = Game(level)
        old = State(bridges=1 << 63, split=((1, 1), (5, 6)))
        hashed = hash(old)
        first = game.get_successors(old)
        self.assertEqual(game.get_successors(old), first)
        self.assertEqual(game.initial_state(), State(3, 0, bridges=1 << 63))
        self.assertEqual(level, before)
        self.assertEqual(hash(old), hashed)
        self.assertEqual(len({old, *[new for _, new, _ in first]}), len(first) + 1)

    def test_mixed_level_replays_all_rules_through_to_a_standing_goal(self) -> None:
        game = Game(mixed_level())
        state = game.initial_state()
        visited = [state]
        for action in "RRRRSLLLLUUUDRRDDRR":
            state = self.advance(game, state, action)
            visited.append(state)
        self.assertTrue(game.is_goal(state))
        self.assertTrue(any(s.split is not None for s in visited))
        self.assertTrue(any((2, 2) in cells(s) for s in visited))  # fragile contact
        self.assertTrue(any((5, 4) in cells(s) for s in visited))  # initially-open bridge
        self.assertTrue(any((3, 4) in cells(s) for s in visited))  # soft-opened bridge
        self.assertIn((1 << 63) | 4, [s.bridges for s in visited])
        self.assertEqual(state.bridges, 4)  # heavy permanently closed bridge 63

    def test_solver_replay_requires_split_swap_soft_switch_bridge_and_merge(self) -> None:
        game = Game(forced_split_level())
        split = self.advance(game, self.advance(game, game.initial_state(), "R"), "R")
        self.assertEqual([a for a, _, _ in game.get_successors(split)], ["S"])
        lengths = []
        for solver in (bfs, ucs, astar):
            with self.subTest(solver=solver.__name__):
                result = solver.solve(game, Limits(max_nodes=2000))
                self.assertTrue(result.solved)
                self.assertIn("S", result.path)
                lengths.append(result.length)
                state = game.initial_state()
                for action in result.path:
                    state = self.advance(game, state, action)
                    if state.split is not None:
                        self.assertFalse(game.is_goal(state))
                self.assertTrue(game.is_goal(state))
                self.assertEqual(result.cost, result.length)
        self.assertEqual(lengths, [8, 8, 8])


if __name__ == "__main__":
    unittest.main()
