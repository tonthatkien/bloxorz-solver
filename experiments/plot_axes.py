"""Readable report axes; plotting dependencies remain lazy for headless unit tests."""
from math import ceil, floor, isfinite, log10
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

TICK_SIZE = 12
VALUE_SIZE = 11.5


def format_value(value: float) -> str:
    """Keep five significant digits so near-one cost ratios remain distinguishable."""
    if not isfinite(value):
        raise ValueError("Cannot label a nonfinite measurement")
    return f"{value:.5g}"


def log_axis(ax: "Axes", values: Iterable[float], reference: bool = True) -> None:
    """Use positive limits and sparse decade labels without inventing measurements."""
    from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullFormatter

    data = list(values)
    if any(not isfinite(v) or v <= 0 for v in data):
        raise ValueError("Log axes require finite positive measurements; use N/A or linear")
    bounds = data + ([1.] if reference else [])
    if not bounds:
        raise ValueError("A log axis requires data or an explicit reference")
    low, high = log10(min(bounds)), log10(max(bounds))
    lower = min(floor(low), low - .12)
    span = max(high - lower, .6)
    upper = max(ceil(high) + .12, high + .42 * span)
    ax.set_yscale("log")
    ax.set_ylim(10 ** lower, 10 ** upper)
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.,), numticks=6))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10, labelOnlyBase=True))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=(2., 5.), numticks=12))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="y", which="major", pad=8, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", which="minor", length=2.5)
    ax.tick_params(axis="x", pad=7, labelsize=TICK_SIZE)
    ax.yaxis.labelpad = 12
    ax.grid(axis="y", which="major", alpha=.22)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def annotate_ratio(ax: "Axes", position: float, value: float | None) -> None:
    """Keep narrow grouped-bar labels separate without rounding near one to one."""
    if value is None:
        ax.text(position, .04, "N/A", transform=ax.get_xaxis_transform(), ha="center",
                va="bottom", rotation=90, fontsize=VALUE_SIZE)
    else:
        ax.annotate(format_value(value), (position, value), xytext=(0, 5),
                    textcoords="offset points", ha="center", va="bottom", rotation=90,
                    fontsize=VALUE_SIZE)


def fit_log_annotations(fig: "Figure") -> None:
    """Reserve real rendered space for bar labels inside each logarithmic panel."""
    for _ in range(12):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        changed = False
        for ax in fig.axes:
            if ax.get_yscale() != "log" or not ax.texts:
                continue
            top = max(t.get_window_extent(renderer).y1 for t in ax.texts if t.get_visible())
            if top > ax.bbox.y1 - 6:
                bottom, upper = map(log10, ax.get_ylim())
                ax.set_ylim(10 ** bottom, 10 ** (bottom + (upper - bottom) * 1.18))
                changed = True
        if not changed:
            return
    raise ValueError("Value labels need a taller panel to fit inside the axes")
