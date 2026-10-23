"""Pure bridge/switch landing rules; movement and split gameplay belong to A2/C1/C3."""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import FrozenSet, Iterable, Mapping, Optional, Tuple

from .fragile import is_fragile_safe
from .level_loader import Level
from .state import Cell, HORIZ, STAND, VERT, State, cells


def _check_mask(bridge_mask: int) -> None:
    if type(bridge_mask) is not int or bridge_mask < 0:
        raise ValueError("bridges: expected a non-negative integer bitmask")


@dataclass(frozen=True)
class SwitchEffect:
    """Immutable snapshot of one soft/heavy switch's effect."""

    type: str
    pos: Cell
    targets: Tuple[int, ...]
    mode: str
    set: Optional[str] = None
    target_mask: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        mask = 0
        for bridge_id in self.targets:
            mask |= 1 << bridge_id
        object.__setattr__(self, "target_mask", mask)


@dataclass(frozen=True)
class TileRules:
    """Static terrain snapshot, prepared once per Level and reused by every successor.

    Build with from_level after parse_level validation. The input Level retains its
    public mutable API; this snapshot cannot be changed by later edits to that Level.
    """

    floor: FrozenSet[Cell]
    fragile: FrozenSet[Cell]
    bridges: Mapping[Cell, int]
    switches: Tuple[SwitchEffect, ...]

    @classmethod
    def from_level(cls, level: Level) -> "TileRules":
        """Copy validated JSON terrain using '#' floor and '.' void, without A1 parsing."""
        floor = frozenset((r, c) for r, row in enumerate(level.grid)
                          for c, char in enumerate(row) if char in "#G")
        bridges = MappingProxyType({bridge.pos: bridge.id for bridge in level.bridges.values()})
        switches = tuple(SwitchEffect(switch.type, switch.pos, tuple(switch.targets),
                                      switch.mode, switch.set)
                         for switch in sorted(level.switches.values(), key=lambda item: item.pos)
                         if switch.type in ("soft", "heavy"))
        return cls(floor, frozenset(level.fragile), bridges, switches)

    def is_bridge_open(self, pos: Cell, bridge_mask: int) -> bool:
        """Report runtime support at a bridge coordinate; return False for non-bridge cells."""
        _check_mask(bridge_mask)
        bridge_id = self.bridges.get(pos)
        return bridge_id is not None and bool(bridge_mask & (1 << bridge_id))

    def is_supported(self, state: State) -> bool:
        """Require support under the entire footprint and enforce fragile weight limits."""
        _check_mask(state.bridges)
        if state.split is None and state.orient not in (STAND, HORIZ, VERT):
            return False
        if not is_fragile_safe(state, self.fragile):
            return False
        return all(pos in self.floor and
                   (pos not in self.bridges or self.is_bridge_open(pos, state.bridges))
                   for pos in cells(state))

    def _pressed(self, switch: SwitchEffect, state: State, footprint: FrozenSet[Cell]) -> bool:
        if switch.pos not in footprint:
            return False
        return switch.type == "soft" or (state.split is None and state.orient == STAND)

    def detect_triggered_switches(self, old: State, landed: State) -> Tuple[SwitchEffect, ...]:
        """Return activation edges in coordinate order; sustained contact never retriggers.

        Heavy activation compares upright pressure, so lying-to-standing on the same
        coordinate enters its activation region. Split switches are reserved for C2.
        """
        previous_cells = frozenset(cells(old))
        landed_cells = frozenset(cells(landed))
        return tuple(switch for switch in self.switches
                     if self._pressed(switch, landed, landed_cells)
                     and not self._pressed(switch, old, previous_cells))

    def apply_switch_effects(self, bridge_mask: int, triggered: Iterable[SwitchEffect]) -> int:
        """Apply one event per switch in ascending (row, column) order to a fresh mask.

        Multiple toggles compose by parity; permanent sets open/close without locking
        out future switches. Coordinate order also resolves mixed effects on one target.
        Pass the events returned by detect_triggered_switches for this TileRules object.
        """
        _check_mask(bridge_mask)
        for switch in sorted(triggered, key=lambda item: item.pos):
            targets_mask = switch.target_mask
            if switch.mode == "toggle":
                bridge_mask ^= targets_mask
            elif switch.set == "open":
                bridge_mask |= targets_mask
            else:
                bridge_mask &= ~targets_mask
        return bridge_mask

    def resolve_landing(self, old: State, landed: State) -> Optional[State]:
        """Resolve tiles AFTER movement, returning None on falling/fragile failure.

        The old state's mask is authoritative; landed provides the new pose/split data.
        Check support before effects, detect activation edges, apply effects, then check
        support again (a switch may close a bridge under the block). No action is rolled
        here, and no State or Level is mutated. A2/C3 must omit None from successors.
        """
        candidate = replace(landed, bridges=old.bridges)
        if not self.is_supported(candidate):
            return None
        triggered = self.detect_triggered_switches(old, candidate)
        updated_mask = self.apply_switch_effects(old.bridges, triggered)
        result = replace(candidate, bridges=updated_mask)
        return result if self.is_supported(result) else None
