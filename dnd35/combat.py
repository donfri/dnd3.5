"""Turn-based D&D 3.5 combat.

Everyone stands on a 5-foot battle grid (see grid.py). Distance limits how far a
creature can move each turn, sets range penalties, and decides who is caught in a
spell's area. On top of the grid, a creature that moves into melee with a foe
becomes *engaged* with it. Engagement drives attacks of opportunity, flanking
(allies on opposite sides of the same foe), firing into melee, and whether a
creature can make a full attack (no move needed).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from . import dice, grid, rules
from .creature import Creature
from .data.items import item_data
from .effects import Effect
from .magic import consume_one_shot, deal_damage, drain_level, saving_throw
from .sheet import short_status
from .ui import c


from .combat_base import CState, wound_word  # noqa: F401
from .combat_maneuvers import ManeuversMixin
from .combat_monsters import MonstersMixin
from .combat_player import PlayerMixin


class Combat(ManeuversMixin, MonstersMixin, PlayerMixin):
    def __init__(self, ui, party: Sequence[Creature], monsters: Sequence[Creature],
                 surprised: Sequence[Creature] = (), can_flee: bool = True,
                 title: str = "COMBAT", dark: bool = False, terrain=None):
        self.ui = ui
        self.party = list(party)
        self.monsters = list(monsters)
        self.surprised = set(id(s) for s in surprised)
        self.can_flee = can_flee
        self.title = title
        self.round = 0
        self.st: Dict[int, CState] = {}
        for p in self.party:
            self.st[p.uid] = CState(p, "pc")
        # animal companions fight alongside their masters
        self.companions: List[Creature] = []
        for p in self.party:
            for comp in (p.companions_all() if hasattr(p, "companions_all") else []):
                if comp.dead or p.dead:
                    continue
                comp.effects = [e for e in comp.effects if e.duration is None
                                and not (e.tags & {"prone", "grappled"})]
                self.companions.append(comp)
                self.st[comp.uid] = CState(comp, "pc")
                if id(p) in self.surprised:
                    self.surprised.add(id(comp))
        for m in self.monsters:
            self.st[m.uid] = CState(m, "mon")
        self.dark = dark
        if dark:
            for x in self.st.values():
                cr = x.c
                if getattr(cr, "is_pc", False):
                    form = cr.wild_form()
                    vision = form.get("vision", "") if form else cr.race_data["vision"]
                else:
                    vision = getattr(cr, "block", {}).get("vision", "")
                if "darkvision" not in vision and "blindsense" not in vision:
                    cr.add_effect(Effect("In the dark", None, tags=["blinded"], hidden=False))
        self._name_monsters()
        self.order: List[CState] = []
        self.xp_monsters: List[Creature] = []
        self.fell_short = False
        if isinstance(terrain, grid.Terrain):
            self.terrain = terrain
        elif terrain:
            self.terrain = grid.generate(terrain)
        else:
            self.terrain = grid.Terrain()
        self.place_tokens()

    def _name_monsters(self):
        counts: Dict[str, int] = {}
        for m in self.monsters:
            counts[m.name] = counts.get(m.name, 0) + 1
        seen: Dict[str, int] = {}
        for m in self.monsters:
            if counts[m.name] > 1:
                seen[m.name] = seen.get(m.name, 0) + 1
                m.name = f"{m.name} {chr(64 + seen[m.name])}"

    # ------------------------------------------------------------ queries
    def s(self, cr: Creature) -> CState:
        return self.st[cr.uid]

    def active(self, cr: Creature) -> bool:
        st = self.s(cr)
        return not cr.dead and not st.fled and not getattr(st, "ridden", False)

    def allies(self, cr: Creature) -> List[Creature]:
        side = self.s(cr).side
        return [x.c for x in self.st.values() if x.side == side and self.active(x.c)]

    def enemies(self, cr: Creature) -> List[Creature]:
        side = self.s(cr).side
        return [x.c for x in self.st.values() if x.side != side and self.active(x.c)]

    def is_engaged(self, a: Creature, b: Creature) -> bool:
        return b.uid in self.s(a).engaged

    def engaged_foes(self, a: Creature) -> List[Creature]:
        return [self.st[u].c for u in self.s(a).engaged if u in self.st and self.active(self.st[u].c)]

    def engage(self, a: Creature, b: Creature) -> None:
        if not self.near(a, b):
            self.s(a).pos = self.melee_square(a, b)
        self.s(a).engaged.add(b.uid)
        self.s(b).engaged.add(a.uid)

    def disengage_all(self, a: Creature, retreat: int = 0) -> None:
        """Break off melee. retreat = feet the creature moves away from its foes."""
        foes = self.engaged_foes(a)
        for u in list(self.s(a).engaged):
            if u in self.st:
                self.st[u].engaged.discard(a.uid)
        self.s(a).engaged.clear()
        if retreat and not a.dead and a.uid in self.st:
            threats = [self.s(f).pos for f in (foes or self.enemies(a))]
            here = self.s(a).pos
            costs, _ = self.terrain.costs(here, self.foe_squares(a))
            occ = set(self.occupied(a))
            opts = [q for q, cst in costs.items() if cst <= retreat
                    and self.fits(a, q, occ)] or [here]
            self.s(a).pos = max(opts, key=lambda q: (
                min((grid.dist(q, t) for t in threats), default=0), -costs.get(q, 0)))

    # ------------------------------------------------------------ the grid
    def speed_of(self, cr: Creature) -> int:
        sp = cr.speed() if callable(getattr(cr, "speed", None)) else \
            getattr(cr, "block", {}).get("speed", 30)
        fly = getattr(cr, "block", {}).get("fly")
        if isinstance(fly, int) and fly > sp:
            sp = fly
        ride = cr.get_effect("Mounted")
        if ride:
            sp = ride.data["speed"]
        if cr.has_tag("slowed"):
            sp //= 2
        return max(5, sp or 30)

    def occupied(self, but: Optional[Creature] = None) -> List[Tuple[int, int]]:
        return [q for x in self.st.values() for q in self.cells(x.c)
                if x.c is not but and not x.c.dead and not x.fled]

    def distance(self, a: Creature, b: Creature) -> int:
        return min(grid.dist(p, q) for p in self.cells(a) for q in self.cells(b))

    def big(self, cr: Creature) -> bool:
        """Large and bigger monsters fill a 10-ft (2 x 2) space."""
        return not cr.is_pc and cr.size in ("large", "huge", "gargantuan", "colossal")

    def cells(self, cr: Creature, at=None) -> List[Tuple[int, int]]:
        x, y = at or self.s(cr).pos
        if not self.big(cr):
            return [(x, y)]
        return [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]

    def fits(self, cr: Creature, at, occ) -> bool:
        return all(grid.in_bounds(q) and self.terrain.walkable(q) and q not in occ
                   for q in self.cells(cr, at))

    def near(self, a: Creature, b: Creature) -> bool:
        return self.distance(a, b) <= 5

    def foe_squares(self, cr: Creature) -> List[Tuple[int, int]]:
        """Squares cr can't move through (living foes)."""
        return [q for f in self.enemies(cr) for q in self.cells(f)]

    def place_tokens(self) -> None:
        """Party on the west edge, foes to the east, 30-45 feet apart (20 in the dark),
        each on open ground."""
        gap = 20 if self.dark else 30 + 5 * (dice.die(4) - 1)
        pcs = [x for x in self.st.values() if x.side == "pc"]
        mons = [x for x in self.st.values() if x.side != "pc"]
        pcs.sort(key=lambda x: (not self.has_melee(x.c), -x.c.ac()))
        front = 2
        mcol = min(grid.W - 2, front + gap // 5)
        free = [(x, y) for x in range(grid.W) for y in range(grid.H)
                if self.terrain.walkable((x, y))]
        taken: set = set()

        def put(group, col, ahead_cost):
            for st in group:
                spots = [q for q in free if self.fits(st.c, q, taken)]
                if not spots:
                    st.pos = (col, grid.H // 2)
                    continue
                q = min(spots, key=lambda q: (ahead_cost(q[0] - col) * 2 + abs(q[1] - 4)
                                              + (1 if self.terrain.difficult(q) else 0),
                                              abs(q[1] - 4)))
                st.pos = q
                taken.update(self.cells(st.c, q))
        put(pcs, front, lambda dx: dx * 3 if dx > 0 else -dx)
        put(mons, mcol, lambda dx: -dx * 3 if dx < 0 else dx)

    def route(self, a: Creature, b: Creature):
        """Best square next to b for a to fight from: (square, cost in feet, path).
        Prefers flanking squares for a little extra walking. (None, INF, []) if no way."""
        bp, ap = self.s(b).pos, self.s(a).pos
        if self.near(a, b):
            return ap, 0, []
        blocked = self.foe_squares(a)
        costs, _ = self.terrain.costs(ap, blocked)
        occ = set(self.occupied(a))
        bcells = self.cells(b)
        if self.big(a):      # a big mover needs room for its whole body
            cands = [q for q in costs if self.fits(a, q, occ) and min(
                grid.dist(c1, c2) for c1 in self.cells(a, q) for c2 in bcells) == 5]
        else:
            cands = list({q for bc in bcells for q in grid.neighbors(bc)
                          if q in costs and q not in occ and q not in bcells})
        if not cands:
            return None, grid.INF, []
        mates = [self.s(o).pos for o in self.allies(a) if o is not a and self.is_engaged(o, b)]

        def flank(q):
            return any((q[0] - bp[0]) * (m[0] - bp[0]) + (q[1] - bp[1]) * (m[1] - bp[1]) < 0
                       for m in mates)
        near = min(costs[q] for q in cands)
        dest = min(cands, key=lambda q: (costs[q] - (15 if flank(q) else 0)
                                         if costs[q] - near <= 10 else 999, costs[q]))
        return dest, costs[dest], self.terrain.path(ap, dest, blocked)

    def melee_square(self, a: Creature, b: Creature) -> Tuple[int, int]:
        dest, _, _ = self.route(a, b)
        if dest is not None:
            return dest
        occ = set(self.occupied(a))
        bp = self.s(b).pos
        cands = [q for q in grid.neighbors(bp) if q not in occ and self.terrain.walkable(q)]
        return min(cands, key=lambda q: grid.dist(q, self.s(a).pos)) if cands else \
            self.s(a).pos

    def route_to_ally(self, a: Creature, b: Creature):
        """Nearest free square next to a friend: (square, cost, path)."""
        ap, bp = self.s(a).pos, self.s(b).pos
        if self.near(a, b):
            return ap, 0, []
        costs, _ = self.terrain.costs(ap, self.foe_squares(a))
        occ = set(self.occupied(a))
        cands = [q for q in grid.neighbors(bp) if q in costs and q not in occ]
        if not cands:
            return None, grid.INF, []
        dest = min(cands, key=costs.get)
        return dest, costs[dest], self.terrain.path(ap, dest, self.foe_squares(a))

    def feet_to_melee(self, a: Creature, b: Creature) -> int:
        if self.is_engaged(a, b) or self.near(a, b):
            return 0
        return self.route(a, b)[1]

    def clear_charge(self, a: Creature, b: Creature) -> bool:
        """A charge needs an open run: no difficult ground on the way."""
        dest, cost, path = self.route(a, b)
        return dest is not None and not any(self.terrain.difficult(q) for q in path)

    def walk_toward(self, mover: Creature, tgt: Creature, budget: int) -> Tuple[int, int]:
        """Where mover ends up spending at most budget feet heading for tgt."""
        here = self.s(mover).pos
        dest, cost, path = self.route(mover, tgt)
        occ = set(self.occupied(mover))
        if dest is not None and path:
            run = self.terrain.path_cost(here, path)
            ok = [q for q, cst in zip(path, run) if cst <= budget and q not in occ]
            return ok[-1] if ok else here
        # no way to get adjacent (blocked): get as close as possible
        costs, _ = self.terrain.costs(here, self.foe_squares(mover))
        opts = [q for q, cst in costs.items() if cst <= budget and q not in occ] + [here]
        tp = self.s(tgt).pos
        return min(opts, key=lambda q: (grid.dist(q, tp), costs.get(q, 0)))

    def advance(self, cr: Creature, tgt: Creature, single: bool = False) -> bool:
        """AI movement: close in if one move gets there (True: can still attack once),
        otherwise run (double move) toward the target."""
        need = self.feet_to_melee(cr, tgt)
        sp = self.speed_of(cr)
        if need <= sp:
            return self.close_in(cr, tgt)
        self.close_in(cr, tgt, budget=sp if single else 2 * sp)
        return False

    def clear_shot(self, a: Creature, b: Creature) -> bool:
        """Line of effect (walls block arrows and spells)."""
        return self.terrain.line_of_effect(self.s(a).pos, self.s(b).pos)

    def range_penalty(self, attacker: Creature, target: Creature, w: dict):
        """(-penalty, out_of_range) for a ranged weapon at this distance."""
        inc = w.get("range") or 0
        if not inc:
            return 0, False
        d = self.distance(attacker, target)
        n = max(0, (d - 1) // inc)
        limit = 5 if w.get("thrown") else 10
        return -2 * n, n >= limit

    def area_targets(self, caster: Creature, spell: str, aim,
                     shape: Optional[Tuple[str, int]] = None) -> List[Creature]:
        """Everyone inside the template. aim is a creature or a square."""
        kind, size = shape or grid.AREAS[spell]
        at = aim if isinstance(aim, tuple) else self.s(aim).pos
        sq = set(grid.area_squares(kind, size, self.s(caster).pos, at, self.terrain))
        return [x.c for x in self.st.values()
                if self.active(x.c) and any(q in sq for q in self.cells(x.c))
                and not (kind != "burst" and x.c is caster)]

    def _area_catch(self, p, spell, aim, cap):
        """(foes, allies) an area spell aimed here would affect."""
        side = self.s(p).side
        inside = self.area_targets(p, spell, aim)
        at = aim if isinstance(aim, tuple) else self.s(aim).pos
        foes = sorted([c_ for c_ in inside if self.s(c_).side != side],
                      key=lambda c_: grid.dist(self.s(c_).pos, at))[:cap]
        friends = [] if spell in grid.SELECTIVE else \
            [c_ for c_ in inside if self.s(c_).side == side]
        return foes, friends

    def pick_area(self, p, spell, foes, cap) -> Optional[List[Creature]]:
        """Aim an area spell on the grid; warns when friends would be caught."""
        ui = self.ui
        kind, size = grid.AREAS[spell]
        shape_txt = {"burst": f"{size}-ft-radius burst", "cone": f"{size}-ft cone",
                     "line": f"{size}-ft line"}[kind]
        aims: list = list(foes)
        if kind == "burst" and spell not in grid.SELECTIVE:
            best, best_score = None, 0
            for xx in range(grid.W):
                for yy in range(grid.H):
                    fo, fr = self._area_catch(p, spell, (xx, yy), cap)
                    score = len(fo) - 10 * len(fr)
                    if fo and score > best_score:
                        best, best_score = (xx, yy), score
            if best is not None:
                aims.insert(0, best)
        opts, results = [], []
        for a in aims:
            fo, fr = self._area_catch(p, spell, a, cap)
            if not fo:
                continue
            where = (f"the best spot (square {a[0]},{a[1]})" if isinstance(a, tuple)
                     else a.name)
            lab = f"Aim at {where}: hits {', '.join(f.name for f in fo)}"
            if fr:
                lab += c(f"; ALSO {', '.join('YOU' if f is p else f.name for f in fr)}",
                         "bred")
            opts.append(lab)
            results.append((fo, fr))
        if not opts:
            ui.bad("No foes can be caught in the area.")
            return None
        ui.out(f"{spell}: {shape_txt}.", ("dim",))
        i = 0 if len(opts) == 1 else ui.choose("Where do you aim it?", opts, allow_cancel=True)
        if i is None:
            return None
        fo, fr = results[i]
        if fr:
            ui.warn("WARNING: " + ", ".join("you" if f is p else f.name for f in fr) +
                    " will be caught too!")
            if not ui.confirm("Cast anyway?", False):
                return None
        return fo + fr

    def battle_tokens(self) -> List[dict]:
        """Who stands where, for the ASCII and web battle maps."""
        out, used = [], set()
        mi = 0
        for x in self.st.values():
            cr = x.c
            if cr.dead or x.fled or getattr(x, "ridden", False):
                continue
            if x.side == "pc":
                base = cr.name[:1].upper() if cr.is_pc else cr.name[:1].lower()
                lab = base
                n = 2
                while lab in used:
                    lab = f"{base}{n}"
                    n += 1
                kind = "pc" if cr.is_pc else "ally"
            else:
                mi += 1
                lab = str(mi) if mi < 10 else chr(ord("a") + mi - 10)
                kind = "foe"
            used.add(lab)
            hp = (f"{cr.hp}/{cr.max_hp()}" if x.side == "pc" else wound_word(cr))
            out.append({"x": x.pos[0], "y": x.pos[1], "label": lab, "name": cr.name,
                        "size": 2 if self.big(cr) else 1,
                        "side": kind, "hp": hp, "down": not cr.conscious,
                        "flying": self.airborne(cr) if x.side != "pc" else cr.has_tag("flying"),
                        "engaged": [self.st[u].c.name for u in x.engaged if u in self.st]})
        return out

    def battle_state(self) -> dict:
        order = []
        for x in self.order:
            if x.c.dead or x.fled or getattr(x, "ridden", False):
                continue
            order.append({"name": x.c.name, "side": "foe" if x.side != "pc" else
                          ("pc" if x.c.is_pc else "ally"),
                          "hp": f"{x.c.hp}/{x.c.max_hp()}" if x.side == "pc"
                          else wound_word(x.c), "down": not x.c.conscious})
        return {"w": grid.W, "h": grid.H, "round": self.round, "title": self.title,
                "order": order, "current": getattr(self, "current", ""),
                "dark": self.dark, "tokens": self.battle_tokens(),
                "terrain": [{"x": q[0], "y": q[1], "k": k} for q, k in self.terrain.cells.items()],
                "legend": [{"k": k, "name": grid.KINDS[k][1], "slow": grid.KINDS[k][5]}
                           for k in sorted(set(self.terrain.cells.values()),
                                           key=list(grid.KINDS).index)]}

    def sync_map(self, inline: bool = False) -> None:
        """Push token positions to a graphical client (the web page), if any."""
        if hasattr(self.ui, "battle"):
            self.ui.battle(self.battle_state(), inline)

    def show_map(self) -> None:
        if hasattr(self.ui, "battle"):
            self.sync_map(inline=True)
            return
        toks = self.battle_tokens()
        cells = {}
        for t in toks:
            lab = (t["label"] + " ")[:2]
            colr = {"pc": "bgreen", "ally": "green", "foe": "bred"}[t["side"]]
            for dx in range(t["size"]):
                for dy in range(t["size"]):
                    cells[(t["x"] + dx, t["y"] + dy)] = c(lab, colr) if not t["down"] \
                        else c(lab, "dim")
        legend = []
        for t in toks:
            extra = " (down)" if t["down"] else (" (flying)" if t["flying"] else "")
            legend.append(f"{t['label']}={t['name']}{extra}")
        lines = grid.render(cells, [], self.terrain)
        for ln in lines:
            self.ui.out("  " + ln, ("dim",) if ln is lines[0] else ())
        self.ui.out("  " + "   ".join(legend) + "   (each square is 5 ft)", ("dim",))
        if self.terrain.cells:
            self.ui.out("  " + "   ".join(self.terrain.legend()), ("dim",))

    def is_flat_footed(self, cr: Creature) -> bool:
        return self.s(cr).flat and not cr.has_uncanny_dodge()

    def has_melee(self, cr: Creature) -> bool:
        for w in cr.weapon_infos():
            if not w["ranged"] and (w.get("wielded") in ("main", "off") or w.get("natural")
                                    or not cr.is_pc):
                if cr.is_pc and w.get("wid") == "unarmed strike" and not cr.has_feat(
                        "Improved Unarmed Strike"):
                    continue
                return True
        return False

    def threatens(self, cr: Creature) -> bool:
        flat_ok = not self.s(cr).flat or cr.has_feat("Combat Reflexes")
        return self.active(cr) and cr.can_act() and flat_ok and self.has_melee(cr)

    def aoo_limit(self, cr: Creature) -> int:
        if cr.has_feat("Combat Reflexes"):
            return 1 + max(0, cr.mod("dex"))
        return 1

    def shooting_into_melee(self, shooter: Creature, target: Creature) -> bool:
        for ally in self.allies(shooter):
            if ally is not shooter and self.is_engaged(ally, target) and ally.conscious:
                return True
        return False

    def flanked(self, attacker: Creature, target: Creature) -> bool:
        if getattr(target, "has_improved_uncanny_dodge", lambda: False)():
            return False
        for ally in self.allies(attacker):
            if ally is attacker:
                continue
            if self.is_engaged(ally, target) and self.threatens(ally):
                tp, ap, mp = self.s(target).pos, self.s(attacker).pos, self.s(ally).pos
                if (ap[0] - tp[0]) * (mp[0] - tp[0]) + (ap[1] - tp[1]) * (mp[1] - tp[1]) < 0:
                    return True
        return False

    def best_melee(self, cr: Creature) -> Optional[dict]:
        ws = [w for w in cr.weapon_infos() if not w["ranged"]]
        if cr.is_pc:
            ws = [w for w in ws if w.get("wielded") == "main"] or \
                 [w for w in ws if w.get("wielded")] or ws
        if not ws:
            return None
        return max(ws, key=lambda w: sum(v for _, v, _ in cr.attack_components(w)))

    # ------------------------------------------------------------ output
    def show_field(self) -> None:
        ui = self.ui
        ui.sub(f"Round {self.round}")
        self.show_map()
        if hasattr(ui, "battle"):
            return      # the web page shows everyone's state on the map and the turn bar
        for p in self.party:
            st = self.s(p)
            eng = ", ".join(f.name for f in self.engaged_foes(p))
            fl = " (fled)" if st.fled else ""
            ui.out(f"  {c(short_status(p), 'bgreen' if p.conscious else 'bred')}{fl}"
                   + (f"  | melee: {eng}" if eng else ""))
        for comp in self.companions:
            if comp.dead or self.s(comp).fled:
                continue
            eng = ", ".join(f.name for f in self.engaged_foes(comp))
            role = "summoned" if getattr(comp, "summoned", False) else \
                f"{comp.owner.name}'s companion"
            ui.out(f"  {c(comp.name, 'green')} ({role}): HP {comp.hp}/"
                   f"{comp.max_hp()}  AC {comp.ac()}"
                   + (f" [{comp.status_word()}]" if comp.status_word() != "ok" else "")
                   + (f"  | melee: {eng}" if eng else ""))
        for m in self.monsters:
            if m.dead:
                continue
            st = self.s(m)
            if st.fled:
                continue
            cond = wound_word(m)
            sw = m.status_word()
            extra = f" [{sw}]" if sw not in ("ok",) else ""
            if self.airborne(m):
                extra += " [flying]"
            eng = ", ".join(f.name for f in self.engaged_foes(m))
            ui.out(f"  {c(m.name, 'bred')}: {cond}{extra}" + (f"  | melee: {eng}" if eng else ""))

    # ------------------------------------------------------------ main loop
    def run(self) -> str:
        ui = self.ui
        ui.header(self.title)
        for m in self.monsters:
            ui.out(f"  {m.name}: {m.block.get('desc', '')}", ("red",))
        if self.terrain.cells:
            ui.out(f"  The ground: {self.terrain.describe()}.", ("dim",))
        self.roll_initiative()
        self.start_auras()
        if self.surprised:
            aware = [x for x in self.order if id(x.c) not in self.surprised]
            if aware and len(aware) < len(self.order):
                ui.warn("SURPRISE ROUND! Only those who noticed the enemy may act "
                        "(one standard or move action).")
                self.show_map()
                self.round = 0
                for x in aware:
                    if self.check_end():
                        break
                    self.take_turn(x, surprise=True)
        while True:
            self.round += 1
            self.show_field()
            self.acted: set = set()
            while True:
                res = self.check_end()
                if res:
                    return self.finish(res)
                pending = [x for x in self.order if id(x) not in self.acted]
                if not pending:
                    break
                x = pending[0]
                self.acted.add(id(x))
                if not self.active(x.c):
                    continue
                self.take_turn(x)
            res = self.check_end()
            if res:
                return self.finish(res)

    def roll_initiative(self) -> None:
        ui = self.ui
        ui.sub("Initiative")
        for x in self.st.values():
            with dice.rolling(x.c, "initiative"):
                r = dice.d20()
            x.init = r + x.c.initiative()
            x.tiebreak = (x.c.initiative(), dice.d20())
            ui.roll(f"{x.c.name}: d20={r} {x.c.initiative():+d} = {x.init}")
        self.order = sorted(self.st.values(), key=lambda x: (x.init, x.tiebreak), reverse=True)
        ui.out("  Order: " + " > ".join(x.c.name for x in self.order))

    def check_end(self) -> Optional[str]:
        mons = [m for m in self.monsters if self.active(m)]
        live_mons = [m for m in mons if not m.helpless()]
        pcs = [p for p in self.party if not p.dead and not self.s(p).fled]
        able = [p for p in pcs if p.conscious]
        if not live_mons:
            return "victory"
        if not pcs and any(self.s(p).fled for p in self.party):
            return "fled"
        if not able:
            return "defeat"
        return None

    def finish(self, result: str) -> str:
        ui = self.ui
        if hasattr(ui, "battle"):
            ui.battle(None, False)
        if result == "victory":
            helpless = [m for m in self.monsters if self.active(m) and m.helpless()]
            for m in helpless:
                if m.nonlethal and m.nonlethal > max(0, m.hp) and m.hp > 0:
                    ui.out(f"{m.name} is out cold. The heroes tie it up and leave it.")
                    m.fled = True
                    self.s(m).fled = True
                    continue
                if m.get_effect("Regenerating"):
                    ui.out(f"{m.name} twitches, already healing. The heroes hack it apart "
                           f"and burn the pieces with torch and oil.")
                else:
                    ui.out(f"{m.name} lies helpless; the heroes finish it off.")
                m.dead = True
            ui.header("VICTORY!")
        elif result == "fled":
            ui.header("YOU ESCAPED")
        else:
            ui.header("DEFEAT")
        for m in self.monsters:
            if m.dead or self.s(m).fled:
                self.xp_monsters.append(m)
        # clean up combat-only conditions
        for comp in self.companions:
            comp.effects = [e for e in comp.effects if not (
                e.tags & {"prone", "grappled", "pinned", "stunned", "dazed", "entangled"})]
            if hasattr(comp, "owner") and not getattr(comp, "summoned", False):
                from .companions import sync_companion
                sync_companion(comp.owner)
        for p in self.party:
            if p.get_effect("Petrified") and result == "victory":
                p.remove_effect("Petrified")
                ui.good(f"The beast's fresh blood, smeared on the statue, turns {p.name} "
                        f"back to flesh.")
            p.remove_effect("Swallowed")
            self.dismount(p, msg=False)
            for e in list(p.effects):
                if e.tags & {"prone", "charging", "total_defense", "fighting_defensively",
                             "_spiritual_weapon", "_sphere", "_stun_primed", "_smite",
                             "stunned", "dazed", "entangled", "frightened", "grappled",
                             "pinned"} \
                        or e.name in ("Dazed", "Turned", "Aura of Courage", "In the dark") \
                        or e.name.endswith(" balks") \
                        or e.name.startswith("Terror ("):
                    p.effects.remove(e)
            st = self.s(p)
            for ammo, n in st.spent_ammo.items():
                back = n // 2
                if back and result == "victory":
                    p.add_item(ammo, back)
                    ui.out(f"{p.name} recovers {back} {ammo}.")
        return result

    # ------------------------------------------------------------ turns
    def start_of_turn(self, x: CState) -> bool:
        """Handle ongoing effects. Returns True if the creature can act."""
        cr = x.c
        ui = self.ui
        x.flat = False
        x.aoo_used = 0
        x.std = x.move = True
        x.full_used = False
        x.moved = False
        x.cleave_used = False
        x.deflect_used = False
        x.mc_used = False
        x.stepped = False
        x.quickened = False
        if getattr(cr, "summoned", False) and not cr.get_effect("Summoned"):
            x.fled = True
            ui.out(f"{cr.name} fades away as the summoning ends.", ("dim",))
            return False
        if x.readied:
            x.readied = None
            ui.out(f"{cr.name}'s readied action lapses.", ("dim",))
        self.check_grapple(cr)
        if x.side == "pc" and cr.conscious:
            self.gaze_check(x)
        # dying
        if cr.is_pc and cr.hp < 0 and not cr.dead:
            if cr.stable:
                return False
            r = dice.percent()
            if r <= 10:
                cr.stable = True
                ui.good(f"{cr.name} stabilizes (d% {r}).")
            else:
                cr.damage += 1
                cr.check_death()
                ui.bad(f"{cr.name} is dying... loses 1 hp ({cr.hp})." if not cr.dead
                       else f"{cr.name} has died.")
            return False
        # damage over time
        for e in list(cr.effects):
            if "_dot" in e.tags:
                r = dice.roll(e.data["dot"])
                ui.out(f"{cr.name} suffers from {e.name}:")
                deal_damage(ui, cr, r.total, e.data.get("dtype", "acid"), self)
                if not self.active(cr):
                    return False
        # regeneration
        if getattr(cr, "regenerate", None):
            was_down = cr.get_effect("Regenerating") is not None
            healed = cr.regenerate()
            if healed:
                ui.warn(f"{cr.name}'s wounds knit closed (regenerates {healed})."
                        + (" It lurches back to its feet!" if was_down
                           and not cr.get_effect("Regenerating") else ""))
        # spiritual weapon / flaming sphere
        if cr.get_effect("Spiritual Weapon"):
            self.spiritual_weapon_attack(cr)
        if cr.get_effect("Mordenkainen's Sword"):
            self.spiritual_weapon_attack(cr, "Mordenkainen's Sword")
        if cr.get_effect("Flaming Sphere"):
            self.flaming_sphere_attack(cr)
        can = cr.can_act()
        reason = cr.status_word()
        for msg in cr.tick(1):
            ui.out(f"  {msg}", ("dim",))
        # save each round (hold person)
        for e in list(cr.effects):
            sv = e.data.get("save_each_round")
            if sv:
                kind, dc, tags = sv
                if saving_throw(ui, cr, kind, dc, tags, e.name):
                    cr.effects.remove(e)
                    ui.good(f"{cr.name} breaks free of {e.name}!")
        if not can:
            ui.out(f"{cr.name} cannot act ({reason}).", ("dim",))
        return can

    def take_turn(self, x: CState, surprise: bool = False) -> None:
        x.provoked_by = set()
        self.current = x.c.name
        self.sync_map()
        if x.delayed:
            x.delayed = False   # coming back after delaying: start-of-turn already done
            x.std = x.move = True
            x.moved = False
        elif not self.start_of_turn(x):
            return
        x.surprise = surprise
        if x.side == "pc" and not x.c.is_pc:
            self.companion_turn(x, surprise)
        elif x.side == "pc":
            self.pc_turn(x, surprise)
        else:
            self.monster_turn(x, surprise)

    # ------------------------------------------------------------ attacks
    def make_attack(self, attacker: Creature, target: Creature, w: dict, bab: int,
                    situational: Sequence[Tuple[str, int, str]] = (), offhand=False,
                    twf=False, aoo=False, power: int = 0, extra_damage: int = 0) -> bool:
        """Resolve one attack roll. Returns True on hit."""
        with dice.rolling(attacker, f"{w.get('name', 'attack')} vs {target.name}"):
            return self._make_attack(attacker, target, w, bab, situational, offhand, twf,
                                     aoo, power, extra_damage)

    def _make_attack(self, attacker: Creature, target: Creature, w: dict, bab: int,
                     situational: Sequence[Tuple[str, int, str]] = (), offhand=False,
                     twf=False, aoo=False, power: int = 0, extra_damage: int = 0) -> bool:
        ui = self.ui
        if w.get("natural") is False and offhand:
            w = dict(w, _offhand_light=w.get("light"))
        sit = list(situational)
        ranged = w.get("ranged", False)
        if attacker.get_effect("Subduing") and not w.get("nonlethal") and not w.get("natural") \
                and not (w.get("wid") == "unarmed strike"
                         and attacker.has_feat("Improved Unarmed Strike")):
            sit.append(("untyped", -4, "subduing"))
        if not ranged:
            if attacker.get_effect("Mounted") and not target.get_effect("Mounted") and \
                    rules.SIZES.index(target.size) <= rules.SIZES.index("medium"):
                sit.append(("untyped", 1, "mounted (higher ground)"))
            if self.flanked(attacker, target):
                sit.append(("untyped", 2, "flanking"))
            if target.helpless():
                sit.append(("untyped", 4, "vs helpless"))
        else:
            if self.shooting_into_melee(attacker, target) and not attacker.has_feat("Precise Shot"):
                sit.append(("untyped", -4, "firing into melee"))
            if target.uid in self.st and attacker.uid in self.st:
                between = set(self.terrain.line(self.s(attacker).pos, self.s(target).pos))
                if self.terrain.cover(self.s(attacker).pos, self.s(target).pos):
                    sit.append(("untyped", -4, "target behind cover"))
                elif not attacker.has_feat("Improved Precise Shot") and any(
                        any(q in between for q in self.cells(o.c)) and not o.c.dead
                        and not o.fled
                        and o.c is not attacker and o.c is not target and o.c.conscious
                        for o in self.st.values()):
                    sit.append(("untyped", -4, "someone in the way (cover)"))
                pen, _ = self.range_penalty(attacker, target, w)
                if pen:
                    sit.append(("untyped", pen, f"range {self.distance(attacker, target)} ft"))
            if target.helpless():
                pass
        comps = attacker.attack_components(w, bab=bab, target=target, offhand=offhand, twf=twf,
                                           power=power, situational=sit)
        consume_one_shot(attacker, "attack")
        bonus = sum(v for _, v, _ in comps)
        feint = target.get_effect("Feinted")
        feinted = bool(feint and feint.data.get("by") == attacker.uid and not ranged)
        if feinted:
            target.effects.remove(feint)
        flat = self.is_flat_footed(target) or target.helpless() or feinted or (
            target.has_tag("grappled") and self.grapple_partner(target) is not attacker)
        ac = target.ac("flat" if flat else "normal", attacker=attacker, ranged=ranged)
        if w.get("touch"):   # incorporeal touch ignores armor
            ac = target.ac("touch", attacker=attacker, ranged=ranged)
            if flat:
                ac -= max(0, target.mod("dex"))
        roll = dice.d20()
        total = roll + bonus
        hit = roll == 20 or (roll != 1 and total >= ac)
        if hit and not ranged and target.get_effect("Mounted") and target.uid in self.st \
                and target.has_feat("Mounted Combat") and target.conscious \
                and not getattr(self.s(target), "mc_used", False):
            self.s(target).mc_used = True
            with dice.rolling(target, "Ride (Mounted Combat)"):
                rr = dice.d20()
            ride = rr + target.skill_total("Ride")
            ui.roll(f"{target.name} Ride: d20={rr} {target.skill_total('Ride'):+d} = {ride} "
                    f"vs the attack roll {total}")
            if ride > total:
                hit = False
                ui.good(f"  {target.name} swerves the mount and the blow goes wide "
                        f"(Mounted Combat).")
        label = "AoO! " if aoo else ""
        if feinted:
            sit.append(("untyped", 0, "feinted: no Dex to AC"))
        sitnote = ", ".join(s for _, v, s in sit if v or "feint" in s)
        if attacker.remove_effect("Invisibility"):
            ui.out(f"{attacker.name} flickers into view as they strike!")
        ui.out(f"{label}{attacker.name} attacks {target.name} with {w['name']}: "
               f"d20={roll} {bonus:+d} = {total} vs AC {ac}"
               + (f" ({sitnote})" if sitnote else "") + " -> "
               + (c("HIT", "bgreen") if hit else c("miss", "dim")))
        if not hit:
            attacker.remove_effect("Stunning Fist")
            return False
        # deflect arrows
        if ranged and not w.get("ray") and target.has_feat("Deflect Arrows") \
                and target.uid in self.st and not self.s(target).deflect_used \
                and not self.is_flat_footed(target) and target.conscious:
            self.s(target).deflect_used = True
            ui.good(f"  {target.name} snatches the missile out of the air (Deflect Arrows)!")
            return False
        # incorporeal targets
        if target.incorporeal and not w.get("touch"):
            magical = attacker.weapon_enhancement(w) > 0 or w.get("magic_force") or (
                w.get("wid") == "unarmed strike" and
                getattr(attacker, "class_level", lambda c_: 0)("monk") >= 4)
            if not magical:
                ui.out(f"  ...the {w['name'].lower()} passes straight through "
                       f"{target.name}! (Only magic weapons can hurt it.)")
                attacker.remove_effect("Stunning Fist")
                return False
            if dice.percent() <= 50:
                ui.out("  ...the blow catches only shadow (50% incorporeal miss chance).")
                attacker.remove_effect("Stunning Fist")
                return False
        # concealment
        conc = target.bonus("concealment")
        if attacker.has_tag("blinded"):
            conc = max(conc, 50)   # can't see the target: total concealment
        if ranged:
            conc = max(conc, target.bonus("concealment_ranged"))
            if attacker.has_feat("Improved Precise Shot") and conc < 100:
                conc = 0
        if conc:
            r = dice.percent()
            if r <= conc:
                if attacker.has_feat("Blind-Fight") and dice.percent() > conc:
                    ui.out("  (Blind-Fight reroll succeeds!)")
                else:
                    ui.out(f"  ...but the blow passes through a blurred image (d% {r} <= "
                           f"{conc}%).")
                    attacker.remove_effect("Stunning Fist")
                    return False
        crit = False
        crange = w.get("crit_range", 20)
        if attacker.has_feat(f"Improved Critical ({w.get('wid')})"):
            crange = 21 - 2 * (21 - crange)
        threat = roll >= crange or roll == 20
        if threat and not target.crit_immune():
            cr = dice.d20()
            ctot = cr + bonus
            crit = cr != 1 and (cr == 20 or ctot >= ac)
            ui.roll(f"Critical threat! Confirm: d20={cr} {bonus:+d} = {ctot} -> "
                    f"{'CRITICAL HIT!' if crit else 'not confirmed'}")
        elif threat:
            ui.roll(f"(threat, but {target.name} is immune to critical hits)")
        self.apply_hit(attacker, target, w, crit, offhand, power, flat, extra_damage)
        return True

    def apply_hit(self, attacker, target, w, crit, offhand, power, target_flat,
                  extra_damage: int = 0):
        ui = self.ui
        dice_expr, comps = attacker.damage_profile(w, target, offhand=offhand, power=power)
        static = sum(v for _, v, _ in comps) + extra_damage
        mult = (w.get("crit_mult", 2) if crit else 1) + getattr(self, "charge_mult", 1) - 1
        total = 0
        rolls = []
        for _ in range(mult):
            r = dice.roll(dice_expr)
            rolls.append(r.total)
            total += r.total + static
        total = max(1, total)
        detail = f"{dice_expr}{static:+d}" if static else dice_expr
        ui.roll(f"Damage: {detail}{' x' + str(mult) if mult > 1 else ''} -> {rolls} = {total}")
        # sneak attack
        sa = attacker.sneak_attack_dice()
        if sa and not target.sneak_immune():
            deny = target_flat or target.helpless()
            flank = (not w.get("ranged")) and self.flanked(attacker, target)
            if deny or flank:
                r = dice.roll(f"{sa}d6")
                ui.roll(f"Sneak attack! {r.detail()}")
                total += r.total
                da = attacker.get_effect("Death attack ready")
                if da and da.data["target"] == target.uid and not w.get("ranged"):
                    attacker.remove_effect("Death attack ready")
                    dc = 10 + attacker.class_level("assassin") + attacker.mod("int")
                    if target.is_living() and "death" not in target.immunities() and \
                            not saving_throw(ui, target, "fort", dc, ["death"], "death attack"):
                        ui.bad(f"  DEATH ATTACK! {target.name} drops, dead.")
                        target.damage = target.max_hp() + 10
                        target.dead = True
                        self.after_damage(target)
                        return
                if "crippling strike" in getattr(attacker, "rogue_specials", []) and \
                        target.ability("str") is not None:
                    target.ability_damage["str"] = target.ability_damage.get("str", 0) + 2
                    ui.out(f"  Crippling strike: {target.name} takes 2 Strength damage.")
        special = w.get("special") or {}
        nonlethal = (w.get("nonlethal") and not attacker.has_feat("Improved Unarmed Strike")) \
            or attacker.get_effect("Subduing") is not None
        if nonlethal and not w.get("natural"):
            if not target.is_living():
                ui.out(f"  {target.name} doesn't feel nonlethal blows.")
                return
            target.take_nonlethal(total)
            ui.out(f"  {target.name} takes {total} nonlethal damage.")
            if target.has_tag("unconscious") and not target.dead:
                ui.warn(f"  {target.name} is knocked out cold!")
                if target.get_effect("Grappling"):
                    self.end_grapple(target)
            return
        if special.get("no_damage"):
            total = 0
        du = getattr(attacker, "class_level", lambda c_: 0)("duelist")
        if du >= 5 and "P" in w.get("dtype", "") and not w.get("two_handed") \
                and not w.get("ranged") and not target.crit_immune():
            r = dice.roll("2d6" if du >= 10 else "1d6")
            ui.roll(f"Precise strike: {r.detail()}")
            total += r.total
        dmg_type = "" if w.get("magic_force") else w.get("dtype", "B")
        if dmg_type and (attacker.weapon_enhancement(w) > 0 or (
                w.get("wid") == "unarmed strike" and
                getattr(attacker, "class_level", lambda c: 0)("monk") >= 4)):
            dmg_type += "*"   # magic weapon: overcomes DR x/magic
        if total and target.is_pc and target.hp - total <= 0 and \
                target.uses_left("defensive_roll") and not self.is_flat_footed(target):
            target.spend("defensive_roll")
            if saving_throw(ui, target, "ref", total, [], "defensive roll"):
                total //= 2
                ui.good(f"  {target.name} rolls with the blow and takes only half!")
        if total:
            deal_damage(ui, target, total, dmg_type, self, magic=False)
        fs = target.get_effect("Fire Shield")
        if fs and not w.get("ranged") and not attacker.dead and not w.get("reach"):
            r = dice.roll(fs.data["dmg"])
            ui.out(f"  {target.name}'s fire shield scorches {attacker.name}!")
            deal_damage(ui, attacker, r.total, "fire", self)
        if attacker.remove_effect("Stunning Fist") and not target.dead:
            if "stun" in target.immunities() or not target.is_living():
                ui.out(f"  {target.name} can't be stunned.")
            else:
                lvl = getattr(attacker, "level", attacker.hit_dice())
                dc = 10 + lvl // 2 + attacker.mod("wis")
                if not saving_throw(ui, target, "fort", dc, ["stun"], "Stunning Fist"):
                    target.add_effect(Effect("Stunned", 1, tags=["stunned"]))
                    ui.warn(f"  {target.name} is STUNNED!")
        extra = special.get("extra_damage")
        if extra and not target.dead:
            r = dice.roll(extra[0])
            deal_damage(ui, target, r.total, extra[1], self)
        if not target.dead and target.is_living():
            if special.get("disease") and "disease" in target.immunities():
                ui.out(f"  {target.name} is immune to disease.")
            elif special.get("disease"):
                dz = special["disease"]
                if not saving_throw(ui, target, "fort", dz["dc"], ["disease"], dz["name"]):
                    if target.is_pc and not any(a["name"] == dz["name"] for a in target.afflictions):
                        target.afflictions.append(dict(dz, successes=0))
                        ui.warn(f"  {target.name} has contracted {dz['name']}!")
            if special.get("poison") and "poison" in target.immunities():
                ui.out(f"  {target.name} is immune to poison.")
            elif special.get("poison") and target.ctype not in ("undead",):
                pz = special["poison"]
                if not saving_throw(ui, target, "fort", pz["dc"], ["poison"], pz["name"]):
                    amt = dice.roll(pz["damage"]).total
                    ab = pz["ability"]
                    target.ability_damage[ab] = target.ability_damage.get(ab, 0) + amt
                    ui.bad(f"  {target.name} takes {amt} {ab.upper()} damage from {pz['name']}!")
            ad = special.get("ability_damage")
            if ad and target.conscious:
                if ad.get("nosave") or not saving_throw(ui, target, "fort", ad["dc"], [],
                                                         ad["name"]):
                    amt = dice.roll(ad["damage"]).total
                    target.ability_damage[ad["ability"]] = \
                        target.ability_damage.get(ad["ability"], 0) + amt
                    ui.bad(f"  {target.name} takes {amt} {ad['ability'].upper()} damage from "
                           f"{ad['name']}!")
            if special.get("drain") and not target.dead:
                drain_level(ui, target, special["drain"]["dc"])
                self.after_damage(target)
            if special.get("grab") and not target.dead and not target.has_tag("grappled") \
                    and not attacker.has_tag("grappled") and target.uid in self.st \
                    and rules.SIZES.index(target.size) <= rules.SIZES.index(attacker.size):
                ui.warn(f"  {attacker.name} tries to seize {target.name}!")
                if self.grapple_check(attacker, target, "Improved grab"):
                    attacker.add_effect(Effect("Grappling", None, tags=["grappled"],
                                               data={"with": target.uid, "holder": True}))
                    target.add_effect(Effect("Grappling", None, tags=["grappled"],
                                             data={"with": attacker.uid}))
                    ui.bad(f"  {target.name} is caught in {attacker.name}'s crushing grip!")
            if special.get("petrify") and target.conscious and target.is_living() \
                    and not target.get_effect("Petrified"):
                if not saving_throw(ui, target, "fort", special["petrify"]["dc"], [],
                                    "petrification"):
                    target.add_effect(Effect("Petrified", None,
                                             tags=["paralyzed", "petrified"], hidden=False))
                    ui.bad(f"  {target.name} stiffens, greys, and turns to STONE!")
                    self.after_damage(target)
            if special.get("paralysis") and target.conscious:
                elf = getattr(target, "race", "") == "elf"
                if elf:
                    ui.out(f"  {target.name}'s elven blood resists the ghoul's paralysis.")
                elif "paralysis" in target.immunities():
                    ui.out(f"  {target.name} shrugs off the paralysis.")
                elif not saving_throw(ui, target, "fort", special["paralysis"]["dc"],
                                      ["paralysis"], "paralysis"):
                    d = dice.roll(special["paralysis"]["duration"]).total
                    target.add_effect(Effect("Ghoul paralysis", d, tags=["paralyzed"]))
                    ui.bad(f"  {target.name} is PARALYZED for {d} rounds!")
            if special.get("trip") and target.conscious and not target.has_tag("prone"):
                self.trip(attacker, target)
        if target.dead or (target.is_pc and target.hp < 0):
            self.try_cleave(attacker, w)

    def try_cleave(self, attacker, w):
        st = self.s(attacker)
        if w.get("ranged") or not attacker.has_feat("Cleave"):
            return
        if st.cleave_used and not attacker.has_feat("Great Cleave"):
            return
        foes = [f for f in self.engaged_foes(attacker) if not f.helpless()]
        if not foes:
            return
        st.cleave_used = True
        tgt = foes[0]
        if attacker.is_pc and len(foes) > 1:
            tgt = foes[self.ui.choose("Cleave! Extra attack against", [f.name for f in foes])]
        self.ui.good(f"{attacker.name} cleaves through to {tgt.name}!")
        self.make_attack(attacker, tgt, w, attacker.bab(),
                         power=getattr(attacker, "power_attack", 0))

    def after_damage(self, target: Creature) -> None:
        if target.get_effect("Mounted") and not target.conscious:
            self.ui.bad(f"  {target.name} topples from the saddle!")
            self.dismount(target, msg=False)
        ui = self.ui
        if target.dead or target.helpless():
            if target.get_effect("Grappling"):
                self.end_grapple(target)
        if not target.dead and target.get_effect("Regenerating") and target.hp <= 0:
            ui.warn(f"  {target.name} collapses... but its flesh is already crawling back "
                    f"together. Fire or acid will finish it.")
        if target.dead:
            ui.bad(f"  {target.name} is {'slain' if not target.is_pc else 'DEAD'}!")
            self.disengage_all(target)
        elif target.is_pc and target.hp < 0:
            ui.bad(f"  {target.name} falls unconscious and is dying!")
        elif target.is_pc and target.hp == 0:
            ui.warn(f"  {target.name} is disabled (0 hp): only one action per turn.")

    def provoke(self, mover: Creature, reason: str, movement: bool = False) -> int:
        """Engaged enemies get attacks of opportunity. Returns damage taken."""
        before = mover.damage
        for foe in self.engaged_foes(mover):
            if movement:
                self.s(mover).provoked_by = set(getattr(self.s(mover), "provoked_by", ())) | {
                    foe.uid}
            self.aoo_from(foe, mover, reason, movement)
            if not mover.conscious:
                break
        return mover.damage - before

    def spiritual_weapon_attack(self, caster: Creature, name: str = "Spiritual Weapon") -> None:
        e = caster.get_effect(name)
        if not e:
            return
        tgt = None
        for x in self.st.values():
            if x.c.uid == e.data["target"] and self.active(x.c):
                tgt = x.c
        if tgt is None:
            foes = [f for f in self.enemies(caster) if not f.dead]
            if not foes:
                return
            tgt = foes[0]
            e.data["target"] = tgt.uid
        roll = dice.d20()
        bonus = e.data["bonus"]
        ac = tgt.ac(attacker=caster)
        hit = roll == 20 or (roll != 1 and roll + bonus >= ac)
        self.ui.out(f"{caster.name}'s {name.lower()} strikes at {tgt.name}: d20={roll}"
                    f"{bonus:+d} = {roll + bonus} vs AC {ac} -> {'HIT' if hit else 'miss'}")
        if hit:
            r = dice.roll(e.data["damage"])
            deal_damage(self.ui, tgt, r.total, "force", self)

    # ------------------------------------------------------------ positioning helpers
    def has_reach(self, cr: Creature) -> bool:
        if cr.size in ("large", "huge"):
            return True
        if not cr.is_pc:
            return bool(getattr(cr, "block", {}).get("reach"))
        main = cr.equipped("main") if hasattr(cr, "equipped") else None
        if main and not cr.wild_form():
            return bool(item_data(main).get("reach"))
        return False

    def reach_weapon(self, cr: Creature) -> Optional[dict]:
        ws = [w for w in cr.weapon_infos() if not w["ranged"] and (w.get("reach") or
                                                                     cr.size in ("large",
                                                                                 "huge"))]
        if cr.is_pc:
            ws = [w for w in ws if w.get("wielded") == "main"]
        return ws[0] if ws else None

    def aoo_from(self, foe: Creature, mover: Creature, reason: str, movement: bool = False,
                 w: Optional[dict] = None) -> int:
        """One creature takes an attack of opportunity. Returns damage dealt."""
        st = self.s(foe)
        if not self.threatens(foe) or st.aoo_used >= self.aoo_limit(foe) or mover.dead:
            return 0
        w = w or self.best_melee(foe)
        if not w:
            return 0
        before = mover.damage
        st.aoo_used += 1
        self.ui.warn(f"{mover.name} {reason}, provoking an attack of opportunity from "
                     f"{foe.name}!")
        sit = []
        if movement and mover.has_feat("Mobility"):
            sit.append(("untyped", -4, "Mobility"))
        self.make_attack(foe, mover, w, foe.bab(), situational=sit, aoo=True)
        return mover.damage - before

    def close_in(self, mover: Creature, tgt: Creature, budget: Optional[int] = None) -> bool:
        """Mover walks toward tgt (up to budget feet, default its speed) and steps into
        melee if it gets there. Reach and readied actions may strike first.
        Returns False if the mover fell short or was dropped on the way in."""
        self.fell_short = False
        if not self.is_engaged(mover, tgt):
            budget = self.speed_of(mover) if budget is None else budget
            dest, cost, _ = self.route(mover, tgt)
            start = self.s(mover).pos
            if dest is None or cost > budget:
                end = self.walk_toward(mover, tgt, budget)
                self.travel(mover, self.terrain.path(start, end, self.foe_squares(mover)))
                end = self.s(mover).pos
                self.fell_short = True
                if end == start:
                    self.ui.out(f"{mover.name} can't find a way through to {tgt.name}.")
                else:
                    slow = " through rough ground" if any(
                        self.terrain.difficult(q) for q in self.terrain.line(start, end) +
                        [end]) else ""
                    self.ui.out(f"{mover.name} moves toward {tgt.name}{slow} "
                                f"(now {self.distance(mover, tgt)} ft away).")
                return False
            path = self.terrain.path(start, dest, self.foe_squares(mover)) \
                if dest != start else []
            if not self.travel(mover, path) or self.s(mover).pos != dest:
                return False
        if not self.active(mover) or not mover.conscious:
            return False
        self.engage(mover, tgt)
        self.trigger_readied(mover, tgt)
        return self.active(mover) and mover.conscious

    def threat_at(self, foe: Creature, sq) -> bool:
        """Does foe threaten this square? (5 ft; 10 ft for big creatures; exactly 10 ft
        for a reach weapon.) Walls block."""
        d = min(grid.dist(q, sq) for q in self.cells(foe))
        if foe.size in ("large", "huge") or getattr(foe, "block", {}).get("reach"):
            ok = d <= 10
        elif self.has_reach(foe):
            ok = d == 10
        else:
            ok = d <= 5
        return ok and d > 0 and self.terrain.line_of_effect(self.s(foe).pos, sq)

    def try_tumble(self, mover: Creature, foes: int) -> bool:
        """Tumble (trained only, DC 15, +2 per extra foe) to slip past without provoking."""
        can = getattr(mover, "can_use_skill", None)
        if not can or not can("Tumble") or mover.has_tag("prone"):
            return False
        a = getattr(mover, "armor_data", lambda: None)()
        if a and a.get("category") in ("medium", "heavy"):
            return False
        dc = 15 + 2 * max(0, foes - 1)
        with dice.rolling(mover, "Tumble"):
            r = dice.d20()
        tot = r + mover.skill_total("Tumble")
        ok = tot >= dc
        self.ui.roll(f"{mover.name} Tumble: d20={r} {mover.skill_total('Tumble'):+d} = {tot} "
                     f"vs DC {dc} -> {'tumbles past safely' if ok else 'failure'}")
        return ok

    def travel(self, mover: Creature, path) -> bool:
        """Walk a path square by square. Leaving a square a foe threatens provokes an
        attack of opportunity (once per foe per move; Tumble can avoid them).
        Returns False if the mover was dropped on the way."""
        x = self.s(mover)
        done = set(getattr(x, "provoked_by", ()))
        tumbled = None
        cur = x.pos
        for nxt in path:
            threats = [f for f in self.enemies(mover) if f.uid not in done
                       and self.threatens(f) and self.s(f).aoo_used < self.aoo_limit(f)
                       and self.threat_at(f, cur)]
            if threats:
                if tumbled is None:
                    tumbled = self.try_tumble(mover, len(threats))
                for f in threats:
                    done.add(f.uid)
                    if tumbled:
                        continue
                    w = self.reach_weapon(f) if grid.dist(self.s(f).pos, cur) > 5 else None
                    self.aoo_from(f, mover, f"moves through {f.name}'s reach",
                                  movement=True, w=w)
                    if not self.active(mover) or not mover.conscious:
                        x.provoked_by = done
                        self.sync_engagement(mover)
                        return False
            cur = nxt
            x.pos = cur
        x.provoked_by = done
        self.sync_engagement(mover)
        return True

    def sync_engagement(self, mover: Creature) -> None:
        """After moving: you're in melee with exactly the foes next to you."""
        x = self.s(mover)
        if mover.has_tag("grappled"):
            return
        for u in list(x.engaged):
            if u in self.st and not self.near(mover, self.st[u].c):
                x.engaged.discard(u)
                self.st[u].engaged.discard(mover.uid)
        for f in self.enemies(mover):
            if self.near(mover, f) and not f.dead \
                    and not self.airborne(f) and mover.conscious:
                x.engaged.add(f.uid)
                self.s(f).engaged.add(mover.uid)

    def trigger_readied(self, mover: Creature, tgt: Creature) -> None:
        for x in list(self.st.values()):
            r = x.readied
            if not r or r.get("counter") or x.side == self.s(mover).side \
                    or not self.active(x.c) \
                    or not x.c.can_act() or mover.dead:
                continue
            w = r["w"]
            if not w["ranged"] and x.c is not tgt:
                continue
            x.readied = None
            self.ui.warn(f"{x.c.name}'s readied attack triggers as {mover.name} closes in!")
            if w["ranged"] and not self._spend_ammo(x.c, w):
                continue
            self.make_attack(x.c, mover, w, x.c.bab(),
                             power=getattr(x.c, "power_attack", 0) if not w["ranged"] else 0)

    # ------------------------------------------------------------ grappling
    def grapple_partner(self, cr: Creature) -> Optional[Creature]:
        e = cr.get_effect("Grappling")
        if not e:
            return None
        for x in self.st.values():
            if x.c.uid == e.data.get("with"):
                return x.c
        return None

    def end_grapple(self, cr: Creature, msg: bool = True) -> None:
        partner = self.grapple_partner(cr)
        cr.remove_effect("Grappling")
        cr.remove_effect("Pinned")
        if cr.get_effect("Swallowed"):
            cr.remove_effect("Swallowed")
            self.ui.good(f"{cr.name} tears free of the beast's gullet!")
        if partner is not None:
            if partner.get_effect("Swallowed"):
                partner.remove_effect("Swallowed")
                self.ui.good(f"{partner.name} is cut free of the carcass.")
            partner.remove_effect("Grappling")
            partner.remove_effect("Pinned")
            if msg:
                self.ui.out(f"{cr.name} and {partner.name} are no longer grappling.")

    def check_grapple(self, cr: Creature) -> None:
        if cr.get_effect("Grappling"):
            partner = self.grapple_partner(cr)
            if partner is None or not self.active(partner) or partner.helpless():
                self.end_grapple(cr)

    def grapple_check(self, a: Creature, d: Creature, label: str) -> bool:
        ra, rd = dice.d20(), dice.d20()
        ba = a.grapple() + (4 if a.has_feat("Improved Grapple") else 0)
        bd = d.grapple() + (4 if d.has_feat("Improved Grapple") else 0)
        win = ra + ba > rd + bd or (ra + ba == rd + bd and ba >= bd)
        self.ui.roll(f"{label}: {a.name} d20={ra}{ba:+d} = {ra + ba} vs {d.name} "
                     f"d20={rd}{bd:+d} = {rd + bd} -> {'success' if win else 'fails'}")
        return win

    def unarmed_damage(self, a: Creature, d: Creature) -> None:
        w = next((w for w in a.weapon_infos() if w.get("natural") or
                  w.get("wid") == "unarmed strike"), None)
        if w is None:
            from .creature import weapon_info_from_entry
            from .data.items import make_item
            w = weapon_info_from_entry(make_item("unarmed strike"), a.size)
        self.apply_hit(a, d, w, False, False, 0, False)

    def flaming_sphere_attack(self, caster: Creature) -> None:
        e = caster.get_effect("Flaming Sphere")
        if not e:
            return
        tgt = next((x.c for x in self.st.values() if x.c.uid == e.data["target"]
                    and self.active(x.c)), None)
        if tgt is None:
            foes = [f for f in self.enemies(caster) if not f.dead]
            if not foes:
                return
            tgt = foes[0]
            e.data["target"] = tgt.uid
        self.ui.out(f"{caster.name}'s flaming sphere rolls over {tgt.name}!")
        if saving_throw(self.ui, tgt, "ref", e.data["dc"], e.data["stags"]):
            self.ui.out(f"  {tgt.name} leaps aside.")
            return
        r = dice.roll("2d6")
        self.ui.roll(r.detail())
        deal_damage(self.ui, tgt, r.total, "fire", self)


def award_xp(ui, party, monsters, party_level: int) -> int:
    alive = [p for p in party if not p.dead]
    if not alive or not monsters:
        return 0
    total = sum(rules.xp_award(party_level, m.cr) for m in monsters)
    each = total // len(alive)
    for p in alive:
        pen = p.xp_penalty() if hasattr(p, "xp_penalty") else 0
        p.xp += int(each * (1 - pen))
        if pen:
            ui.warn(f"{p.name} earns only {int(each * (1 - pen))} XP (uneven multiclass "
                    f"levels: -{int(pen * 100)}%).")
    ui.good(f"Each surviving hero earns {each} XP.")
    for p in alive:
        if p.can_level_up():
            ui.warn(f"{p.name} has enough experience to reach level {p.level + 1}! "
                    f"(Rest or use 'level up' from the menu.)")
    return each
