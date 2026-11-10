"""Turn-based D&D 3.5 combat.

Positioning is abstracted as *engagement*: a creature that moves into melee with
a foe becomes engaged with it. Engagement drives attacks of opportunity,
flanking (two allies engaged with the same foe), firing into melee, and
whether a creature can make a full attack (no move needed).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from . import dice, rules
from .creature import Creature
from .data.classes import CLASSES
from .data.items import item_data, item_name
from .data.spells import SPELLS
from .effects import Effect, ROUNDS_PER_MINUTE
from .magic import (cast_spell, caster_cl, caster_dc, consume_one_shot, deal_damage,
                    saving_throw, scroll_usable, touch_attack, use_scroll_check)
from .sheet import render, short_status
from .ui import c


class CState:
    def __init__(self, cr: Creature, side: str):
        self.c = cr
        self.side = side
        self.init = 0
        self.flat = True
        self.engaged: set = set()
        self.aoo_used = 0
        self.std = True
        self.move = True
        self.full_used = False
        self.moved = False
        self.cleave_used = False
        self.fled = False
        self.spent_ammo: Dict[str, int] = {}
        self.burst_cd = 0
        self.surprise = False


def wound_word(cr: Creature) -> str:
    if cr.dead:
        return "dead"
    frac = cr.hp / max(1, cr.max_hp())
    if frac >= 1:
        return "unhurt"
    if frac > 0.75:
        return "scratched"
    if frac > 0.5:
        return "wounded"
    if frac > 0.25:
        return "badly wounded"
    return "near death"


class Combat:
    def __init__(self, ui, party: Sequence[Creature], monsters: Sequence[Creature],
                 surprised: Sequence[Creature] = (), can_flee: bool = True,
                 title: str = "COMBAT"):
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
        for m in self.monsters:
            self.st[m.uid] = CState(m, "mon")
        self._name_monsters()
        self.order: List[CState] = []
        self.xp_monsters: List[Creature] = []

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
        return not cr.dead and not st.fled

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
        self.s(a).engaged.add(b.uid)
        self.s(b).engaged.add(a.uid)

    def disengage_all(self, a: Creature) -> None:
        for u in list(self.s(a).engaged):
            if u in self.st:
                self.st[u].engaged.discard(a.uid)
        self.s(a).engaged.clear()

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
        return (self.active(cr) and cr.can_act() and not self.s(cr).flat
                and self.has_melee(cr))

    def shooting_into_melee(self, shooter: Creature, target: Creature) -> bool:
        for ally in self.allies(shooter):
            if ally is not shooter and self.is_engaged(ally, target) and ally.conscious:
                return True
        return False

    def flanked(self, attacker: Creature, target: Creature) -> bool:
        for ally in self.allies(attacker):
            if ally is attacker:
                continue
            if self.is_engaged(ally, target) and self.threatens(ally):
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
        for p in self.party:
            st = self.s(p)
            eng = ", ".join(f.name for f in self.engaged_foes(p))
            fl = " (fled)" if st.fled else ""
            ui.out(f"  {c(short_status(p), 'bgreen' if p.conscious else 'bred')}{fl}"
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
            eng = ", ".join(f.name for f in self.engaged_foes(m))
            ui.out(f"  {c(m.name, 'bred')}: {cond}{extra}" + (f"  | melee: {eng}" if eng else ""))

    # ------------------------------------------------------------ main loop
    def run(self) -> str:
        ui = self.ui
        ui.header(self.title)
        for m in self.monsters:
            ui.out(f"  {m.name}: {m.block.get('desc', '')}", ("red",))
        self.roll_initiative()
        if self.surprised:
            aware = [x for x in self.order if id(x.c) not in self.surprised]
            if aware and len(aware) < len(self.order):
                ui.warn("SURPRISE ROUND! Only those who noticed the enemy may act "
                        "(one standard or move action).")
                self.round = 0
                for x in aware:
                    if self.check_end():
                        break
                    self.take_turn(x, surprise=True)
        while True:
            self.round += 1
            self.show_field()
            for x in list(self.order):
                res = self.check_end()
                if res:
                    return self.finish(res)
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
        if result == "victory":
            helpless = [m for m in self.monsters if self.active(m) and m.helpless()]
            for m in helpless:
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
        for p in self.party:
            for e in list(p.effects):
                if e.tags & {"prone", "charging", "total_defense", "fighting_defensively",
                             "_spiritual_weapon"} or e.name in ("Dazed", "Turned"):
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
        # spiritual weapon
        if cr.get_effect("Spiritual Weapon"):
            self.spiritual_weapon_attack(cr)
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
        if not self.start_of_turn(x):
            return
        x.surprise = surprise
        if x.side == "pc":
            self.pc_turn(x, surprise)
        else:
            self.monster_turn(x, surprise)

    # ------------------------------------------------------------ attacks
    def make_attack(self, attacker: Creature, target: Creature, w: dict, bab: int,
                    situational: Sequence[Tuple[str, int, str]] = (), offhand=False,
                    twf=False, aoo=False, power: int = 0) -> bool:
        """Resolve one attack roll. Returns True on hit."""
        ui = self.ui
        if w.get("natural") is False and offhand:
            w = dict(w, _offhand_light=w.get("light"))
        sit = list(situational)
        ranged = w.get("ranged", False)
        if not ranged:
            if self.flanked(attacker, target):
                sit.append(("untyped", 2, "flanking"))
            if target.helpless():
                sit.append(("untyped", 4, "vs helpless"))
        else:
            if self.shooting_into_melee(attacker, target) and not attacker.has_feat("Precise Shot"):
                sit.append(("untyped", -4, "firing into melee"))
            if target.helpless():
                pass
        comps = attacker.attack_components(w, bab=bab, target=target, offhand=offhand, twf=twf,
                                           power=power, situational=sit)
        consume_one_shot(attacker, "attack")
        bonus = sum(v for _, v, _ in comps)
        flat = self.is_flat_footed(target) or target.helpless()
        ac = target.ac("flat" if flat else "normal", attacker=attacker, ranged=ranged)
        roll = dice.d20()
        total = roll + bonus
        hit = roll == 20 or (roll != 1 and total >= ac)
        label = "AoO! " if aoo else ""
        sitnote = ", ".join(s for _, v, s in sit if v)
        ui.out(f"{label}{attacker.name} attacks {target.name} with {w['name']}: "
               f"d20={roll} {bonus:+d} = {total} vs AC {ac}"
               + (f" ({sitnote})" if sitnote else "") + " -> "
               + (c("HIT", "bgreen") if hit else c("miss", "dim")))
        if not hit:
            return False
        # concealment
        conc = target.bonus("concealment")
        if conc:
            r = dice.percent()
            if r <= conc:
                if attacker.has_feat("Blind-Fight") and dice.percent() > conc:
                    ui.out("  (Blind-Fight reroll succeeds!)")
                else:
                    ui.out(f"  ...but the blow passes through a blurred image (d% {r} <= "
                           f"{conc}%).")
                    return False
        crit = False
        threat = roll >= w.get("crit_range", 20) or roll == 20
        if threat and not target.crit_immune():
            cr = dice.d20()
            ctot = cr + bonus
            crit = cr != 1 and (cr == 20 or ctot >= ac)
            ui.roll(f"Critical threat! Confirm: d20={cr} {bonus:+d} = {ctot} -> "
                    f"{'CRITICAL HIT!' if crit else 'not confirmed'}")
        elif threat:
            ui.roll(f"(threat, but {target.name} is immune to critical hits)")
        self.apply_hit(attacker, target, w, crit, offhand, power, flat)
        return True

    def apply_hit(self, attacker, target, w, crit, offhand, power, target_flat):
        ui = self.ui
        dice_expr, comps = attacker.damage_profile(w, target, offhand=offhand, power=power)
        static = sum(v for _, v, _ in comps)
        mult = w.get("crit_mult", 2) if crit else 1
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
        dmg_type = "" if w.get("magic_force") else w.get("dtype", "B")
        deal_damage(ui, target, total, dmg_type, self, magic=False)
        special = w.get("special") or {}
        extra = special.get("extra_damage")
        if extra and not target.dead:
            r = dice.roll(extra[0])
            deal_damage(ui, target, r.total, extra[1], self)
        if not target.dead and target.is_living():
            if special.get("disease"):
                dz = special["disease"]
                if not saving_throw(ui, target, "fort", dz["dc"], ["disease"], dz["name"]):
                    if target.is_pc and not any(a["name"] == dz["name"] for a in target.afflictions):
                        target.afflictions.append(dict(dz, successes=0))
                        ui.warn(f"  {target.name} has contracted {dz['name']}!")
            if special.get("paralysis") and target.conscious:
                elf = getattr(target, "race", "") == "elf"
                if elf:
                    ui.out(f"  {target.name}'s elven blood resists the ghoul's paralysis.")
                elif not saving_throw(ui, target, "fort", special["paralysis"]["dc"],
                                      ["paralysis"], "paralysis"):
                    d = dice.roll(special["paralysis"]["duration"]).total
                    target.add_effect(Effect("Ghoul paralysis", d, tags=["paralyzed"]))
                    ui.bad(f"  {target.name} is PARALYZED for {d} rounds!")
            if special.get("trip") and target.conscious and not target.has_tag("prone"):
                self.trip(attacker, target)
        if target.dead or (target.is_pc and target.hp < 0):
            self.try_cleave(attacker, w)

    def trip(self, attacker, target):
        ui = self.ui
        a = dice.d20() + attacker.mod("str") + rules.SIZE_GRAPPLE[attacker.size] // 1
        best = max(target.mod("str"), target.mod("dex"))
        stab = getattr(target, "race_data", {}).get("stability", 0)
        d = dice.d20() + best + rules.SIZE_GRAPPLE[target.size] + stab
        ui.roll(f"Trip attempt: {attacker.name} {a} vs {target.name} {d}")
        if a > d:
            target.add_effect(Effect("Prone", None, tags=["prone"]))
            ui.warn(f"  {target.name} is knocked prone!")

    def try_cleave(self, attacker, w):
        st = self.s(attacker)
        if w.get("ranged") or st.cleave_used or not attacker.has_feat("Cleave"):
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
        ui = self.ui
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
            st = self.s(foe)
            if not self.threatens(foe) or st.aoo_used:
                continue
            w = self.best_melee(foe)
            if not w:
                continue
            st.aoo_used = 1
            self.ui.warn(f"{mover.name} {reason}, provoking an attack of opportunity from "
                         f"{foe.name}!")
            sit = []
            if movement and mover.has_feat("Mobility"):
                sit.append(("untyped", -4, "Mobility"))
            self.make_attack(foe, mover, w, foe.bab(), situational=sit, aoo=True)
            if not mover.conscious:
                break
        return mover.damage - before

    def spiritual_weapon_attack(self, caster: Creature) -> None:
        e = caster.get_effect("Spiritual Weapon")
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
        self.ui.out(f"{caster.name}'s spiritual weapon strikes at {tgt.name}: d20={roll}"
                    f"{bonus:+d} = {roll + bonus} vs AC {ac} -> {'HIT' if hit else 'miss'}")
        if hit:
            r = dice.roll(e.data["damage"])
            deal_damage(self.ui, tgt, r.total, "force", self)

    # ------------------------------------------------------------ PC turn
    def pc_turn(self, x: CState, surprise: bool) -> None:
        with self.ui.acting(getattr(x.c, "player", "")):
            self._pc_turn(x, surprise)

    def _pc_turn(self, x: CState, surprise: bool) -> None:
        ui = self.ui
        p = x.c
        disabled = p.hp == 0
        while True:
            if self.check_end() or not self.active(p) or not p.can_act():
                return
            if disabled and (not x.std or not x.move):
                return
            if not x.std and not x.move:
                return
            ui.out()
            acts = []
            eng = self.engaged_foes(p)
            head = (f">> {c(p.name, 'bold', 'bgreen')}'s turn ({p.player or 'player'})  "
                    f"HP {p.hp}/{p.max_hp()}  AC {p.ac()}  "
                    f"[{'standard' if x.std else ''}{' move' if x.move else ''} left]")
            ui.out(head)
            if eng:
                ui.out(f"   In melee with: {', '.join(f.name for f in eng)}")

            def add(label, fn, *args):
                acts.append((label, fn, args))

            full_ok = x.std and x.move and not x.moved and not surprise and not disabled
            if x.std:
                add("Attack (standard action; moves into melee first if needed)", self.act_attack,
                    x, False)
            if full_ok:
                add("Full attack (all your attacks; must already be in position)",
                    self.act_attack, x, True)
                if not p.has_tag("fatigued"):
                    add("Charge (+2 attack, -2 AC; move and attack a foe you're not engaged with)",
                        self.act_charge, x)
            if x.std and getattr(p, "available_casts", None) and p.available_casts() \
                    and not p.has_tag("raging"):
                add("Cast a spell", self.act_cast, x)
            if x.std and self.usable_items(p):
                add("Use an item (potion, scroll, alchemist's fire...)", self.act_item, x)
            if x.std and p.uses_left("turn") and any(m.ctype == "undead" for m in self.enemies(p)):
                add(f"Turn undead ({p.uses_left('turn')} left)", self.act_turn, x)
            if p.uses_left("rage") and not p.has_tag("raging") and not p.has_tag("fatigued"):
                add("Rage! (free action)", self.act_rage, x)
            if p.uses_left("feat_of_strength") and not p.get_effect("Feat of Strength"):
                add("Feat of Strength (free action)", self.act_feat_strength, x)
            dying = [a for a in self.allies(p) if a.is_pc and a.hp < 0 and not a.stable
                     and not a.dead]
            if x.std and dying:
                add("Stabilize a dying ally (Heal check DC 15)", self.act_stabilize, x)
            if x.move:
                if p.has_tag("prone"):
                    add("Stand up (move action, provokes)", self.act_stand, x)
                foes = [f for f in self.enemies(p) if not self.is_engaged(p, f)]
                if foes:
                    add("Move into melee with a foe (move action)", self.act_approach, x)
                if eng:
                    add("Move away from melee (move action, provokes attacks of opportunity)",
                        self.act_move_away, x)
                add("Draw / switch weapon (move action)", self.act_draw, x)
            if eng and full_ok:
                add("Withdraw (full round: leave melee safely)", self.act_withdraw, x)
            if x.std:
                add("Total defense (+4 dodge AC until your next turn)", self.act_total_defense, x)
            if p.has_feat("Power Attack"):
                add(f"Set Power Attack (now {p.power_attack})", self.act_power, x)
            if not p.get_effect("Fighting defensively") and x.std:
                add("Toggle: fight defensively this turn (-4 attack, +2 AC)", self.act_defensive, x)
            add("Look: battlefield / my character sheet / foe details", self.act_look, x)
            if self.can_flee and full_ok:
                add("Flee the battle (withdraw out of the fight)", self.act_flee, x)
            add("End turn", None)
            groups = []
            for a in acts:
                lab = a[0]
                if lab.startswith(("Attack", "Full attack", "Charge", "Cast", "Use an item",
                                   "Turn undead", "Rage", "Feat of Strength")):
                    groups.append("Fight")
                elif lab.startswith(("Move", "Stand", "Draw", "Withdraw", "Flee")):
                    groups.append("Move")
                elif lab.startswith(("End turn",)):
                    groups.append("Turn")
                elif lab.startswith(("Look",)):
                    groups.append("Game")
                else:
                    groups.append("Tactics")
            i = ui.choose(f"{p.name}, what do you do?", [a[0] for a in acts], groups=groups)
            label, fn, args = acts[i]
            if fn is None:
                return
            before = (x.std, x.move)
            fn(*args)
            if surprise and (x.std, x.move) != before:
                return

    def _pick_target(self, p, pool, prompt="Target") -> Optional[Creature]:
        if not pool:
            self.ui.out("No valid targets.")
            return None
        opts = []
        for f in pool:
            tag = []
            if self.is_engaged(p, f):
                tag.append("in melee with you")
            if f.helpless():
                tag.append(f.status_word())
            opts.append(f"{f.name} ({wound_word(f) if not f.is_pc else str(f.hp) + ' hp'}"
                        f"{'; ' + ', '.join(tag) if tag else ''})")
        i = self.ui.choose(prompt, opts, allow_cancel=True)
        return None if i is None else pool[i]

    def _choose_weapon(self, p, want_ranged: Optional[bool] = None,
                       x: Optional[CState] = None) -> Optional[dict]:
        ws = p.weapon_infos()
        if x is not None and not x.move and not p.has_feat("Quick Draw"):
            ws = [w for w in ws if w.get("wielded")]
        if x is not None and not x.move:
            ws = [w for w in ws if w["ranged"] or self.engaged_foes(p)]
        if want_ranged is not None:
            ws = [w for w in ws if w["ranged"] == want_ranged]
        usable = []
        for w in ws:
            if w.get("ammo") and p.ammo_count(w["ammo"]) <= 0:
                continue
            usable.append(w)
        if not usable:
            self.ui.out("No usable weapon.")
            return None
        if len(usable) == 1:
            return usable[0]
        opts = []
        for w in usable:
            ab = sum(v for _, v, _ in p.attack_components(w))
            d, dc = p.damage_profile(w)
            db = sum(v for _, v, _ in dc)
            state = {"main": "", "off": " [off hand]", None: " [needs drawing: move action]"}[
                w.get("wielded")]
            opts.append(f"{w['name']}{state}  {ab:+d}  {d}{db:+d}" if db else
                        f"{w['name']}{state}  {ab:+d}  {d}")
        i = self.ui.choose("With which weapon?", opts, allow_cancel=True)
        return None if i is None else usable[i]

    def _ready_weapon(self, x: CState, w: dict) -> bool:
        """Draw a stowed weapon if needed. Returns False if no action left."""
        p = x.c
        if w.get("wielded"):
            return True
        if not p.has_feat("Quick Draw"):
            if not x.move:
                self.ui.bad("You need a move action to draw that weapon.")
                return False
            x.move = False
        entry = w.get("entry")
        if entry:
            self.ui.out(p.equip(entry))
        return True

    def _spend_ammo(self, p, w) -> bool:
        if w.get("ammo"):
            if not p.use_ammo(w["ammo"]):
                self.ui.bad(f"Out of {w['ammo']}!")
                return False
            st = self.s(p)
            st.spent_ammo[w["ammo"]] = st.spent_ammo.get(w["ammo"], 0) + 1
        elif w.get("thrown") and w.get("entry"):
            e = w["entry"]
            st = self.s(p)
            st.spent_ammo[e["id"]] = st.spent_ammo.get(e["id"], 0) + 1
            if e.get("qty", 1) > 1:
                e["qty"] -= 1
            else:
                e.pop("slot", None)
                if e in p.inventory:
                    p.inventory.remove(e)
        return True

    def act_attack(self, x: CState, full: bool) -> None:
        p = x.c
        ui = self.ui
        foes = self.enemies(p)
        w = self._choose_weapon(p, x=x)
        if not w:
            return
        if full and not w.get("wielded") and not p.has_feat("Quick Draw"):
            ui.bad("Draw that weapon first (move action), then attack.")
            return
        if w["ranged"]:
            tgt = self._pick_target(p, foes)
            if not tgt:
                return
            if not self._ready_weapon(x, w):
                return
            if self.engaged_foes(p):
                self.provoke(p, "shoots while in melee")
                if not p.conscious:
                    x.std = x.move = False
                    return
        else:
            if not x.move or x.surprise:
                foes = [f for f in foes if self.is_engaged(p, f)] or foes
            tgt = self._pick_target(p, foes)
            if not tgt:
                return
            if not self._ready_weapon(x, w):
                return
            if not self.is_engaged(p, tgt):
                if full:
                    ui.bad("You must already be in melee with that foe to full attack.")
                    return
                if x.surprise:
                    ui.bad("In the surprise round you can move OR attack, not both. Choose "
                           "'Move into melee' instead.")
                    return
                if not x.move:
                    ui.bad("No move action left to close the distance.")
                    return
                x.move = False
                x.moved = True
                self.engage(p, tgt)
                ui.out(f"{p.name} closes in on {tgt.name}.")
        sit = []
        if p.get_effect("Fighting defensively"):
            sit.append(("untyped", -4, "fighting defensively"))
        power = p.power_attack if not w["ranged"] else 0
        if not full:
            x.std = False
            if not self._spend_ammo(p, w):
                return
            self.make_attack(p, tgt, w, p.bab(), sit, power=power)
            if p.hp == 0 and not p.dead:
                self._strain(p)
            return
        x.std = x.move = False
        x.full_used = True
        self.full_attack(p, tgt, w, sit, power)

    def full_attack(self, p, tgt, w, sit, power):
        ui = self.ui
        babs = rules.iterative_attacks(p.bab())
        offhand = None
        twf = False
        if not w["ranged"]:
            off = p.equipped("off")
            if off and item_data(off)["kind"] == "weapon":
                from .creature import weapon_info_from_entry
                offhand = weapon_info_from_entry(off, p.base_size)
                offhand["_offhand_light"] = offhand.get("light")
                twf = ui.confirm("Attack with your off-hand weapon too (two-weapon fighting)?",
                                 True)
        extra = 0
        if p.has_tag("hasted"):
            extra += 1
        rapid = w["ranged"] and p.has_feat("Rapid Shot") and ui.confirm(
            "Use Rapid Shot (extra arrow, all attacks -2)?", True)
        if rapid:
            sit = sit + [("untyped", -2, "Rapid Shot")]
        seq = [babs[0]] * (1 + extra + (1 if rapid else 0)) + babs[1:]
        main_w = dict(w, _offhand_light=offhand.get("light") if offhand else False)
        for b in seq:
            if not self.active(tgt) or tgt.dead:
                alts = [f for f in self.enemies(p) if (w["ranged"] or self.is_engaged(p, f))]
                if not alts:
                    return
                tgt = alts[0] if len(alts) == 1 else alts[ui.choose(
                    "Next target", [f.name for f in alts])]
            if not self._spend_ammo(p, w):
                return
            self.make_attack(p, tgt, main_w, b, sit, twf=twf, power=power)
            if not p.conscious:
                return
        if twf and offhand:
            if not self.active(tgt):
                alts = [f for f in self.engaged_foes(p)]
                if not alts:
                    return
                tgt = alts[0]
            self.make_attack(p, tgt, offhand, babs[0], sit, offhand=True, twf=True, power=power)

    def _strain(self, p):
        p.damage += 1
        p.check_death()
        self.ui.bad(f"{p.name} strains while disabled and takes 1 damage ({p.hp} hp)!")
        self.after_damage(p)

    def act_charge(self, x: CState) -> None:  # noqa: C901
        p = x.c
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f)]
        tgt = self._pick_target(p, foes, "Charge whom?")
        if not tgt:
            return
        w = self.best_melee(p)
        if not w or w["ranged"]:
            self.ui.bad("You need a melee weapon in hand to charge.")
            return
        x.std = x.move = False
        x.moved = True
        if self.engaged_foes(p):
            self.provoke(p, "charges away", movement=True)
            if not p.conscious:
                return
            self.disengage_all(p)
        self.engage(p, tgt)
        p.add_effect(Effect("Charging", 1, tags=["charging"]))
        self.ui.out(f"{p.name} CHARGES {tgt.name}!")
        sit = [("untyped", 2, "charge")]
        self.make_attack(p, tgt, w, p.bab(), sit, power=p.power_attack)

    def act_approach(self, x: CState) -> None:
        p = x.c
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f)]
        tgt = self._pick_target(p, foes, "Move next to whom?")
        if not tgt:
            return
        x.move = False
        x.moved = True
        self.engage(p, tgt)
        self.ui.out(f"{p.name} moves into melee with {tgt.name}.")

    def act_move_away(self, x: CState) -> None:
        p = x.c
        x.move = False
        x.moved = True
        self.provoke(p, "moves out of melee", movement=True)
        self.disengage_all(p)
        if p.conscious:
            self.ui.out(f"{p.name} backs away from the fight.")

    def act_withdraw(self, x: CState) -> None:
        p = x.c
        x.std = x.move = False
        self.disengage_all(p)
        self.ui.out(f"{p.name} withdraws carefully from melee.")

    def act_stand(self, x: CState) -> None:
        p = x.c
        x.move = False
        self.provoke(p, "stands up")
        p.remove_effect("Prone")
        self.ui.out(f"{p.name} stands up.")

    def act_draw(self, x: CState) -> None:
        p = x.c
        ws = [w for w in p.weapon_infos() if w.get("entry") and w.get("wielded") is None
              and not w.get("thrown")]
        if not ws:
            self.ui.out("No other weapons to draw.")
            return
        i = self.ui.choose("Draw which weapon?", [w["name"] for w in ws], allow_cancel=True)
        if i is None:
            return
        x.move = False
        self.ui.out(p.equip(ws[i]["entry"]))

    def act_total_defense(self, x: CState) -> None:
        p = x.c
        x.std = False
        p.add_effect(Effect("Total defense", 1, [("ac", "dodge", 4)], ["total_defense"]))
        self.ui.out(f"{p.name} focuses entirely on defense (+4 AC).")

    def act_defensive(self, x: CState) -> None:
        p = x.c
        p.add_effect(Effect("Fighting defensively", 1, [("ac", "dodge", 2)],
                            ["fighting_defensively"]))
        self.ui.out(f"{p.name} fights defensively (-4 attack, +2 AC) this round.")

    def act_power(self, x: CState) -> None:
        p = x.c
        p.power_attack = self.ui.ask_int("Power Attack amount (attack penalty = damage bonus, "
                                         "x2 two-handed)", 0, max(0, p.bab()), p.power_attack)

    def act_rage(self, x: CState) -> None:
        p = x.c
        p.spend("rage")
        con_after = (p.ability("con") or 10) + 4
        dur = 3 + rules.ability_mod(con_after)
        p.add_effect(Effect("Rage", dur, [("str", "morale", 4), ("con", "morale", 4),
                                          ("save_will", "morale", 2)], ["raging"],
                            data={"on_end": "rage"}))
        self.ui.warn(f"{p.name} flies into a RAGE! (+4 Str, +4 Con, +2 Will, -2 AC for "
                     f"{dur} rounds)")

    def act_feat_strength(self, x: CState) -> None:
        p = x.c
        p.spend("feat_of_strength")
        lvl = p.class_level("cleric")
        p.add_effect(Effect("Feat of Strength", 1, [("str", "enhancement", lvl)]))
        self.ui.good(f"{p.name} calls on divine might: +{lvl} Strength this round.")

    def act_stabilize(self, x: CState) -> None:
        p = x.c
        dying = [a for a in self.allies(p) if a.is_pc and a.hp < 0 and not a.stable]
        tgt = dying[0] if len(dying) == 1 else dying[self.ui.choose(
            "Who?", [d.name for d in dying])]
        x.std = False
        if self.engaged_foes(p):
            self.provoke(p, "tends to a fallen friend")
        r = dice.d20()
        tot = r + p.skill_total("Heal")
        self.ui.roll(f"Heal check: d20={r} + {tot - r} = {tot} vs DC 15")
        if tot >= 15:
            tgt.stable = True
            self.ui.good(f"{tgt.name} is stabilized.")
        else:
            self.ui.bad("The bleeding won't stop...")

    def act_turn(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        x.std = False
        p.spend("turn")
        lvl = p.class_level("cleric")
        if "Sun" in getattr(p, "domains", []):
            pass
        r = dice.d20()
        check = r + p.mod("cha")
        if p.skill_ranks.get("Knowledge (religion)", 0) >= 5:
            check += 2
        max_hd = rules.turning_max_hd(check, lvl)
        dmg_roll = dice.roll("2d6")
        pool = dmg_roll.total + lvl + p.mod("cha")
        ui.out(f"{p.name} presents a holy symbol and calls upon {p.deity or 'the divine'}!",
               ("byellow",))
        ui.roll(f"Turning check: d20={r} {p.mod('cha'):+d} = {check} -> affects undead up to "
                f"{max_hd} HD; turning damage {dmg_roll.detail()} + {lvl + p.mod('cha')} = "
                f"{pool} HD")
        undead = sorted([m for m in self.enemies(p) if m.ctype == "undead" and not m.dead
                         and not m.has_tag("turned")], key=lambda m: m.hit_dice())
        any_turned = False
        for m in undead:
            hd = m.hit_dice()
            if hd > max_hd or hd > pool:
                continue
            pool -= hd
            any_turned = True
            if lvl >= 2 * hd:
                ui.good(f"  {m.name} crumbles to dust!")
                m.dead = True
                self.disengage_all(m)
            else:
                m.add_effect(Effect("Turned", ROUNDS_PER_MINUTE, tags=["turned"]))
                self.disengage_all(m)
                ui.good(f"  {m.name} is TURNED and cowers away from the holy light!")
        if not any_turned:
            ui.out("  The undead resist the turning.")

    def act_flee(self, x: CState) -> None:
        p = x.c
        x.std = x.move = False
        if self.engaged_foes(p):
            self.provoke(p, "flees", movement=True)
        if p.conscious:
            self.disengage_all(p)
            self.s(p).fled = True
            self.ui.warn(f"{p.name} flees the battle!")
            # carry any unconscious friends? (no: they stay)

    def act_look(self, x: CState) -> None:
        ui = self.ui
        p = x.c
        i = ui.choose("Look at", ["Battlefield", f"{p.name}'s character sheet",
                                  "A foe (Knowledge check reveals more)"], allow_cancel=True)
        if i == 0:
            self.show_field()
        elif i == 1:
            ui.out(render(p, full=False))
        elif i == 2:
            foes = self.enemies(p)
            if not foes:
                return
            f = foes[ui.choose("Which?", [f.name for f in foes])]
            ui.out(f"{f.name}: {f.block.get('desc', '')}")
            ui.out(f"  Condition: {wound_word(f)}; {f.status_word()}")
            skill = {"undead": "Knowledge (religion)", "animal": "Knowledge (nature)",
                     "humanoid": "Knowledge (local)"}.get(f.ctype, "Knowledge (arcana)")
            if p.skill_ranks.get(skill, 0) > 0:
                r = dice.d20()
                tot = r + p.skill_total(skill)
                dc = 10 + f.hit_dice()
                ui.roll(f"{skill}: d20={r} -> {tot} vs DC {dc}")
                if tot >= dc:
                    ui.good("  " + f.statline())
                    if f.dr():
                        ui.good("  Damage reduction: " + ", ".join(
                            f"{a}/{'bludgeoning' if b == 'B' else 'slashing' if b == 'S' else b}"
                            for a, b in f.dr()))
                    if f.immunities():
                        ui.good(f"  Immune: {', '.join(sorted(set(f.immunities())))}")
                    if f.vulnerabilities():
                        ui.good(f"  Vulnerable: {', '.join(f.vulnerabilities())}")
            else:
                ui.out(f"  (Train {skill} to learn more about such creatures.)")

    # ------------------------------------------------------------ items
    def usable_items(self, p) -> List[dict]:
        if not p.is_pc:
            return []
        out = []
        for e in p.inventory:
            d = item_data(e)
            if d["kind"] == "consumable" and d.get("use") in ("spell", "scroll", "splash"):
                if d.get("use") == "scroll" and not scroll_usable(p, d)[0]:
                    continue
                out.append(e)
        return out

    def act_item(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        items = self.usable_items(p)
        i = ui.choose("Use which item?", [f"{item_name(e)} x{e['qty']}: "
                                          f"{item_data(e).get('desc', '')}" for e in items],
                      allow_cancel=True)
        if i is None:
            return
        e = items[i]
        d = item_data(e)
        if d["use"] == "splash":
            tgt = self._pick_target(p, self.enemies(p), "Throw at whom?")
            if not tgt:
                return
            x.std = False
            if self.engaged_foes(p):
                self.provoke(p, "throws a flask in melee")
            p.remove_item(e, 1)
            if not p.conscious:
                return
            if touch_attack(ui, p, tgt, True, self):
                if d.get("only_vs") and tgt.ctype not in d["only_vs"]:
                    ui.out("  It splashes harmlessly.")
                    return
                r = dice.roll(d["damage"])
                deal_damage(ui, tgt, r.total, d["dtype"], self)
                if e["id"] == "alchemist's fire" and not tgt.dead:
                    tgt.add_effect(Effect("Burning", 1, tags=["_dot"],
                                          data={"dot": "1d6", "dtype": "fire"}))
            return
        spell = d["spell"]
        sp = SPELLS[spell]
        if d["use"] == "scroll":
            kind = sp["target"]
            targets = self._spell_targets(p, spell, kind)
            if targets is None:
                return
            x.std = False
            if self.engaged_foes(p):
                self.provoke(p, "reads a scroll in melee")
                if not p.conscious:
                    return
            if not use_scroll_check(ui, p, d):
                return
            p.remove_item(e, 1)
            lvl = min(v for v in sp["levels"].values())
            cast_spell(ui, p, spell, targets, d.get("cl", 1), 10 + lvl + (lvl + 1) // 2, self,
                       allies=self.allies(p), enemies=self.enemies(p))
            return
        # potion: drink or administer to adjacent ally
        allies = [a for a in self.allies(p) if not a.dead]
        tgt = p
        if len(allies) > 1:
            tgt = allies[ui.choose("Who drinks it?", [f"{a.name} ({a.hp}/{a.max_hp()})"
                                                      for a in allies])]
        x.std = False
        if self.engaged_foes(p):
            self.provoke(p, "uncorks a potion in melee")
            if not p.conscious and tgt is p:
                return
        p.remove_item(e, 1)
        ui.out(f"{tgt.name} drinks {item_name(e)}." if tgt is p else
               f"{p.name} pours {item_name(e)} down {tgt.name}'s throat.")
        cast_spell(ui, tgt, spell, [tgt], d.get("cl", 1), 11, self, allies=[tgt])

    # ------------------------------------------------------------ spells
    def _spell_targets(self, p, spell, kind) -> Optional[List[Creature]]:
        ui = self.ui
        sp = SPELLS[spell]
        if kind == "enemy":
            t = self._pick_target(p, self.enemies(p))
            return [t] if t else None
        if kind == "enemies":
            foes = self.enemies(p)
            if not foes:
                return None
            n = min(sp["max_targets"], len(foes))
            if n == len(foes) and spell in ("Fireball", "Sleep"):
                picks = list(range(len(foes)))
                if not ui.confirm(f"Target all {len(foes)} foes?", True):
                    picks = ui.choose_many("Targets", [f.name for f in foes], n)
            else:
                picks = ui.choose_many("Targets", [f.name for f in foes], n)
            targets = [foes[i] for i in picks]
            if spell == "Fireball":
                caught = [a for a in self.allies(p) if any(self.is_engaged(a, t)
                                                           for t in targets)]
                if caught:
                    ui.warn("WARNING: " + ", ".join(a.name for a in caught) +
                            " will be caught in the blast!")
                    if not ui.confirm("Cast anyway?", False):
                        return None
                    targets += caught
            return targets
        if kind == "ally":
            allies = [a for a in self.allies(p) if not a.dead]
            if len(allies) == 1:
                return allies
            i = ui.choose("Target", [f"{a.name} ({a.hp}/{a.max_hp()} hp)" for a in allies],
                          allow_cancel=True)
            return None if i is None else [allies[i]]
        if kind == "allies":
            return [a for a in self.allies(p) if not a.dead]
        return [p]

    def act_cast(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        casts = [c_ for c_ in p.available_casts() if not SPELLS[c_["spell"]]["utility"]]
        if not casts:
            ui.out("No combat spells available.")
            return
        opts = []
        for c_ in casts:
            tag = " (spontaneous)" if c_.get("spontaneous") else (" (domain)" if c_.get("domain")
                                                                   else "")
            opts.append(f"L{c_['level']} {c_['spell']}{tag}: {SPELLS[c_['spell']]['desc']}")
        i = ui.choose("Cast which spell?", opts, allow_cancel=True)
        if i is None:
            return
        cast = casts[i]
        spell = cast["spell"]
        targets = self._spell_targets(p, spell, SPELLS[spell]["target"])
        if targets is None:
            return
        x.std = False
        lvl = cast["level"]
        p.expend(cast)
        # touch spells on enemies require being in melee
        if spell in ("Inflict Light Wounds", "Inflict Moderate Wounds") or (
                spell.startswith("Cure") and targets and targets[0].ctype == "undead"):
            t = targets[0]
            if not self.is_engaged(p, t):
                if x.move:
                    x.move = False
                    x.moved = True
                    self.engage(p, t)
                    ui.out(f"{p.name} closes in on {t.name}.")
                else:
                    ui.bad("Too far away to touch; the spell is wasted.")
                    return
        if self.engaged_foes(p):
            if ui.confirm(f"You're in melee. Cast defensively (Concentration DC {15 + lvl}) "
                          f"to avoid attacks of opportunity?", True):
                r = dice.d20()
                tot = r + p.skill_total("Concentration") + (4 if p.has_feat("Combat Casting") else 0)
                ui.roll(f"Concentration: d20={r} -> {tot} vs DC {15 + lvl}")
                if tot < 15 + lvl:
                    ui.bad("Concentration broken: the spell is lost!")
                    return
            else:
                taken = self.provoke(p, "casts a spell in melee")
                if not p.conscious:
                    ui.bad("The spell is lost.")
                    return
                if taken:
                    dc = 10 + taken + lvl
                    r = dice.d20()
                    tot = r + p.skill_total("Concentration")
                    ui.roll(f"Concentration after being hit: d20={r} -> {tot} vs DC {dc}")
                    if tot < dc:
                        ui.bad("Concentration broken: the spell is lost!")
                        return
        asf = p.arcane_spell_failure() if CLASSES[cast["class"]].get("caster") == "arcane" else 0
        if asf:
            r = dice.percent()
            if r <= asf:
                ui.bad(f"Arcane spell failure! (d% {r} <= {asf}%) The armor fouls the gestures.")
                return
        cast_spell(ui, p, spell, targets, caster_cl(p, cast), caster_dc(p, cast), self,
                   allies=self.allies(p), enemies=self.enemies(p))
        if p.hp == 0 and not p.dead:
            self._strain(p)

    # ------------------------------------------------------------ monster AI
    def monster_turn(self, x: CState, surprise: bool) -> None:
        m = x.c
        ui = self.ui
        pcs = [p for p in self.enemies(m)]
        able = [p for p in pcs if p.conscious]
        if not pcs:
            return
        block = getattr(m, "block", {})
        # morale
        if block.get("morale") and m.hp <= m.max_hp() / 3 and dice.die(2) == 1:
            ui.warn(f"{m.name} panics and flees!")
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
        targets = able or ([p for p in pcs] if block.get("savage") else [])
        if not targets:
            return
        engaged = [p for p in self.engaged_foes(m) if p in targets]
        melee = [w for w in m.melee_attacks()]
        ranged = [w for w in m.ranged_attacks()]
        single = block.get("single_actions")

        if engaged and melee:
            tgt = min(engaged, key=lambda p: (p.hp, p.ac()))
            self.monster_melee(m, tgt, full=not surprise and not single)
            return
        # ranged option
        use_ranged = ranged and (block.get("prefers_ranged") or not melee or
                                 (dice.percent() <= 30 and self.round <= 2))
        if use_ranged:
            tgt = min(targets, key=lambda p: (p.ac(), p.hp))
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
            return (-(ganged if dice.percent() < 60 else 0), p.hp + dice.die(6))
        tgt = min(targets, key=score)
        self.engage(m, tgt)
        x.moved = True
        ui.out(f"{m.name} rushes at {tgt.name}!")
        if surprise or single:
            return
        self.monster_melee(m, tgt, full=False)

    def monster_melee(self, m, tgt, full: bool) -> None:
        melee = m.melee_attacks()
        naturals = [w for w in melee if w.get("natural")]
        if naturals and full:
            for w in naturals:
                if not self.active(tgt) or (tgt.is_pc and not tgt.conscious
                                            and not m.block.get("savage")):
                    others = [p for p in self.engaged_foes(m) if p.conscious]
                    if not others:
                        return
                    tgt = others[0]
                self.make_attack(m, tgt, w, m.bab())
            return
        w = naturals[0] if naturals else melee[0]
        babs = rules.iterative_attacks(m.bab()) if full else [m.bab()]
        for b in babs:
            if not self.active(tgt):
                return
            self.make_attack(m, tgt, w, b)


def award_xp(ui, party, monsters, party_level: int) -> int:
    alive = [p for p in party if not p.dead]
    if not alive or not monsters:
        return 0
    total = sum(rules.xp_award(party_level, m.cr) for m in monsters)
    each = total // len(alive)
    for p in alive:
        p.xp += each
    ui.good(f"Each surviving hero earns {each} XP.")
    for p in alive:
        if p.can_level_up():
            ui.warn(f"{p.name} has enough experience to reach level {p.level + 1}! "
                    f"(Rest or use 'level up' from the menu.)")
    return each
