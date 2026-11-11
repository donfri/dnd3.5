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
from .data.items import item_data, item_name
from .data.spells import SPELLS
from .effects import Effect, ROUNDS_PER_MINUTE
from .abilities import (inspire_courage, lay_on_hands, revert_shape, wholeness_of_body,
                        wild_shape)
from .data.classes import CLASSES
from .data.monsters import MONSTERS
from .magic import (call_bolt, cast_spell, caster_cl, caster_dc, consume_one_shot, deal_damage,
                    device_spells, drain_level, pay_metamagic, pick_metamagic, saving_throw,
                    use_device_check, scroll_usable, touch_attack, use_scroll_check)
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
        self.deflect_used = False
        self.stepped = False
        self.delayed = False
        self.readied: Optional[dict] = None
        self.quickened = False

    @property
    def single(self) -> bool:
        """Surprise round or slowed: one move OR one standard action."""
        return self.surprise or self.c.has_tag("slowed")


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
        # animal companions fight alongside their masters
        self.companions: List[Creature] = []
        for p in self.party:
            comp = p.companion_creature() if hasattr(p, "companion_creature") else None
            if comp is not None and not comp.dead and not p.dead:
                comp.effects = [e for e in comp.effects if e.duration is None
                                and not (e.tags & {"prone", "grappled"})]
                self.companions.append(comp)
                self.st[comp.uid] = CState(comp, "pc")
                if id(p) in self.surprised:
                    self.surprised.add(id(comp))
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
            for e in list(p.effects):
                if e.tags & {"prone", "charging", "total_defense", "fighting_defensively",
                             "_spiritual_weapon", "_sphere", "_stun_primed", "_smite",
                             "stunned", "dazed", "entangled", "frightened", "grappled",
                             "pinned"} \
                        or e.name in ("Dazed", "Turned"):
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
        flat = self.is_flat_footed(target) or target.helpless() or (
            target.has_tag("grappled") and self.grapple_partner(target) is not attacker)
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
            attacker.remove_effect("Stunning Fist")
            return False
        # deflect arrows
        if ranged and not w.get("ray") and target.has_feat("Deflect Arrows") \
                and target.uid in self.st and not self.s(target).deflect_used \
                and not self.is_flat_footed(target) and target.conscious:
            self.s(target).deflect_used = True
            ui.good(f"  {target.name} snatches the missile out of the air (Deflect Arrows)!")
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
        if dmg_type and (attacker.weapon_enhancement(w) > 0 or (
                w.get("wid") == "unarmed strike" and
                getattr(attacker, "class_level", lambda c: 0)("monk") >= 4)):
            dmg_type += "*"   # magic weapon: overcomes DR x/magic
        deal_damage(ui, target, total, dmg_type, self, magic=False)
        if attacker.remove_effect("Stunning Fist") and not target.dead:
            if "stun" in target.immunities() or not target.is_living():
                ui.out(f"  {target.name} can't be stunned.")
            else:
                lvl = getattr(attacker, "level", attacker.hit_dice())
                dc = 10 + lvl // 2 + attacker.mod("wis")
                if not saving_throw(ui, target, "fort", dc, ["stun"], "Stunning Fist"):
                    target.add_effect(Effect("Stunned", 1, tags=["stunned"]))
                    ui.warn(f"  {target.name} is STUNNED!")
        special = w.get("special") or {}
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
                if not saving_throw(ui, target, "fort", ad["dc"], [], ad["name"]):
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

    def trip(self, attacker, target, w: Optional[dict] = None, counter: bool = True) -> bool:
        """Opposed trip check (the touch attack, if any, is already made). True if the
        target falls."""
        ui = self.ui
        if rules.SIZES.index(target.size) - rules.SIZES.index(attacker.size) >= 2:
            ui.out(f"  {target.name} is far too big to trip.")
            return False
        ra, rd = dice.d20(), dice.d20()
        ba = attacker.mod("str") + rules.SIZE_GRAPPLE[attacker.size]
        if attacker.has_feat("Improved Trip"):
            ba += 4
        if w:
            ba += w.get("trip_bonus", 0)
        bd = max(target.mod("str"), target.mod("dex")) + rules.SIZE_GRAPPLE[target.size]
        bd += getattr(target, "race_data", {}).get("stability", 0)
        if target.ctype in ("animal", "magical beast", "vermin") and not target.is_pc:
            bd += 4   # more than two legs
        ok = ra + ba > rd + bd
        ui.roll(f"Trip: {attacker.name} d20={ra}{ba:+d} = {ra + ba} vs {target.name} "
                f"d20={rd}{bd:+d} = {rd + bd}")
        if ok:
            target.add_effect(Effect("Prone", None, tags=["prone"]))
            ui.warn(f"  {target.name} is knocked prone!")
            return True
        if counter and attacker.is_pc and target.conscious and not target.has_tag("prone"):
            ui.out(f"  {target.name} keeps its footing and tries to trip {attacker.name} back!")
            self.trip(target, attacker, counter=False)
        return False

    def disarmable(self, f: Creature) -> bool:
        if f.is_pc:
            return bool(f.equipped("main"))
        return any(not item_data(e).get("ranged") for e in getattr(f, "weapons", []))

    def _maneuver_target(self, p, pool, prompt):
        if not pool:
            self.ui.out("No one in reach.")
            return None
        return self._pick_target(p, pool, prompt)

    def act_trip(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, self.engaged_foes(p), "Trip whom?")
        if not tgt:
            return
        x.std = False
        w = self.best_melee(p)
        if not p.has_feat("Improved Trip"):
            if self.aoo_from(tgt, p, "reaches out to trip") and not p.conscious:
                return
        if not p.conscious:
            return
        if not touch_attack(ui, p, tgt, False, self):
            return
        if self.trip(p, tgt, w) and p.has_feat("Improved Trip") and w and not tgt.dead:
            ui.good(f"  Improved Trip: {p.name} follows up with a free attack!")
            self.make_attack(p, tgt, w, p.bab(), power=getattr(p, "power_attack", 0))

    def act_disarm(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if self.disarmable(f)],
                                    "Disarm whom?")
        if not tgt:
            return
        x.std = False
        w = self.best_melee(p)
        if not p.has_feat("Improved Disarm"):
            self.aoo_from(tgt, p, "lunges for their weapon")
            if not p.conscious:
                return
        tw = self.best_melee(tgt)
        if not w or not tw:
            ui.out("  Nothing to disarm with.")
            return

        def opposed(cr, wi):
            b = sum(v for _, v, _ in cr.attack_components(wi))
            if wi.get("two_handed"):
                b += 4
            elif wi.get("light") and not wi.get("natural"):
                b -= 4
            b += rules.SIZE_GRAPPLE[cr.size]
            return b

        ba = opposed(p, w) + (4 if p.has_feat("Improved Disarm") else 0) + w.get("disarm_bonus", 0)
        bd = opposed(tgt, tw)
        ra, rd = dice.d20(), dice.d20()
        ui.roll(f"Disarm: {p.name} d20={ra}{ba:+d} = {ra + ba} vs {tgt.name} "
                f"d20={rd}{bd:+d} = {rd + bd}")
        if ra + ba <= rd + bd:
            ui.out(f"  {tgt.name} keeps a firm grip.")
            return
        if tgt.is_pc:
            main = tgt.equipped("main")
            main.pop("slot", None)
        else:
            entry = next(e for e in tgt.weapons if not item_data(e).get("ranged"))
            tgt.weapons.remove(entry)
            tgt.add_effect(Effect("Disarmed", None, tags=["disarmed"], data={"entry": entry}))
        ui.warn(f"  {tgt.name}'s {tw['name'].lower()} goes clattering away!")

    def act_grapple(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, self.engaged_foes(p), "Grapple whom?")
        if not tgt:
            return
        if rules.SIZES.index(tgt.size) - rules.SIZES.index(p.size) >= 2:
            ui.bad(f"{tgt.name} is far too big to wrestle.")
            return
        x.std = False
        if not p.has_feat("Improved Grapple"):
            if self.aoo_from(tgt, p, "tries to grab hold"):
                ui.out("  The blow breaks the attempt to grab hold.")
                return
            if not p.conscious:
                return
        if not touch_attack(ui, p, tgt, False, self):
            return
        if not self.grapple_check(p, tgt, "Grapple"):
            return
        p.add_effect(Effect("Grappling", None, tags=["grappled"], data={"with": tgt.uid}))
        tgt.add_effect(Effect("Grappling", None, tags=["grappled"], data={"with": p.uid}))
        ui.warn(f"  {p.name} and {tgt.name} are locked in a grapple! (Neither can move away; "
                f"others hit them more easily.)")
        if p.has_feat("Improved Unarmed Strike") or p.wild_form():
            self.unarmed_damage(p, tgt)

    def act_grapple_hurt(self, x: CState, partner: Creature) -> None:
        x.std = False
        if self.grapple_check(x.c, partner, "Grapple (damage)"):
            self.unarmed_damage(x.c, partner)

    def act_grapple_pin(self, x: CState, partner: Creature) -> None:
        x.std = False
        if self.grapple_check(x.c, partner, "Grapple (pin)"):
            partner.add_effect(Effect("Pinned", 1, [("ac", "untyped", -4)],
                                      tags=["pinned", "dazed"]))
            self.ui.warn(f"  {partner.name} is PINNED and can't act next turn!")

    def act_grapple_escape(self, x: CState, partner: Creature) -> None:
        x.std = False
        p = x.c
        r = dice.d20()
        ea = max(p.skill_total("Escape Artist") if p.is_pc else -99,
                 p.grapple() + (4 if p.has_feat("Improved Grapple") else 0))
        rd = dice.d20()
        bd = partner.grapple() + (4 if partner.has_feat("Improved Grapple") else 0)
        self.ui.roll(f"Escape: {p.name} d20={r}{ea:+d} = {r + ea} vs {partner.name} "
                     f"d20={rd}{bd:+d} = {rd + bd}")
        if r + ea > rd + bd:
            self.end_grapple(p)
        else:
            self.ui.out(f"  {p.name} can't break the hold.")

    def act_bull_rush(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, self.engaged_foes(p), "Bull rush whom?")
        if not tgt:
            return
        x.std = False
        if not p.has_feat("Improved Bull Rush"):
            self.aoo_from(tgt, p, "barrels into them")
            if not p.conscious:
                return
        ra, rd = dice.d20(), dice.d20()
        ba = p.mod("str") + rules.SIZE_GRAPPLE[p.size] + (4 if p.has_feat("Improved Bull Rush")
                                                         else 0)
        bd = tgt.mod("str") + rules.SIZE_GRAPPLE[tgt.size] + \
            getattr(tgt, "race_data", {}).get("stability", 0)
        ui.roll(f"Bull rush: {p.name} d20={ra}{ba:+d} = {ra + ba} vs {tgt.name} "
                f"d20={rd}{bd:+d} = {rd + bd}")
        if ra + ba > rd + bd:
            if tgt.get_effect("Grappling"):
                self.end_grapple(tgt)
            self.disengage_all(tgt)
            ui.warn(f"  {tgt.name} is shoved back out of the melee! It will have to come "
                    f"back in.")
        else:
            ui.out(f"  {tgt.name} doesn't budge.")

    def act_step(self, x: CState) -> None:
        p = x.c
        foe = self.engaged_foes(p)[0]
        x.move = False
        x.stepped = True
        self.disengage_all(p)
        self.ui.out(f"{p.name} takes a careful step back from {foe.name}.")

    def act_ready(self, x: CState) -> None:
        p = x.c
        w = self._choose_weapon(p, x=x)
        if not w:
            return
        if not w.get("wielded"):
            self.ui.bad("Ready a weapon you're holding.")
            return
        x.std = False
        x.move = False
        x.readied = {"w": w}
        what = ("the first foe who closes in on anyone in the party" if w["ranged"]
                else "the first foe who comes at them")
        self.ui.out(f"{p.name} readies {w['name']} and waits to strike {what}.")

    def later_this_round(self, x: CState) -> List[CState]:
        acted = getattr(self, "acted", set())
        return [y for y in self.order if id(y) not in acted and y is not x
                and self.active(y.c)]

    def act_delay(self, x: CState, later: List[CState]) -> None:
        i = self.ui.choose("Act right after whom?", [y.c.name for y in later],
                           allow_cancel=True)
        if i is None:
            return
        after = later[i]
        self.order.remove(x)
        self.order.insert(self.order.index(after) + 1, x)
        self.acted.discard(id(x))
        x.delayed = True
        x.std = x.move = False   # ends this turn; the real one comes later
        self.ui.out(f"{x.c.name} waits for the right moment (acts after {after.c.name}).")

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
            self.aoo_from(foe, mover, reason, movement)
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

    def close_in(self, mover: Creature, tgt: Creature) -> bool:
        """Mover steps into melee with tgt. Reach and readied actions may strike first.
        Returns False if the mover was dropped on the way in."""
        if self.has_reach(tgt) and not self.has_reach(mover) and not self.is_engaged(mover, tgt):
            w = self.reach_weapon(tgt)
            if w:
                self.aoo_from(tgt, mover, f"has to close past {tgt.name}'s long reach",
                              movement=True, w=w)
        if not self.active(mover) or not mover.conscious:
            return False
        self.engage(mover, tgt)
        self.trigger_readied(mover, tgt)
        return self.active(mover) and mover.conscious

    def trigger_readied(self, mover: Creature, tgt: Creature) -> None:
        for x in list(self.st.values()):
            r = x.readied
            if not r or x.side == self.s(mover).side or not self.active(x.c) \
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
        if partner is not None:
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

            single = x.single
            grappled = p.has_tag("grappled")
            entangled = p.has_tag("entangled") or grappled
            full_ok = (x.std and (x.move or x.stepped) and not x.moved and not single
                       and not disabled)
            foes_all = self.enemies(p)
            if x.std:
                add("Attack (standard action; moves into melee first if needed)", self.act_attack,
                    x, False)
            if full_ok:
                add("Full attack (all your attacks; must already be in position)",
                    self.act_attack, x, True)
            if full_ok and x.move:
                if not p.has_tag("fatigued") and not entangled:
                    add("Charge (+2 attack, -2 AC; move and attack a foe you're not engaged with)",
                        self.act_charge, x)
                if p.has_feat("Spring Attack") and not entangled and \
                        any(not self.is_engaged(p, f) for f in foes_all):
                    add("Spring Attack: dart in, strike, and dart back out (full round)",
                        self.act_spring, x)
            if x.std and p.uses_left("smite"):
                add(f"Smite evil ({p.uses_left('smite')} left): attack +Cha, +"
                    f"{p.class_level('paladin')} damage vs evil", self.act_attack, x, False,
                    "smite")
            if x.std and p.uses_left("stunning_fist") and not p.wild_form():
                add(f"Stunning Fist ({p.uses_left('stunning_fist')} left): unarmed attack that "
                    f"can stun", self.act_attack, x, False, "stun")
            if x.std and p.has_feat("Manyshot") and p.bab() >= 6 and any(
                    w.get("bow") and p.ammo_count(w["ammo"]) >= 2 for w in p.weapon_infos()):
                add("Manyshot: loose two arrows at once (-4 each)", self.act_manyshot, x)
            partner = self.grapple_partner(p)
            if x.std and partner is not None:
                add(f"Grapple: hurt {partner.name} (opposed grapple check, unarmed damage)",
                    self.act_grapple_hurt, x, partner)
                if not partner.has_tag("pinned"):
                    add(f"Grapple: pin {partner.name} (they lose their next turn)",
                        self.act_grapple_pin, x, partner)
                add("Grapple: break free (opposed grapple check)", self.act_grapple_escape, x,
                    partner)
            elif x.std and eng and not p.wild_form():
                add("Trip a foe (knock them prone)", self.act_trip, x)
                if any(self.disarmable(f) for f in eng):
                    add("Disarm a foe (knock their weapon away)", self.act_disarm, x)
                add("Grapple a foe (wrestle them; they can't move away)", self.act_grapple, x)
                add("Bull rush a foe (shove them out of melee)", self.act_bull_rush, x)
            elif x.std and eng:
                add("Trip a foe (knock them prone)", self.act_trip, x)
                add("Bull rush a foe (shove them out of melee)", self.act_bull_rush, x)
            lightning = next((e for e in p.effects if "_lightning" in e.tags), None)
            if x.std and lightning and lightning.data.get("bolts", 0) > 0:
                add(f"Call down lightning ({lightning.data['bolts']} bolts left)",
                    self.act_lightning, x, lightning)
            if (x.std or (p.has_feat("Quicken Spell") and not x.quickened)) and \
                    getattr(p, "available_casts", None) and p.available_casts() \
                    and p.can_cast_now():
                add("Cast a spell" if x.std else "Cast a quickened spell (free action)",
                    self.act_cast, x)
            if x.std and self.usable_items(p):
                add("Use an item (potion, scroll, alchemist's fire...)", self.act_item, x)
            if x.std and p.uses_left("turn") and any(m.ctype == "undead" for m in self.enemies(p)):
                add(f"Turn undead ({p.uses_left('turn')} left)", self.act_turn, x)
            if x.std and p.uses_left("music") and p.skill_ranks.get("Perform", 0) >= 3 \
                    and not p.wild_form():
                add(f"Bardic music: inspire courage ({p.uses_left('music')} left)",
                    self.act_music, x)
            hurt = [a for a in self.allies(p) if a.damage > 0 and not a.dead]
            if x.std and p.uses_left("lay_on_hands") and hurt:
                add(f"Lay on hands ({p.uses_left('lay_on_hands')} hp of healing left)",
                    self.act_lay_on_hands, x)
            if x.std and p.uses_left("wholeness") and p.damage > 0:
                add(f"Wholeness of body ({p.uses_left('wholeness')} hp left)",
                    self.act_wholeness, x)
            if x.std and p.uses_left("wild_shape") and not p.wild_form():
                add(f"Wild shape: become an animal ({p.uses_left('wild_shape')} left)",
                    self.act_wild_shape, x)
            if x.std and p.wild_form():
                add("Return to your normal form", self.act_revert, x)
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
                if foes and not entangled:
                    add("Move into melee with a foe (move action)", self.act_approach, x)
                if eng and not entangled:
                    add("Move away from melee (move action, provokes attacks of opportunity)",
                        self.act_move_away, x)
                if (len(eng) == 1 and not x.moved and not entangled
                        and not self.has_reach(eng[0])):
                    add(f"5-foot step back from {eng[0].name} (no attack of opportunity; no "
                        f"other movement this turn)", self.act_step, x)
                if not p.wild_form():
                    add("Draw / switch weapon (move action)", self.act_draw, x)
            if eng and full_ok and x.move and not entangled:
                add("Withdraw (full round: leave melee safely)", self.act_withdraw, x)
            if x.std:
                add("Total defense (+4 dodge AC until your next turn)", self.act_total_defense, x)
            if x.std and not single:
                add("Ready an attack (strike the first foe who comes at you)", self.act_ready, x)
            later = self.later_this_round(x)
            if x.std and x.move and not x.moved and not x.stepped and not single and later:
                add("Delay (take your turn later this round)", self.act_delay, x, later)
            if p.has_feat("Power Attack"):
                add(f"Set Power Attack (now {p.power_attack})", self.act_power, x)
            if not p.get_effect("Fighting defensively") and x.std:
                add("Toggle: fight defensively this turn (-4 attack, +2 AC)", self.act_defensive, x)
            add("Look: battlefield / my character sheet / foe details", self.act_look, x)
            if self.can_flee and full_ok and x.move and not entangled:
                add("Flee the battle (withdraw out of the fight)", self.act_flee, x)
            add("End turn", None)
            groups = []
            for a in acts:
                lab = a[0]
                if lab.startswith(("Attack", "Full attack", "Charge", "Cast", "Use an item",
                                   "Turn undead", "Rage", "Feat of Strength", "Smite",
                                   "Stunning", "Manyshot", "Spring", "Call down", "Bardic",
                                   "Lay on", "Wholeness", "Wild shape", "Return to",
                                   "Trip", "Disarm", "Grapple", "Bull rush")):
                    groups.append("Fight")
                elif lab.startswith(("Move", "Stand", "Draw", "Withdraw", "Flee", "5-foot")):
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
            if x.single and (x.std, x.move) != before:
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

    def act_attack(self, x: CState, full: bool, mode: Optional[str] = None) -> None:
        p = x.c
        ui = self.ui
        foes = self.enemies(p)
        partner = self.grapple_partner(p)
        if partner is not None:
            light = [w for w in p.weapon_infos() if not w["ranged"] and w.get("wielded")
                     and (w.get("light") or w.get("natural") or w.get("wid") == "unarmed strike")]
            if not light:
                from .creature import weapon_info_from_entry
                from .data.items import make_item
                light = [dict(weapon_info_from_entry(make_item("unarmed strike"), p.size),
                              wielded="main")]
            w = light[0] if len(light) == 1 else light[ui.choose(
                "In a grapple you can only use a light weapon, natural weapons or your fists:",
                [lw["name"] for lw in light])]
            if mode == "stun" and w.get("wid") != "unarmed strike":
                mode = None
            sit = []
            x.std = False
            if full:
                x.move = False
                for b in rules.iterative_attacks(p.bab()):
                    if partner.dead:
                        break
                    self.make_attack(p, partner, w, b, power=0)
            else:
                if mode == "stun":
                    p.spend("stunning_fist")
                    p.add_effect(Effect("Stunning Fist", 1, tags=["_stun_primed"], hidden=True))
                self.make_attack(p, partner, w, p.bab(), power=0)
                p.remove_effect("Stunning Fist")
            return
        if mode == "stun":
            w = next((w for w in p.weapon_infos() if w.get("wid") == "unarmed strike"), None)
            if w is None:
                ui.bad("You need your fists free for that.")
                return
        else:
            w = self._choose_weapon(p, want_ranged=False if mode == "smite" else None, x=x)
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
            if not x.move or x.single or p.has_tag("entangled"):
                foes = [f for f in foes if self.is_engaged(p, f) or (
                    w.get("reach") and any(self.is_engaged(a, f) for a in self.allies(p)
                                           if a is not p))] or foes
            tgt = self._pick_target(p, foes)
            if not tgt:
                return
            if not self._ready_weapon(x, w):
                return
            reach_ok = w.get("reach") and any(self.is_engaged(a, tgt) for a in self.allies(p)
                                              if a is not p)
            if reach_ok and not self.is_engaged(p, tgt):
                ui.out(f"{p.name} strikes at {tgt.name} from behind the front line with "
                       f"{w['name']} (reach).")
            elif not self.is_engaged(p, tgt):
                if full:
                    ui.bad("You must already be in melee with that foe to full attack.")
                    return
                if p.has_tag("entangled"):
                    ui.bad("You're entangled and can't move to reach that foe.")
                    return
                if x.single:
                    ui.bad("You get only one action this turn: move OR attack, not both. "
                           "Choose 'Move into melee' instead.")
                    return
                if not x.move:
                    ui.bad("No move action left to close the distance.")
                    return
                x.move = False
                x.moved = True
                ui.out(f"{p.name} closes in on {tgt.name}.")
                if not self.close_in(p, tgt):
                    x.std = False
                    return
        sit = []
        if p.get_effect("Fighting defensively"):
            sit.append(("untyped", -4, "fighting defensively"))
        power = p.power_attack if not w["ranged"] else 0
        if not full:
            x.std = False
            if not self._spend_ammo(p, w):
                return
            extra = 0
            if mode == "smite":
                p.spend("smite")
                cha = max(0, p.mod("cha"))
                if tgt.evil:
                    ui.out(f"{p.name} calls on holy power to SMITE {tgt.name}!", ("byellow",))
                    if cha:
                        sit.append(("untyped", cha, "smite evil"))
                    extra = p.class_level("paladin")
                else:
                    ui.out(f"{p.name} attempts to smite, but {tgt.name} is not evil: the "
                           f"smite is wasted.")
            elif mode == "stun":
                p.spend("stunning_fist")
                p.add_effect(Effect("Stunning Fist", 1, tags=["_stun_primed"], hidden=True))
                ui.out(f"{p.name} strikes at a nerve cluster...")
            self.make_attack(p, tgt, w, p.bab(), sit, power=power, extra_damage=extra)
            p.remove_effect("Stunning Fist")
            if p.hp == 0 and not p.dead:
                self._strain(p)
            return
        x.std = x.move = False
        x.full_used = True
        self.full_attack(p, tgt, w, sit, power)

    def full_attack(self, p, tgt, w, sit, power):
        ui = self.ui
        if w.get("natural"):
            for nat in p.natural_attacks():
                if not self.active(tgt) or tgt.dead:
                    alts = [f for f in self.engaged_foes(p)]
                    if not alts:
                        return
                    tgt = alts[0]
                self.make_attack(p, tgt, nat, p.bab(), sit, power=power)
                if not p.conscious:
                    return
            return
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
        monk = getattr(p, "class_level", lambda c: 0)("monk")
        if (monk and not w["ranged"] and not twf and p.monk_unarmored()
                and w.get("wid") in ("unarmed strike", "quarterstaff", "club", "dagger",
                                     "handaxe", "javelin")
                and ui.confirm("Flurry of blows (one extra attack"
                               + (", all attacks " + str(-2 if monk <= 4 else -1)
                                  if monk <= 8 else "") + ")?", True)):
            extra += 1
            if monk <= 8:
                sit = sit + [("untyped", -2 if monk <= 4 else -1, "flurry of blows")]
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
            off_babs = [babs[0]]
            if p.has_feat("Improved Two-Weapon Fighting"):
                off_babs.append(babs[0] - 5)
            for b in off_babs:
                if not self.active(tgt) or tgt.dead:
                    alts = [f for f in self.engaged_foes(p)]
                    if not alts:
                        return
                    tgt = alts[0]
                self.make_attack(p, tgt, offhand, b, sit, offhand=True, twf=True, power=power)
                if not p.conscious:
                    return

    def act_manyshot(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        bows = [w for w in p.weapon_infos() if w.get("bow") and p.ammo_count(w["ammo"]) >= 2]
        w = bows[0]
        tgt = self._pick_target(p, self.enemies(p), "Manyshot at whom?")
        if not tgt or not self._ready_weapon(x, w):
            return
        x.std = False
        if self.engaged_foes(p):
            self.provoke(p, "shoots while in melee")
            if not p.conscious:
                return
        ui.out(f"{p.name} nocks two arrows at once and lets fly!")
        for _ in range(2):
            if tgt.dead or not self._spend_ammo(p, w):
                return
            self.make_attack(p, tgt, w, p.bab(), [("untyped", -4, "Manyshot")])

    def act_spring(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f)]
        tgt = self._pick_target(p, foes, "Spring at whom?")
        if not tgt:
            return
        w = self.best_melee(p)
        if not w or w["ranged"]:
            ui.bad("You need a melee weapon in hand.")
            return
        x.std = x.move = False
        x.moved = True
        if self.engaged_foes(p):
            self.provoke(p, "darts away", movement=True)
            if not p.conscious:
                return
            self.disengage_all(p)
        ui.out(f"{p.name} darts in at {tgt.name}...")
        if not self.close_in(p, tgt):
            return
        self.make_attack(p, tgt, w, p.bab(), power=p.power_attack)
        if p.conscious:
            self.disengage_all(p)
            ui.out("...and springs back out of reach.")

    def act_lightning(self, x: CState, e) -> None:
        p = x.c
        tgt = self._pick_target(p, self.enemies(p), "Call lightning on whom?")
        if not tgt:
            return
        x.std = False
        call_bolt(self.ui, p, e, tgt, self)

    def act_music(self, x: CState) -> None:
        x.std = False
        inspire_courage(self.ui, x.c, self.allies(x.c))

    def act_lay_on_hands(self, x: CState) -> None:
        p = x.c
        hurt = [a for a in self.allies(p) if a.damage > 0 and not a.dead]
        tgt = hurt[0] if len(hurt) == 1 else hurt[self.ui.choose(
            "Lay hands on whom?", [f"{a.name} ({a.hp}/{a.max_hp()})" for a in hurt])]
        if tgt is not p and not self.is_engaged(p, tgt) and self.engaged_foes(p):
            pass  # adjacency is abstract: allies are always within reach
        x.std = False
        lay_on_hands(self.ui, p, tgt)

    def act_wholeness(self, x: CState) -> None:
        x.std = False
        wholeness_of_body(self.ui, x.c)

    def act_wild_shape(self, x: CState) -> None:
        if wild_shape(self.ui, x.c):
            x.std = False

    def act_revert(self, x: CState) -> None:
        x.std = False
        revert_shape(self.ui, x.c)

    def _strain(self, p):
        p.damage += 1
        p.check_death()
        self.ui.bad(f"{p.name} strains while disabled and takes 1 damage ({p.hp} hp)!")
        self.after_damage(p)

    def act_charge(self, x: CState) -> None:  # noqa: C901
        p = x.c
        if p.has_tag("entangled"):
            self.ui.bad("You're entangled!")
            return
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
        p.add_effect(Effect("Charging", 1, tags=["charging"]))
        self.ui.out(f"{p.name} CHARGES {tgt.name}!")
        if not self.close_in(p, tgt):
            return
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
        self.ui.out(f"{p.name} moves into melee with {tgt.name}.")
        self.close_in(p, tgt)

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
        lvl = p.turn_level()
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
            bard = p.class_level("bard")
            if p.skill_ranks.get(skill, 0) > 0 or bard:
                r = dice.d20()
                tot = r + p.skill_total(skill) if p.skill_ranks.get(skill, 0) > 0 else 0
                label = skill
                if bard and r + bard + p.mod("int") > tot:
                    tot = r + bard + p.mod("int")
                    label = "Bardic knowledge"
                dc = 10 + f.hit_dice()
                ui.roll(f"{label}: d20={r} -> {tot} vs DC {dc}")
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
        if not p.is_pc or p.wild_form():
            return []
        out = []
        for e in p.inventory:
            d = item_data(e)
            if d["kind"] in ("wand", "staff"):
                out.append(e)
                continue
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
        if d["kind"] in ("wand", "staff"):
            spells = [s_ for s_, _ in device_spells(d)]
            spell = spells[0] if len(spells) == 1 else spells[ui.choose(
                "Cast which spell?", spells, allow_cancel=True) or 0]
            targets = self._spell_targets(p, spell, SPELLS[spell]["target"])
            if targets is None:
                return
            x.std = False
            if self.engaged_foes(p):
                self.provoke(p, f"uses {item_name(e).split(' (')[0].lower()} in melee")
                if not p.conscious:
                    return
            if use_device_check(ui, p, d, spell):
                from .magic import device_cast
                device_cast(ui, p, e, spell, targets, self, allies=self.allies(p),
                            enemies=self.enemies(p))
            return
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
        if kind == "summon":
            return [p]
        if kind == "creature":
            pool = [c_ for c_ in self.allies(p) + self.enemies(p) if not c_.dead]
            t = self._pick_target(p, pool, "Target (friend or foe)")
            return [t] if t else None
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
        casts = [c_ for c_ in p.available_casts() if not SPELLS[c_["spell"]]["utility"]
                 and SPELLS[c_["spell"]]["combat"]]
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
        meta = pick_metamagic(ui, p, cast)
        if meta is None:
            return
        if not x.std and "Quicken Spell" not in meta.get("feats", ()):
            ui.bad("You've used your standard action; only a quickened spell is possible now.")
            return
        if "Quicken Spell" in meta.get("feats", ()) and x.quickened:
            ui.bad("You can cast only one quickened spell per round.")
            return
        targets = self._spell_targets(p, spell, SPELLS[spell]["target"])
        if targets is None:
            return
        if "Quicken Spell" in meta.get("feats", ()):
            x.quickened = True
        else:
            x.std = False
            if meta and not CLASSES[cast["class"]].get("prepared") and not meta.get("rod"):
                x.move = False   # spontaneous metamagic takes a full round
        lvl = cast["level"]
        if meta:
            pay_metamagic(p, cast, meta)
        else:
            p.expend(cast)
        # touch spells on enemies require being in melee
        if spell in ("Inflict Light Wounds", "Inflict Moderate Wounds", "Bestow Curse",
                     "Poison", "Slay Living") or (
                spell.startswith("Cure") and targets and targets[0].ctype == "undead"):
            t = targets[0]
            if not self.is_engaged(p, t):
                if x.move:
                    x.move = False
                    x.moved = True
                    ui.out(f"{p.name} closes in on {t.name}.")
                    if not self.close_in(p, t):
                        ui.bad("The spell is lost.")
                        return
                else:
                    ui.bad("Too far away to touch; the spell is wasted.")
                    return
        if p.has_tag("grappled"):
            dc = 20 + lvl
            r = dice.d20()
            tot = r + p.skill_total("Concentration")
            ui.roll(f"Concentration while grappling: d20={r} -> {tot} vs DC {dc}")
            if tot < dc:
                ui.bad("Wrestling for your life, you botch the spell!")
                return
        elif self.engaged_foes(p):
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
        asf = p.arcane_spell_failure(cast["class"])
        if asf:
            r = dice.percent()
            if r <= asf:
                ui.bad(f"Arcane spell failure! (d% {r} <= {asf}%) The armor fouls the gestures.")
                return
        cast_spell(ui, p, spell, targets, caster_cl(p, cast), caster_dc(p, cast), self,
                   allies=self.allies(p), enemies=self.enemies(p),
                   meta=meta.get("feats", ()))
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
            ui.out(f"{m.name} crushes {partner.name} in its grip!")
            self.monster_melee(m, partner, full=True)
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
        x.moved = True
        ui.out(f"{m.name} rushes at {tgt.name}!")
        if not self.close_in(m, tgt):
            return
        if surprise or single:
            return
        self.monster_melee(m, tgt, full=False)

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
        self.st[m.uid] = x
        self.companions.append(m)
        idx = self.order.index(self.s(caster)) + 1 if self.s(caster) in self.order else len(
            self.order)
        self.order.insert(idx, x)
        if hasattr(self, "acted"):
            self.acted.add(id(x))   # it acts from next round
        self.ui.good(f"  A {MONSTERS[key]['name'].lower()} appears beside {caster.name}, "
                     f"ready to fight for {rounds} rounds.")

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
        if not self.is_engaged(comp, t):
            if comp.has_tag("entangled"):
                ui.out(f"{comp.name} is stuck in the plants.")
                return
            ui.out(f"{comp.name} lunges at {t.name}!")
            if not self.close_in(comp, t):
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
