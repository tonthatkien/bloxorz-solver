"""Heuristic nâng cao cho A* (task E2), bổ sung cho solvers/heuristics.py.

Mọi hàm có chữ ký `h(game, state) -> float`; truyền cho A* bằng hàm hoặc bằng tên:
    astar.solve_with(game, "advanced")        # tên nằm trong HEURISTICS

Ý tưởng: nới lỏng luật Bloxorz rồi tính khoảng cách chính xác trong bài toán đã nới lỏng. Khoảng
cách đó là cận dưới của chi phí thật nên admissible. Phép nới lỏng dùng chung là "đồ thị khối":
đỉnh (hàng, cột, tư thế), cạnh là phép lăn thật, bỏ qua công tắc, giữ ô trống và luật không
được đứng trên ô dễ vỡ.

- h_switch_aware: khối chưa tách. Dùng đúng bitmask cầu hiện tại; nếu goal bị cầu đóng chắn thì
  cộng cả đoạn đường ghé một công tắc. Đích nới lỏng gồm goal và các công tắc split.
- h_split_cubes: đang tách. Hai cube phải ghép lại rồi khối ghép mới tới được đích.
- h_advanced: h_split_cubes khi đang tách, ngược lại h_switch_aware (mặc định của A*).

Định nghĩa và chứng minh admissible/consistent: docs/cost_heuristic.md, mục III.
Dữ liệu tính trước được cache theo đối tượng Level; gọi clear_caches() khi nạp lại màn hoặc trong
test.
"""
import heapq
import math
from collections import deque
from typing import Callable, Dict, List, Optional, Tuple, Union

from game.block import Block
from game.board import Board
from game.state import HORIZ, STAND, VERT, Cell, State

from .heuristics import COST_MIN, h_manhattan, h_manhattan_orient, h_relaxed_maze, h_zero

Heuristic = Callable[[object, State], float]
_DIRECTIONS = "UDLR"
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class _LevelModel:
    """Dữ liệu nới lỏng tính trước cho một màn chơi."""

    def __init__(self, level) -> None:
        self.level = level
        self.board = Board.from_strings(level.grid)
        self.fragile = frozenset(level.fragile)
        self.bridge_of: Dict[Cell, int] = {b.pos: b.id for b in level.bridges.values()}
        goal = Block(level.goal[0], level.goal[1], STAND)
        self.targets: List[Block] = [goal] + [
            Block(sw.pos[0], sw.pos[1], STAND)
            for sw in level.switches.values() if sw.type == "split"]
        self.triggers = self._trigger_blocks()
        self.open_dist = self._distances({t: 0 for t in self.targets}, None)
        self._tables: Dict[int, Dict[Block, int]] = {}
        self._cube_tables: Dict[Cell, Dict[Cell, int]] = {}
        self._merge_options: Optional[List[Tuple[Cell, Cell, int]]] = None
        self._split_memo: Dict[Tuple[Cell, Cell], float] = {}

    def _floor(self, cell: Cell, mask: Optional[int]) -> bool:
        """Ô đứng được; mask=None nghĩa là mọi cầu đều mở."""
        if not self.board.is_floor(*cell):
            return False
        bridge_id = self.bridge_of.get(cell)
        return mask is None or bridge_id is None or bool((mask >> bridge_id) & 1)

    def _supported(self, block: Block, mask: Optional[int]) -> bool:
        if not all(self._floor(cell, mask) for cell in block.cells()):
            return False
        return not (block.orient == STAND and (block.r, block.c) in self.fragile)

    def _distances(self, sources: Dict[Block, int], mask: Optional[int]) -> Dict[Block, int]:
        """Dijkstra nhiều nguồn (cạnh trọng số 1, có độ lệch ban đầu) trên đồ thị khối."""
        heap, counter = [], 0
        for block, offset in sources.items():
            if self._supported(block, mask):
                heap.append((offset, counter, block))
                counter += 1
        heapq.heapify(heap)
        dist: Dict[Block, int] = {}
        while heap:
            d, _, block = heapq.heappop(heap)
            if block in dist:
                continue
            dist[block] = d
            for direction in _DIRECTIONS:
                nxt = block.roll(direction)
                if nxt not in dist and self._supported(nxt, mask):
                    heapq.heappush(heap, (d + 1, counter, nxt))
                    counter += 1
        return dist

    def _trigger_blocks(self) -> set:
        """Vị trí khối có thể làm đổi bitmask cầu (công tắc mềm/nặng có targets)."""
        found = set()
        for sw in self.level.switches.values():
            if sw.type == "split" or not sw.targets:
                continue
            r, c = sw.pos
            found.add(Block(r, c, STAND))
            if sw.type == "soft":
                found.update((Block(r, c, HORIZ), Block(r, c - 1, HORIZ),
                              Block(r, c, VERT), Block(r - 1, c, VERT)))
        return found

    def table(self, mask: int) -> Dict[Block, int]:
        """Bảng số lần lăn cho bitmask `mask` (hai trường hợp (i), (ii) gộp một lần Dijkstra)."""
        cached = self._tables.get(mask)
        if cached is None:
            sources = {t: 0 for t in self.targets}
            for p in self.triggers:
                base = self.open_dist.get(p)
                if base is not None and base < sources.get(p, base + 1):
                    sources[p] = base
            cached = self._distances(sources, mask)
            self._tables[mask] = cached
        return cached

    def cube_from(self, cell: Cell) -> Dict[Cell, int]:
        """BFS 4 hướng của một cube đơn từ `cell` (cầu coi như sàn)."""
        cached = self._cube_tables.get(cell)
        if cached is None:
            cached = {cell: 0}
            queue = deque([cell])
            while queue:
                r, c = queue.popleft()
                for dr, dc in _NEIGHBORS:
                    nxt = (r + dr, c + dc)
                    if nxt not in cached and self.board.is_floor(*nxt):
                        cached[nxt] = cached[(r, c)] + 1
                        queue.append(nxt)
            self._cube_tables[cell] = cached
        return cached

    def merge_options(self) -> List[Tuple[Cell, Cell, int]]:
        """Mọi cặp ô kề (a, b) kèm cận d_mở(khối ghép, T); bỏ cặp không thể tới T."""
        if self._merge_options is None:
            options = []
            for r in range(self.level.rows):
                for c in range(self.level.cols):
                    for dr, dc, orient in ((0, 1, HORIZ), (1, 0, VERT)):
                        a, b = (r, c), (r + dr, c + dc)
                        steps = self.open_dist.get(Block(r, c, orient))
                        if steps is not None and self.board.is_floor(*a) \
                                and self.board.is_floor(*b):
                            options.append((a, b, steps))
            self._merge_options = options
        return self._merge_options

    def split_steps(self, c1: Cell, c2: Cell) -> float:
        """Cận số bước từ trạng thái tách (c1, c2) tới khi thắng."""
        key = (c1, c2) if c1 <= c2 else (c2, c1)
        cached = self._split_memo.get(key)
        if cached is None:
            d1, d2 = self.cube_from(c1), self.cube_from(c2)
            cached = math.inf
            for a, b, steps in self.merge_options():
                for x, y in ((a, b), (b, a)):
                    if x in d1 and y in d2:
                        cached = min(cached, d1[x] + d2[y] + steps)
            self._split_memo[key] = cached
        return cached


_MODELS: Dict[int, Tuple[object, _LevelModel]] = {}


def _model(level) -> _LevelModel:
    entry = _MODELS.get(id(level))
    if entry is None or entry[0] is not level:
        entry = (level, _LevelModel(level))
        _MODELS[id(level)] = entry
    return entry[1]


def clear_caches() -> None:
    """Xóa dữ liệu tính trước (dùng trong test hoặc khi nạp lại màn)."""
    _MODELS.clear()


def _cost(steps: Optional[float]) -> float:
    return math.inf if steps is None else steps * COST_MIN


def h_switch_aware(game, state: State) -> float:
    """Khối chưa tách: cận số lần lăn theo bitmask cầu hiện tại; 0 nếu đang tách."""
    if state.split is not None:
        return 0.0
    block = Block(state.r, state.c, state.orient)
    return _cost(_model(game.level).table(state.bridges).get(block))


def h_split_cubes(game, state: State) -> float:
    """Trạng thái đang tách: cận ghép cube rồi tới đích; chưa tách: h_switch_aware."""
    if state.split is None:
        return h_switch_aware(game, state)
    return _cost(_model(game.level).split_steps(*state.split))


def h_advanced(game, state: State) -> float:
    """Heuristic tổng hợp dùng được trên mọi nhóm màn."""
    if state.split is not None:
        return h_split_cubes(game, state)
    return h_switch_aware(game, state)


HEURISTICS: Dict[str, Heuristic] = {
    "zero": h_zero,
    "manhattan": h_manhattan,
    "manhattan_orient": h_manhattan_orient,
    "relaxed_maze": h_relaxed_maze,
    "switch_aware": h_switch_aware,
    "split_cubes": h_split_cubes,
    "advanced": h_advanced,
}


def get_heuristic(heuristic: Union[str, Heuristic]) -> Heuristic:
    """Nhận tên trong HEURISTICS hoặc chính hàm heuristic; trả về hàm."""
    if callable(heuristic):
        return heuristic
    try:
        return HEURISTICS[heuristic]
    except KeyError:
        raise KeyError(f"Heuristic '{heuristic}' không tồn tại; có: {sorted(HEURISTICS)}") from None
