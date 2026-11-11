"""Battle grid geometry: 5-foot squares, 3.5 distance counting, area templates.

The combat engine still tracks *engagement* (who is in melee with whom) for attacks
of opportunity and flanking; the grid adds real distances, movement, range
increments, and spell areas (bursts, cones, lines).
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Tuple

W, H = 14, 9          # 70 x 45 feet
Pos = Tuple[int, int]

# spell and breath areas: ("burst", radius ft) / ("cone", length ft) / ("line", length ft)
AREAS: Dict[str, Tuple[str, int]] = {
    "Fireball": ("burst", 20), "Delayed Blast Fireball": ("burst", 20),
    "Sleep": ("burst", 10), "Sound Burst": ("burst", 10), "Ice Storm": ("burst", 20),
    "Flame Strike": ("burst", 10), "Holy Smite": ("burst", 20), "Entangle": ("burst", 20),
    "Grease": ("burst", 5), "Slow": ("burst", 15), "Confusion": ("burst", 15),
    "Song of Discord": ("burst", 15), "Fire Storm": ("burst", 20), "Sunburst": ("burst", 20),
    "Horrid Wilting": ("burst", 15), "Storm of Vengeance": ("burst", 30),
    "Blade Barrier": ("line", 60), "Holy Word": ("burst", 40), "Mass Hold Monster": ("burst", 15),
    "Wail of the Banshee": ("burst", 20), "Creeping Doom": ("burst", 10),
    "Burning Hands": ("cone", 15), "Color Spray": ("cone", 15), "Cone of Cold": ("cone", 60),
    "Fear": ("cone", 30), "Shout": ("cone", 30), "Waves of Fatigue": ("cone", 30),
    "Sunbeam": ("line", 60), "Lightning Bolt": ("line", 120), "Chain Lightning": ("burst", 30),
    "Meteor Swarm": ("burst", 20),
}

# areas where the caster picks which creatures inside are affected (allies are spared)
SELECTIVE = {"Chain Lightning", "Slow", "Mass Hold Monster", "Holy Word", "Holy Smite",
             "Wail of the Banshee"}


def dist(a: Pos, b: Pos) -> int:
    """Distance in feet with the 3.5 alternating-diagonal rule (5, 10, 5, 10...)."""
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    diag, straight = min(dx, dy), abs(dx - dy)
    return 5 * (straight + diag + diag // 2)


def adjacent(a: Pos, b: Pos) -> bool:
    return a != b and max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1


def in_bounds(p: Pos) -> bool:
    return 0 <= p[0] < W and 0 <= p[1] < H


def neighbors(p: Pos) -> List[Pos]:
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = (p[0] + dx, p[1] + dy)
            if (dx or dy) and in_bounds(q):
                out.append(q)
    return out


def step_path(start: Pos, goal: Pos, occupied: Iterable[Pos], max_ft: int,
              stop_adjacent: bool = True) -> Pos:
    """Walk greedily toward goal (around occupied squares) spending at most max_ft.
    Returns the end square."""
    occ = set(occupied)
    cur, spent, diagonals = start, 0, 0
    while True:
        if (stop_adjacent and adjacent(cur, goal)) or cur == goal:
            return cur
        best, best_d = None, None
        for q in neighbors(cur):
            if q in occ or (q == goal and stop_adjacent):
                continue
            diag = q[0] != cur[0] and q[1] != cur[1]
            cost = 10 if diag and diagonals % 2 == 1 else 5
            if spent + cost > max_ft:
                continue
            d = dist(q, goal)
            if best_d is None or d < best_d:
                best, best_d, best_cost, best_diag = q, d, cost, diag
        if best is None or best_d >= dist(cur, goal):
            return cur
        cur = best
        spent += best_cost
        diagonals += 1 if best_diag else 0


def step_away(start: Pos, threats: List[Pos], occupied: Iterable[Pos], max_ft: int) -> Pos:
    occ = set(occupied)
    cur, spent = start, 0
    while spent + 5 <= max_ft:
        opts = [q for q in neighbors(cur) if q not in occ]
        if not opts:
            break
        best = max(opts, key=lambda q: min((dist(q, t) for t in threats), default=0))
        if threats and min(dist(best, t) for t in threats) <= min(dist(cur, t) for t in threats):
            break
        cur = best
        spent += 5
    return cur


def nearest_free(around: Pos, occupied: Iterable[Pos], prefer: Optional[Pos] = None) -> Pos:
    occ = set(occupied)
    cands = [q for q in neighbors(around) if q not in occ]
    if not cands:
        ring = [(x, y) for x in range(W) for y in range(H) if (x, y) not in occ]
        return min(ring, key=lambda q: dist(q, around)) if ring else around
    if prefer is None:
        return cands[0]
    return min(cands, key=lambda q: dist(q, prefer))


def area_squares(kind: str, size: int, origin: Pos, aim: Pos) -> List[Pos]:
    """Squares covered by a template. Bursts center on aim; cones and lines start at the
    caster (origin) and point at aim."""
    out = []
    if kind == "burst":
        for x in range(W):
            for y in range(H):
                if dist((x, y), aim) <= size:
                    out.append((x, y))
        return out
    vx, vy = aim[0] - origin[0], aim[1] - origin[1]
    length = math.hypot(vx, vy) or 1.0
    ux, uy = vx / length, vy / length
    for x in range(W):
        for y in range(H):
            if (x, y) == origin:
                continue
            wx, wy = x - origin[0], y - origin[1]
            along = wx * ux + wy * uy
            if along <= 0 or dist((x, y), origin) > size:
                continue
            across = abs(wx * uy - wy * ux)
            if kind == "cone" and across <= along + 0.01:
                out.append((x, y))
            elif kind == "line" and across <= 0.71:
                out.append((x, y))
    return out


def render(tokens: Dict[Pos, str], legend: List[str]) -> List[str]:
    """ASCII map: two characters per square."""
    top = "   " + "".join(f"{x % 10} " for x in range(W))
    lines = [top]
    for y in range(H):
        row = "".join(tokens.get((x, y), ". ") for x in range(W))
        lines.append(f"{y:>2} {row}")
    return lines + legend
