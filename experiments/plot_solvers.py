"""Grouped UCS-relative solver comparisons and absolute per-level appendices."""
from typing import TYPE_CHECKING

from .plot_data import METRICS, SOLVERS, Run, geometric_mean, ordered, solver_ratios
from .plot_style import MAIN_HEIGHT_INCHES, REPORT_WIDTH_INCHES, display_value, solver_color

if TYPE_CHECKING:
    from matplotlib.figure import Figure

LABELS = {"bfs": "BFS", "dfs": "DFS", "ucs": "UCS", "astar": "A*"}
METRIC_LABELS = {"time_sec": "Thời gian (s)", "peak_memory_kb": "Bộ nhớ đỉnh (MB)",
                 "expanded_nodes": "Số nút mở rộng", "length": "Độ dài lời giải (bước)",
                 "cost": "Chi phí lời giải"}
MODE_LABELS = {"unit": "Chi phí đều (unit)", "weighted": "Chi phí không đều (weighted)"}


def level_labels(levels: list[str]) -> dict[str, str]:
    """Make compact, unique map labels for the appendix and manifest."""
    labels = {level: level.split("_")[0].upper() + "-" + level.split("_")[2]
              if len(level.split("_")) >= 3 else level for level in levels}
    if len(set(labels.values())) == len(levels):
        return labels
    return {level: level for level in levels}


def solver_figure(runs: list[Run], mode: str) -> "Figure":
    """Show geometric means of per-level UCS ratios, grouped by G1-G4."""
    import matplotlib.pyplot as plt
    import numpy as np

    groups = sorted({r.group for r in runs if r.mode == mode})
    names = ordered((r.series for r in runs if r.mode == mode), SOLVERS)
    metrics = ("expanded_nodes", "time_sec", "peak_memory_kb", "cost")
    titles = ("Số nút mở rộng / UCS", "Thời gian / UCS", "Bộ nhớ đỉnh / UCS",
              "Chi phí lời giải / UCS" + (" (= độ dài / UCS)" if mode == "unit" else ""))
    fig, axes = plt.subplots(4, 1, figsize=(REPORT_WIDTH_INCHES, MAIN_HEIGHT_INCHES))
    width = .8 / len(names)
    for ax, metric, title in zip(axes.flat, metrics, titles):
        batches = [solver_ratios(runs, mode, metric, group) for group in groups]
        for index, name in enumerate(names):
            values = [geometric_mean(paired[name]) for paired, _ in batches]
            x = np.arange(len(groups)) + (index - (len(names)-1)/2) * width
            ax.bar(x, [np.nan if v is None else v for v in values], width=width,
                   color=solver_color(name), label=LABELS.get(name, name))
            for pos, value in zip(x, values):
                if value is None:
                    ax.text(pos, .04, "N/A", transform=ax.get_xaxis_transform(),
                            ha="center", va="bottom", rotation=90, fontsize=10.5)
                else:
                    ax.annotate(f"{value:.3g}", (pos, value), xytext=(0, 4),
                                textcoords="offset points", ha="center", va="bottom",
                                rotation=90, fontsize=10.5)
        _format_group_axis(ax, groups, batches, title)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .94),
               ncol=len(names), frameon=False)
    fig.suptitle("So sánh thuật toán theo nhóm màn\n" + MODE_LABELS[mode], fontsize=14)
    fig.text(.025, .015, "Trung bình nhân tỉ số từng màn/UCS; n: màn chung / tổng số màn.\n"
             "Giữ lời giải chưa tối ưu. BFS weighted không bảo đảm cost tối ưu.\n"
             "Đường ngang 1: UCS, mốc cost tối ưu tham chiếu.", fontsize=10.5)
    fig.tight_layout(rect=(0, .095, 1, .90), h_pad=1.0)
    return fig


def _format_group_axis(ax, groups, batches, title):
    ax.set_yscale("log")
    ax.set_xlim(-.6, len(groups)-.4)
    ax.axhline(1, color="#475569", linestyle="--", linewidth=1)
    ax.set_xticks(range(len(groups)),
                  [f"{g.upper()}\nn={len(next(iter(p.values()), []))}/{total}"
                   for g, (p, total) in zip(groups, batches)])
    ax.set_title(title, loc="left", fontsize=12.5)
    ax.set_ylabel("Tỉ số (log)")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    bottom, _ = ax.get_ylim()
    bottom = min(bottom, .8)
    largest = max([1, *[p.get_height() for p in ax.patches if p.get_height() > 0]])
    # Reserve upper log-space for vertical value labels without touching the title.
    ax.set_ylim(bottom, largest * (largest / bottom) ** .7)


def solver_appendix(runs: list[Run], mode: str) -> "Figure":
    """Keep absolute per-level measurements as a lookup appendix."""
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
                values.append(np.nan if value is None else display_value(metric, value))
            present.extend(v for v in values if np.isfinite(v))
            ax.plot(range(len(levels)), values, marker=("o", "s", "^", "D")[index % 4],
                    markersize=4, linewidth=1.3, color=solver_color(name),
                    label=LABELS.get(name, name))
            ax.scatter([x + index * .06 for x in failed], [.025] * len(failed), marker="x",
                       color=solver_color(name), transform=ax.get_xaxis_transform())
        log = metric in METRICS[:3] and present and min(present) > 0
        if log:
            ax.set_yscale("log")
        else:
            ax.set_ylim(bottom=0)
        ax.set_title(METRIC_LABELS[metric] + (" — thang log" if log else ""), loc="left")
        ax.set_xticks(range(len(levels)), list(level_labels(levels).values()),
                      rotation=55, ha="right")
        ax.grid(axis="y", alpha=.22)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in list(axes.flat)[len(metrics):]:
        ax.axis("off")
    fig.suptitle("PHỤ LỤC · Chi tiết từng màn · " + MODE_LABELS[mode], fontsize=17, y=.99)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .956),
               ncol=4, frameon=False)
    solved = sum(r.solved for r in items)
    note = (f"{len(levels)} màn; {solved}/{len(levels)*len(names)} điều kiện giải được. "
            "× ở chân trục = thiếu/chưa giải, không gán thành 0.\n")
    note += ("Weighted: ít bước không đồng nghĩa cost tối ưu." if mode == "weighted"
             else "Unit: cost bằng số bước.")
    note += " Đường nối chỉ để tra cứu, không biểu thị xu hướng."
    fig.text(.025, .012, note, fontsize=10)
    fig.tight_layout(rect=(0, .07, 1, .91))
    return fig
