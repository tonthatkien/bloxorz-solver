"""SearchResult + công cụ đo đạc dùng chung cho mọi solver.

Chữ ký chung:  solve(game, limits=None) -> SearchResult

Cách đếm (thống nhất để so sánh công bằng):
- expanded_nodes: số nút được LẤY RA khỏi frontier và sinh successor.
- Thời gian: time.perf_counter(), chạy KHÔNG bật tracemalloc.
- Bộ nhớ đỉnh: chạy lần riêng với tracemalloc, lấy peak.
"""
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class Limits:
    max_nodes: int = 2_000_000
    timeout_sec: float = 60.0


@dataclass
class SearchResult:
    solved: bool = False
    path: List[str] = field(default_factory=list)   # ví dụ ["R","R","D","S"]
    expanded_nodes: int = 0
    time_sec: float = 0.0
    peak_memory_kb: float = 0.0
    length: int = 0
    cost: float = 0.0
    note: str = ""        # "timeout" / "node_limit" nếu bị cắt


class LimitReached(Exception):
    """Solver ném ra khi vượt Limits; run_measured sẽ bắt và ghi note."""


class LimitChecker:
    """Dùng trong vòng lặp của solver:  checker.tick(expanded)  mỗi lần mở rộng 1 nút."""
    def __init__(self, limits: Optional[Limits]):
        self.limits = limits or Limits()
        self.t0 = time.perf_counter()

    def tick(self, expanded: int) -> None:
        if expanded > self.limits.max_nodes:
            raise LimitReached("node_limit")
        if (expanded & 0x3FF) == 0 and time.perf_counter() - self.t0 > self.limits.timeout_sec:
            raise LimitReached("timeout")


def reconstruct_path(parent: dict, state) -> List[str]:
    """parent: state -> (prev_state, action) (gốc ánh xạ tới None). Truy vết về gốc."""
    path = []
    while parent.get(state) is not None:
        state, action = parent[state]
        path.append(action)
    path.reverse()
    return path


def run_measured(solve_fn: Callable, game, limits: Optional[Limits] = None,
                 repeats: int = 3) -> SearchResult:
    """Chạy solver, đo time (trung bình `repeats` lần) và peak memory (1 lần riêng)."""
    def _run():
        try:
            return solve_fn(game, limits)
        except LimitReached as e:
            return SearchResult(solved=False, note=str(e))

    times, res = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        res = _run()
        times.append(time.perf_counter() - t0)
        if res.note:        # bị cắt thì khỏi lặp lại
            break
    res.time_sec = sum(times) / len(times)

    tracemalloc.start()
    _run()
    res.peak_memory_kb = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    res.length = len(res.path)
    return res
