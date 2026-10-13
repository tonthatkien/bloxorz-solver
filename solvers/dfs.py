"""Solver DFS/IDS. TODO [E5]."""
from typing import Optional

from .base import LimitChecker, Limits, SearchResult, reconstruct_path


def solve(game, limits: Optional[Limits] = None) -> SearchResult:
    checker = LimitChecker(limits)   # gọi checker.tick(expanded) mỗi lần mở rộng nút
    raise NotImplementedError
