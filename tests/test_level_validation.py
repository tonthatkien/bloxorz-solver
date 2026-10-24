"""B1 validation, compatibility and input-isolation regression tests."""
import copy
import io
import json
import unittest
from unittest.mock import mock_open, patch

from game.level_loader import LevelValidationError, Switch, load_level, parse_level


def basic_level() -> dict:
    """Return a fresh rectangular level using the documented JSON symbols."""
    return {"grid": ["######", "#####G", "######", "######"],
            "start": [0, 0], "goal": [1, 5]}


def advanced_level() -> dict:
    """Return mixed terrain with unordered, non-contiguous bridge IDs."""
    return dict(basic_level(), fragile=[[1, 3]], bridges=[
        {"id": 7, "pos": [2, 2], "open": True},
        {"id": 2, "pos": [2, 3], "open": False}], switches=[
        {"type": "soft", "pos": [1, 1], "targets": [2, 7]},
        {"type": "heavy", "pos": [3, 2], "targets": [7],
         "mode": "permanent", "set": "close"},
        {"type": "split", "pos": [0, 2], "cubes": [[3, 3], [1, 4]]}])


class TestLevelValidation(unittest.TestCase):
    """Check both accepted data and field-specific diagnostics for rejected data."""

    def test_basic_defaults_and_dimensions(self):
        level = parse_level(basic_level())
        self.assertEqual((level.name, level.rows, level.cols), ("unnamed", 4, 6))
        self.assertEqual((level.start, level.goal), ((0, 0), (1, 5)))
        self.assertEqual((level.fragile, level.bridges, level.switches), (set(), {}, {}))
        self.assertEqual(level.initial_bridge_mask(), 0)

    def test_mixed_tiles_preserve_schema_and_id_mask(self):
        level = parse_level(advanced_level())
        self.assertEqual(level.initial_bridge_mask(), 1 << 7)
        self.assertEqual(level.fragile, {(1, 3)})
        self.assertEqual(level.switches[(1, 1)].targets, [2, 7])
        self.assertEqual(level.switches[(3, 2)].set, "close")
        self.assertEqual(level.switches[(0, 2)].cubes, [(3, 3), (1, 4)])
        self.assertEqual(level.grid[0][0], "#")

    def test_parsing_detaches_all_mutable_input_and_does_not_mutate_it(self):
        data = advanced_level()
        before = copy.deepcopy(data)
        level = parse_level(data)
        self.assertEqual(data, before)
        data["grid"][0] = "......"
        data["start"][0] = 99
        data["fragile"][0][0] = 99
        data["bridges"][0]["open"] = False
        data["switches"][0]["targets"].append(99)
        data["switches"][2]["cubes"][0][0] = 99
        self.assertEqual(level.grid[0], "######")
        self.assertEqual(level.start, (0, 0))
        self.assertEqual(level.fragile, {(1, 3)})
        self.assertEqual(level.initial_bridge_mask(), 1 << 7)
        self.assertEqual(level.switches[(1, 1)].targets, [2, 7])
        self.assertEqual(level.switches[(0, 2)].cubes[0], (3, 3))

    def test_json_round_trip_preserves_loaded_data(self):
        data = advanced_level()
        self.assertEqual(parse_level(data), parse_level(json.loads(json.dumps(data))))

    def test_documented_defaults_for_bridges_and_switches(self):
        data = advanced_level()
        del data["bridges"][0]["open"]
        level = parse_level(data)
        self.assertFalse(level.bridges[7].open)
        self.assertEqual(level.switches[(1, 1)].mode, "toggle")

    def test_permanent_json_set_and_public_switch_constructor_remain_compatible(self):
        for setting in ("open", "close"):
            data = advanced_level()
            data["switches"][1]["set"] = setting
            loaded = parse_level(data).switches[(3, 2)]
            expected = Switch("heavy", (3, 2), targets=[7], mode="permanent", set=setting)
            self.assertEqual(loaded, expected)
            self.assertEqual(loaded.set, setting)
        self.assertEqual(set([2, 7, 2]), {2, 7})

    def test_each_pair_of_special_types_is_rejected_with_coordinate_and_types(self):
        # D1 covers every switch kind, including soft switches on fragile tiles.
        kinds = ("fragile", "bridge", "soft", "heavy", "split", "goal")
        for first_index, first in enumerate(kinds):
            for second in kinds[first_index + 1:]:
                if first in ("soft", "heavy", "split") and second in ("heavy", "split"):
                    continue  # Duplicate switch positions have their own validation test.
                with self.subTest(first=first, second=second):
                    data = basic_level()
                    pos = data["goal"] if "goal" in (first, second) else [2, 2]
                    for kind in (first, second):
                        if kind == "fragile":
                            data["fragile"] = [pos]
                        elif kind == "bridge":
                            data["bridges"] = [{"id": 0, "pos": pos}]
                        elif kind != "goal":
                            switch = {"type": kind, "pos": pos}
                            if kind == "split":
                                switch["cubes"] = [[0, 1], [0, 2]]
                            data["switches"] = [switch]
                    with self.assertRaises(LevelValidationError) as caught:
                        parse_level(data)
                    message = str(caught.exception)
                    self.assertIn(str(tuple(pos)), message)
                    self.assertIn(first if first not in ("soft", "heavy", "split")
                                  else f"switch ({first})", message)
                    self.assertIn(second if second not in ("soft", "heavy", "split")
                                  else f"switch ({second})", message)

    def test_bridge_and_target_ids_accept_zero_and_63_without_renumbering(self):
        data = dict(basic_level(), bridges=[
            {"id": 63, "pos": [2, 2], "open": True},
            {"id": 0, "pos": [2, 3], "open": True}], switches=[
            {"type": "soft", "pos": [1, 1], "targets": [63, 0]}])
        level = parse_level(data)
        self.assertEqual(level.initial_bridge_mask(), (1 << 63) | 1)
        self.assertEqual(level.switches[(1, 1)].targets, [63, 0])

    def test_bridge_and_target_ids_reject_out_of_range_and_non_integer_values(self):
        for bridge_id in (-1, 64, 10**9, True, False, 1.0, "1", None):
            for field in ("bridge", "target"):
                with self.subTest(bridge_id=bridge_id, field=field):
                    data = advanced_level()
                    if field == "bridge":
                        data["bridges"][0]["id"] = bridge_id
                    else:
                        data["switches"][0]["targets"] = [bridge_id]
                    with self.assertRaisesRegex(LevelValidationError, "id|targets"):
                        parse_level(data)

    def test_unknown_target_inside_id_range_is_rejected(self):
        data = advanced_level()
        data["switches"][0]["targets"] = [63]
        with self.assertRaisesRegex(LevelValidationError, r"\(1, 1\).*unknown bridge ID 63"):
            parse_level(data)

    def test_split_destinations_require_ordinary_floor(self):
        for destination, reason in (([1, 3], "fragile"), ([2, 2], "bridge"),
                                    ([2, 3], "bridge"), ([1, 5], "goal"),
                                    ([1, 1], "switch"), ([3, 2], "switch"),
                                    ([0, 2], "switch"), ([99, 1], "outside")):
            with self.subTest(destination=destination):
                data = advanced_level()
                data["switches"][2]["cubes"][0] = destination
                with self.assertRaises(LevelValidationError) as caught:
                    parse_level(data)
                message = str(caught.exception)
                self.assertIn("cubes", message)
                self.assertIn(str(tuple(destination)), message)
                self.assertIn(reason, message)
        data = advanced_level()
        data["grid"][3] = "#.####"
        data["switches"][2]["cubes"][0] = [3, 1]
        with self.assertRaisesRegex(LevelValidationError, "cubes.*void"):
            parse_level(data)

    def test_coordinate_range_is_independent_of_bridge_id_limit(self):
        data = {"grid": ["#" * 65 + "G"], "start": [0, 64], "goal": [0, 65]}
        self.assertEqual(parse_level(data).start, (0, 64))

    def test_root_required_fields_and_collections(self):
        for bad in (None, [], 3, "level"):
            with self.subTest(root=bad), self.assertRaisesRegex(LevelValidationError, "level"):
                parse_level(bad)
        for key in ("grid", "start", "goal"):
            data = basic_level()
            del data[key]
            with self.subTest(missing=key), self.assertRaisesRegex(LevelValidationError, key):
                parse_level(data)
        for key in ("fragile", "bridges", "switches"):
            for bad in (None, {}, "text", False):
                with self.subTest(key=key, bad=bad), self.assertRaisesRegex(LevelValidationError, key):
                    parse_level(dict(basic_level(), **{key: bad}))
        with self.assertRaisesRegex(LevelValidationError, "name"):
            parse_level(dict(basic_level(), name=7))

    def test_grid_shape_symbols_and_goal_count(self):
        for grid in ([], [""], ["##", "#G#"], [[], []], "#G", ["#?G"],
                     ["###"], ["GG#"], [False]):
            with self.subTest(grid=grid), self.assertRaisesRegex(LevelValidationError, "grid"):
                parse_level(dict(basic_level(), grid=grid))

    def test_coordinates_reject_coercion_wrong_length_void_and_outside(self):
        for field in ("start", "goal"):
            for bad in ([-1, 0], [99, 0], [0, 99], [True, 0], [0.5, 0],
                        ["0", 0], [0], [0, 0, 0], "00", None):
                with self.subTest(field=field, bad=bad), self.assertRaisesRegex(LevelValidationError, field):
                    parse_level(dict(basic_level(), **{field: bad}))
        data = basic_level()
        data["grid"][0] = ".#####"
        with self.assertRaisesRegex(LevelValidationError, "start"):
            parse_level(data)
        with self.assertRaisesRegex(LevelValidationError, "goal"):
            parse_level(dict(basic_level(), goal=[0, 1]))

    def test_fragile_records_and_invalid_initial_support(self):
        for fragile in ([[0, 0]], [[99, 0]], [[True, 1]], [[1, 5]], [[1, 1], [1, 1]]):
            with self.subTest(fragile=fragile), self.assertRaisesRegex(LevelValidationError, "fragile"):
                parse_level(dict(basic_level(), fragile=fragile))
        data = advanced_level()
        data["bridges"][0]["pos"] = [0, 0]
        data["bridges"][0]["open"] = False
        with self.assertRaisesRegex(LevelValidationError, "start.*closed"):
            parse_level(data)
        data["bridges"][0]["open"] = True
        self.assertEqual(parse_level(data).start, (0, 0))

    def test_bridge_invalid_records_ids_positions_and_boolean(self):
        for changes in ({"id": -1}, {"id": True}, {"id": 1.5}, {"id": "1"},
                        {"open": "false"}, {"open": 1}, {"pos": [99, 0]},
                        {"pos": [1, 5]}, {"pos": [True, 2]}):
            data = advanced_level()
            data["bridges"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(LevelValidationError, "bridge"):
                parse_level(data)
        for item in (None, [], {}, {"id": 1}):
            with self.subTest(item=item), self.assertRaisesRegex(LevelValidationError, "bridges"):
                parse_level(dict(basic_level(), bridges=[item]))
        for key in ("id", "pos"):
            data = advanced_level()
            data["bridges"][1][key] = data["bridges"][0][key]
            with self.subTest(duplicate=key), self.assertRaisesRegex(LevelValidationError, "duplicate"):
                parse_level(data)

    def test_switch_invalid_records_links_modes_and_types(self):
        cases = [{"type": "unknown"}, {"type": []}, {"mode": "bad"},
                 {"mode": False}, {"mode": "permanent"},
                 {"mode": "permanent", "set": "invalid"}, {"set": "open"},
                 {"targets": [999]}, {"targets": [True]}, {"targets": [2.0]},
                 {"targets": [2, 2]}, {"targets": None}, {"cubes": [[1, 1], [1, 2]]},
                 {"pos": [99, 1]}, {"pos": [1, 5]}, {"pos": [False, 1]}]
        for changes in cases:
            data = advanced_level()
            data["switches"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(LevelValidationError, "switch"):
                parse_level(data)
        for item in (None, [], {}, {"type": "soft"}):
            with self.subTest(item=item), self.assertRaisesRegex(LevelValidationError, "switches"):
                parse_level(dict(basic_level(), switches=[item]))
        data = advanced_level()
        data["switches"][1]["pos"] = data["switches"][0]["pos"]
        with self.assertRaisesRegex(LevelValidationError, "duplicate"):
            parse_level(data)

    def test_split_metadata_validation(self):
        for cubes in (None, [], [[1, 1]], [[1, 1]] * 2, [[1, 1]] * 3,
                      [[99, 1], [1, 1]], [[True, 1], [1, 1]]):
            data = advanced_level()
            data["switches"][2]["cubes"] = cubes
            with self.subTest(cubes=cubes), self.assertRaisesRegex(LevelValidationError, "cubes"):
                parse_level(data)
        data = advanced_level()
        del data["switches"][2]["cubes"]
        with self.assertRaisesRegex(LevelValidationError, "cubes"):
            parse_level(data)
        data = advanced_level()
        data["switches"][2]["targets"] = [2]
        with self.assertRaisesRegex(LevelValidationError, "split"):
            parse_level(data)

    def test_json_decoder_value_errors_use_loader_exception(self):
        # Python 3.11+ rejects excessively long integer tokens before schema validation.
        error = ValueError("integer string exceeds interpreter limit")
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("game.level_loader.json.load", side_effect=error):
                with self.assertRaisesRegex(LevelValidationError, "invalid JSON value") as caught:
                    load_level("levels/invalid-value.json")
        self.assertIs(caught.exception.__cause__, error)

    def test_missing_file_and_invalid_json_keep_distinct_errors(self):
        with patch("builtins.open", side_effect=FileNotFoundError("missing")):
            with self.assertRaises(FileNotFoundError):
                load_level("levels/missing.json")
        with patch("builtins.open", mock_open(read_data='{invalid')):
            with self.assertRaisesRegex(
                    LevelValidationError, "invalid.json.*line 1, column 2") as caught:
                load_level("levels/invalid.json")
            self.assertIsInstance(caught.exception.__cause__, json.JSONDecodeError)
            self.assertIsInstance(caught.exception, ValueError)
        with patch("builtins.open", mock_open()) as opened:
            opened.return_value.read.side_effect = UnicodeDecodeError(
                "utf-8", b"\xff", 0, 1, "invalid start byte")
            with self.assertRaisesRegex(LevelValidationError, "UTF-8"):
                load_level("levels/invalid-encoding.json")
        with patch("builtins.open", return_value=io.StringIO(json.dumps(basic_level()))):
            self.assertEqual(load_level("levels/basic.json"), parse_level(basic_level()))


if __name__ == "__main__":
    unittest.main()
