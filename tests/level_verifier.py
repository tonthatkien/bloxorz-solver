"""Test-only bounded BFS/replay using the production Game's integrated tile rules."""
from collections import deque
from dataclasses import dataclass, replace

from game.game import Game
from game.level_loader import Level
from game.state import State


@dataclass(frozen=True)
class Solution:
    """A shortest unit-cost action sequence and deterministic search counts."""

    path: tuple[str, ...]
    expanded: int
    discovered: int


class VerificationGame:
    """Delegate to Game, optionally omitting switches for a negative control."""

    def __init__(self, level: Level, disable_switches: bool = False) -> None:
        if any(switch.type == "split" for switch in level.switches.values()):
            raise ValueError("T2 verifier excludes split gameplay")
        self.level = replace(level, switches={}) if disable_switches else level
        self.core = Game(self.level)

    def initial_state(self) -> State:
        """Use the real Game start and initial bridge mask."""
        return self.core.initial_state()

    def is_goal(self, state: State) -> bool:
        """Use Game's full-block upright goal condition."""
        return self.core.is_goal(state)

    def get_successors(self, state: State) -> list[tuple[str, State, float]]:
        """Use production transitions directly, without applying tile effects twice."""
        return self.core.get_successors(state)


def solve(game: VerificationGame | Game, max_expanded: int = 20000) -> Solution | None:
    """Run deterministic unit-cost BFS, failing explicitly on a verification budget limit."""
    initial = game.initial_state()
    frontier = deque([initial])
    parent: dict[State, tuple[State, str] | None] = {initial: None}
    expanded = 0
    while frontier:
        state = frontier.popleft()
        if game.is_goal(state):
            path = []
            while parent[state] is not None:
                state, action = parent[state]
                path.append(action)
            return Solution(tuple(reversed(path)), expanded, len(parent))
        if expanded >= max_expanded:
            raise RuntimeError("T2 verification exceeded its expansion budget")
        expanded += 1
        for action, next_state, _ in game.get_successors(state):
            if next_state not in parent:
                parent[next_state] = (state, action)
                frontier.append(next_state)
    return None


def replay(game: VerificationGame | Game, path: tuple[str, ...]) -> list[State]:
    """Require every recorded action to be a real successor and end at the goal."""
    states = [game.initial_state()]
    for action in path:
        successors = {name: state for name, state, _ in game.get_successors(states[-1])}
        if action not in successors:
            raise AssertionError(f"Illegal replay action {action!r} from {states[-1]}")
        states.append(successors[action])
    if not game.is_goal(states[-1]):
        raise AssertionError("Replay did not reach an upright full-block goal")
    return states
