"""F4: reproducible solver/heuristic figures from F3 CSVs (PNG and vector PDF)."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
from statistics import fmean
from typing import Sequence

from .plot_data import (HEURISTICS, MODES, Run, check_heuristics, geometric_mean,
                        optimality_counts, ordered, paired_values, read_runs, solver_ratios,
                        validate_summary)
from .plot_solvers import level_labels, solver_appendix, solver_figure
from .plot_style import DISPLAY_UNITS, MAIN_HEIGHT_INCHES, REPORT_WIDTH_INCHES

ROOT = Path(__file__).resolve().parent
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#64748B")
LABELS = {"zero": "Zero (h=0)", "manhattan": "Manhattan",
          "manhattan_orient": "Manhattan + tư thế", "relaxed_maze": "Relaxed maze",
          "switch_aware": "Switch-aware", "split_cubes": "Split cubes", "advanced": "Advanced"}
MODE_LABELS = {"unit": "Chi phí đều (unit)", "weighted": "Chi phí không đều (weighted)"}


def _heuristic_figure(runs: list[Run], mode: str):
    import matplotlib.pyplot as plt

    metrics = ("expanded_nodes", "time_sec", "peak_memory_kb", "tightness")
    titles = ("Số nút đã mở rộng / h=0", "Thời gian / h=0",
              "Bộ nhớ đỉnh / h=0", "Độ sát: h(start) / C*")
    fig, axes = plt.subplots(4, 1, figsize=(REPORT_WIDTH_INCHES, MAIN_HEIGHT_INCHES))
    for ax, metric, title in zip(axes.flat, metrics, titles):
        paired, total = paired_values(runs, mode, metric)
        count = len(next(iter(paired.values()), []))
        values = {name: (fmean(data) if metric == "tightness" else geometric_mean(data))
                  if data else None for name, data in paired.items()}
        for i, (name, value) in enumerate(values.items()):
            if value is not None:
                ax.barh(i, value, color=COLORS[i % len(COLORS)], height=.63)
            ax.text((value or 0) + .025, i, "N/A" if value is None else f"{value:.3f}",
                    va="center", fontsize=11)
        ax.set_yticks(range(len(values)), [LABELS.get(n, n) for n in values])
        ax.invert_yaxis()
        ax.axvline(1, color="#475569", linestyle="--", linewidth=1)
        largest = max((v for v in values.values() if v is not None), default=1)
        ax.set_xlim(0, max(1.18, largest * 1.2))
        ax.set_title(f"{title}\nn={count}/{total} màn chung", loc="left", fontsize=12.5)
        ax.grid(axis="x", alpha=.18)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("So sánh heuristic A*\n" + MODE_LABELS[mode], fontsize=14)
    fig.text(.025, .015, "Mốc: A* h=0 cùng màn và chế độ; n: màn chung / tổng số màn.\n"
             "Ratio: trung bình nhân, thấp hơn tốt hơn; độ sát: trung bình cộng.\n"
             "Độ sát gần 1 là sát hơn; phép đo 0 không dùng làm log-ratio.", fontsize=10.5)
    fig.tight_layout(rect=(0, .095, 1, .92), h_pad=1.0)
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
    fig, axes = plt.subplots(len(modes), 1, figsize=(8, 4.1 * len(modes)),
                             squeeze=False, layout="constrained")
    for row, mode in enumerate(modes):
        ax = axes[row, 0]
        selected = [p for p in panels if p[0] == mode]
        values = [a+b for a, b in zip(selected[0][2], selected[1][2])]
        counts = [a+b for a, b in zip(selected[0][3], selected[1][3])]
        mesh = ax.pcolormesh(np.array(values, dtype=float), cmap="RdYlBu_r", norm=norm,
                             edgecolors="white", linewidth=.5, rasterized=False)
        ax.set_ylim(len(names), 0)
        for i, cells in enumerate(values):
            for j, value in enumerate(cells):
                label = "N/A" if value is None else f"{value:.3f}\nn={counts[i][j]}"
                color = "white" if value is not None and value < .3 else "black"
                ax.text(j + .5, i + .5, label, ha="center", va="center", fontsize=11.5,
                        color=color)
        labels = [f"{metric}\n{g.upper()}" for metric in ("Nút", "TG") for g in groups]
        ax.set_xticks([j + .5 for j in range(len(labels))], labels, fontsize=11.5)
        ax.set_yticks([i + .5 for i in range(len(names))], [LABELS.get(n, n) for n in names])
        ax.set_title(MODE_LABELS[mode], fontsize=12.5)
    colorbar = fig.colorbar(mesh, ax=list(axes.flat), shrink=.8,
                            label="Tỉ số / h=0; thấp hơn tốt hơn")
    colorbar.solids.set_rasterized(False)
    fig.suptitle("Hiệu quả heuristic theo nhóm màn", fontsize=14)
    fig.supxlabel("Nút = nút mở rộng; TG = thời gian · n: số màn ghép cặp chung", fontsize=10.5)
    return fig


def render(results: list[Run], heuristics: list[Run], output: Path,
           formats: Sequence[str] = ("png", "pdf"), dpi: int = 300) -> list[Path]:
    """Render report figures with a headless backend; no plotting imports during tests."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11.5,
                         "pdf.fonttype": 42, "svg.fonttype": "none", "axes.titlepad": 10})
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    factories = [(f"solvers_{m}", lambda m=m: solver_figure(results, m)) for m in MODES
                 if any(r.mode == m for r in results)]
    if heuristics:
        factories += [(f"heuristics_{m}", lambda m=m: _heuristic_figure(heuristics, m))
                      for m in MODES
                      if any(r.mode == m for r in heuristics)]
        factories += [("heuristics_groups", lambda: _group_figure(heuristics))]
    factories += [(f"appendix_solvers_{m}", lambda m=m: solver_appendix(results, m))
                  for m in MODES if any(r.mode == m for r in results)]
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
    for suffix in ("png", "pdf", "svg"):
        (output / f"heuristics_quality.{suffix}").unlink(missing_ok=True)
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
        for mode in {r.mode for r in results}:
            solver_ratios(results, mode, "cost")
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
                "units": DISPLAY_UNITS,
                "level_labels": level_labels(sorted({r.level for r in results})),
                "ratio_baseline": {"solver": "UCS on the same level and cost_mode",
                                   "heuristic": "A* h=0 on the same level and cost_mode"},
                "heuristic_optimality": optimality_counts(heuristics),
                "quality_note": "Observed cost agreement does not prove admissibility",
                "page_order": "grouped solvers, heuristics, per-level solver appendices",
                "aggregation": "geometric mean of common positive ratios; arithmetic tightness",
                "failure_policy": {"solver": "common solved positive values; keep nonoptimal paths",
                                   "heuristic": "common optimal cohorts with positive ratios"}}
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"Generated {len(paths)} files in {args.out_dir}; summary verified: {bool(args.summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
