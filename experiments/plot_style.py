"""Report units and solver colors; no graphical dependency is needed to import."""

SOLVER_COLORS = {"bfs": "#1F77B4", "dfs": "#FF7F0E", "ucs": "#2CA02C", "astar": "#D62728"}
REPORT_WIDTH_INCHES = 7.2
MAIN_HEIGHT_INCHES = 8.3
DISPLAY_UNITS = {"time": "seconds", "memory": "MB (decimal, KiB * 1024 / 1000000)"}


def solver_color(name: str) -> str:
    """Keep algorithm colors stable even when another series is absent."""
    if name.startswith("astar_"):
        return SOLVER_COLORS["astar"]
    return SOLVER_COLORS.get(name, "#64748B")


def display_value(metric: str, value: float) -> float:
    """Convert F3's memory KiB to report MB; other stored metrics retain their units."""
    return value * 1024 / 1_000_000 if metric == "peak_memory_kb" else value
