"""Tiện ích đo đạc và kiểm chứng kết quả solver (task E1).

Module này đứng CẠNH `solvers/base.py` và dùng lại `SearchResult`, `Limits`,
`run_measured` ở đó. Việc đo time / peak memory / expanded / length do
`base.run_measured` thực hiện; module này bổ sung:

- measure():        gọi run_measured và điền thêm `cost` bằng cách đi lại lời giải.
- verify_path():    kiểm tra lời giải có hợp lệ không (đi theo path bằng get_successors).
- result_to_row():  đổi SearchResult thành dict để ghi CSV (experiments/run_all.py).
- format_result():  chuỗi gọn để hiển thị (GUI, log, báo cáo).

Quy ước đếm `expanded_nodes` (theo docs/CODING_STANDARDS.md, mục 4): mỗi lần LẤY MỘT NÚT
RA KHỎI frontier thì tăng expanded đúng một lần và gọi `checker.tick(expanded)`.
"""
from typing import Callable, Dict, List, Optional, Tuple

from .base import Limits, SearchResult, run_measured


def verify_path(game, path: List[str]) -> Tuple[bool, float]:
    """Đi lại `path` từ trạng thái đầu bằng get_successors.

    Trả về (hợp_lệ, tổng_chi_phí). Hợp lệ = mọi bước đều có trong successors
    VÀ trạng thái cuối là đích. Chỉ dùng 3 hàm của Game theo hợp đồng.
    """
    state = game.initial_state()
    total = 0.0
    for action in path:
        step = next(((s, c) for a, s, c in game.get_successors(state) if a == action), None)
        if step is None:
            return False, total
        state, cost = step
        total += cost
    return game.is_goal(state), total


def measure(solve_fn: Callable, game, limits: Optional[Limits] = None,
            repeats: int = 3) -> SearchResult:
    """Chạy solver qua `run_measured` rồi điền `cost` nếu lời giải hợp lệ."""
    res = run_measured(solve_fn, game, limits, repeats)
    if res.solved:
        valid, cost = verify_path(game, res.path)
        res.cost = cost
        if not valid:
            res.note = (res.note + " invalid_path").strip()
    return res


def result_to_row(level: str, solver: str, res: SearchResult) -> Dict[str, object]:
    """Một dòng CSV, cột đúng gợi ý trong experiments/run_all.py."""
    return {
        "level": level,
        "solver": solver,
        "solved": res.solved,
        "length": res.length,
        "cost": res.cost,
        "expanded_nodes": res.expanded_nodes,
        "time_sec": round(res.time_sec, 6),
        "peak_memory_kb": round(res.peak_memory_kb, 1),
        "note": res.note,
    }


def format_result(res: SearchResult) -> str:
    """Chuỗi hiển thị gọn một kết quả."""
    if not res.solved:
        return (f"Không tìm được lời giải ({res.note or 'hết không gian tìm kiếm'}); "
                f"expanded={res.expanded_nodes}")
    return (f"length={res.length} | cost={res.cost:g} | expanded={res.expanded_nodes} | "
            f"time={res.time_sec * 1000:.2f} ms | peak_mem={res.peak_memory_kb:.1f} KB")