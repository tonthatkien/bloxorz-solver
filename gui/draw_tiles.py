"""Advanced terrain and switch markers in the board's existing oblique projection."""
from dataclasses import replace
from math import cos, pi, sin

import pygame

from game.level_loader import Level
from gui.render_board import _draw_floor_tile, _poly_aa, _tile_quad

FRAGILE_TOP = (229, 147, 57)
FRAGILE_EDGE = (139, 78, 36)
BRIDGE_TOP = (177, 137, 85)
BRIDGE_EDGE = (98, 72, 47)
SOFT_TOP = (105, 210, 211)
HEAVY_INK = (255, 225, 126)
SPLIT_INK = (232, 196, 255)
MARKER_EDGE = (49, 65, 62)


def terrain_view(level: Level, bridge_mask: int) -> Level:
    """Hide closed bridges for both drawing and neighboring cliff-edge geometry.

    This is a display-only copy. The original Level and runtime State remain unchanged.
    """
    closed = [bridge.pos for bridge in level.bridges.values()
              if not bridge_mask & (1 << bridge.id)]
    if not closed:
        return level
    rows = [list(row) for row in level.grid]
    for r, c in closed:
        rows[r][c] = "."
    return replace(level, grid=["".join(row) for row in rows])


def _point(x: int, y: int, tw: int, th: int, skew: int,
           u: float, v: float) -> tuple[int, int]:
    # Interpolate along the two edges of render_board._tile_quad.
    tl, tr, _, bl = _tile_quad(x, y, tw, th, skew)
    return (round(tl[0] + u * (tr[0] - tl[0]) + v * (bl[0] - tl[0])),
            round(tl[1] + u * (tr[1] - tl[1]) + v * (bl[1] - tl[1])))


def draw_fragile_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                      x: int, y: int, tw: int, th: int, skew: int) -> None:
    """Draw orange fragile terrain with a crack below any block drawn afterward."""
    _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)
    _poly_aa(surface, FRAGILE_TOP, _tile_quad(x, y, tw, th, skew), FRAGILE_EDGE)
    crack = [_point(x, y, tw, th, skew, u, v) for u, v in
             ((0.55, 0.12), (0.43, 0.40), (0.60, 0.55), (0.46, 0.85))]
    pygame.draw.lines(surface, FRAGILE_EDGE, False, crack, max(1, tw // 35))


def draw_bridge_tile(surface: pygame.Surface, level: Level, r: int, c: int,
                     x: int, y: int, tw: int, th: int, skew: int,
                     opened: bool = True) -> None:
    """Draw a plank surface for an open bridge; a closed bridge contributes no floor."""
    if not opened:
        return
    _draw_floor_tile(surface, level, r, c, x, y, tw, th, skew)
    _poly_aa(surface, BRIDGE_TOP, _tile_quad(x, y, tw, th, skew), BRIDGE_EDGE)
    for v in (0.2, 0.4, 0.6, 0.8):
        pygame.draw.line(surface, BRIDGE_EDGE,
                         _point(x, y, tw, th, skew, 0.04, v),
                         _point(x, y, tw, th, skew, 0.96, v))


def _disc(surface: pygame.Surface, color: tuple[int, int, int],
          x: int, y: int, tw: int, th: int, skew: int) -> None:
    points = [_point(x, y, tw, th, skew, 0.5 + 0.30 * cos(i * pi / 4),
                     0.5 + 0.34 * sin(i * pi / 4)) for i in range(8)]
    _poly_aa(surface, color, points, MARKER_EDGE)


def draw_soft_switch(surface: pygame.Surface, x: int, y: int,
                     tw: int, th: int, skew: int) -> None:
    """Draw the soft switch as a cyan octagonal pressure plate."""
    _disc(surface, SOFT_TOP, x, y, tw, th, skew)


def draw_heavy_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Draw a contrasting X for the heavy switch without evaluating activation."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for start, end in (((0.31, 0.27), (0.69, 0.73)),
                       ((0.31, 0.73), (0.69, 0.27))):
        pygame.draw.line(surface, HEAVY_INK,
                         _point(x, y, tw, th, skew, *start),
                         _point(x, y, tw, th, skew, *end), max(1, tw // 17))


def draw_split_switch(surface: pygame.Surface, x: int, y: int,
                      tw: int, th: int, skew: int) -> None:
    """Draw paired purple brackets for the split switch; no cube logic lives here."""
    _disc(surface, MARKER_EDGE, x, y, tw, th, skew)
    for mirror in (False, True):
        points = [_point(x, y, tw, th, skew, 1 - u if mirror else u, v)
                  for u, v in ((0.40, 0.27), (0.32, 0.37), (0.29, 0.50),
                               (0.32, 0.63), (0.40, 0.73))]
        pygame.draw.lines(surface, SPLIT_INK, False, points, max(1, tw // 25))


def draw_switch(surface: pygame.Surface, kind: str, x: int, y: int,
                tw: int, th: int, skew: int) -> None:
    """Draw the marker belonging to a validated switch type."""
    drawers = {"soft": draw_soft_switch, "heavy": draw_heavy_switch,
               "split": draw_split_switch}
    drawers[kind](surface, x, y, tw, th, skew)
