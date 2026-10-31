"""So sánh các heuristic của A* với nhau (phần thực nghiệm riêng cho heuristic).

Chạy từ THƯ MỤC GỐC của dự án:

    python -m experiments.benchmark_heuristics
    python -m experiments.benchmark_heuristics --levels g1 g2 --repeats 1
    python -m experiments.benchmark_heuristics --heuristics manhattan_orient advanced

Cùng một solver (A*), cùng màn, cùng giới hạn; chỉ đổi heuristic. Heuristic `zero`
(A* == UCS) LUÔN được chạy làm mốc so sánh. Hai file kết quả:

1. heuristics.csv         mỗi dòng = (màn, chế độ chi phí, heuristic), gồm các cột đo của
                          run_all và các cột suy ra bên dưới.
2. heuristics_summary.csv tổng hợp theo (chế độ, nhóm màn, heuristic).

Cột suy ra (so với mốc `zero` trên cùng màn và chế độ):
- h_start        h(trạng thái đầu); trống nếu vô hạn hoặc heuristic lỗi.
- optimal_cost   chi phí tối ưu thật (chi phí của lời giải UCS/zero).
- tightness      h_start / optimal_cost, trong [0, 1]: càng gần 1 heuristic càng "sát".
                 Vượt 1 nghĩa là heuristic KHÔNG admissible.
- node_ratio     số nút mở rộng / số nút của zero: càng nhỏ càng hiệu quả.
- time_ratio     thời gian / thời gian của zero (đã gồm chi phí dựng bảng heuristic).
- optimal        chi phí tìm được có bằng optimal_cost không (False = nghi không admissible).
"""
import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from game.level_loader import load_level
from solvers import astar
from solvers.base import Limits
from solvers.heuristics_advanced import HEURISTICS, get_heuristic

from .common import (CUT_NOTES, FIELDNAMES, MODES, RESULT_DIR, TOL, Row, add_common_arguments,
                     build_game, configure_output, describe_row, limits_from_args,
                     reset_heuristic_caches, run_one, select_levels_from_args, to_number,
                     with_fresh_cache, write_csv)

log = logging.getLogger("experiments")

BASELINE = "zero"
HEURISTIC_FIELDNAMES = [name if name != "solver" else "heuristic" for name in FIELDNAMES] + [
    "h_start", "optimal_cost", "tightness", "node_ratio", "time_ratio", "optimal",
]
SUMMARY_FIELDNAMES = [
    "cost_mode", "group", "heuristic", "levels", "geo_node_ratio", "geo_time_ratio",
    "mean_tightness", "node_wins", "non_optimal",
]


def ordered_heuristics(names: Sequence[str]) -> List[str]:
    """Luôn có mốc `zero` ở đầu; còn lại theo thứ tự khai báo trong HEURISTICS."""
    chosen = set(names) | {BASELINE}
    return [name for name in HEURISTICS if name in chosen]


def initial_h(game, name: str) -> object:
    """h(trạng thái đầu), tính ngoài vùng đo. Trống nếu vô hạn hoặc heuristic lỗi."""
    reset_heuristic_caches()
    try:
        value = float(get_heuristic(name)(game, game.initial_state()))
    except Exception:  # noqa: BLE001 - lỗi sẽ hiện ở dòng đo của chính heuristic này
        return ""
    return round(value, 4) if math.isfinite(value) else ""


def run_benchmark(level_paths: Sequence[Path], heuristics: Sequence[str], modes: Sequence[str],
                  limits: Limits, repeats: int) -> List[Row]:
    """Chạy A* với từng heuristic trên từng (màn, chế độ) rồi tính các cột suy ra."""
    names = ordered_heuristics(heuristics)
    rows: List[Row] = []
    total = len(level_paths) * len(modes) * len(names)
    for path in level_paths:
        level = load_level(str(path))
        for mode in modes:
            game = build_game(level, mode == "weighted")
            for name in names:
                solve_fn = with_fresh_cache(astar.solver_for(name))
                row = run_one(path, level, mode, name, solve_fn, limits, repeats)
                row["heuristic"] = row.pop("solver")
                row["h_start"] = initial_h(game, name)
                rows.append(row)
                log.info("[%d/%d] %s | %s | %s: %s", len(rows), total, path.stem, mode, name,
                         describe_row(row))
    add_derived(rows)
    return rows


def add_derived(rows: Sequence[Row]) -> None:
    """Thêm optimal_cost, tightness, node_ratio, time_ratio, optimal (so với mốc zero)."""
    baseline = {(row["level"], row["cost_mode"]): row
                for row in rows if row["heuristic"] == BASELINE}
    for row in rows:
        row.update(optimal_cost="", tightness="", node_ratio="", time_ratio="", optimal="")
        ref = baseline.get((row["level"], row["cost_mode"]))
        if ref is None or not ref["solved"]:
            continue
        optimal_cost = to_number(ref["cost"])
        row["optimal_cost"] = optimal_cost
        h_start = to_number(row["h_start"])
        if h_start is not None and optimal_cost and optimal_cost > 0:
            row["tightness"] = round(h_start / optimal_cost, 4)
        if not row["solved"]:
            continue
        row["optimal"] = abs(to_number(row["cost"]) - optimal_cost) <= TOL
        nodes, ref_nodes = to_number(row["expanded_nodes"]), to_number(ref["expanded_nodes"])
        if nodes is not None and ref_nodes:
            row["node_ratio"] = round(nodes / ref_nodes, 4)
        seconds, ref_seconds = to_number(row["time_sec"]), to_number(ref["time_sec"])
        if seconds is not None and ref_seconds:
            row["time_ratio"] = round(seconds / ref_seconds, 4)


def check_benchmark(rows: Sequence[Row]) -> List[str]:
    """Vấn đề cần xem lại (rỗng = đạt): heuristic không admissible, lỗi, mất lời giải."""
    problems: List[str] = []
    baseline = {(row["level"], row["cost_mode"]): row
                for row in rows if row["heuristic"] == BASELINE}
    for row in rows:
        tag = f"{row['level']}/{row['cost_mode']}/{row['heuristic']}"
        note = str(row["note"])
        if note.startswith("error"):
            problems.append(f"{tag}: lỗi ({note})")
        if "invalid_path" in note:
            problems.append(f"{tag}: lời giải không hợp lệ (invalid_path)")
        if row["optimal"] is False:
            problems.append(f"{tag}: cost={row['cost']} khác chi phí tối ưu {row['optimal_cost']} "
                            "(heuristic có thể không admissible)")
        tightness = to_number(row["tightness"])
        if tightness is not None and tightness > 1 + TOL:
            problems.append(f"{tag}: h_start vượt chi phí tối ưu (tightness={tightness}), "
                            "heuristic không admissible")
        ref = baseline.get((row["level"], row["cost_mode"]))
        cut_or_error = note in CUT_NOTES or note.startswith("error")
        if ref is not None and ref["solved"] and not row["solved"] and not cut_or_error:
            problems.append(f"{tag}: kết luận không giải được trong khi zero giải được")
    return problems


def _geo_mean(values: Sequence[Optional[float]]) -> object:
    positives = [v for v in values if v is not None and v > 0]
    if not positives:
        return ""
    return round(math.exp(sum(math.log(v) for v in positives) / len(positives)), 4)


def _mean(values: Sequence[Optional[float]]) -> object:
    numbers = [v for v in values if v is not None]
    return round(sum(numbers) / len(numbers), 4) if numbers else ""


def _rank(name: str) -> int:
    order = list(HEURISTICS)
    return order.index(name) if name in order else len(order)


def summarize(rows: Sequence[Row]) -> List[Row]:
    """Tổng hợp theo (chế độ, nhóm màn, heuristic); nhóm 'all' gộp mọi màn.

    - geo_node_ratio / geo_time_ratio: trung bình nhân của tỉ lệ so với zero (<1 là tốt hơn).
    - node_wins: số màn mà heuristic có số nút mở rộng nhỏ nhất (hòa thì tính cho tất cả).
    - non_optimal: số màn heuristic cho chi phí khác tối ưu (mong đợi 0).
    """
    fewest: Dict[tuple, float] = {}
    for row in rows:
        nodes = to_number(row["expanded_nodes"])
        if row["solved"] and nodes is not None:
            key = (row["cost_mode"], row["level"])
            fewest[key] = min(nodes, fewest.get(key, nodes))

    buckets: Dict[tuple, List[Row]] = {}
    for row in rows:
        for group in (row["group"], "all"):
            buckets.setdefault((row["cost_mode"], group, row["heuristic"]), []).append(row)

    summary: List[Row] = []
    for (mode, group, name), items in buckets.items():
        wins = sum(1 for r in items
                   if r["solved"] and to_number(r["expanded_nodes"]) is not None
                   and to_number(r["expanded_nodes"]) == fewest.get((mode, r["level"])))
        summary.append({
            "cost_mode": mode, "group": group, "heuristic": name,
            "levels": sum(1 for r in items if r["solved"]),
            "geo_node_ratio": _geo_mean([to_number(r["node_ratio"]) for r in items]),
            "geo_time_ratio": _geo_mean([to_number(r["time_ratio"]) for r in items]),
            "mean_tightness": _mean([to_number(r["tightness"]) for r in items]),
            "node_wins": wins,
            "non_optimal": sum(1 for r in items if r["optimal"] is False),
        })
    summary.sort(key=lambda r: (MODES.index(r["cost_mode"]), 0 if r["group"] == "all" else 1,
                                r["group"], _rank(r["heuristic"])))
    return summary


def _fmt(value: object) -> str:
    return "-" if value == "" else f"{float(value):.3f}"


def format_summary(summary: Sequence[Row], group: str = "all") -> str:
    """Bảng chữ gọn của một nhóm màn (mặc định gộp tất cả) cho từng chế độ chi phí."""
    lines: List[str] = []
    for mode in MODES:
        subset = [r for r in summary if r["cost_mode"] == mode and r["group"] == group]
        if not subset:
            continue
        lines.append(f"== chi phí: {mode} | nhóm màn: {group} (so với zero; ratio < 1 là tốt hơn) ==")
        lines.append(f"{'heuristic':<18}{'levels':>7}{'nodes/zero':>12}{'time/zero':>11}"
                     f"{'tightness':>11}{'wins':>6}{'non-opt':>9}")
        for r in subset:
            lines.append(f"{r['heuristic']:<18}{r['levels']:>7}{_fmt(r['geo_node_ratio']):>12}"
                         f"{_fmt(r['geo_time_ratio']):>11}{_fmt(r['mean_tightness']):>11}"
                         f"{r['node_wins']:>6}{r['non_optimal']:>9}")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Điểm vào dòng lệnh. Trả 0 nếu đạt; 1 nếu phát hiện vấn đề (vd. heuristic không admissible)."""
    parser = argparse.ArgumentParser(
        prog="python -m experiments.benchmark_heuristics",
        description="So sánh các heuristic của A* (zero luôn được chạy làm mốc).")
    add_common_arguments(parser)
    parser.add_argument("--heuristics", nargs="*", default=list(HEURISTICS), metavar="NAME",
                        choices=list(HEURISTICS), help="mặc định: tất cả heuristic")
    parser.add_argument("--out", type=Path, default=RESULT_DIR / "heuristics.csv")
    parser.add_argument("--summary-out", type=Path, default=RESULT_DIR / "heuristics_summary.csv")
    parser.add_argument("--summary-group", default="all",
                        help="nhóm màn in ra console (all, g1, g2, ...)")
    args = parser.parse_args(argv)
    configure_output(args.quiet)

    level_paths = select_levels_from_args(parser, args)
    rows = run_benchmark(level_paths, args.heuristics, args.modes, limits_from_args(args),
                         args.repeats)
    summary = summarize(rows)
    write_csv(rows, args.out, HEURISTIC_FIELDNAMES)
    write_csv(summary, args.summary_out, SUMMARY_FIELDNAMES)
    if not args.quiet:
        print(format_summary(summary, args.summary_group))
        print(f"Đã ghi {len(rows)} dòng vào {args.out} và {len(summary)} dòng vào "
              f"{args.summary_out}")

    if args.no_check:
        return 0
    problems = check_benchmark(rows)
    for problem in problems:
        print(f"CẢNH BÁO: {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} vấn đề cần xem lại trước khi dùng số liệu.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
