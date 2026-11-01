"""C2: activation of split switches for the Bloxorz game."""
from typing import Optional

from .cube import try_merge
from .level_loader import Level
from .state import STAND, State


def activate_split_switch(old: State, landed: State, level: Level) -> Optional[State]:
    """Split a standing block when it lands on a split switch.

    Return the split state when the switch is activated, otherwise return None.
    The switch's configured ``cubes`` positions are used as-is. If those positions
    are already adjacent, normalize immediately to the corresponding full block.

    Rules (C2):
    - Only a STANDING full block (``split is None``) can trigger a split switch.
    - A single cube never triggers a split switch.
    - The switch fires on the *entering* edge of standing pressure; staying on the
      same switch while upright does NOT retrigger.
    - If the configured cube positions are already edge-adjacent, the block is
      normalized to the merged full block instead of producing an invalid split.
    """
    if landed.split is not None or landed.orient != STAND:
        return None

    switch = level.switches.get((landed.r, landed.c))
    if switch is None or switch.type != "split" or not switch.cubes:
        return None

    was_standing_on_same_switch = (
        old.split is None
        and old.orient == STAND
        and (old.r, old.c) == switch.pos
    )
    if was_standing_on_same_switch:
        return None

    cube_a, cube_b = switch.cubes
    merged = try_merge(cube_a, cube_b, landed.bridges)
    if merged is not None:
        return merged
    return State(bridges=landed.bridges, split=(cube_a, cube_b))