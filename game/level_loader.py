"""Load and validate the team's JSON level format without changing its public data API."""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

Cell = Tuple[int, int]


@dataclass
class Bridge:
    """One bridge tile, addressed by its ID rather than its position in JSON."""

    id: int
    pos: Cell
    open: bool = False


@dataclass
class Switch:
    """Static switch configuration; split data is reserved for C1/C2."""

    type: str
    pos: Cell
    targets: List[int] = field(default_factory=list)
    mode: str = "toggle"
    set: Optional[str] = None
    cubes: Optional[List[Cell]] = None


@dataclass
class Level:
    """Parsed level data, detached from the input JSON's mutable containers."""

    name: str
    grid: List[str]
    start: Cell
    goal: Cell
    fragile: Set[Cell]
    bridges: Dict[int, Bridge]
    switches: Dict[Cell, Switch]

    @property
    def rows(self) -> int:
        """Number of rows."""
        return len(self.grid)

    @property
    def cols(self) -> int:
        """Number of columns in the rectangular grid."""
        return len(self.grid[0]) if self.grid else 0

    def initial_bridge_mask(self) -> int:
        """Return bit i set exactly when bridge ID i starts open."""
        mask = 0
        for bridge in self.bridges.values():
            if bridge.open:
                mask |= 1 << bridge.id
        return mask


def _object(value: object, field_name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name}: expected an object")
    return value


def _list(value: object, field_name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{field_name}: expected a list")
    return value


def _required(data: dict, key: str, field_name: str) -> object:
    if key not in data:
        raise ValueError(f"{field_name}.{key}: required field is missing")
    return data[key]


def _integer(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name}: expected a non-negative integer, got {value!r}")
    return value


def _cell(value: object, field_name: str) -> Cell:
    pair = _list(value, field_name)
    if len(pair) != 2:
        raise ValueError(f"{field_name}: expected [row, column]")
    return (_integer(pair[0], f"{field_name}[0]"), _integer(pair[1], f"{field_name}[1]"))


def _grid(value: object) -> List[str]:
    rows = _list(value, "grid")
    if not rows or any(not isinstance(row, str) or not row for row in rows):
        raise ValueError("grid: expected non-empty strings in a non-empty list")
    if len({len(row) for row in rows}) != 1:
        raise ValueError("grid: rows must have the same length")
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char not in ".#G":
                raise ValueError(f"grid[{r}][{c}]: unsupported tile {char!r}")
    if sum(row.count("G") for row in rows) != 1:
        raise ValueError("grid: expected exactly one 'G' goal tile")
    return list(rows)


def _bridges(value: object) -> Dict[int, Bridge]:
    result = {}
    positions = set()
    for index, item in enumerate(_list(value, "bridges")):
        label = f"bridges[{index}]"
        item = _object(item, label)
        bridge_id = _integer(_required(item, "id", label), f"{label}.id")
        pos = _cell(_required(item, "pos", label), f"{label}.pos")
        opened = item.get("open", False)
        if type(opened) is not bool:
            raise ValueError(f"{label}.open: expected a boolean")
        if bridge_id in result:
            raise ValueError(f"{label}.id: duplicate bridge ID {bridge_id}")
        if pos in positions:
            raise ValueError(f"{label}.pos: duplicate bridge position {pos}")
        positions.add(pos)
        result[bridge_id] = Bridge(bridge_id, pos, opened)
    return result


def _switch(item: object, label: str) -> Switch:
    item = _object(item, label)
    kind = _required(item, "type", label)
    if kind not in ("soft", "heavy", "split"):
        raise ValueError(f"{label}.type: unsupported switch type {kind!r}")
    pos = _cell(_required(item, "pos", label), f"{label}.pos")
    mode = item.get("mode", "toggle")
    if mode not in ("toggle", "permanent"):
        raise ValueError(f"{label}.mode: expected 'toggle' or 'permanent'")
    setting = item.get("set")
    if mode == "permanent" and setting not in ("open", "close"):
        raise ValueError(f"{label}.set: permanent mode requires 'open' or 'close'")
    if mode == "toggle" and setting is not None:
        raise ValueError(f"{label}.set: only valid in permanent mode")
    if kind == "split":
        if item.get("targets", []) != [] or mode != "toggle":
            raise ValueError(f"{label}: split switches cannot control bridges")
        cubes = [_cell(p, f"{label}.cubes[{i}]") for i, p in enumerate(
            _list(_required(item, "cubes", label), f"{label}.cubes"))]
        if len(cubes) != 2 or cubes[0] == cubes[1]:
            raise ValueError(f"{label}.cubes: expected two distinct positions")
        return Switch(kind, pos, cubes=cubes)
    if "cubes" in item:
        raise ValueError(f"{label}.cubes: only valid for split switches")
    targets = [_integer(t, f"{label}.targets[{i}]") for i, t in enumerate(
        _list(item.get("targets", []), f"{label}.targets"))]
    if len(set(targets)) != len(targets):
        raise ValueError(f"{label}.targets: duplicate bridge IDs")
    return Switch(kind, pos, targets, mode, setting)


def load_level(path: str) -> Level:
    """Load a UTF-8 JSON file; preserve file and JSON exceptions for caller diagnostics."""
    with open(path, encoding="utf-8") as source:
        return parse_level(json.load(source))


def parse_level(d: dict) -> Level:
    """Validate JSON data and return the existing Level/Bridge/Switch public types."""
    d = _object(d, "level")
    name = d.get("name", "unnamed")
    if not isinstance(name, str):
        raise ValueError("name: expected a string")
    fragile_list = [_cell(p, f"fragile[{i}]") for i, p in enumerate(
        _list(d.get("fragile", []), "fragile"))]
    if len(set(fragile_list)) != len(fragile_list):
        raise ValueError("fragile: duplicate positions")
    switches = {}
    for i, item in enumerate(_list(d.get("switches", []), "switches")):
        switch = _switch(item, f"switches[{i}]")
        if switch.pos in switches:
            raise ValueError(f"switches[{i}].pos: duplicate position {switch.pos}")
        switches[switch.pos] = switch
    level = Level(
        name, _grid(_required(d, "grid", "level")),
        _cell(_required(d, "start", "level"), "start"),
        _cell(_required(d, "goal", "level"), "goal"),
        set(fragile_list), _bridges(d.get("bridges", [])), switches,
    )
    _validate(level)
    return level


def _validate(level: Level) -> None:
    def tile(pos: Cell) -> Optional[str]:
        r, c = pos
        return level.grid[r][c] if 0 <= r < level.rows and 0 <= c < level.cols else None

    def floor(pos: Cell, label: str) -> None:
        if tile(pos) != "#":
            raise ValueError(f"{label} {pos}: expected a '#' floor tile inside grid")

    if tile(level.start) not in ("#", "G"):
        raise ValueError(f"start {level.start}: expected floor inside grid")
    if tile(level.goal) != "G":
        raise ValueError(f"goal {level.goal}: must match the 'G' tile inside grid")
    for pos in level.fragile:
        floor(pos, "fragile")
    for bridge in level.bridges.values():
        floor(bridge.pos, f"bridge {bridge.id}.pos")
    for switch in level.switches.values():
        floor(switch.pos, f"switch {switch.pos}.pos")
        for target in switch.targets:
            if target not in level.bridges:
                raise ValueError(f"switch {switch.pos}.targets: unknown bridge ID {target}")
        for pos in switch.cubes or []:
            if tile(pos) not in ("#", "G"):
                raise ValueError(f"switch {switch.pos}.cubes {pos}: expected floor inside grid")
    if level.start in level.fragile:
        raise ValueError(f"start {level.start}: standing on fragile would immediately fall")
    for bridge in level.bridges.values():
        if bridge.pos == level.start and not bridge.open:
            raise ValueError(f"start {level.start}: bridge {bridge.id} is initially closed")
