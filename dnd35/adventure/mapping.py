"""Auto-drawn maps. Rooms have no coordinates, so we lay them out on a grid from
their exit directions (north = up the page, and so on), avoiding overlaps."""
from __future__ import annotations

from collections import deque
from typing import Dict, Tuple

DIRS = {
    "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
    "up": (0, -1), "down": (0, 1), "in": (1, 0), "out": (-1, 0),
    "northeast": (1, -1), "northwest": (-1, -1), "southeast": (1, 1), "southwest": (-1, 1),
}
_layout_cache: Dict[str, Dict[str, Tuple[int, int]]] = {}


def _free_near(want, used):
    if want not in used:
        return want
    x, y = want
    for r in range(1, 6):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                cand = (x + dx, y + dy)
                if cand not in used:
                    return cand
    return (x + 7, y)


def layout(adv) -> Dict[str, Tuple[int, int]]:
    if adv.ID in _layout_cache:
        return _layout_cache[adv.ID]
    pos = {adv.START: (0, 0)}
    used = {(0, 0)}
    q = deque([adv.START])
    while q:
        rid = q.popleft()
        x, y = pos[rid]
        for ex_id, ex in adv.ROOMS[rid].get("exits", {}).items():
            to = ex["to"]
            if to in pos or to not in adv.ROOMS:
                continue
            dx, dy = DIRS.get(ex_id, (1, 1))
            p = _free_near((x + dx, y + dy), used)
            pos[to] = p
            used.add(p)
            q.append(to)
    for rid in adv.ROOMS:  # anything unreachable goes off to the side
        if rid not in pos:
            p = _free_near((max(x for x, _ in used) + 1, 0), used)
            pos[rid] = p
            used.add(p)
    _layout_cache[adv.ID] = pos
    return pos


def map_data(gm_or_gs) -> dict:
    """What the party knows: visited rooms, plus doorways they've seen out of them."""
    gs = gm_or_gs
    adv = gs.adv
    pos = layout(adv)
    visited = {r for r, st in gs.rooms.items() if st.get("visited")}
    visited.add(gs.room)
    nodes: Dict[str, dict] = {}
    edges = []
    seen_edges = set()
    for rid in visited:
        room = adv.ROOMS.get(rid)
        if not room:
            continue
        st = gs.rooms.get(rid, {})
        nodes[rid] = {"id": rid, "name": room["name"], "visited": True,
                      "current": rid == gs.room, "town": bool(room.get("town"))}
        for ex_id, ex in room.get("exits", {}).items():
            if ex.get("hidden") and ex_id not in st.get("revealed", []):
                continue
            to = ex["to"]
            if to not in adv.ROOMS:
                continue
            if to not in nodes and to not in visited:
                nodes[to] = {"id": to, "name": "?", "visited": False, "current": False,
                             "town": False}
            key = tuple(sorted((rid, to)))
            locked = bool(ex.get("lock")) and ex_id not in st.get("unlocked", [])
            trap = ex.get("trap")
            trap_known = bool(trap) and trap in st.get("found_traps", []) and \
                trap not in st.get("disabled_traps", [])
            if key in seen_edges:
                for e in edges:
                    if tuple(sorted((e["a"], e["b"]))) == key:
                        e["locked"] = e["locked"] or locked
                        e["trap"] = e["trap"] or trap_known
                continue
            seen_edges.add(key)
            edges.append({"a": rid, "b": to, "dir": ex_id, "locked": locked,
                          "trap": trap_known})
    for rid, n in nodes.items():
        n["x"], n["y"] = pos[rid]
    return {"nodes": list(nodes.values()), "edges": edges}
