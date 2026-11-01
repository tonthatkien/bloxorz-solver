"""Grouped UCS-relative solver comparisons and absolute per-level appendices."""
from typing import TYPE_CHECKING

from .plot_axes import annotate_ratio, fit_log_annotations, log_axis
from .plot_data import METRICS, SOLVERS, Run, geometric_mean, ordered, solver_ratios
from .plot_style import MAIN_HEIGHT_INCHES, REPORT_WIDTH_INCHES, display_value, solver_color

if TYPE_CHECKING:
    from matplotlib.axes import Axes
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


def draw_solver_panel(ax: "Axes", runs: list[Run], mode: str, metric: str, title: str) -> None:
    """Draw unchanged common-cohort ratios with readable ticks and value labels."""
    import numpy as np

    groups = sorted({r.group for r in runs if r.mode == mode})
    names = ordered((r.series for r in runs if r.mode == mode), SOLVERS)
    batches = [solver_ratios(runs, mode, metric, group) for group in groups]
    width = .8 / len(names)
    present = []
    for index, name in enumerate(names):
        values = [geometric_mean(paired[name]) for paired, _ in batches]
        x = np.arange(len(groups)) + (index - (len(names)-1)/2) * width
        ax.bar(x, [np.nan if v is None else v for v in values], width=width * .94,
               color=solver_color(name), label=LABELS.get(name, name))
        for pos, value in zip(x, values):
            annotate_ratio(ax, pos, value)
        present.extend(v for v in values if v is not None)
    log_axis(ax, present)
    ax.set_xlim(-.65, len(groups)-.35)
    ax.axhline(1, color="#475569", linestyle="--", linewidth=1)
    ax.set_xticks(range(len(groups)),
                  [f"{g.upper()}\nn={len(next(iter(p.values()), []))}/{total}"
                   for g, (p, total) in zip(groups, batches)])
    ax.set_title(title, loc="left", fontsize=13, pad=14)
    ax.set_ylabel("Tỉ số / UCS (log)", fontsize=12)


def solver_figure(runs: list[Run], mode: str,
                  metrics: tuple[str, ...] = ("expanded_nodes", "time_sec")) -> "Figure":
    """Use two full-height panels per report page rather than four cramped panels."""
    import matplotlib.pyplot as plt

    titles = {"expanded_nodes": "Số nút mở rộng / UCS", "time_sec": "Thời gian / UCS",
              "peak_memory_kb": "Bộ nhớ đỉnh / UCS", "cost": "Chi phí lời giải / UCS"}
    fig, axes = plt.subplots(len(metrics), 1, squeeze=False,
                             figsize=(REPORT_WIDTH_INCHES, MAIN_HEIGHT_INCHES))
    for ax, metric in zip(axes.flat, metrics):
        title = titles[metric]
        if metric == "cost" and mode == "unit":
            title += " (= độ dài / UCS)"
        draw_solver_panel(ax, runs, mode, metric, title)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.56, .92),
               ncol=len(labels), frameon=False, fontsize=12)
    fig.suptitle("So sánh thuật toán theo nhóm màn\n" + MODE_LABELS[mode], fontsize=14)
    fig.text(.025, .015, "Trung bình nhân tỉ số từng màn/UCS; n: màn chung / tổng số màn.\n"
             "Giữ lời giải chưa tối ưu. BFS weighted không bảo đảm cost tối ưu.\n"
             "Đường ngang 1: UCS, mốc cost tối ưu tham chiếu.", fontsize=10.5)
    fig.subplots_adjust(left=.17, right=.98, bottom=.14, top=.83, hspace=.68)
    fit_log_annotations(fig)
    return fig


def solver_appendix(runs: list[Run], mode: str, metrics: tuple[str, ...]) -> "Figure":
    """Keep absolute per-level measurements as a lookup appendix."""
    import matplotlib.pyplot as plt
    import numpy as np

    items = [r for r in runs if r.mode == mode]
    levels = sorted({r.level for r in items})
    names = ordered((r.series for r in items), SOLVERS)
    table = {(r.level, r.series): r for r in items}
    height = MAIN_HEIGHT_INCHES if len(metrics) == 2 else 5.4
    fig, axes = plt.subplots(len(metrics), 1, squeeze=False,
                             figsize=(REPORT_WIDTH_INCHES, height))
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
            log_axis(ax, present, reference=False)
        else:
            from matplotlib.ticker import MaxNLocator
            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.set_title(METRIC_LABELS[metric] + (" — thang log" if log else ""), loc="left")
        ax.set_xticks(range(len(levels)), list(level_labels(levels).values()),
                      rotation=75, ha="right")
        ax.tick_params(axis="y", labelsize=12, pad=8)
        ax.tick_params(axis="x", labelsize=10.5, pad=5)
        ax.grid(axis="y", alpha=.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("PHỤ LỤC · Chi tiết từng màn\n" + MODE_LABELS[mode], fontsize=14, y=.99)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.56, .92),
               ncol=4, frameon=False, fontsize=12)
    solved = sum(r.solved for r in items)
    note = (f"{len(levels)} màn; {solved}/{len(levels)*len(names)} điều kiện giải được.\n"
            "×: thiếu/chưa giải; không gán thành 0. Đường nối chỉ để tra cứu.\n")
    note += ("Weighted: ít bước không đồng nghĩa cost tối ưu." if mode == "weighted"
             else "Unit: cost bằng số bước.")
    fig.text(.025, .015, note, fontsize=10.5)
    bottom, top = (.20, .82) if len(metrics) == 2 else (.28, .74)
    fig.subplots_adjust(left=.17, right=.98, bottom=bottom, top=top, hspace=.88)
    return fig
