"""Chạy mọi solver trên mọi màn trong levels/, ghi CSV vào experiments/results/ (task F3).

Chạy từ THƯ MỤC GỐC của dự án (không chạy `python experiments/run_all.py`):

    python -m experiments.run_all                          # chạy đầy đủ, cả hai chế độ chi phí
    python -m experiments.run_all --levels g1 --repeats 1  # chạy thử nhanh
    python -m experiments.run_all --astar-heuristics all   # thêm A* với từng heuristic

Hai chế độ chi phí (cột `cost_mode`):
- unit:     mọi bước chi phí 1 -> UCS trùng BFS, A* chỉ khác ở số nút mở rộng.
- weighted: hàm chi phí không đều của F1 (`make_cost_fn`) -> UCS/A* khác BFS/DFS.
BFS và DFS không dùng chi phí để tìm đường nhưng cột `cost` vẫn là chi phí thật của
đường họ tìm được, nên so sánh được với UCS/A*.

Mỗi dòng CSV là một cặp (màn, chế độ, solver). Cột và quy ước ô trống: xem
`experiments/common.py`.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from game.level_loader import load_level
from solvers import astar, bfs, dfs, ucs
from solvers.base import Limits
from solvers.heuristics_advanced import HEURISTICS

from .common import (CUT_NOTES, FIELDNAMES, MODES, RESULT_DIR, TOL, Row, SolveFn,
                     add_common_arguments, configure_output, describe_row, limits_from_args,
                     run_one, select_levels_from_args, to_number, with_fresh_cache, write_csv)

log = logging.getLogger("experiments")


def build_solvers(extra_heuristics: Sequence[str] = ()) -> Dict[str, SolveFn]:
    """Bảng solver: tên cột `solver` -> hàm solve(game, limits).

    `astar` dùng heuristic mặc định của nhóm (h_advanced). `extra_heuristics` thêm các dòng
    `astar_<tên>`. A* luôn được bọc `with_fresh_cache` để thời gian/bộ nhớ gồm cả chi phí
    dựng bảng heuristic ở MỌI lần lặp (đo công bằng).
    """
    solvers: Dict[str, SolveFn] = {
        "bfs": bfs.solve,
        "dfs": dfs.solve,
        "ucs": ucs.solve,
        "astar": with_fresh_cache(astar.solve),
    }
    for name in extra_heuristics:
        solvers[f"astar_{name}"] = with_fresh_cache(astar.solver_for(name))
    return solvers


def run_experiments(level_paths: Sequence[Path], solvers: Dict[str, SolveFn],
                    modes: Sequence[str], limits: Limits, repeats: int) -> List[Row]:
    """Vòng lặp chính: màn -> chế độ chi phí -> solver. Trả về mọi dòng kết quả."""
    rows: List[Row] = []
    total = len(level_paths) * len(modes) * len(solvers)
    for path in level_paths:
        level = load_level(str(path))
        for mode in modes:
            for name, solve_fn in solvers.items():
                row = run_one(path, level, mode, name, solve_fn, limits, repeats)
                rows.append(row)
                log.info("[%d/%d] %s | %s | %s: %s", len(rows), total, path.stem, mode, name,
                         describe_row(row))
    return rows


def _is_optimal_solver(name: str) -> bool:
    """UCS và mọi biến thể A* (heuristic admissible) phải cho chi phí tối ưu."""
    return name == "ucs" or name.startswith("astar")


def _complete(row: Row) -> bool:
    """Solver chạy hết (không bị cắt, không lỗi) nên kết luận của nó đáng tin."""
    note = str(row["note"])
    return note not in CUT_NOTES and not note.startswith("error")


def sanity_check(rows: Sequence[Row], tol: float = TOL) -> List[str]:
    """Đối chiếu chéo các solver; trả về danh sách vấn đề (rỗng = đạt).

    1. Không có lời giải sai (`invalid_path`) hay solver lỗi.
    2. Các solver chạy hết phải thống nhất màn có giải được hay không.
    3. BFS cho lời giải ít bước nhất.
    4. UCS và A* cùng chi phí tối ưu; BFS/DFS không được rẻ hơn UCS
       (ở chế độ unit, BFS phải bằng UCS vì chi phí = số bước).
    """
    problems: List[str] = []
    table: Dict[tuple, Dict[str, Row]] = {}
    for row in rows:
        tag = f"{row['level']}/{row['cost_mode']}/{row['solver']}"
        note = str(row["note"])
        if "invalid_path" in note:
            problems.append(f"{tag}: lời giải không hợp lệ (invalid_path)")
        if note.startswith("error"):
            problems.append(f"{tag}: solver báo lỗi ({note})")
        table.setdefault((row["level"], row["cost_mode"]), {})[row["solver"]] = row

    for (level, mode), by_solver in table.items():
        tag = f"{level}/{mode}"
        complete = {name: row for name, row in by_solver.items() if _complete(row)}
        if len({bool(row["solved"]) for row in complete.values()}) > 1:
            problems.append(f"{tag}: các solver bất đồng về việc màn có giải được hay không")
        solved = {name: row for name, row in complete.items() if row["solved"]}

        bfs_row = solved.get("bfs")
        if bfs_row is not None:
            shortest = to_number(bfs_row["length"])
            for name, row in solved.items():
                length = to_number(row["length"])
                if shortest is not None and length is not None and length < shortest - tol:
                    problems.append(f"{tag}: {name} có length {row['length']} ngắn hơn "
                                    f"BFS {bfs_row['length']} (BFS phải ngắn nhất)")

        ref = solved.get("ucs")
        if ref is None:
            continue
        ref_cost = to_number(ref["cost"])
        for name, row in solved.items():
            cost = to_number(row["cost"])
            if cost is None or ref_cost is None:
                continue
            exact = _is_optimal_solver(name) or (name == "bfs" and mode == "unit")
            if exact and abs(cost - ref_cost) > tol:
                problems.append(f"{tag}: {name} cost={cost:g} khác UCS cost={ref_cost:g}")
            elif not exact and cost < ref_cost - tol:
                problems.append(f"{tag}: {name} cost={cost:g} rẻ hơn UCS cost={ref_cost:g} "
                                "(UCS không tối ưu?)")
    return problems


def _resolve_heuristics(parser: argparse.ArgumentParser, names: Sequence[str]) -> List[str]:
    """'all' -> mọi heuristic; tên lạ -> báo lỗi dòng lệnh."""
    if "all" in names:
        return list(HEURISTICS)
    unknown = [name for name in names if name not in HEURISTICS]
    if unknown:
        parser.error(f"heuristic không tồn tại: {unknown}; có: {sorted(HEURISTICS)} hoặc 'all'")
    return list(names)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Điểm vào dòng lệnh. Trả 0 nếu đạt; 1 nếu bước tự kiểm tra phát hiện vấn đề."""
    parser = argparse.ArgumentParser(
        prog="python -m experiments.run_all",
        description="Chạy mọi solver trên bộ màn chơi và ghi kết quả ra CSV.")
    add_common_arguments(parser)
    parser.add_argument("--out", type=Path, default=RESULT_DIR / "results.csv",
                        help="file CSV kết quả (mặc định experiments/results/results.csv)")
    parser.add_argument("--astar-heuristics", nargs="*", default=[], metavar="NAME",
                        help="thêm các dòng astar_<NAME>; 'all' = mọi heuristic")
    args = parser.parse_args(argv)
    configure_output(args.quiet)

    heuristics = _resolve_heuristics(parser, args.astar_heuristics)
    level_paths = select_levels_from_args(parser, args)
    rows = run_experiments(level_paths, build_solvers(heuristics), args.modes,
                           limits_from_args(args), args.repeats)
    write_csv(rows, args.out, FIELDNAMES)
    if not args.quiet:
        print(f"Đã ghi {len(rows)} dòng vào {args.out}")

    if args.no_check:
        return 0
    problems = sanity_check(rows)
    for problem in problems:
        print(f"CẢNH BÁO: {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} vấn đề cần xem lại trước khi dùng số liệu.", file=sys.stderr)
        return 1
    if not args.quiet:
        print("Tự kiểm tra chéo: ĐẠT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
