"""Fragile safety checks, independent of movement and the Game API."""
from typing import AbstractSet

from .state import Cell, STAND, State, cells


def is_fragile_safe(state: State, fragile: AbstractSet[Cell]) -> bool:
    """Reject an upright full block on fragile; lying blocks and single cubes are safe.

    Call on the position AFTER rolling. This checks weight only; the caller must
    also check that every occupied cell has support. No terrain or State is mutated.
    """
    return state.split is not None or state.orient != STAND or cells(state)[0] not in fragile
