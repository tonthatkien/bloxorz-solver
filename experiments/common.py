"""Hàm dùng chung cho các script thực nghiệm (task F3).

Nguyên tắc:
- Chỉ GỌI solver/game qua giao diện chung, không sửa `solvers/` hay `game/`.
- Mọi script dùng cùng một cách đo (`solvers.metrics.measure`), cùng `Limits`
  và cùng định dạng dòng CSV, để số liệu so sánh được với nhau.

Quy ước giá trị trong CSV (F4 và báo cáo cần biết):
- `solved=False`  -> `length` và `cost` để TRỐNG (không phải 0, tránh vẽ biểu đồ sai).
- `note` là `timeout` / `node_limit` -> `expanded_nodes` cũng để TRỐNG, vì
  `run_measured` làm mất số nút đã mở rộng khi solver bị cắt.
- `note` bắt đầu bằng `error:` -> solver ném ngoại lệ; script vẫn chạy tiếp.
"""
import argparse
import csv
import gc
import logging
import re
import sys
import tracemalloc
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from game.game import Game
from game.level_loader import Level
from solvers import heuristics as _heuristics
from solvers.base import Limits, SearchResult
from solvers.heuristics import make_cost_fn
from solvers.heuristics_advanced import clear_caches
from solvers.metrics import measure, result_to_row

ROOT = Path(__file__).resolve().parent.parent
LEVEL_DIR = ROOT / "levels"
RESULT_DIR = ROOT / "experiments" / "results"

DEFAULT_REPEATS = 3
DEFAULT_MAX_NODES = 2_000_000
DEFAULT_TIMEOUT_SEC = 60.0
TOL = 1e-6

MODES = ("unit", "weighted")
DEMO_LEVELS = frozenset({"g3_switch_demo"})
CUT_NOTES = frozenset({"timeout", "node_limit"})

FIELDNAMES = [
    "group", "level", "cost_mode", "solver", "solved", "length", "cost",
    "expanded_nodes", "time_sec", "peak_memory_kb", "note",
]

Row = Dict[str, object]
SolveFn = Callable[..., SearchResult]
log = logging.getLogger("experiments")

_GROUP_RE = re.compile(r"^(g\d+)_")


def group_of(level_name: str) -> str:
    """'g2_fragile_01' -> 'g2'; tên không theo quy ước -> 'other'."""
    match = _GROUP_RE.match(level_name)
    return match.group(1) if match else "other"


def list_levels(level_dir: Path = LEVEL_DIR, include_demo: bool = False) -> List[Path]:
    """Các file màn, xếp theo (nhóm, tên) để thứ tự chạy cố định giữa các lần."""
    paths = [p for p in Path(level_dir).glob("*.json")
             if include_demo or p.stem not in DEMO_LEVELS]
    return sorted(paths, key=lambda p: (group_of(p.stem), p.stem))


def select_levels(paths: Sequence[Path], prefixes: Sequence[str]) -> List[Path]:
    """Giữ các màn có tên bắt đầu bằng một trong `prefixes`; rỗng = giữ tất cả."""
    if not prefixes:
        return list(paths)
    return [p for p in paths if any(p.stem.startswith(prefix) for prefix in prefixes)]


def build_game(level: Level, weighted: bool) -> Game:
    """Game với chi phí 1/bước (unit) hoặc hàm chi phí không đều của F1 (weighted)."""
    return Game(level, cost_fn=make_cost_fn(level) if weighted else None)


def reset_heuristic_caches() -> None:
    """Xóa MỌI cache heuristic để mỗi lần chạy A* đều tự trả chi phí dựng bảng.

    `clear_caches()` chỉ xóa cache của heuristics_advanced; `h_relaxed_maze` có cache
    riêng (`_RelaxedMazeCache._cache`) nên xóa thêm ở đây (truy cập phòng thủ).
    """
    clear_caches()
    cache = getattr(getattr(_heuristics, "_RelaxedMazeCache", None), "_cache", None)
    if isinstance(cache, dict):
        cache.clear()


def with_fresh_cache(solve_fn: SolveFn) -> SolveFn:
    """Bọc solver: mỗi lần chạy bắt đầu với cache heuristic rỗng (đo công bằng)."""
    def wrapped(game, limits: Optional[Limits] = None) -> SearchResult:
        reset_heuristic_caches()
        return solve_fn(game, limits)
    return wrapped


def run_one(level_path: Path, level: Level, mode: str, solver_name: str,
            solve_fn: SolveFn, limits: Limits, repeats: int) -> Row:
    """Đo một cặp (màn, chế độ chi phí, solver) và trả về MỘT dòng CSV.

    Không bao giờ ném ngoại lệ do solver: lỗi được ghi vào `note` để cả đợt chạy
    không bị hỏng giữa chừng.
    """
    if mode not in MODES:
        raise ValueError(f"mode phải là một trong {MODES}, nhận {mode!r}")
    game = build_game(level, mode == "weighted")
    gc.collect()
    try:
        res = measure(solve_fn, game, limits, repeats)
    except Exception as exc: 
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        text = " ".join(f"{type(exc).__name__}: {exc}".split())
        res = SearchResult(solved=False, note=f"error: {text}"[:200])
        log.warning("%s | %s | %s: %s", level_path.stem, mode, solver_name, res.note)

    row: Row = result_to_row(level_path.stem, solver_name, res)
    row["group"] = group_of(level_path.stem)
    row["cost_mode"] = mode
    if not res.solved:
        row["length"] = ""
        row["cost"] = ""
        if res.note in CUT_NOTES:
            row["expanded_nodes"] = ""
    return row


def to_number(value: object) -> Optional[float]:
    """Số hoặc None nếu ô trống (CSV) / None."""
    if value is None or value == "":
        return None
    return float(value)


def describe_row(row: Row) -> str:
    """Một dòng tóm tắt để in tiến độ."""
    if not row["solved"]:
        return f"KHONG GIAI DUOC ({row['note'] or 'het khong gian tim kiem'})"
    return (f"length={row['length']} cost={float(row['cost']):g} "
            f"nodes={row['expanded_nodes']} time={float(row['time_sec']) * 1000:.1f}ms "
            f"mem={row['peak_memory_kb']}KB")


def write_csv(rows: Sequence[Row], path: Path, fieldnames: Sequence[str] = FIELDNAMES) -> None:
    """Ghi CSV UTF-8, tự tạo thư mục cha; `newline=""` để Windows không chèn dòng trống."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("phải là số nguyên >= 1")
    return value


def _positive_float(text: str) -> float:
    value = float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("phải > 0")
    return value


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Tham số chung của run_all và benchmark_heuristics."""
    parser.add_argument("--levels", nargs="*", default=[], metavar="PREFIX",
                        help="chỉ chạy các màn có tên bắt đầu bằng PREFIX (vd: g1 g2_fragile_01)")
    parser.add_argument("--level-dir", type=Path, default=LEVEL_DIR,
                        help="thư mục chứa file màn (mặc định: levels/)")
    parser.add_argument("--include-demo", action="store_true",
                        help="chạy cả màn demo g3_switch_demo (mặc định bỏ qua)")
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES),
                        help="chế độ chi phí cần chạy (mặc định: cả hai)")
    parser.add_argument("--repeats", type=_positive_int, default=DEFAULT_REPEATS,
                        help="số lần lặp để lấy trung bình thời gian (mặc định 3)")
    parser.add_argument("--max-nodes", type=_positive_int, default=DEFAULT_MAX_NODES)
    parser.add_argument("--timeout", type=_positive_float, default=DEFAULT_TIMEOUT_SEC,
                        help="giây cho mỗi lần chạy solver")
    parser.add_argument("--no-check", action="store_true",
                        help="bỏ bước tự kiểm tra chéo kết quả")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="không in tiến độ và bảng tổng hợp")


def limits_from_args(args: argparse.Namespace) -> Limits:
    """Một `Limits` duy nhất, dùng chung cho mọi solver."""
    return Limits(max_nodes=args.max_nodes, timeout_sec=args.timeout)


def select_levels_from_args(parser: argparse.ArgumentParser,
                            args: argparse.Namespace) -> List[Path]:
    """Danh sách màn theo tham số; không có màn nào thì báo lỗi dòng lệnh."""
    paths = select_levels(list_levels(args.level_dir, args.include_demo), args.levels)
    if not paths:
        parser.error(f"không tìm thấy màn nào trong {args.level_dir} khớp --levels {args.levels}")
    return paths


def configure_output(quiet: bool) -> None:
    """Bật UTF-8 cho console (Windows) và cấu hình mức log."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    logging.basicConfig(level=logging.WARNING if quiet else logging.INFO, format="%(message)s")
