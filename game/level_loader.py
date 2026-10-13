"""Đọc màn chơi từ file JSON (định dạng xem README.md, mục 'Định dạng màn chơi')."""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

Cell = Tuple[int, int]


@dataclass
class Bridge:
    id: int
    pos: Cell
    open: bool = False


@dataclass
class Switch:
    type: str                      # "soft" | "heavy" | "split"
    pos: Cell
    targets: List[int] = field(default_factory=list)   # id các cầu bị tác động
    mode: str = "toggle"           # "toggle" | "permanent"
    set: Optional[str] = None      # permanent: "open" | "close"
    cubes: Optional[List[Cell]] = None   # split: 2 vị trí cube sau khi tách


@dataclass
class Level:
    name: str
    grid: List[str]                # '.' trống, '#' sàn, 'G' đích
    start: Cell
    goal: Cell
    fragile: Set[Cell]
    bridges: Dict[int, Bridge]     # id -> Bridge
    switches: Dict[Cell, Switch]   # pos -> Switch

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def initial_bridge_mask(self) -> int:
        mask = 0
        for b in self.bridges.values():
            if b.open:
                mask |= 1 << b.id
        return mask


def _cell(x) -> Cell:
    return (int(x[0]), int(x[1]))


def load_level(path: str) -> Level:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return parse_level(d)


def parse_level(d: dict) -> Level:
    grid = d["grid"]
    if len({len(row) for row in grid}) != 1:
        raise ValueError("Các dòng của grid phải cùng độ dài")
    level = Level(
        name=d.get("name", "unnamed"),
        grid=grid,
        start=_cell(d["start"]),
        goal=_cell(d["goal"]),
        fragile={_cell(p) for p in d.get("fragile", [])},
        bridges={b["id"]: Bridge(b["id"], _cell(b["pos"]), bool(b.get("open", False)))
                 for b in d.get("bridges", [])},
        switches={},
    )
    for s in d.get("switches", []):
        sw = Switch(
            type=s["type"], pos=_cell(s["pos"]), targets=list(s.get("targets", [])),
            mode=s.get("mode", "toggle"), set=s.get("set"),
            cubes=[_cell(p) for p in s["cubes"]] if "cubes" in s else None,
        )
        level.switches[sw.pos] = sw
    _validate(level)
    return level


def _validate(lv: Level) -> None:
    def inside(p): return 0 <= p[0] < lv.rows and 0 <= p[1] < lv.cols
    def walkable(p): return inside(p) and lv.grid[p[0]][p[1]] != "."

    if not walkable(lv.start):
        raise ValueError(f"start {lv.start} không nằm trên ô sàn")
    if not inside(lv.goal) or lv.grid[lv.goal[0]][lv.goal[1]] != "G":
        raise ValueError(f"goal {lv.goal} phải là ô 'G' trong grid")
    for p in lv.fragile:
        if not walkable(p):
            raise ValueError(f"ô dễ vỡ {p} không nằm trên ô sàn")
    for b in lv.bridges.values():
        if not inside(b.pos):
            raise ValueError(f"cầu {b.id} nằm ngoài bản đồ")
    for sw in lv.switches.values():
        if not walkable(sw.pos):
            raise ValueError(f"công tắc {sw.pos} không nằm trên ô sàn")
        if sw.type == "split":
            if not sw.cubes or len(sw.cubes) != 2:
                raise ValueError("công tắc split cần đúng 2 vị trí trong 'cubes'")
        else:
            for t in sw.targets:
                if t not in lv.bridges:
                    raise ValueError(f"công tắc {sw.pos} trỏ tới cầu không tồn tại: {t}")
        if sw.mode == "permanent" and sw.set not in ("open", "close"):
            raise ValueError("mode permanent cần 'set': 'open' hoặc 'close'")
