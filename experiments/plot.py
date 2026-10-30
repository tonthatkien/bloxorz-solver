"""F4: reproducible solver/heuristic figures from F3 CSVs (PNG and vector PDF)."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
from statistics import fmean
from typing import Sequence

from .plot_data import (HEURISTICS, METRICS, MODES, SOLVERS, Run, check_heuristics,
                        geometric_mean, ordered, paired_values, read_runs, summarize,
                        validate_summary)

ROOT = Path(__file__).resolve().parent
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#64748B")
LABELS = {"bfs": "BFS", "dfs": "DFS", "ucs": "UCS", "astar": "A*",
          "zero": "Zero (h=0)", "manhattan": "Manhattan",
          "manhattan_orient": "Manhattan + tư thế", "relaxed_maze": "Relaxed maze",
          "switch_aware": "Switch-aware", "split_cubes": "Split cubes", "advanced": "Advanced"}
METRIC_LABELS = {"time_sec": "Thời gian (ms)", "peak_memory_kb": "Bộ nhớ đỉnh (KiB)",
                 "expanded_nodes": "Số nút mở rộng", "length": "Độ dài lời giải (bước)",
                 "cost": "Chi phí lời giải"}
MODE_LABELS = {"unit": "Chi phí đều (unit)", "weighted": "Chi phí không đều (weighted)"}


def _aliases(levels: list[str]) -> dict[str, str]:
    labels = {level: level.split("_")[0].upper() + "-" + level.split("_")[2]
              if len(level.split("_")) >= 3 else level for level in levels}
    if len(set(labels.values())) == len(levels):
        return labels
    return {level: level for level in levels}


def _solver_figure(runs: list[Run], mode: str):
    import matplotlib.pyplot as plt
    import numpy as np

    items = [r for r in runs if r.mode == mode]
    levels = sorted({r.level for r in items})
    names = ordered((r.series for r in items), SOLVERS)
    table = {(r.level, r.series): r for r in items}
    metrics = METRICS if mode == "weighted" else METRICS[:-1]
    fig, axes = plt.subplots((len(metrics) + 1) // 2, 2, figsize=(16, 4.7 * ((len(metrics)+1)//2)))
    for ax, metric in zip(axes.flat, metrics):
        present = []
        for index, name in enumerate(names):
            values, failed = [], []
            for x, level in enumerate(levels):
                run = table.get((level, name))
                value = run.values[metric] if run and run.solved else None
                if value is None:
                    failed.append(x)
                scale = 1000 if metric == "time_sec" else 1
                values.append(np.nan if value is None else value * scale)
            present.extend(v for v in values if np.isfinite(v))
            ax.plot(range(len(levels)), values, marker=("o", "s", "^", "D")[index % 4],
                    markersize=4, linewidth=1.3, color=COLORS[index % len(COLORS)],
                    label=LABELS.get(name, name))
            ax.scatter([x + index * .06 for x in failed], [.025] * len(failed), marker="x",
                       color=COLORS[index % len(COLORS)], transform=ax.get_xaxis_transform())
        log = metric in METRICS[:3] and present and min(present) > 0
        if log:
            ax.set_yscale("log")
        else:
            ax.set_ylim(bottom=0)
        ax.set_title(METRIC_LABELS[metric] + (" — thang log" if log else ""), loc="left")
        ax.set_xticks(range(len(levels)), list(_aliases(levels).values()), rotation=55, ha="right")
        ax.grid(axis="y", alpha=.22)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in list(axes.flat)[len(metrics):]:
        ax.axis("off")
    fig.suptitle("So sánh thuật toán · " + MODE_LABELS[mode], fontsize=17, y=.99)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .956),
               ncol=4, frameon=False)
    solved = sum(r.solved for r in items)
    note = (f"{len(levels)} màn; {solved}/{len(levels)*len(names)} điều kiện giải được. "
            "× ở chân trục = thiếu/chưa giải, không gán thành 0.\n")
    note += ("Weighted tối ưu theo cost, không nhất thiết ít bước nhất." if mode == "weighted"
             else "Unit: cost bằng số bước.")
    fig.text(.025, .012, note, fontsize=10)
    fig.tight_layout(rect=(0, .07, 1, .91))
    return fig


def _heuristic_figure(runs: list[Run], mode: str):
    import matplotlib.pyplot as plt

    metrics = ("expanded_nodes", "time_sec", "peak_memory_kb", "tightness")
    titles = ("Node / h=0 · thấp hơn tốt hơn", "Thời gian / h=0 · thấp hơn tốt hơn",
              "Bộ nhớ / h=0 · thấp hơn tốt hơn", "h(start) / C* · gần 1 hơn là sát hơn")
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    for ax, metric, title in zip(axes.flat, metrics, titles):
        paired, total = paired_values(runs, mode, metric)
        count = len(next(iter(paired.values()), []))
        values = {name: (fmean(data) if metric == "tightness" else geometric_mean(data))
                  if data else None for name, data in paired.items()}
        for i, (name, value) in enumerate(values.items()):
            if value is not None:
                ax.barh(i, value, color=COLORS[i % len(COLORS)], height=.63)
            ax.text((value or 0) + .025, i, "N/A" if value is None else f"{value:.3f}",
                    va="center", fontsize=10)
        ax.set_yticks(range(len(values)), [LABELS.get(n, n) for n in values])
        ax.invert_yaxis()
        ax.axvline(1, color="#475569", linestyle="--", linewidth=1)
        largest = max((v for v in values.values() if v is not None), default=1)
        ax.set_xlim(0, max(1.18, largest * 1.2))
        ax.set_title(f"{title}\nn={count}/{total} màn chung", loc="left", fontsize=12)
        ax.grid(axis="x", alpha=.18)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("So sánh heuristic A* · " + MODE_LABELS[mode], fontsize=17)
    fig.text(.025, .015, "Mốc so sánh: A* với h=0 trên cùng màn và cost mode. "
             "Ratio: trung bình nhân; tightness: trung bình cộng.\nChỉ dùng các màn hợp lệ "
             "chung cho mọi heuristic; phép đo bằng 0 không dùng làm log-ratio.", fontsize=10)
    fig.tight_layout(rect=(0, .07, 1, .94))
    return fig


def _group_figure(runs: list[Run]):
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    import numpy as np

    modes = [m for m in MODES if any(r.mode == m for r in runs)]
    names = ordered((r.series for r in runs), HEURISTICS)
    groups = sorted({r.group for r in runs})
    panels = []
    for mode in modes:
        for metric in ("expanded_nodes", "time_sec"):
            values, counts = [], []
            batches = {g: paired_values(runs, mode, metric, g)[0] for g in groups}
            for name in names:
                data = [batches[g].get(name, []) for g in groups]
                values.append([geometric_mean(v) for v in data])
                counts.append([len(v) for v in data])
            panels.append((mode, metric, values, counts))
    finite = [v for _, _, rows, _ in panels for row in rows for v in row if v is not None]
    largest = max(finite, default=1)
    norm = TwoSlopeNorm(vmin=0, vcenter=1, vmax=max(1.1, largest))
    fig, axes = plt.subplots(len(modes), 2, figsize=(15, 4.6 * len(modes)),
                             squeeze=False, layout="constrained")
    for ax, (mode, metric, values, counts) in zip(axes.flat, panels):
        image = ax.pcolormesh(np.array(values, dtype=float), cmap="RdYlBu_r", norm=norm,
                              edgecolors="white", linewidth=.5, rasterized=False)
        ax.set_ylim(len(names), 0)
        for i, row in enumerate(values):
            for j, value in enumerate(row):
                label = "N/A" if value is None else f"{value:.3f}\nn={counts[i][j]}"
                color = "white" if value is not None and value < .3 else "black"
                ax.text(j + .5, i + .5, label, ha="center", va="center", fontsize=9,
                        color=color)
        ax.set_xticks([j + .5 for j in range(len(groups))], [g.upper() for g in groups])
        ax.set_yticks([i + .5 for i in range(len(names))], [LABELS.get(n, n) for n in names])
        ax.set_title(MODE_LABELS[mode] + (" · node / h=0" if metric == "expanded_nodes"
                                         else " · thời gian / h=0"), fontsize=12)
    colorbar = fig.colorbar(image, ax=list(axes.flat), shrink=.8,
                            label="Ratio (trung bình nhân); thấp hơn tốt hơn")
    colorbar.solids.set_rasterized(False)
    fig.suptitle("Hiệu quả heuristic theo nhóm màn", fontsize=17)
    fig.supxlabel("Cùng thang màu cho cả hai cost mode · n: số màn ghép cặp chung", fontsize=10)
    return fig


def _quality_figure(runs: list[Run]):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    modes = [m for m in MODES if any(r.mode == m for r in runs)]
    names = ordered((r.series for r in runs), HEURISTICS)
    summary = summarize(runs)
    fig, axes = plt.subplots(len(modes), 2, figsize=(15, 4.8 * len(modes)), squeeze=False)
    for row, mode in enumerate(modes):
        total = len({r.level for r in runs if r.mode == mode})
        wins = [summary.get((mode, "all", n), {}).get("node_wins", 0) for n in names]
        axes[row, 0].barh(range(len(names)), wins, color=[COLORS[i % 7] for i in range(len(names))])
        for i, value in enumerate(wins):
            axes[row, 0].text(value + .12, i, str(value), va="center")
        for i, name in enumerate(names):
            batch = [r for r in runs if r.mode == mode and r.series == name]
            good = sum(r.optimal is True and r.solved for r in batch)
            bad = sum(r.optimal is False and r.solved for r in batch)
            for count, left, color in ((good, 0, "#009E73"), (bad, good, "#D55E00"),
                                       (total-good-bad, good+bad, "#CBD5E1")):
                axes[row, 1].barh(i, count, left=left, color=color)
            axes[row, 1].text(total + .12, i, f"{good}/{total}", va="center")
        for col in (0, 1):
            ax = axes[row, col]
            ax.set_yticks(range(len(names)), [LABELS.get(n, n) for n in names])
            ax.invert_yaxis()
            ax.set_xlim(0, total * 1.15)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis="x", alpha=.18)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.set_title(MODE_LABELS[mode] + (" · ít node nhất (kể cả hòa)" if col == 0
                                             else " · số màn có cost tối ưu"), fontsize=12)
    fig.suptitle("Chất lượng heuristic trên bộ dữ liệu đã đo", fontsize=17)
    fig.text(.025, .015, "Mỗi heuristic hòa ít node nhất đều được tính một lượt thắng. "
             "Tối ưu: cost bằng A*(h=0) trên cùng màn.\nXanh: tối ưu; cam: không tối ưu; "
             "xám: chưa xác nhận. Không suy ra xác suất thắng từ tổng các cột hòa.", fontsize=10)
    fig.tight_layout(rect=(0, .07, 1, .94))
    return fig


def render(results: list[Run], heuristics: list[Run], output: Path,
           formats: Sequence[str] = ("png", "pdf"), dpi: int = 300) -> list[Path]:
    """Render report figures with a headless backend; no plotting imports during tests."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "pdf.fonttype": 42, "svg.fonttype": "none", "axes.titlepad": 10})
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    factories = [(f"solvers_{m}", lambda m=m: _solver_figure(results, m)) for m in MODES
                 if any(r.mode == m for r in results)]
    if heuristics:
        factories += [(f"heuristics_{m}", lambda m=m: _heuristic_figure(heuristics, m))
                      for m in MODES
                      if any(r.mode == m for r in heuristics)]
        factories += [("heuristics_groups", lambda: _group_figure(heuristics)),
                      ("heuristics_quality", lambda: _quality_figure(heuristics))]
    book_path = output / "all_figures.pdf"
    book_context = PdfPages(book_path) if "pdf" in formats else nullcontext(None)
    with book_context as book:
        for stem, factory in factories:
            fig = factory()
            try:
                for suffix in formats:
                    path = output / f"{stem}.{suffix}"
                    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
                    paths.append(path)
                if book is not None:
                    book.savefig(fig, bbox_inches="tight", facecolor="white")
            finally:
                plt.close(fig)
    if "pdf" in formats:
        paths.append(book_path)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    """Validate F3 inputs, render figures, and write a provenance manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/results.csv")
    parser.add_argument("--heuristics", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results/f4")
    parser.add_argument("--formats", nargs="+", choices=("png", "pdf", "svg"),
                        default=["png", "pdf"])
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args(argv)
    if args.dpi <= 0 or (args.summary and not args.heuristics):
        parser.error("dpi must be positive; --summary requires --heuristics")
    try:
        results = read_runs(args.results)
        heuristics = read_runs(args.heuristics, "heuristic") if args.heuristics else []
        if heuristics:
            check_heuristics(heuristics)
        if args.summary:
            validate_summary(args.summary, heuristics)
        paths = render(results, heuristics, args.out_dir, args.formats, args.dpi)
    except (OSError, ValueError, ImportError) as error:
        parser.exit(2, f"Cannot generate F4 figures: {error}\n")
    inputs = [p for p in (args.results, args.heuristics, args.summary) if p is not None]
    manifest = {"inputs": [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in inputs], "result_rows": len(results),
                "heuristic_rows": len(heuristics), "summary_verified": args.summary is not None,
                "figures": [p.name for p in paths], "dpi": args.dpi,
                "matplotlib_version": __import__("matplotlib").__version__,
                "units": {"time": "milliseconds (CSV seconds * 1000)",
                          "memory": "KiB (F3 tracemalloc bytes / 1024)"},
                "level_labels": _aliases(sorted({r.level for r in results})),
                "ratio_baseline": "A* h=0 on the same level and cost_mode",
                "aggregation": "geometric mean of common positive ratios; arithmetic tightness",
                "failure_policy": "missing/unsolved are not zero; common optimal cohorts only"}
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"Generated {len(paths)} files in {args.out_dir}; summary verified: {bool(args.summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
