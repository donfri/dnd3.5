"""Battle grid geometry: 5-foot squares, 3.5 distance counting, area templates.

The combat engine still tracks *engagement* (who is in melee with whom) for attacks
of opportunity and flanking; the grid adds real distances, movement, range
increments, and spell areas (bursts, cones, lines).
"""
from __future__ import annotations

import heapq
import math
from typing import Dict, Iterable, List, Optional, Tuple

from . import dice

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


def area_squares(kind: str, size: int, origin: Pos, aim: Pos,
                 terrain: Optional["Terrain"] = None) -> List[Pos]:
    """Squares covered by a template. Bursts center on aim; cones and lines start at the
    caster (origin) and point at aim. Walls stop the effect (line of effect)."""
    out = _area_squares(kind, size, origin, aim)
    if terrain is None or not terrain.cells:
        return out
    src = aim if kind == "burst" else origin
    return [q for q in out if not terrain.blocks_sight(q) and terrain.line_of_effect(src, q)]


def _area_squares(kind: str, size: int, origin: Pos, aim: Pos) -> List[Pos]:
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


def render(tokens: Dict[Pos, str], legend: List[str],
           terrain: Optional["Terrain"] = None) -> List[str]:
    """ASCII map: two characters per square."""
    top = "   " + "".join(f"{x % 10} " for x in range(W))
    lines = [top]
    for y in range(H):
        row = "".join(tokens.get((x, y)) or (terrain.char((x, y)) if terrain else ". ")
                      for x in range(W))
        lines.append(f"{y:>2} {row}")
    return lines + legend


# ---------------------------------------------------------------- terrain
# kind: (map char, name, walkable, blocks sight, gives cover, difficult)
KINDS = {
    "wall":   ("#", "wall / pillar", False, True, True, False),
    "tree":   ("^", "tree", False, False, True, False),
    "crate":  ("&", "carts and crates", False, False, True, False),
    "deep":   ("=", "deep water", False, False, False, False),
    "chasm":  ("v", "sheer drop", False, False, False, False),
    "water":  ("~", "shallow water", True, False, False, True),
    "rubble": (":", "rubble", True, False, False, True),
    "brush":  ('"', "undergrowth / reeds", True, False, False, True),
    "mud":    (",", "deep mud", True, False, False, True),
}

THEME_TEXT = {
    "open": "open ground",
    "forest": "woodland: trees block movement and give cover; undergrowth is slow going",
    "marsh": "marsh: deep pools can't be crossed; shallow water and reeds are slow going",
    "dungeon": "stone hall: pillars block movement and sight; rubble is slow going",
    "cave": "cave: rock walls close in; rubble is slow going",
    "town": "carts, crates and mud: crates give cover, mud is slow going",
    "bridge": "a narrow crossing over deep water: there's no way round",
    "ledge": "a narrow ledge above a sheer drop: there's no way round",
}

INF = 10 ** 6


class Terrain:
    def __init__(self, theme: str = "open", cells: Optional[Dict[Pos, str]] = None):
        self.theme = theme
        self.cells: Dict[Pos, str] = dict(cells or {})

    # ---- what a square is like
    def kind(self, p: Pos) -> Optional[str]:
        return self.cells.get(p)

    def char(self, p: Pos) -> str:
        k = self.cells.get(p)
        return (KINDS[k][0] + " ") if k else ". "

    def walkable(self, p: Pos) -> bool:
        k = self.cells.get(p)
        return in_bounds(p) and (k is None or KINDS[k][2])

    def blocks_sight(self, p: Pos) -> bool:
        k = self.cells.get(p)
        return bool(k and KINDS[k][3])

    def gives_cover(self, p: Pos) -> bool:
        k = self.cells.get(p)
        return bool(k and KINDS[k][4])

    def difficult(self, p: Pos) -> bool:
        k = self.cells.get(p)
        return bool(k and KINDS[k][5])

    def describe(self) -> str:
        return THEME_TEXT.get(self.theme, self.theme)

    def legend(self) -> List[str]:
        used = sorted(set(self.cells.values()), key=list(KINDS).index)
        return [f"{KINDS[k][0]} {KINDS[k][1]}{' (costs double)' if KINDS[k][5] else ''}"
                for k in used]

    # ---- movement (3.5 diagonals, difficult terrain x2, no cutting wall corners)
    def costs(self, start: Pos, blocked: Iterable[Pos] = ()) -> Tuple[Dict[Pos, int], Dict]:
        """Cheapest cost in feet from start to every square, and back-links for paths.
        blocked squares (foes) can't be entered."""
        block = set(blocked)
        best: Dict[Pos, int] = {start: 0}
        prev: Dict[Tuple[Pos, int], Optional[Tuple[Pos, int]]] = {(start, 0): None}
        seen: Dict[Tuple[Pos, int], int] = {(start, 0): 0}
        heap = [(0, start, 0)]
        while heap:
            c, p, par = heapq.heappop(heap)
            if seen.get((p, par), INF) < c:
                continue
            for q in neighbors(p):
                if q in block or not self.walkable(q):
                    continue
                diag = q[0] != p[0] and q[1] != p[1]
                if diag and not (self.walkable((q[0], p[1])) and self.walkable((p[0], q[1]))):
                    continue
                step = (10 if par else 5) if diag else 5
                if self.difficult(q):
                    step *= 2
                npar = (1 - par) if diag else par
                nc = c + step
                if nc < seen.get((q, npar), INF):
                    seen[(q, npar)] = nc
                    prev[(q, npar)] = (p, par)
                    if nc < best.get(q, INF):
                        best[q] = nc
                    heapq.heappush(heap, (nc, q, npar))
        self._last = (start, seen, prev)
        return best, prev

    def path(self, start: Pos, goal: Pos, blocked: Iterable[Pos] = ()) -> List[Pos]:
        """Squares walked from start to goal (excluding start), cheapest route."""
        best, prev = self.costs(start, blocked)
        if goal not in best:
            return []
        _, seen, _ = self._last
        state = min(((goal, par) for par in (0, 1) if (goal, par) in seen),
                    key=lambda s_: seen[s_])
        out = []
        while state is not None and state[0] != start:
            out.append(state[0])
            state = prev.get(state)
        out.reverse()
        return out

    def path_cost(self, start: Pos, path: List[Pos]) -> List[int]:
        """Running cost along a path."""
        out, c, par, cur = [], 0, 0, start
        for q in path:
            diag = q[0] != cur[0] and q[1] != cur[1]
            step = (10 if par else 5) if diag else 5
            if diag:
                par = 1 - par
            c += step * (2 if self.difficult(q) else 1)
            out.append(c)
            cur = q
        return out

    # ---- sight
    def line(self, a: Pos, b: Pos) -> List[Pos]:
        """Squares a straight line between two square centers passes through."""
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 4
        out: List[Pos] = []
        for i in range(1, n):
            t = i / n
            q = (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))
            if q not in (a, b) and q not in out:
                out.append(q)
        return out

    def line_of_effect(self, a: Pos, b: Pos) -> bool:
        return not any(self.blocks_sight(q) for q in self.line(a, b))

    def cover(self, a: Pos, b: Pos) -> bool:
        return any(self.gives_cover(q) for q in self.line(a, b))

    def connected(self) -> bool:
        free = [(x, y) for x in range(W) for y in range(H) if self.walkable((x, y))]
        if not free:
            return False
        best, _ = self.costs(free[0])
        return all(q in best for q in free)


def _blob(cells, kind, n, rows=None, cols=None, keep=()):
    """Grow a random patch of n squares."""
    rows = rows or (0, H - 1)
    cols = cols or (2, W - 3)
    p = (dice.die(cols[1] - cols[0] + 1) + cols[0] - 1, dice.die(rows[1] - rows[0] + 1) + rows[0] - 1)
    for _ in range(n):
        if in_bounds(p) and p not in keep:
            cells.setdefault(p, kind)
        q = dice.choice(neighbors(p))
        if rows[0] <= q[1] <= rows[1] and cols[0] <= q[0] <= cols[1]:
            p = q


def _scatter(cells, kind, n, cols=(3, W - 4), rows=(0, H - 1)):
    for _ in range(n):
        p = (dice.die(cols[1] - cols[0] + 1) + cols[0] - 1,
             dice.die(rows[1] - rows[0] + 1) + rows[0] - 1)
        cells.setdefault(p, kind)


def generate(theme: str) -> Terrain:
    """A random battlefield for the theme, always fully connected."""
    for attempt in range(20):
        cells: Dict[Pos, str] = {}
        if theme == "forest":
            _scatter(cells, "tree", 9 + dice.die(5))
            for _ in range(3):
                _blob(cells, "brush", 4 + dice.die(4))
        elif theme == "marsh":
            for _ in range(2 + dice.die(2) - 1):
                _blob(cells, "deep", 3 + dice.die(4), cols=(3, W - 4))
            for _ in range(3):
                _blob(cells, "water", 4 + dice.die(4))
            _blob(cells, "brush", 5)
        elif theme == "dungeon":
            for x in range(W):
                cells[(x, 0)] = "wall"
                cells[(x, H - 1)] = "wall"
            for x in (4, 7, 10):
                for y in (2, 6):
                    if dice.die(4) > 1:
                        cells[(x, y)] = "wall"
            for _ in range(2):
                _blob(cells, "rubble", 3 + dice.die(3), rows=(1, H - 2))
        elif theme == "cave":
            for x in range(W):
                for y in range(dice.die(3) - 1):
                    cells[(x, y)] = "wall"
                for y in range(dice.die(3) - 1):
                    cells[(x, H - 1 - y)] = "wall"
            _scatter(cells, "wall", 2 + dice.die(3), rows=(2, H - 3))
            for _ in range(2):
                _blob(cells, "rubble", 3 + dice.die(4))
        elif theme == "town":
            for _ in range(3 + dice.die(2)):
                x, y = dice.die(W - 7) + 2, dice.die(H) - 1
                for q in ((x, y), (x + 1, y)) if dice.die(2) == 1 else ((x, y), (x, y + 1)):
                    if in_bounds(q):
                        cells[q] = "crate"
            _blob(cells, "mud", 4 + dice.die(4))
        elif theme in ("bridge", "ledge"):
            gone = "deep" if theme == "bridge" else "chasm"
            for x in range(W):
                for y in list(range(0, 3)) + list(range(6, H)):
                    cells[(x, y)] = gone
            if theme == "ledge":
                _scatter(cells, "rubble", 3, rows=(3, 5))
        else:  # open ground: a few rocks and rough patches
            _scatter(cells, "wall", dice.die(3) - 1)
            if dice.die(2) == 1:
                _blob(cells, "brush", 3 + dice.die(4))
        # keep the edges where the sides start walkable
        for y in range(H):
            for x in (0, 1, 2, W - 1, W - 2):
                if cells.get((x, y)) in ("tree", "crate", "deep") and theme not in ("bridge",):
                    cells.pop((x, y), None)
        t = Terrain(theme, cells)
        if t.connected():
            return t
    return Terrain(theme, {})


THEME_WORDS = [
    ("bridge", ("bridge", "causeway")),
    ("ledge", ("goat trail", "ledge", "cliff path")),
    ("marsh", ("fen", "reed", "marsh", "swamp", "sunken", "flooded", "black water")),
    ("cave", ("cave", "grotto", "warren", "den")),
    ("forest", ("wood", "forest", "thorn", "hollow", "tree")),
    ("dungeon", ("hall", "crypt", "chamber", "cellar", "stair", "tomb", "barracks", "kennel",
                 "vault", "cells", "shrine", "tower", "lantern", "nave", "undercroft",
                 "lamp room", "barrow")),
    ("town", ("village", "square", "yard", "camp", "market", "cottage", "beach", "gate",
              "pier", "inn", "shingle")),
]


def theme_for(room: dict) -> str:
    """Pick a battlefield theme for a room: its own 'terrain' key, or from its words
    (the room's name first, then whichever theme its description mentions most)."""
    import re
    if room.get("terrain"):
        return room["terrain"]

    def hits(text, words):
        return sum(len(re.findall(r"\b" + re.escape(w) + r"s?\b", text)) for w in words)
    name = room.get("name", "").lower()
    for theme, words in THEME_WORDS:
        if hits(name, words):
            return theme
    text = str(room.get("desc", "")).lower()
    scores = [(hits(text, words), -i, theme) for i, (theme, words) in enumerate(THEME_WORDS)]
    best = max(scores)
    return best[2] if best[0] else "open"
