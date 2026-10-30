"""T3: kiểm tra bộ test nhóm 4 (có công tắc tách)."""
import glob
import unittest
from dataclasses import replace
from pathlib import Path

from game.game import Game
from game.level_loader import load_level
from solvers import bfs
from solvers.base import Limits
from tests.level_verifier import replay

LEVEL_DIR = Path(__file__).resolve().parent.parent / "levels"
LIMITS = Limits(max_nodes=200_000)

# Độ dài lời giải tối ưu (BFS, mỗi bước chi phí 1).
EXPECTED_LENGTH = {
    "g4_mixed_01": 5,
    "g4_mixed_02": 8,
    "g4_mixed_03": 13,
    "g4_mixed_04": 21,
}
# Các loại công tắc mà màn đó BẮT BUỘC phải dùng.
NEEDED_SWITCHES = {
    "g4_mixed_01": ("split",),
    "g4_mixed_02": ("split", "soft"),
    "g4_mixed_03": ("split",),
    "g4_mixed_04": ("split", "soft", "heavy"),
}
# Các màn mà ô dễ vỡ làm lời giải dài hơn.
FRAGILE_MATTERS = ("g4_mixed_03", "g4_mixed_04")


def _level(name: str):
    return load_level(str(LEVEL_DIR / (name + ".json")))


def _solve(level):
    return bfs.solve(Game(level), LIMITS)


def _without_switch(level, kind: str):
    kept = {pos: sw for pos, sw in level.switches.items() if sw.type != kind}
    return replace(level, switches=kept)


class TestGroup4Levels(unittest.TestCase):
    def test_all_expected_files_exist_and_load(self):
        found = {Path(p).stem for p in glob.glob(str(LEVEL_DIR / "g4_*.json"))}
        for name in EXPECTED_LENGTH:
            self.assertIn(name, found)
            self.assertEqual(_level(name).name, name)

    def test_every_level_has_split_switch(self):
        for name in EXPECTED_LENGTH:
            with self.subTest(level=name):
                level = _level(name)
                self.assertTrue(any(s.type == "split" for s in level.switches.values()))

    def test_every_level_is_solvable_with_expected_length(self):
        for name, length in EXPECTED_LENGTH.items():
            with self.subTest(level=name):
                game = Game(_level(name))
                result = bfs.solve(game, LIMITS)
                self.assertTrue(result.solved)
                self.assertEqual(result.length, length)
                replay(game, tuple(result.path))   # mọi bước phải hợp lệ, cuối là đích

    def test_solution_actually_splits_the_block(self):
        for name in EXPECTED_LENGTH:
            with self.subTest(level=name):
                game = Game(_level(name))
                path = bfs.solve(game, LIMITS).path
                states = replay(game, tuple(path))
                self.assertTrue(any(s.split is not None for s in states))

    def test_difficulty_increases(self):
        lengths = [EXPECTED_LENGTH[n] for n in sorted(EXPECTED_LENGTH)]
        self.assertEqual(lengths, sorted(lengths))
        self.assertEqual(len(set(lengths)), len(lengths))

    def test_needed_switches_are_really_needed(self):
        # Đối chứng: bỏ một loại công tắc cần thiết thì màn phải không giải được.
        for name, kinds in NEEDED_SWITCHES.items():
            for kind in kinds:
                with self.subTest(level=name, removed=kind):
                    level = _without_switch(_level(name), kind)
                    self.assertFalse(_solve(level).solved)

    def test_fragile_tiles_make_solution_longer(self):
        for name in FRAGILE_MATTERS:
            with self.subTest(level=name):
                level = _level(name)
                relaxed = _solve(replace(level, fragile=set()))
                self.assertTrue(relaxed.solved)
                self.assertLess(relaxed.length, EXPECTED_LENGTH[name])


if __name__ == "__main__":
    unittest.main()