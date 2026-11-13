"""How monsters, companions and summoned creatures act, and monster special powers."""

from __future__ import annotations

from typing import List

from . import dice, grid, rules
from .creature import Creature
from .data.spells import SPELLS
from .effects import Effect
from .data.monsters import MONSTERS
from .magic import cast_spell, deal_damage, saving_throw
from .ui import c

from .combat_base import CState, wound_word


class MonstersMixin:
    # ------------------------------------------------------------ monster AI
    def monster_turn(self, x: CState, surprise: bool) -> None:
        m = x.c
        ui = self.ui
        pcs = [p for p in self.enemies(m)]
        able = [p for p in pcs if p.conscious]
        if not pcs:
            return
        block = getattr(m, "block", {})
        if m.has_tag("confused"):
            r = dice.percent()
            if r <= 25:
                ui.out(f"{m.name} shakes off its confusion for a moment.")
            elif r <= 50:
                ui.out(f"{m.name} babbles incoherently (confused).")
                return
            elif r <= 75:
                ui.out(f"{m.name} wanders off in a daze (confused).")
                self.disengage_all(m, retreat=self.speed_of(m))
                return
            else:
                near = [c_ for c_ in self.engaged_foes(m)] + \
                    [a for a in self.allies(m) if a is not m]
                if near:
                    t = dice.choice(near)
                    ui.out(f"{m.name} lashes out wildly at {t.name} (confused)!")
                    w = (m.melee_attacks() or [None])[0]
                    if w:
                        self.make_attack(m, t, w, m.bab())
                    return
        # morale / magical fear
        frightened = m.has_tag("frightened")
        if frightened or (block.get("morale") and m.hp <= m.max_hp() / 3 and dice.die(2) == 1):
            ui.warn(f"{m.name} {'flees in terror' if frightened else 'panics and flees'}!")
            self.provoke(m, "flees", movement=True)
            if not m.dead:
                self.disengage_all(m)
                x.fled = True
            return
        # special: ember burst
        burst = block.get("special", {}).get("ember_burst")
        if burst and not surprise:
            if x.burst_cd <= 0 and self.engaged_foes(m):
                x.burst_cd = burst["recharge"]
                ui.out(f"{m.name}'s chest flares! A wave of embers bursts outward!", ("bred",))
                r = dice.roll(burst["damage"])
                ui.roll(r.detail())
                for p in [p for p in self.engaged_foes(m) if p.is_pc]:
                    amt = r.total
                    if saving_throw(ui, p, "ref", burst["dc"], ["trap"] * 0):
                        amt = 0 if getattr(p, "has_evasion", lambda: False)() else amt // 2
                    deal_damage(ui, p, amt, "fire", self)
                return
            x.burst_cd -= 1
        # breath weapon
        breath = block.get("breath")
        if breath and not surprise and able:
            if x.breath_cd <= 0 and (self.round <= 1 or dice.percent() <= 60):
                self.breathe(m, breath, able)
                x.breath_cd = dice.roll(breath["recharge"]).total
                return
            x.breath_cd -= 1
        # spell-like abilities
        if block.get("slas") and able and not surprise and self.monster_sla(m, able):
            return
        targets = able or ([p for p in pcs] if block.get("savage") else [])
        if not targets:
            return
        engaged = [p for p in self.engaged_foes(m) if p in targets]
        melee = [w for w in m.melee_attacks()]
        ranged = [w for w in m.ranged_attacks()]
        single = block.get("single_actions") or m.has_tag("slowed")
        dis = m.get_effect("Disarmed")
        if dis:
            self.provoke(m, "scrambles for its dropped weapon")
            if not self.active(m) or not m.conscious:
                return
            m.weapons.insert(0, dis.data["entry"])
            m.remove_effect("Disarmed")
            ui.out(f"{m.name} snatches up its weapon.")
            single = True
            surprise = True
        partner = self.grapple_partner(m)
        hold = m.get_effect("Grappling")
        if partner is not None and hold and hold.data.get("holder"):
            if partner.get_effect("Swallowed"):
                ui.out(f"{m.name}'s belly heaves as {partner.name} struggles inside.")
            elif block.get("swallow") and rules.SIZES.index(partner.size) < \
                    rules.SIZES.index(m.size) - 1 and \
                    self.grapple_check(m, partner, "Swallow whole"):
                partner.add_effect(Effect("Swallowed", None, tags=["_dot"],
                                          data={"dot": block["swallow"], "dtype": "acid"}))
                ui.bad(f"{m.name} throws back its head and SWALLOWS {partner.name} whole! "
                       f"(Cut your way out with the grapple options, or break free.)")
            else:
                ui.out(f"{m.name} crushes {partner.name} in its grip!")
                self.monster_melee(m, partner, full=True)
                if block.get("constrict") and not partner.dead and \
                        self.grapple_check(m, partner, "Constrict"):
                    r = dice.roll(block["constrict"])
                    ui.out(f"  The coils tighten ({r.detail()}).")
                    deal_damage(ui, partner, r.total, "B", self, magic=False)
            return
        if block.get("swarm"):
            self.swarm_turn(m, targets, block["swarm"])
            return
        if block.get("trample") and not surprise and not single and len(targets) >= 1 \
                and not self.engaged_foes(m) and dice.percent() <= 50:
            self.trample(m, targets, block["trample"])
            return
        if partner is not None:
            if dice.percent() <= 50 and self.grapple_check(m, partner, f"{m.name} struggles"):
                self.end_grapple(m)
                ui.out(f"{m.name} breaks free!")
                return
            ws = [w for w in m.melee_attacks() if w.get("natural") or w.get("light")]
            if ws:
                ui.out(f"{m.name} fights in the grapple.")
                self.make_attack(m, partner, ws[0], m.bab())
            elif partner.uid in self.st:
                if self.grapple_check(m, partner, "Grapple (damage)"):
                    self.unarmed_damage(m, partner)
            return
        if m.has_tag("prone"):
            self.provoke(m, "struggles to its feet")
            m.remove_effect("Prone")
            if not self.active(m) or not m.conscious:
                return
            ui.out(f"{m.name} gets back up.")
            single = True
            surprise = True  # only a single attack left
        if m.has_tag("entangled") and not engaged:
            if ranged:
                tgt = min(targets, key=lambda p: (p.ac(), p.hp))
                ui.out(f"{m.name}, tangled in the plants, attacks from where it stands.")
                self.make_attack(m, tgt, ranged[0], m.bab())
            else:
                ui.out(f"{m.name} strains against the grasping plants.")
            return

        if engaged and melee:
            tgt = min(engaged, key=lambda p: (p.hp, p.ac()))
            self.monster_melee(m, tgt, full=not (surprise or single or block.get("flyby")))
            if block.get("flyby") and self.active(m):
                self.disengage_all(m)
                ui.out(f"{m.name} wheels away into the air.")
            return
        # ranged option
        far = all(self.feet_to_melee(m, p) > self.speed_of(m) for p in targets)
        shots = [p for p in targets if self.clear_shot(m, p)]
        use_ranged = ranged and shots and (block.get("prefers_ranged") or not melee or far or
                                           (dice.percent() <= 30 and self.round <= 2))
        if use_ranged:
            tgt = min(shots, key=lambda p: (p.ac(), p.hp, self.distance(m, p)))
            w = ranged[0]
            ui.out(f"{m.name} {'fires' if not w.get('thrown') else 'hurls'} at {tgt.name}!")
            self.make_attack(m, tgt, w, m.bab())
            if w.get("thrown") and w.get("entry") in m.weapons:
                m.weapons.remove(w["entry"])
            return
        if not melee:
            return
        # approach a target: prefer one already fighting allies (gang up) or weakest
        def score(p):
            ganged = sum(1 for a in self.allies(m) if self.is_engaged(a, p))
            return (-(ganged if dice.percent() < 60 else 0),
                    self.feet_to_melee(m, p) // 20, p.hp + dice.die(6))
        tgt = min(targets, key=score)
        x.moved = True
        need, sp = self.feet_to_melee(m, tgt), self.speed_of(m)
        if need <= sp:
            ui.out(f"{m.name} rushes at {tgt.name}!")
            if not self.close_in(m, tgt):
                return
            if surprise or single:
                return
            self.monster_melee(m, tgt, full=False)
        elif need <= 2 * sp and not (surprise or single) and not m.has_tag("fatigued") \
                and self.clear_charge(m, tgt):
            ui.out(f"{m.name} CHARGES {tgt.name}!")
            m.add_effect(Effect("Charging", 1, tags=["charging"]))
            if not self.close_in(m, tgt, budget=2 * sp):
                return
            ws = m.melee_attacks()
            self.make_attack(m, tgt, ws[0], m.bab(), [("untyped", 2, "charge")])
        else:
            ui.out(f"{m.name} {'runs' if not single else 'moves'} toward {tgt.name}.")
            self.close_in(m, tgt, budget=sp if (surprise or single) else 2 * sp)

    def swarm_turn(self, m: Creature, targets, sw: dict) -> None:
        """A swarm flows over its victims: automatic damage, no attack roll, and the
        crawling mass is distracting (Fortitude or sickened for a round)."""
        ui = self.ui
        near = [t for t in targets if self.near(m, t)]
        if not near:
            tgt = min(targets, key=lambda t: self.distance(m, t))
            ui.out(f"{m.name} pours across the ground toward {tgt.name}!")
            self.close_in(m, tgt)
            near = [t for t in targets if self.near(m, t)]
        for t in near:
            r = dice.roll(sw["damage"])
            ui.out(f"{m.name} swarms over {t.name}, biting and clawing!", ("bred",))
            deal_damage(ui, t, r.total, "P", self, magic=False)
            if t.conscious and not saving_throw(ui, t, "fort", sw["dc"], [], "distraction"):
                t.add_effect(Effect("Distracted by the swarm", 1, tags=["shaken"]))
                ui.bad(f"  {t.name} is distracted (-2 on attacks, saves and checks).")

    def trample(self, m: Creature, targets, tr: dict) -> None:
        """A huge beast simply runs its victims down: Reflex for half, no attack roll."""
        ui = self.ui
        line = sorted(targets, key=lambda t: self.distance(m, t))
        line = [t for t in line if self.distance(m, t) <= 2 * self.speed_of(m)][:3]
        if not line:
            return
        ui.out(f"{m.name} lowers its head and TRAMPLES straight through "
               f"{', '.join(t.name for t in line)}!", ("bred",))
        r = dice.roll(tr["damage"])
        ui.roll(r.detail())
        from .magic import _area_damage
        for t in line:
            _area_damage(ui, t, r.total, "B", tr["dc"], [], self)
        self.disengage_all(m)
        occ = set(self.occupied(m))
        costs, _ = self.terrain.costs(self.s(m).pos, [])
        last = self.s(line[-1]).pos
        spots = [q for q in costs if self.fits(m, q, occ)]
        if spots:
            self.s(m).pos = min(spots, key=lambda q: (abs(grid.dist(q, last) - 10), costs[q]))
        self.sync_engagement(m)

    def gaze_check(self, x: CState) -> None:
        """Start of a hero's turn near a creature with a petrifying gaze."""
        cr, ui = x.c, self.ui
        if cr.has_tag("blinded") or cr.get_effect("Petrified"):
            return
        for f in self.enemies(cr):
            g = getattr(f, "block", {}).get("gaze")
            if not g or not f.conscious or self.distance(cr, f) > g["range"] \
                    or not self.clear_shot(cr, f):
                continue
            if dice.percent() <= 50:
                ui.out(f"{cr.name} keeps their eyes off {f.name}.", ("dim",))
                continue
            ui.warn(f"{cr.name} meets {f.name}'s terrible gaze!")
            if not saving_throw(ui, cr, "fort", g["dc"], [], "petrifying gaze"):
                cr.add_effect(Effect("Petrified", None, tags=["paralyzed", "petrified"],
                                     hidden=False))
                ui.bad(f"  {cr.name} stiffens, greys, and turns to STONE!")
                return

    def add_summon(self, caster: Creature, key: str, rounds: int) -> None:
        from .monster import Monster
        m = Monster(key, f"{caster.name}'s {MONSTERS[key]['name'].lower()}", roll_hp=False,
                    overrides={"morale": False, "evil": False})
        m.owner = caster
        m.summoned = True
        m.add_effect(Effect("Summoned", rounds, data={"cl": rounds, "summoned": True},
                            source=caster.name, hidden=True))
        x = CState(m, self.s(caster).side)
        x.flat = False
        occ = set(self.occupied())
        cp = self.s(caster).pos
        foes = self.enemies(caster)
        spots = [q for q in grid.neighbors(cp) if q not in occ and self.terrain.walkable(q)] or \
            [q for q in ((xx, yy) for xx in range(grid.W) for yy in range(grid.H))
             if q not in occ and self.terrain.walkable(q)] or [cp]
        x.pos = min(spots, key=lambda q: (grid.dist(q, cp) > 5,
                                          grid.dist(q, self.s(foes[0]).pos) if foes else 0))
        self.st[m.uid] = x
        self.companions.append(m)
        idx = self.order.index(self.s(caster)) + 1 if self.s(caster) in self.order else len(
            self.order)
        self.order.insert(idx, x)
        if hasattr(self, "acted"):
            self.acted.add(id(x))   # it acts from next round
        self.ui.good(f"  A {MONSTERS[key]['name'].lower()} appears beside {caster.name}, "
                     f"ready to fight for {rounds} rounds.")

    # ------------------------------------------------------------ monster powers
    def airborne(self, cr: Creature) -> bool:
        return bool(getattr(cr, "block", {}).get("fly")) and not self.s(cr).engaged \
            and not cr.helpless() and not cr.has_tag("prone") and not cr.has_tag("grappled")

    def reachable(self, p: Creature, f: Creature) -> bool:
        """Can p walk up to f? Flying foes in the air need flight (or reach/ranged)."""
        return not self.airborne(f) or p.has_tag("flying") or self.airborne(p)

    def start_auras(self) -> None:
        ui = self.ui
        side_pc = [x.c for x in self.st.values() if x.side == "pc" and self.active(x.c)]
        if any(getattr(p, "class_level", lambda c_: 0)("paladin") >= 3 and p.conscious
               for p in self.party):
            for a in side_pc:
                a.add_effect(Effect("Aura of Courage", None, [("saves_vs_fear", "morale", 4)],
                                    hidden=True))
        for m in self.monsters:
            aura = m.block.get("fear_aura")
            if not aura:
                continue
            ui.warn(f"{aura['text']}!")
            for p in side_pc:
                if "fear" in p.immunities() or p.dead:
                    if "fear" in p.immunities():
                        ui.good(f"  {p.name} is unafraid.")
                    continue
                if not saving_throw(ui, p, "will", aura["dc"], ["fear"], "fear"):
                    d = dice.roll(aura["duration"]).total
                    tag = aura.get("effect", "shaken")
                    p.add_effect(Effect(f"Terror ({m.name})", d, tags=[tag, "fear_effect"]))
                    ui.bad(f"  {p.name} is {tag} with terror for {d} rounds!")

    def breathe(self, m: Creature, breath: dict, able: List[Creature]) -> None:
        ui = self.ui
        shape = breath.get("area") or (("cone", 30) if "cone" in breath.get("text", "") else None)
        if shape and m.uid in self.st:
            side = self.s(m).side

            def caught(t):
                return [c_ for c_ in self.area_targets(m, "breath", t, tuple(shape))
                        if self.s(c_).side != side]
            aim = max(able, key=lambda t: (len(caught(t)), -self.distance(m, t)))
            targets = caught(aim) or [aim]
        else:
            eng = [p for p in able if self.is_engaged(m, p)]
            rest = [p for p in able if p not in eng]
            dice.shuffle(rest)
            targets = (eng + rest)[:breath.get("targets", 2)]
        ui.out(f"{m.name} {breath.get('text', 'breathes')}!", ("bred",))
        r = dice.roll(breath["dice"])
        ui.roll(r.detail())
        from .magic import _area_damage
        for t in targets:
            _area_damage(ui, t, r.total, breath["dtype"], breath["dc"], ["breath"], self)

    def monster_sla(self, m: Creature, able: List[Creature]) -> bool:
        """Maybe use a spell-like ability. Returns True if the turn was used."""
        x = self.s(m)
        ready = [a for a in m.block["slas"] if x.sla_used.get(a["spell"], 0) < a.get("uses", 99)]
        if not ready:
            return False
        selfies = [a for a in ready if a.get("self") and not m.get_effect(a["spell"])]
        if selfies and self.round <= 1:
            a = selfies[0]
        else:
            offense = [a for a in ready if not a.get("self")]
            if not offense or dice.percent() > 45:
                return False
            a = dice.choice(offense)
        x.sla_used[a["spell"]] = x.sla_used.get(a["spell"], 0) + 1
        sp = SPELLS[a["spell"]]
        if a.get("self"):
            targets = [m]
        elif sp["target"] == "enemies" and a["spell"] in grid.AREAS:
            best = max(able, key=lambda t: len(self._area_catch(m, a["spell"], t,
                                                                sp["max_targets"])[0]))
            targets = self._area_catch(m, a["spell"], best, sp["max_targets"])[0] or [best]
        elif sp["target"] == "enemies":
            targets = list(able)
            dice.shuffle(targets)
            targets = targets[:sp["max_targets"]]
        else:
            targets = [dice.choice(able)]
        self.ui.warn(f"{m.name} begins to weave {a['spell'].lower()}...")
        if self.try_counterspell(m, a):
            return True
        cast_spell(self.ui, m, a["spell"], targets, a["cl"], a.get("dc", 10), self,
                   allies=self.allies(m), enemies=self.enemies(m))
        return True

    def try_counterspell(self, m: Creature, sla: dict) -> bool:
        ui = self.ui
        lvl = min(SPELLS[sla["spell"]]["levels"].values())
        for x in self.st.values():
            r = x.readied
            if not r or not r.get("counter") or x.side == self.s(m).side \
                    or not self.active(x.c) or not x.c.can_act():
                continue
            p = x.c
            x.readied = None
            roll = dice.d20()
            tot = roll + p.skill_total("Spellcraft") if p.can_use_skill("Spellcraft") else -99
            ui.roll(f"{p.name} identifies the spell (Spellcraft): {tot} vs DC {15 + lvl}")
            if tot < 15 + lvl:
                ui.out(f"  {p.name} can't make out the spell in time.")
                continue
            casts = p.available_casts()
            same = next((c_ for c_ in casts if c_["spell"] == sla["spell"]), None)
            disp = next((c_ for c_ in casts if c_["spell"] == "Dispel Magic"), None)
            if same:
                p.expend(same)
                ui.good(f"  {p.name} counters with {sla['spell'].lower()} of their own! The "
                         f"spell unravels.")
                return True
            if disp:
                p.expend(disp)
                r2 = dice.d20()
                cl = min(10, p.caster_level(disp["class"]))
                ok = r2 + cl >= 11 + sla["cl"]
                ui.roll(f"  Counter with dispel magic: d20={r2}+{cl} = {r2 + cl} vs DC "
                        f"{11 + sla['cl']}")
                if ok:
                    ui.good(f"  {p.name}'s dispel snuffs out the spell!")
                    return True
                ui.out("  The counter fails.")
            else:
                ui.out(f"  {p.name} knows the spell but has nothing to counter it with.")
        return False

    # ------------------------------------------------------------ animal companions
    def companion_turn(self, x: CState, surprise: bool) -> None:
        comp = x.c
        owner = getattr(comp, "owner", None)
        with self.ui.acting(getattr(owner, "player", "")):
            self._companion_turn(x, surprise, owner)

    def _companion_turn(self, x: CState, surprise: bool, owner) -> None:
        ui = self.ui
        comp = x.c
        foes = [f for f in self.enemies(comp) if not f.dead]
        if not foes:
            return
        ui.out()
        ui.out(f">> {c(comp.name, 'bold', 'green')} ({owner.name if owner else ''}'s "
               f"{comp.block['name'].lower()})  HP {comp.hp}/{comp.max_hp()}  AC {comp.ac()}")
        partner = self.grapple_partner(comp)
        if partner is not None:
            self.make_attack(comp, partner, comp.melee_attacks()[0], comp.bab())
            return
        eng = self.engaged_foes(comp)
        opts, targets = [], []
        for f in foes:
            how = "attack" if self.is_engaged(comp, f) else "rush in and bite"
            tag = []
            if any(self.is_engaged(a, f) for a in self.allies(comp) if a is not comp):
                tag.append("flank with an ally")
            if f.helpless():
                tag.append(f.status_word())
            opts.append(f"{how.capitalize()}: {f.name} ({wound_word(f)}"
                        f"{'; ' + ', '.join(tag) if tag else ''})")
            targets.append(f)
        if owner is not None and not owner.dead:
            opts.append(f"Guard {owner.name} (stay close, +2 dodge AC for {owner.name})")
            targets.append("guard")
        opts.append("Hold back (do nothing)")
        targets.append(None)
        default = 0
        if eng:
            default = targets.index(eng[0])
        elif owner is not None:
            near = [f for f in self.engaged_foes(owner)] if owner.uid in self.st else []
            if near and near[0] in targets:
                default = targets.index(near[0])
        i = ui.choose(f"{comp.name}, what do you do?", opts, default=default)
        t = targets[i]
        if t is None:
            return
        if t == "guard":
            owner.add_effect(Effect(f"Guarded by {comp.name}", 1, [("ac", "dodge", 2)]))
            if not self.is_engaged(comp, owner):
                for f in self.engaged_foes(owner):
                    self.engage(comp, f)
                    break
            ui.out(f"{comp.name} plants itself beside {owner.name}, snarling.")
            return
        if comp.has_tag("prone"):
            self.provoke(comp, "scrambles up")
            comp.remove_effect("Prone")
            if not self.active(comp):
                return
            surprise = True
        if not self.is_engaged(comp, t) and not self.reachable(comp, t):
            ui.out(f"{comp.name} snarls up at {t.name}, which is out of reach in the air.")
            return
        if not self.is_engaged(comp, t):
            if comp.has_tag("entangled"):
                ui.out(f"{comp.name} is stuck in the plants.")
                return
            ui.out(f"{comp.name} lunges at {t.name}!")
            if not self.advance(comp, t, single=surprise or x.single):
                return
            if surprise:
                return
            self.make_attack(comp, t, comp.melee_attacks()[0], comp.bab())
            return
        self.monster_melee(comp, t, full=not (surprise or x.single))

    def monster_melee(self, m, tgt, full: bool) -> None:
        melee = m.melee_attacks()
        naturals = [w for w in melee if w.get("natural")]
        if naturals and full:
            claws = {}
            for w in naturals:
                if not self.active(tgt) or (tgt.is_pc and not tgt.conscious
                                            and not m.block.get("savage")):
                    others = [p for p in self.engaged_foes(m) if p.conscious]
                    if not others:
                        return
                    tgt = others[0]
                if self.make_attack(m, tgt, w, m.bab()) and w["name"] == "claw":
                    claws[tgt.uid] = claws.get(tgt.uid, 0) + 1
            rend = m.block.get("rend")
            if rend and claws.get(tgt.uid, 0) >= 2 and self.active(tgt) and not tgt.dead:
                r = dice.roll(rend)
                self.ui.bad(f"{m.name} digs in both claws and rends {tgt.name}!")
                self.ui.roll(r.detail())
                deal_damage(self.ui, tgt, r.total, "S", self, magic=False)
            return
        w = naturals[0] if naturals else melee[0]
        babs = rules.iterative_attacks(m.bab()) if full else [m.bab()]
        for b in babs:
            if not self.active(tgt):
                return
            self.make_attack(m, tgt, w, b)
