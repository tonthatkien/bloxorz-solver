"""Bộ mô phỏng luật ĐỘC LẬP làm "thước đo" cho test heuristic (task E2).

KHÔNG phải `game.game.Game`: file này dựng lại luật Bloxorz đầy đủ theo đề (ô dễ vỡ, cầu,
công tắc mềm/nặng/split, toggle/permanent, tách/ghép cube, hành động S) chỉ để test, vì Game
thật chưa có phần C3. Nhờ đó mới kiểm được heuristic trên màn có công tắc và split ngay bây giờ.
Khi C3 merge: chạy lại test bằng Game thật (xem TestRealGameAdvancedLevels) rồi cân nhắc xóa file.

Quy ước luật dùng ở đây (nếu C2/C3 khác thì báo, heuristic chỉ dựa vào các nới lỏng nhẹ hơn):
- Lăn: các ô khối chiếm phải là sàn (cầu đóng = trống); không được ĐỨNG trên ô dễ vỡ.
- Sau khi tới ô mới, kích hoạt công tắc ở các ô khối chiếm (mềm: bất kỳ phần nào; nặng và
  split: chỉ khi khối đứng), áp dụng toggle/permanent, rồi kiểm tra lại chỗ đứng với cầu mới.
- Đứng trên công tắc split: chuyển thành hai cube ở `cubes`, cube đầu tiên được điều khiển.
- Cube đơn: đi 1 ô (không được đè lên cube kia), chỉ kích hoạt công tắc mềm; hai cube kề nhau
  thì ghép lại ngay.
"""
import heapq
import math
import random
from collections import deque
from typing import Dict, List

from game.block import Block
from game.board import Board
from game.level_loader import Bridge, Level, Switch
from game.state import HORIZ, STAND, VERT, State
from solvers.heuristics import make_cost_fn

DELTA = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


class ReferenceGame:
    """Cùng giao diện initial_state / is_goal / get_successors như Game."""

    def __init__(self, level: Level, weighted: bool = False) -> None:
        self.level = level
        self.board = Board.from_strings(level.grid)
        self.bridge_of = {b.pos: b.id for b in level.bridges.values()}
        self.cost_fn = make_cost_fn(level) if weighted else None

    def initial_state(self) -> State:
        r, c = self.level.start
        return State(r, c, STAND, self.level.initial_bridge_mask(), None)

    def is_goal(self, s: State) -> bool:
        return s.split is None and s.orient == STAND and (s.r, s.c) == tuple(self.level.goal)

    def _floor(self, cell, mask: int) -> bool:
        if not self.board.is_floor(*cell):
            return False
        bridge_id = self.bridge_of.get(cell)
        return bridge_id is None or bool((mask >> bridge_id) & 1)

    def _effects(self, cells, full_standing: bool, mask: int):
        """Trả về (bitmask mới, công tắc split bị kích hoạt hoặc None)."""
        split = None
        for cell in cells:
            sw = self.level.switches.get(cell)
            if sw is None:
                continue
            if sw.type == "soft" or (sw.type == "heavy" and full_standing):
                for target in sw.targets:
                    if sw.mode == "toggle":
                        mask ^= 1 << target
                    elif sw.set == "open":
                        mask |= 1 << target
                    else:
                        mask &= ~(1 << target)
            elif sw.type == "split" and full_standing:
                split = sw
        return mask, split

    def _block_moves(self, s: State):
        mask, block = s.bridges, Block(s.r, s.c, s.orient)
        for d in "UDLR":
            nb = block.roll(d)
            cells = nb.cells()
            if not all(self._floor(c, mask) for c in cells):
                continue
            if nb.orient == STAND and (nb.r, nb.c) in self.level.fragile:
                continue
            new_mask, split = self._effects(cells, nb.orient == STAND, mask)
            if not all(self._floor(c, new_mask) for c in cells):
                continue
            if split is not None:
                cubes = (tuple(split.cubes[0]), tuple(split.cubes[1]))
                yield d, State(0, 0, STAND, new_mask, cubes)
            else:
                yield d, State(nb.r, nb.c, nb.orient, new_mask, None)

    def _cube_moves(self, s: State):
        mask = s.bridges
        active, other = s.split
        for d, (dr, dc) in DELTA.items():
            cell = (active[0] + dr, active[1] + dc)
            if cell == other or not self._floor(cell, mask):
                continue
            new_mask, _ = self._effects([cell], False, mask)
            if not (self._floor(cell, new_mask) and self._floor(other, new_mask)):
                continue
            if abs(cell[0] - other[0]) + abs(cell[1] - other[1]) == 1:
                a, b = sorted([cell, other])
                yield d, State(a[0], a[1], HORIZ if a[0] == b[0] else VERT, new_mask, None)
            else:
                yield d, State(0, 0, STAND, new_mask, (cell, other))
        yield "S", State(0, 0, STAND, mask, (other, active))

    def get_successors(self, s: State):
        moves = self._block_moves(s) if s.split is None else self._cube_moves(s)
        return [(a, ns, self.step_cost(s, a, ns)) for a, ns in moves]

    def step_cost(self, old: State, action: str, new: State) -> float:
        return 1.0 if self.cost_fn is None else self.cost_fn(old, action, new)


def explore(game) -> Dict[State, list]:
    """Mọi state tới được từ trạng thái đầu, kèm danh sách successor."""
    start = game.initial_state()
    edges = {start: game.get_successors(start)}
    queue = deque([start])
    while queue:
        for _a, nxt, _c in edges[queue.popleft()]:
            if nxt not in edges:
                edges[nxt] = game.get_successors(nxt)
                queue.append(nxt)
    return edges


def true_costs(game, edges: Dict[State, list]) -> Dict[State, float]:
    """h*(s): chi phí tối ưu thật tới đích (math.inf nếu không tới được), Dijkstra ngược."""
    reverse: Dict[State, list] = {s: [] for s in edges}
    for s, successors in edges.items():
        for _a, nxt, cost in successors:
            reverse[nxt].append((s, cost))
    dist = {s: math.inf for s in edges}
    heap, tie = [], 0
    for s in edges:
        if game.is_goal(s):
            dist[s] = 0.0
            heap.append((0.0, tie, s))
            tie += 1
    heapq.heapify(heap)
    while heap:
        d, _, s = heapq.heappop(heap)
        if d > dist[s]:
            continue
        for prev, cost in reverse[s]:
            if d + cost < dist[prev]:
                dist[prev] = d + cost
                heapq.heappush(heap, (d + cost, tie, prev))
                tie += 1
    return dist


def find_violations(game, heuristic, edges=None, star=None) -> List[str]:
    """Kiểm tra brute-force: admissible, consistent và không trả inf sai. Rỗng = đạt."""
    edges = edges if edges is not None else explore(game)
    star = star if star is not None else true_costs(game, edges)
    problems = []
    for s, successors in edges.items():
        h = heuristic(game, s)
        if h > star[s] + 1e-9:
            problems.append(f"không admissible: h={h} > h*={star[s]} tại {s}")
        for _a, nxt, cost in successors:
            h_next = heuristic(game, nxt)
            if h > cost + h_next + 1e-9:
                problems.append(f"không consistent: h={h} > {cost}+{h_next}, {s} -> {nxt}")
    return problems


def random_level(rng: random.Random, rows: int = 4, cols: int = 5) -> Level:
    """Màn ngẫu nhiên nhỏ: ô đặc biệt không chồng nhau, có thể có cầu/công tắc/split."""
    while True:
        floor = {(r, c) for r in range(rows) for c in range(cols) if rng.random() < 0.8}
        if len(floor) < 8:
            continue
        goal, start = rng.sample(sorted(floor), 2)
        rest = sorted(floor - {goal, start})
        rng.shuffle(rest)

        def take(n: int) -> list:
            return [rest.pop() for _ in range(min(n, len(rest)))]

        fragile = set(take(rng.randint(0, 2)))
        bridges = {i: Bridge(i, p, rng.random() < 0.4)
                   for i, p in enumerate(take(rng.randint(0, 3)))}
        switches = {}
        for pos in take(rng.randint(0, 3)):
            if not bridges:
                break
            mode = rng.choice(["toggle", "permanent"])
            switches[pos] = Switch(
                rng.choice(["soft", "heavy"]), pos,
                rng.sample(sorted(bridges), rng.randint(1, len(bridges))), mode,
                rng.choice(["open", "close"]) if mode == "permanent" else None)
        if rng.random() < 0.5:
            spots = take(3)
            if len(spots) == 3:
                switches[spots[0]] = Switch("split", spots[0], [], "toggle", None,
                                            [spots[1], spots[2]])
        grid = ["".join("G" if (r, c) == goal else "#" if (r, c) in floor else "."
                        for c in range(cols)) for r in range(rows)]
        return Level("random", grid, start, goal, fragile, bridges, switches)
