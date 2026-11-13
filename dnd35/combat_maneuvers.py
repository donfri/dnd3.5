"""Special combat actions: trip, disarm, grapple, bull rush, sunder, feint, overrun,
aid another, coup de grace, demoralize, ready, delay and class stances."""

from __future__ import annotations

from typing import List, Optional

from . import dice, rules
from .creature import Creature
from .data.items import item_data
from .effects import Effect
from .magic import saving_throw, touch_attack

from .combat_base import CState


class ManeuversMixin:
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
            self.disengage_all(tgt, retreat=5 * (1 + max(0, (ra + ba - rd - bd) // 5)))
            ui.warn(f"  {tgt.name} is shoved back out of the melee! It will have to come "
                    f"back in.")
        else:
            ui.out(f"  {tgt.name} doesn't budge.")

    def act_sunder(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if self.disarmable(f)],
                                    "Whose weapon?")
        if not tgt:
            return
        x.std = False
        w = self.best_melee(p)
        tw = self.best_melee(tgt)
        if not p.has_feat("Improved Sunder"):
            self.aoo_from(tgt, p, "swings at their weapon")
            if not p.conscious:
                return
        ba = sum(v for _, v, _ in p.attack_components(w)) + rules.SIZE_GRAPPLE[p.size] + (
            4 if p.has_feat("Improved Sunder") else 0) + (4 if w.get("two_handed") else 0)
        bd = sum(v for _, v, _ in tgt.attack_components(tw)) + rules.SIZE_GRAPPLE[tgt.size] + (
            4 if tw.get("two_handed") else 0)
        need = 10 * tw.get("enhancement", 0)   # magic weapons are much tougher
        ra, rd = dice.d20(), dice.d20()
        ui.roll(f"Sunder: {p.name} d20={ra}{ba:+d} = {ra + ba} vs {tgt.name} "
                f"d20={rd}{bd:+d} = {rd + bd}" + (f" (needs to win by {need})" if need else ""))
        if ra + ba - (rd + bd) <= need:
            ui.out(f"  {tgt.name}'s {tw['name'].lower()} holds.")
            return
        if tgt.is_pc:
            e = tgt.equipped("main")
            tgt.inventory.remove(e)
        else:
            e = next(e for e in tgt.weapons if not item_data(e).get("ranged"))
            tgt.weapons.remove(e)
        ui.warn(f"  CRACK! {tgt.name}'s {tw['name'].lower()} shatters!")

    def act_feint(self, x: CState, move: bool = False) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if not f.helpless()],
                                    "Feint against whom?")
        if not tgt:
            return
        if move:
            x.move = False
        else:
            x.std = False
        r = dice.d20()
        bluff = r + p.skill_total("Bluff")
        rd = dice.d20()
        sense = rd + tgt.skill_total("Sense Motive") + tgt.bab()
        if tgt.ctype in ("animal",):
            sense += 8   # hard to fool an animal
        if (tgt.ability("int") or 0) < 3 or getattr(tgt, "block", {}).get("mindless"):
            ui.out(f"  {tgt.name} is too mindless to be fooled.")
            return
        ui.roll(f"Feint: {p.name} Bluff {bluff} vs {tgt.name} Sense Motive {sense}")
        if bluff > sense:
            tgt.add_effect(Effect("Feinted", 2, tags=[], data={"by": p.uid}, hidden=True))
            ui.good(f"  {tgt.name} falls for it: {p.name}'s next attack catches it off guard!")
        else:
            ui.out(f"  {tgt.name} doesn't bite.")

    def act_demoralize(self, x: CState) -> None:
        """Intimidate: a foe within 30 ft is shaken for a round (or more)."""
        p = x.c
        ui = self.ui
        foes = [f for f in self.enemies(p) if self.distance(p, f) <= 30
                and not f.helpless() and "fear" not in f.immunities()
                and f.ctype not in ("undead", "construct", "vermin", "ooze", "plant")]
        tgt = self._maneuver_target(p, foes, "Demoralize whom?")
        if not tgt:
            return
        x.std = False
        with dice.rolling(p, "Intimidate"):
            r = dice.d20()
        tot = r + p.skill_total("Intimidate")
        hd = getattr(tgt, "hd", None) or getattr(tgt, "level", 1)
        dc = 10 + hd + tgt.mod("wis") + (tgt.bonus("saves_vs_fear") if hasattr(tgt, "bonus")
                                         else 0)
        ui.roll(f"{p.name} Intimidate: d20={r} {p.skill_total('Intimidate'):+d} = {tot} "
                f"vs DC {dc}")
        if tot >= dc:
            rounds = 1 + (tot - dc) // 5
            tgt.add_effect(Effect("Demoralized", rounds, tags=["shaken", "fear_effect"]))
            ui.good(f"  {tgt.name} is shaken for {rounds} round{'s' if rounds > 1 else ''} "
                    f"(-2 on attacks, saves and checks).")
        else:
            ui.out(f"  {tgt.name} is not impressed.")

    def act_overrun(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if not f.incorporeal],
                                    "Overrun whom?")
        if not tgt:
            return
        x.std = False
        imp = p.has_feat("Improved Overrun")
        ra, rd = dice.d20(), dice.d20()
        ba = p.mod("str") + rules.SIZE_GRAPPLE[p.size] + (4 if imp else 0)
        bd = max(tgt.mod("str"), tgt.mod("dex")) + rules.SIZE_GRAPPLE[tgt.size] + \
            getattr(tgt, "race_data", {}).get("stability", 0)
        if tgt.ctype in ("animal", "magical beast", "vermin") and not tgt.is_pc:
            bd += 4
        ui.roll(f"Overrun: {p.name} d20={ra}{ba:+d} = {ra + ba} vs {tgt.name} "
                f"d20={rd}{bd:+d} = {rd + bd}")
        if ra + ba > rd + bd:
            tgt.add_effect(Effect("Prone", None, tags=["prone"]))
            self.s(p).engaged.discard(tgt.uid)
            self.s(tgt).engaged.discard(p.uid)
            ui.warn(f"  {p.name} bowls {tgt.name} over and charges past!")
            others = [f for f in self.enemies(p) if f is not tgt and not self.is_engaged(p, f)
                      and self.reachable(p, f)]
            if others:
                nxt = others[0] if len(others) == 1 else others[ui.choose(
                    "Keep going: engage whom?", [f.name for f in others], default=0)]
                self.close_in(p, nxt)
        else:
            ui.out(f"  {tgt.name} stands firm.")

    def act_aid(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        pairs = [(a, f) for f in self.engaged_foes(p) for a in self.allies(p)
                 if a is not p and self.is_engaged(a, f)]
        labels = [f"Help {a.name} hit {f.name} (+2 attack)" for a, f in pairs] + \
                 [f"Distract {f.name} to protect {a.name} (+2 AC)" for a, f in pairs]
        i = ui.choose("Aid another", labels, allow_cancel=True)
        if i is None:
            return
        x.std = False
        a, f = pairs[i % len(pairs)]
        r = dice.d20()
        bonus = p.bab() + p.mod("str")
        ui.roll(f"Aid another: d20={r}{bonus:+d} = {r + bonus} vs AC 10")
        if r + bonus < 10:
            ui.out("  The distraction doesn't work.")
            return
        if i < len(pairs):
            a.add_effect(Effect(f"Aided by {p.name}", 2, [("attack", "circumstance", 2)],
                                tags=["consume_attack"]))
            ui.good(f"  {a.name} gets +2 on their next attack.")
        else:
            a.add_effect(Effect(f"Covered by {p.name}", 2, [("ac", "circumstance", 2)]))
            ui.good(f"  {a.name} gets +2 AC.")

    def act_coup(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if f.helpless()
                                        and not f.dead], "Finish whom?")
        if not tgt:
            return
        x.std = x.move = False
        w = self.best_melee(p)
        self.provoke(p, "takes careful aim at a helpless foe")
        if not p.conscious or not w:
            return
        ui.out(f"{p.name} delivers a coup de grace to {tgt.name}!")
        if getattr(p, "class_level", lambda c_: 0)("paladin") and not tgt.evil \
                and not getattr(p, "fallen", False) and (tgt.ability("int") or 0) >= 3:
            p.fallen = True
            ui.bad(f"  Murdering a helpless creature that isn't evil breaks {p.name}'s oath. "
                   f"{p.name} has FALLEN and loses their paladin powers until they seek "
                   f"atonement at a temple.")
        before = tgt.damage
        if tgt.crit_immune():
            self.apply_hit(p, tgt, w, False, False, p.power_attack, True)
        else:
            self.apply_hit(p, tgt, w, True, False, p.power_attack, True)
        dealt = tgt.damage - before
        if not tgt.dead and tgt.is_living() and not tgt.crit_immune() and dealt > 0:
            if not saving_throw(ui, tgt, "fort", 10 + dealt, [], "coup de grace"):
                tgt.dead = True
                ui.bad(f"  {tgt.name} is slain!")
                self.after_damage(tgt)

    def act_ready_counter(self, x: CState) -> None:
        x.std = False
        x.move = False
        x.readied = {"counter": True, "w": None}
        self.ui.out(f"{x.c.name} watches the enemy's hands, ready to counter the next spell.")

    def act_subdue(self, x: CState) -> None:
        p = x.c
        if p.remove_effect("Subduing"):
            self.ui.out(f"{p.name} fights to kill again.")
        else:
            p.add_effect(Effect("Subduing", None, hidden=True))
            self.ui.out(f"{p.name} pulls their blows, fighting to subdue (nonlethal).")

    def act_stance(self, x: CState) -> None:
        p = x.c
        p.spend("stance")
        con_after = (p.ability("con") or 10) + 4
        dur = 3 + rules.ability_mod(con_after)
        p.add_effect(Effect("Defensive stance", dur,
                            [("str", "morale", 2), ("con", "morale", 4),
                             ("saves", "resistance", 2), ("ac", "dodge", 4)], ["rooted"],
                            data={"on_end": "rage",
                                  "tireless": p.class_level("dwarven defender") >= 8}))
        self.ui.warn(f"{p.name} plants their feet like the roots of a mountain! (+2 Str, +4 "
                     f"Con, +2 saves, +4 AC; can't move, {dur} rounds)")

    def act_hail(self, x: CState) -> None:
        p = x.c
        w = next(w for w in p.weapon_infos() if w.get("bow"))
        if not self._ready_weapon(x, w):
            return
        x.std = False
        p.spend("hail_of_arrows")
        foes = self.enemies(p)[:p.class_level("arcane archer")]
        self.ui.out(f"{p.name} fires a hail of arrows!", ("bmagenta",))
        for f in foes:
            if not f.dead and self._spend_ammo(p, w):
                self.make_attack(p, f, w, p.bab())

    def act_study(self, x: CState) -> None:
        p = x.c
        foes = [f for f in self.enemies(p) if not f.dead]
        st_eff = p.get_effect("Studying")
        tgt = None
        if st_eff:
            tgt = next((f for f in foes if f.uid == st_eff.data["target"]), None)
        if tgt is None:
            tgt = self._pick_target(p, foes, "Study whom?")
            if not tgt:
                return
            st_eff = p.add_effect(Effect("Studying", None, hidden=True,
                                         data={"target": tgt.uid, "n": 0}))
        x.std = False
        st_eff.data["n"] += 1
        self.ui.out(f"{p.name} studies {tgt.name}'s movements ({st_eff.data['n']}/3).")
        if st_eff.data["n"] >= 3:
            p.remove_effect("Studying")
            p.add_effect(Effect("Death attack ready", 3, hidden=True,
                                data={"target": tgt.uid}))
            self.ui.warn(f"{p.name} is ready: the next sneak attack on {tgt.name} within 3 "
                         f"rounds is a DEATH ATTACK.")

    def act_step(self, x: CState) -> None:
        p = x.c
        foe = self.engaged_foes(p)[0]
        x.move = False
        x.stepped = True
        self.disengage_all(p, retreat=5)
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
