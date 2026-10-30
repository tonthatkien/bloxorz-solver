"""Read F3 CSV data and verify comparisons without importing plotting dependencies."""
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Iterable

MODES = ("unit", "weighted")
SOLVERS = ("bfs", "dfs", "ucs", "astar")
HEURISTICS = ("zero", "manhattan", "manhattan_orient", "relaxed_maze",
              "switch_aware", "split_cubes", "advanced")
METRICS = ("time_sec", "peak_memory_kb", "expanded_nodes", "length", "cost")
DERIVED = ("h_start", "optimal_cost", "tightness", "node_ratio", "time_ratio")
SUMMARY = ("levels", "geo_node_ratio", "geo_time_ratio", "mean_tightness",
           "node_wins", "non_optimal")
ROUNDING_TOL = 0.000051  # F3 stores derived quantities and summaries to four decimals.


@dataclass(frozen=True)
class Run:
    """One measured condition; absent metrics remain None, never fabricated zeroes."""

    group: str
    level: str
    mode: str
    series: str
    solved: bool
    values: dict[str, float | None]
    note: str
    optimal: bool | None = None


def _table(path: Path, required: Iterable[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        missing = set(required) - set(fields)
        if missing or len(fields) != len(set(fields)):
            raise ValueError(f"{path.name}: missing columns {sorted(missing)} or duplicate headers")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}:{line}: malformed CSV row")
            rows.append({key: value.strip() for key, value in row.items()})
    if not rows:
        raise ValueError(f"{path.name}: empty data")
    return rows


def _bool(value: str, label: str) -> bool:
    if value.lower() not in ("true", "false"):
        raise ValueError(f"{label}: expected True or False, got {value!r}")
    return value.lower() == "true"


def _number(value: str, label: str) -> float | None:
    if not value:
        return None
    try:
        result = float(value)
    except ValueError as error:
        raise ValueError(f"{label}: invalid number {value!r}") from error
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label}: expected a finite non-negative number")
    return result


def ordered(names: Iterable[str], reference: tuple[str, ...]) -> list[str]:
    """Keep documented order, followed by any extra F3 solver/heuristic names."""
    found = set(names)
    return [name for name in reference if name in found] + sorted(found - set(reference))


def read_runs(path: Path, series_field: str = "solver") -> list[Run]:
    """Validate an F3 result CSV, including explicit booleans and unique conditions."""
    extra = DERIVED + ("optimal",) if series_field == "heuristic" else ()
    fields = ("group", "level", "cost_mode", series_field, "solved", "note") + METRICS + extra
    result, seen = [], set()
    for line, row in enumerate(_table(path, fields), 2):
        label = f"{path.name}:{line}"
        group, level, mode, series = (row[k] for k in ("group", "level", "cost_mode", series_field))
        key = (mode, level, series)
        if (mode not in MODES or group not in ("g1", "g2", "g3", "g4")
                or not level.startswith(group + "_") or not series or key in seen):
            raise ValueError(f"{label}: invalid or duplicate condition {key}")
        seen.add(key)
        solved = _bool(row["solved"], label)
        values = {key: _number(row[key], f"{label}/{key}") for key in METRICS + extra
                  if key != "optimal"}
        if solved and (any(values[key] is None for key in METRICS) or row["note"]):
            raise ValueError(f"{label}: solved row has missing metrics or a failure note")
        for key in ("length", "expanded_nodes"):
            if values[key] is not None and not values[key].is_integer():
                raise ValueError(f"{label}/{key}: expected an integer")
        if not solved:
            values["length"] = values["cost"] = None
        optimal = _bool(row["optimal"], label) if row.get("optimal") else None
        result.append(Run(group, level, mode, series, solved, values, row["note"], optimal))
    return result


def geometric_mean(values: Iterable[float | None]) -> float | None:
    """Match F3: geometric mean of defined positive ratios, None if none exist."""
    positive = [value for value in values if value is not None and value > 0]
    return math.exp(fmean(math.log(value) for value in positive)) if positive else None


def _same(actual: float | None, expected: float | None, label: str) -> None:
    if actual is None or expected is None:
        equal = actual is expected
    else:
        equal = math.isclose(actual, expected, rel_tol=0, abs_tol=ROUNDING_TOL)
    if not equal:
        raise ValueError(f"{label}: CSV value {actual} differs from computed value {expected}")


def check_heuristics(runs: list[Run]) -> None:
    """Check every stored ratio/optimal flag against zero on the same level and mode."""
    baseline = {(r.mode, r.level): r for r in runs if r.series == "zero"}
    for run in runs:
        key = (run.mode, run.level)
        if key not in baseline:
            raise ValueError(f"Missing zero baseline for {key}")
        ref = baseline[key]
        if not ref.solved:
            continue
        cost = ref.values["cost"]
        _same(run.values["optimal_cost"], cost, f"{key}/{run.series}/optimal_cost")
        if cost:
            h = run.values["h_start"]
            _same(run.values["tightness"], None if h is None else h / cost,
                  f"{key}/{run.series}/tightness")
        if run.solved:
            optimal = math.isclose(run.values["cost"], cost, rel_tol=0, abs_tol=1e-6)
            if run.optimal is not optimal:
                raise ValueError(f"{key}/{run.series}: inconsistent optimal flag")
            for metric, field in (("expanded_nodes", "node_ratio"), ("time_sec", "time_ratio")):
                denominator = ref.values[metric]
                expected = run.values[metric] / denominator if denominator else None
                _same(run.values[field], expected, f"{key}/{run.series}/{field}")


def summarize(runs: list[Run]) -> dict[tuple[str, str, str], dict[str, float | None]]:
    """Recompute all F3 summary columns; node wins include every tied minimum."""
    minima = {}
    for run in runs:
        key = (run.mode, run.level)
        if run.solved:
            minima[key] = min(minima.get(key, math.inf), run.values["expanded_nodes"])
    buckets = defaultdict(list)
    for run in runs:
        for group in (run.group, "all"):
            buckets[run.mode, group, run.series].append(run)
    result = {}
    for key, items in buckets.items():
        tightness = [r.values["tightness"] for r in items if r.values["tightness"] is not None]
        result[key] = {
            "levels": sum(r.solved for r in items),
            "geo_node_ratio": geometric_mean(r.values["node_ratio"] for r in items),
            "geo_time_ratio": geometric_mean(r.values["time_ratio"] for r in items),
            "mean_tightness": fmean(tightness) if tightness else None,
            "node_wins": sum(r.solved and r.values["expanded_nodes"] == minima[r.mode, r.level]
                             for r in items),
            "non_optimal": sum(r.optimal is False for r in items),
        }
    return result


def validate_summary(path: Path, runs: list[Run]) -> None:
    """Reject stale, incomplete or inconsistent F3 summary data before making figures."""
    expected = summarize(runs)
    actual = {}
    for row in _table(path, ("cost_mode", "group", "heuristic") + SUMMARY):
        key = (row["cost_mode"], row["group"], row["heuristic"])
        if key in actual:
            raise ValueError(f"{path.name}: duplicate summary {key}")
        actual[key] = {field: _number(row[field], f"{key}/{field}") for field in SUMMARY}
        for field in ("levels", "node_wins", "non_optimal"):
            value = actual[key][field]
            if value is None or not value.is_integer():
                raise ValueError(f"{path.name}/{key}/{field}: expected an integer")
    if actual.keys() != expected.keys():
        raise ValueError(f"{path.name}: summary conditions do not match heuristics.csv")
    for key, values in expected.items():
        for field, value in values.items():
            _same(actual[key][field], value, f"{path.name}/{key}/{field}")


def paired_values(runs: list[Run], mode: str, metric: str,
                  group: str = "all") -> tuple[dict[str, list[float]], int]:
    """Compare on common solved levels with positive metrics; report total coverage.

    A* h=0 is the paired baseline. Zero/rounded-away timings are not log ratios.
    Failure, non-optimal or missing values exclude that condition for ALL heuristics.
    """
    items = [r for r in runs if r.mode == mode and (group == "all" or r.group == group)]
    names = ordered((r.series for r in runs if r.mode == mode), HEURISTICS)
    table = {(r.level, r.series): r for r in items}
    levels = sorted({r.level for r in items})
    result = {name: [] for name in names}
    for level in levels:
        batch = [table.get((level, name)) for name in names]
        field = {"expanded_nodes": "node_ratio", "time_sec": "time_ratio"}.get(metric)
        if not all(r and r.solved and r.optimal is True and r.values[metric] is not None
                   and (r.values[metric] > 0 or metric == "tightness")
                   and (not field or (r.values[field] is not None and r.values[field] > 0))
                   for r in batch):
            continue
        ref = table.get((level, "zero"))
        if ref is None:
            raise ValueError(f"Missing zero baseline for {mode}/{level}")
        for run in batch:
            value = (run.values[metric] if metric == "tightness" else
                     run.values[field] if field else run.values[metric] / ref.values[metric])
            result[run.series].append(value)
    return result, len(levels)
