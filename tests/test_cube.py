"""Kiểm thử bất biến của trạng thái split và di chuyển cube đơn (C1)."""
import unittest

from game.cube import move_cube
from game.level_loader import Bridge, Level
from game.state import HORIZ, STAND, State, VERT


def make_level(grid: tuple[str, ...], bridges: tuple[Bridge, ...] = ()) -> Level:
    """Tạo màn chơi nhỏ để kiểm thử di chuyển cube."""
    return Level(
        name="cube-test",
        grid=list(grid),
        start=(0, 0),
        goal=(0, 1),
        fragile=set(),
        bridges={bridge.id: bridge for bridge in bridges},
        switches={},
    )


class TestSplitState(unittest.TestCase):
    """Kiểm tra biểu diễn split đã chuẩn hóa và có thể băm."""

    def test_split_state_is_canonical_and_hashable(self) -> None:
        state = State(r=8, c=9, orient=VERT, bridges=3, split=((1, 2), (4, 5)))
        canonical = State(bridges=3, split=((1, 2), (4, 5)))

        self.assertEqual(state, canonical)
        self.assertEqual(hash(state), hash(canonical))
        self.assertEqual((state.r, state.c, state.orient), (0, 0, STAND))

    def test_split_state_rejects_mutable_or_invalid_positions(self) -> None:
        with self.assertRaises(TypeError):
            State(split=[(1, 2), (4, 5)])
        with self.assertRaises(TypeError):
            State(split=((1, 2), [4, 5]))
        with self.assertRaises(ValueError):
            State(split=((1, 2), (1, 2)))

    def test_swap_changes_active_cube_and_preserves_bridge_mask(self) -> None:
        state = State(bridges=5, split=((1, 2), (4, 5)))

        swapped = move_cube(state, "S", make_level(("#####",) * 5))

        self.assertEqual(swapped.split, ((4, 5), (1, 2)))
        self.assertEqual(swapped.bridges, 5)
        self.assertEqual((swapped.r, swapped.c, swapped.orient), (0, 0, STAND))

class TestSingleCubeMovement(unittest.TestCase):
    """Kiểm tra bước đi một ô, mặt sàn hợp lệ và cơ chế tự ghép."""

    def setUp(self) -> None:
        self.level = make_level(("#####",) * 5)

    def test_moves_one_cell_in_each_direction(self) -> None:
        state = State(split=((2, 2), (0, 0)))
        expected = {
            "U": ((1, 2), (0, 0)),
            "D": ((3, 2), (0, 0)),
            "L": ((2, 1), (0, 0)),
            "R": ((2, 3), (0, 0)),
        }

        for action, positions in expected.items():
            with self.subTest(action=action):
                self.assertEqual(move_cube(state, action, self.level).split, positions)

    def test_rejects_moves_outside_board_in_all_directions(self) -> None:
        cases = (
            (((0, 2), (4, 4)), "U"),
            (((4, 2), (0, 0)), "D"),
            (((2, 0), (4, 4)), "L"),
            (((2, 4), (0, 0)), "R"),
        )
        for positions, action in cases:
            with self.subTest(action=action, positions=positions):
                self.assertIsNone(move_cube(State(split=positions), action, self.level))

    def test_rejects_move_onto_void(self) -> None:
        level = make_level(("#####", "##.##", "#####"))
        state = State(split=((1, 1), (2, 4)))

        self.assertIsNone(move_cube(state, "R", level))

    def test_single_cube_can_stand_on_fragile_cells(self) -> None:
        level = make_level(("#####",) * 5)
        level.fragile.add((2, 3))
        state = State(split=((2, 2), (0, 0)))

        moved = move_cube(state, "R", level)

        self.assertEqual(moved.split, ((2, 3), (0, 0)))

    def test_rejects_closed_bridge_and_allows_open_bridge(self) -> None:
        bridge = Bridge(id=2, pos=(2, 3), open=False)
        level = make_level(("#####",) * 5, (bridge,))
        state = State(split=((2, 2), (0, 0)))

        self.assertIsNone(move_cube(state, "R", level))
        opened = State(bridges=1 << 2, split=state.split)
        self.assertEqual(
            move_cube(opened, "R", level).split,
            ((2, 3), (0, 0)),
        )

    def test_rejects_merge_across_a_void_cell(self) -> None:
        level = make_level(("#####", "##.##", "#####"))
        state = State(split=((1, 1), (1, 3)))

        self.assertIsNone(move_cube(state, "R", level))

    def test_merges_horizontally_and_vertically(self) -> None:
        horizontal = move_cube(State(split=((1, 1), (1, 3))), "R", self.level)
        vertical = move_cube(State(split=((1, 1), (3, 1))), "D", self.level)

        self.assertEqual(horizontal, State(1, 2, HORIZ))
        self.assertEqual(vertical, State(2, 1, VERT))

    def test_rejects_invalid_actions_and_unsplit_states(self) -> None:
        state = State(split=((2, 2), (0, 0)))

        with self.assertRaises(ValueError):
            move_cube(state, "X", self.level)
        with self.assertRaises(ValueError):
            move_cube(State(), "U", self.level)

    def test_move_rejects_an_unmerged_adjacent_split_state(self) -> None:
        state = State(split=((1, 1), (1, 2)))

        with self.assertRaisesRegex(ValueError, "kề nhau"):
            move_cube(state, "L", self.level)


if __name__ == "__main__":
    unittest.main()
