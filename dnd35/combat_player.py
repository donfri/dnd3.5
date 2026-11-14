"""A hero's turn: the action menu and everything a player can choose to do."""

from __future__ import annotations

from typing import Dict, List, Optional

from . import dice, grid, rules
from .creature import Creature
from .data.items import item_data, item_name, item_clash
from .data.spells import SPELLS
from .effects import Effect, ROUNDS_PER_MINUTE
from .abilities import (bardic_music, lay_on_hands, protective_ward, revert_shape, wholeness_of_body, wild_shape)
from .data.classes import CLASSES
from .magic import (call_bolt, cast_spell, caster_cl, caster_dc, deal_damage, device_spells, pay_metamagic, pick_metamagic, saving_throw, use_device_check, scroll_usable, touch_attack, use_scroll_check)
from .sheet import render
from .ui import c


from .combat_base import CState, wound_word  # noqa: F401


class PlayerMixin:
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
            entangled = p.has_tag("entangled") or grappled or p.has_tag("rooted")
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
            if x.std and p.uses_left("dsmite"):
                add(f"Destruction smite: +4 attack, +{p.class_level('cleric')} damage (1/day)",
                    self.act_attack, x, False, "dsmite")
            if x.std and p.uses_left("death_touch") and eng:
                add("Death touch (Death domain, 1/day)", self.act_death_touch, x)
            if x.std and p.uses_left("protective_ward"):
                add("Protective ward on an ally (Protection domain, 1/day)", self.act_ward, x)
            if x.std and p.uses_left("quivering_palm") and eng and not p.wild_form():
                add("Quivering palm (1/day: an unarmed hit can kill outright)",
                    self.act_attack, x, False, "palm")
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
                solid = [f for f in eng if not f.incorporeal]
                if solid:
                    add("Trip a foe (knock them prone)", self.act_trip, x)
                if any(self.disarmable(f) for f in eng):
                    add("Disarm a foe (knock their weapon away)", self.act_disarm, x)
                    add("Sunder a foe's weapon (smash it)", self.act_sunder, x)
                if solid:
                    add("Grapple a foe (wrestle them; they can't move away)", self.act_grapple,
                        x)
                    add("Bull rush a foe (shove them out of melee)", self.act_bull_rush, x)
                    add("Overrun a foe (knock it down and push past)", self.act_overrun, x)
                add("Feint (Bluff: your next attack catches them off guard)", self.act_feint,
                    x)
                if any(self.is_engaged(a, f) for f in eng for a in self.allies(p)
                       if a is not p):
                    add("Aid another (+2 to an ally's next attack, or +2 AC)", self.act_aid, x)
            if x.std and not p.wild_form() and foes_all:
                add("Demoralize a foe (Intimidate: shaken, -2 on its rolls)",
                    self.act_demoralize, x)
            if full_ok and x.move and [f for f in eng if f.helpless() and not f.dead]:
                add("Coup de grace (finish a helpless foe: automatic critical)",
                    self.act_coup, x)
            if x.move and p.has_feat("Improved Feint") and eng and x.std is False:
                add("Feint as a move action (Improved Feint)", self.act_feint, x, True)
            if x.std and eng and p.wild_form() and partner is None:
                # an animal form can't disarm or wrestle, but it can still bowl foes over
                add("Trip a foe (knock them prone)", self.act_trip, x)
                add("Bull rush a foe (shove them out of melee)", self.act_bull_rush, x)
            lightning = next((e for e in p.effects if "_lightning" in e.tags), None)
            if x.std and lightning and lightning.data.get("bolts", 0) > 0:
                add(f"Call down lightning ({lightning.data['bolts']} bolts left)",
                    self.act_lightning, x, lightning)
            if (x.std or (p.has_feat("Quicken Spell") and not x.quickened)) and \
                    getattr(p, "available_casts", None) and p.available_casts() \
                    and p.can_cast_now() and not p.missing_focus():
                add("Cast a spell" if x.std else "Cast a quickened spell (free action)",
                    self.act_cast, x)
            if x.std and self.usable_items(p):
                add("Use an item (potion, scroll, alchemist's fire...)", self.act_item, x)
            if x.std and p.uses_left("turn") and any(m.ctype == "undead" for m in self.enemies(p)):
                add(f"Turn undead ({p.uses_left('turn')} left)", self.act_turn, x)
            if x.std and p.uses_left("music") and p.skill_ranks.get("Perform", 0) >= 3 \
                    and not p.wild_form():
                add(f"Bardic music ({p.uses_left('music')} left)",
                    self.act_music, x)
            hurt = [a for a in self.allies(p) if a.damage > 0 and not a.dead]
            if x.std and p.uses_left("lay_on_hands") and hurt:
                add(f"Lay on hands ({p.uses_left('lay_on_hands')} hp of healing left)",
                    self.act_lay_on_hands, x)
            if x.std and p.uses_left("wholeness") and p.damage > 0:
                add(f"Wholeness of body ({p.uses_left('wholeness')} hp left)",
                    self.act_wholeness, x)
            if x.std and (p.uses_left("wild_shape") or p.uses_left("elemental_shape")) \
                    and not p.wild_form():
                add(f"Wild shape: become an animal ({p.uses_left('wild_shape')} left)",
                    self.act_wild_shape, x)
            if x.std and p.wild_form():
                add("Return to your normal form", self.act_revert, x)
            if p.uses_left("stance") and not p.has_tag("rooted") and not p.has_tag("fatigued"):
                add(f"Defensive stance! (free action; {p.uses_left('stance')} left)",
                    self.act_stance, x)
            if x.std and p.uses_left("hail_of_arrows") and any(
                    w.get("bow") for w in p.weapon_infos()):
                add("Hail of arrows (1/day: one arrow at every foe)", self.act_hail, x)
            if x.std and p.uses_left("arrow_of_death") and any(
                    w.get("bow") for w in p.weapon_infos()):
                add("Arrow of death (1/day)", self.act_attack, x, False, "death_arrow")
            if x.std and p.class_level("assassin") and not p.get_effect("Death attack ready"):
                st_eff = p.get_effect("Studying")
                n = st_eff.data["n"] if st_eff else 0
                add(f"Study a foe for a death attack ({n}/3 rounds)", self.act_study, x)
            if p.uses_left("rage") and not p.has_tag("raging") and not p.has_tag("fatigued"):
                add("Rage! (free action)", self.act_rage, x)
            if p.uses_left("feat_of_strength") and not p.get_effect("Feat of Strength"):
                add("Feat of Strength (free action)", self.act_feat_strength, x)
            dying = [a for a in self.allies(p) if a.is_pc and a.hp < 0 and not a.stable
                     and not a.dead]
            if x.std and dying:
                add("Stabilize a dying ally (Heal check DC 15)", self.act_stabilize, x)
            foes = [f for f in self.enemies(p) if not self.is_engaged(p, f)
                    and self.reachable(p, f)]
            if foes and not entangled and not x.move and x.std and not single and \
                    not disabled and not p.has_tag("prone"):
                add(f"Move toward a foe again (uses your standard action; up to "
                    f"{self.speed_of(p)} ft)", self.act_approach, x)
            if (x.move or (x.std and not single and not disabled)) and not entangled \
                    and not p.has_tag("prone"):
                add(f"Move to a square (pick it on the map; up to {self.speed_of(p)} ft)",
                    self.act_move_to, x)
            if full_ok and x.move and not entangled and not p.has_tag("prone") \
                    and not p.has_tag("fatigued"):
                add("Run (full round: up to 4x speed in a straight dash, lose Dex bonus to AC)",
                    self.act_move_to, x, True)
            if x.move and p.get_effect("Mounted"):
                add("Dismount (move action)", self.act_dismount, x)
            elif x.move and not p.wild_form() and not grappled and self.my_mount(p) \
                    and self.distance(p, self.my_mount(p)) <= self.speed_of(p):
                add("Mount your warhorse (move action: ride at its speed, +1 to hit foes "
                    "on foot)", self.act_mount, x)
            if x.move:
                if p.has_tag("prone"):
                    add("Stand up (move action, provokes)", self.act_stand, x)
                if foes and not entangled:
                    add(f"Move toward a foe (move action; up to {self.speed_of(p)} ft)",
                        self.act_approach, x)
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
                if p.available_casts() and p.can_use_skill("Spellcraft"):
                    add("Ready a counterspell (stop the next spell a foe casts)",
                        self.act_ready_counter, x)
            add(("Stop fighting to subdue" if p.get_effect("Subduing") else
                 "Fight to subdue (deal nonlethal damage, -4 attack with lethal weapons)"),
                self.act_subdue, x)
            later = self.later_this_round(x)
            if x.std and x.move and not x.moved and not x.stepped and not single and later:
                add("Delay (take your turn later this round)", self.act_delay, x, later)
            if p.has_feat("Power Attack"):
                add(f"Set Power Attack (now {p.power_attack})", self.act_power, x)
            if not p.get_effect("Fighting defensively") and x.std:
                add("Toggle: fight defensively this turn (-4 attack, +2 AC)", self.act_defensive, x)
            for e_, d_ in p.minds():
                if not p.daily.get(f"mind:{e_['id']}") and not item_clash(p.alignment, d_):
                    add(f"Ask {d_['name']} to {d_['intelligent']['power']['label']} "
                        f"(once a day, free)", self.act_item_power, x, e_)
            add("Look: battlefield / my character sheet / foe details", self.act_look, x)
            if self.can_flee and full_ok and x.move and not entangled:
                add("Flee the battle (withdraw out of the fight)", self.act_flee, x)
            add("End turn", None)
            MAIN = ("Attack", "Full attack", "Charge", "Cast", "Use an item", "Turn undead",
                    "Rage", "Smite", "Stunning", "Call down", "Bardic", "Lay on", "Wild shape",
                    "Return to", "Grapple:", "Coup de grace", "Stabilize")
            MOVE = ("Move t", "Stand", "5-foot", "Move away", "Mount", "Dismount")
            groups, keys = [], []
            for a in acts:
                lab = a[0]
                if lab.startswith(MAIN):
                    groups.append("Fight")
                elif lab.startswith(MOVE):
                    groups.append("Move")
                elif lab.startswith("End turn"):
                    groups.append("Turn")
                elif lab.startswith("Look"):
                    groups.append("Game")
                else:
                    groups.append("Tactics")
                key = a[1].__name__[4:] if a[1] else "end"
                if key == "attack":
                    extra = a[2][2] if len(a[2]) > 2 else ("full" if a[2][1] else "")
                    key = f"attack_{extra}" if extra else "attack"
                elif key == "move_to" and len(a[2]) > 1:
                    key = "run"
                elif key == "feint" and len(a[2]) > 1:
                    key = "feint_move"
                keys.append(key)
            ui.option_keys = keys
            self.sync_map()
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
            elif p.uid in self.st and f.uid in self.st:
                tag.append(f"{self.distance(p, f)} ft")
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
        # a pair of identical natural weapons (two claws) is one choice
        seen, keep = set(), []
        for o, w in zip(opts, usable):
            if o not in seen:
                seen.add(o)
                keep.append((o, w))
        if len(keep) == 1:
            return keep[0][1]
        i = self.ui.choose("With which weapon?", [o for o, _ in keep], allow_cancel=True)
        return None if i is None else keep[i][1]

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
        if mode == "death_arrow":
            w = next(w for w in p.weapon_infos() if w.get("bow"))
        elif mode in ("stun", "palm"):
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
            if not self.clear_shot(p, tgt):
                ui.bad(f"There's no clear shot at {tgt.name}: a wall is in the way.")
                return
            if self.range_penalty(p, tgt, w)[1]:
                ui.bad(f"{tgt.name} is {self.distance(p, tgt)} ft away, beyond the "
                       f"{w['name']}'s maximum range.")
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
                    w.get("reach") and self.distance(p, f) <= 10)] or foes
            tgt = self._pick_target(p, foes)
            if not tgt:
                return
            if not self._ready_weapon(x, w):
                return
            reach_ok = w.get("reach") and self.distance(p, tgt) <= 10 and \
                self.clear_shot(p, tgt)
            if reach_ok and not self.is_engaged(p, tgt):
                ui.out(f"{p.name} strikes at {tgt.name} from behind the front line with "
                       f"{w['name']} (reach).")
            elif not self.is_engaged(p, tgt):
                if full:
                    ui.bad("You must already be in melee with that foe to full attack.")
                    return
                if not self.reachable(p, tgt):
                    ui.bad(f"{tgt.name} is up in the air, out of reach. Use a ranged attack, "
                           f"ready an attack for when it swoops, or get magic to fly.")
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
                need, sp = self.feet_to_melee(p, tgt), self.speed_of(p)
                if need > sp:
                    ui.warn(f"{tgt.name} is {self.distance(p, tgt)} ft away; you can move "
                            f"{sp} ft and still attack.")
                    if (need <= 2 * sp and not x.moved and not p.has_tag("fatigued")
                            and not mode and not p.has_tag("prone")
                            and self.clear_charge(p, tgt)):
                        if ui.confirm(f"Charge {tgt.name} instead (+2 attack, -2 AC)?", True):
                            self.act_charge(x, tgt)
                        return
                    if ui.confirm(f"Move {sp} ft toward {tgt.name} instead?", True):
                        x.move = False
                        x.moved = True
                        self.close_in(p, tgt)
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
            elif mode == "dsmite":
                p.spend("dsmite")
                sit.append(("untyped", 4, "destruction smite"))
                extra = p.class_level("cleric")
                ui.out(f"{p.name} calls down destruction on {tgt.name}!", ("byellow",))
            elif mode == "stun":
                p.spend("stunning_fist")
                p.add_effect(Effect("Stunning Fist", 1, tags=["_stun_primed"], hidden=True))
                ui.out(f"{p.name} strikes at a nerve cluster...")
            elif mode == "death_arrow":
                p.spend("arrow_of_death")
                ui.out(f"{p.name} looses a black-fletched arrow of death!", ("bmagenta",))
                if self.make_attack(p, tgt, w, p.bab(), sit) and not tgt.dead and \
                        tgt.is_living() and "death" not in tgt.immunities():
                    if not saving_throw(ui, tgt, "fort", 20 + p.mod("cha"), ["death"],
                                        "arrow of death"):
                        ui.bad(f"  {tgt.name} falls dead!")
                        tgt.dead = True
                        self.after_damage(tgt)
                return
            elif mode == "palm":
                p.spend("quivering_palm")
                ui.out(f"{p.name} strikes with the quivering palm...", ("bmagenta",))
                if self.make_attack(p, tgt, w, p.bab(), sit, power=power) and not tgt.dead:
                    if tgt.is_living() and tgt.hit_dice() <= p.level and \
                            "death" not in tgt.immunities() and \
                            not saving_throw(ui, tgt, "fort", 10 + p.class_level("monk") // 2
                                             + p.mod("wis"), [], "quivering palm"):
                        ui.bad(f"  {p.name} wills the vibrations to stop. {tgt.name} dies!")
                        tgt.dead = True
                        self.after_damage(tgt)
                return
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
            extra += 2 if monk >= 11 else 1
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
            if p.has_feat("Greater Two-Weapon Fighting"):
                off_babs.append(babs[0] - 10)
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
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f) and self.reachable(p, f)]
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
            self.disengage_all(p, retreat=max(5, self.speed_of(p) - 5))
            ui.out("...and springs back out of reach.")

    def act_lightning(self, x: CState, e) -> None:
        p = x.c
        tgt = self._pick_target(p, self.enemies(p), "Call lightning on whom?")
        if not tgt:
            return
        x.std = False
        call_bolt(self.ui, p, e, tgt, self)

    def act_music(self, x: CState) -> None:
        from .abilities import music_options
        p = x.c
        opts = music_options(p, True)
        i = self.ui.choose("Which song?", [o[1] for o in opts], allow_cancel=True)
        if i is None:
            return
        x.std = False
        bardic_music(self.ui, p, [a for a in self.allies(p) if not a.dead],
                     self.enemies(p), opts[i][0])

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

    def act_charge(self, x: CState, tgt: Optional[Creature] = None) -> None:  # noqa: C901
        p = x.c
        if p.has_tag("entangled"):
            self.ui.bad("You're entangled!")
            return
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f) and self.reachable(p, f)]
        tgt = tgt or self._pick_target(p, foes, "Charge whom?")
        if not tgt:
            return
        w = self.best_melee(p)
        if not w or w["ranged"]:
            self.ui.bad("You need a melee weapon in hand to charge.")
            return
        if self.feet_to_melee(p, tgt) > 2 * self.speed_of(p):
            self.ui.bad(f"{tgt.name} is {self.distance(p, tgt)} ft away: too far to charge "
                        f"(you can charge up to {2 * self.speed_of(p)} ft).")
            return
        if not self.clear_charge(p, tgt):
            self.ui.bad(f"There's no clear run at {tgt.name}: rough ground or obstacles in "
                        f"the way. Move toward it instead.")
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
        if not self.close_in(p, tgt, budget=2 * self.speed_of(p)):
            return
        sit = [("untyped", 2, "charge")]
        if p.get_effect("Mounted"):
            # a lance doubles damage on a mounted charge; Spirited Charge adds one more
            self.charge_mult = (2 if w.get("wid") == "lance" else 1) + \
                (1 if p.has_feat("Spirited Charge") else 0)
            if self.charge_mult > 1:
                self.ui.out(f"  Mounted charge: damage x{self.charge_mult}!", ("byellow",))
        try:
            self.make_attack(p, tgt, w, p.bab(), sit, power=p.power_attack)
        finally:
            self.charge_mult = 1
        if p.get_effect("Mounted") and p.has_feat("Ride-By Attack") and p.conscious:
            self.s(p).provoked_by = set(getattr(self.s(p), "provoked_by", ())) | {tgt.uid}
            self.disengage_all(p, retreat=self.speed_of(p))
            self.ui.out(f"{p.name} thunders past and wheels away (Ride-By Attack).")

    def act_approach(self, x: CState) -> None:
        p = x.c
        foes = [f for f in self.enemies(p) if not self.is_engaged(p, f) and self.reachable(p, f)]
        tgt = self._pick_target(p, foes, "Move toward whom?")
        if not tgt:
            return
        if x.move:
            x.move = False
        else:
            x.std = False   # a second move in place of the standard action
        x.moved = True
        if self.feet_to_melee(p, tgt) <= self.speed_of(p):
            self.ui.out(f"{p.name} moves into melee with {tgt.name}.")
        self.close_in(p, tgt)

    def reachable_squares(self, cr: Creature, budget: int) -> Dict[tuple, int]:
        costs, _ = self.terrain.costs(self.s(cr).pos, self.foe_squares(cr))
        occ = set(self.occupied(cr))
        return {q: c_ for q, c_ in costs.items() if 0 < c_ <= budget and q not in occ}

    def act_move_to(self, x: CState, run: bool = False) -> None:
        """Move to a square you choose (typed as column,row or tapped on the map)."""
        p = x.c
        ui = self.ui
        sp = self.speed_of(p)
        heavy = (getattr(p, "armor_data", lambda: None)() or {}).get("category") == "heavy"
        budget = sp * (3 if heavy else 4) if run else sp
        ok = self.reachable_squares(p, budget)
        if not ok:
            ui.bad("There's nowhere you can move to.")
            return
        ans = ui.ask(f"Move to which square? Type column,row (you can go {budget} ft) "
                     f"or tap the map", "")
        try:
            cx, cy = [int(v) for v in ans.replace(" ", "").split(",")[:2]]
        except (ValueError, TypeError):
            ui.out("No move made.")
            return
        if (cx, cy) not in ok:
            ui.bad(f"You can't reach square {cx},{cy} this turn (too far, blocked or taken).")
            return
        if run:
            x.std = x.move = False
            p.add_effect(Effect("Running", 1, [("ac", "untyped", -max(0, p.mod("dex")))],
                                hidden=False))
        elif x.move:
            x.move = False
        else:
            x.std = False
        x.moved = True
        start = x.pos
        path = self.terrain.path(start, (cx, cy), self.foe_squares(p))
        ui.out(f"{p.name} {'RUNS' if run else 'moves'} {ok[(cx, cy)]} ft.")
        self.travel(p, path)

    def my_mount(self, p: Creature) -> Optional[Creature]:
        from .companions import Mount
        for comp in self.companions:
            if isinstance(comp, Mount) and getattr(comp, "owner", None) is p \
                    and not comp.dead and comp.conscious and not self.s(comp).fled:
                return comp
        return None

    def act_mount(self, x: CState) -> None:
        p = x.c
        m = self.my_mount(p)
        x.move = False
        self.disengage_all(m)
        x.pos = self.s(m).pos if self.near(p, m) else x.pos
        self.s(m).ridden = True
        p.add_effect(Effect("Mounted", None, tags=["mounted"],
                            data={"mount": m.uid, "speed": self.speed_of(m)}, hidden=False))
        self.sync_engagement(p)
        self.ui.out(f"{p.name} swings into {m.name}'s saddle (rides at {self.speed_of(p)} ft, "
                    f"+1 to hit foes on foot).")

    def dismount(self, p: Creature, msg: bool = True) -> None:
        e = p.get_effect("Mounted")
        if not e:
            return
        p.remove_effect("Mounted")
        mx = self.st.get(e.data["mount"])
        if mx is not None:
            mx.ridden = False
            occ = set(self.occupied(mx.c))
            spots = [q for q in grid.neighbors(self.s(p).pos) if self.fits(mx.c, q, occ)]
            if spots:
                mx.pos = spots[0]
            self.sync_engagement(mx.c)
        if msg:
            self.ui.out(f"{p.name} is out of the saddle.")

    def act_dismount(self, x: CState) -> None:
        x.move = False
        self.dismount(x.c)

    def act_item_power(self, x: CState, entry: dict) -> None:
        """An intelligent weapon grants its once-a-day gift."""
        p, ui = x.c, self.ui
        d = item_data(entry)
        p.daily[f"mind:{entry['id']}"] = 1
        power = d["intelligent"]["power"]["id"]
        if power == "heal":
            r = dice.roll("2d8+5")
            ui.out(f"{d['name']} flares with dawn light.", ("byellow",))
            from .magic import heal
            heal(ui, p, r.total)
        elif power == "invisibility":
            p.add_effect(Effect("Invisibility", 10 * ROUNDS_PER_MINUTE,
                                [("concealment", "concealment", 50),
                                 ("attack", "untyped", 2)], ["invisible"],
                                source=d["name"]))
            ui.good(f"'Hold your breath,' says {d['name']}. {p.name} fades from sight.")

    def act_move_away(self, x: CState) -> None:
        p = x.c
        x.move = False
        x.moved = True
        self.provoke(p, "moves out of melee", movement=True)
        self.disengage_all(p, retreat=self.speed_of(p))
        if p.conscious:
            self.ui.out(f"{p.name} backs away from the fight.")

    def act_withdraw(self, x: CState) -> None:
        p = x.c
        x.std = x.move = False
        self.disengage_all(p, retreat=2 * self.speed_of(p))
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
        b = p.class_level("barbarian")
        sc, will, name = (8, 4, "MIGHTY RAGE") if b >= 20 else (6, 3, "GREATER RAGE") \
            if b >= 11 else (4, 2, "RAGE")
        con_after = (p.ability("con") or 10) + sc
        dur = 3 + rules.ability_mod(con_after)
        mods = [("str", "morale", sc), ("con", "morale", sc), ("save_will", "morale", will)]
        if b >= 14:
            mods.append(("saves_vs_enchantment", "untyped", 4))
        p.add_effect(Effect("Rage", dur, mods, ["raging"],
                            data={"on_end": "rage", "tireless": b >= 17}))
        self.ui.warn(f"{p.name} flies into a {name}! (+{sc} Str, +{sc} Con, +{will} Will, -2 AC "
                     f"for {dur} rounds)")

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
        negative = getattr(p, "energy", "positive") == "negative"
        greater = False
        if not negative and p.uses_left("greater_turning") and ui.confirm(
                "Use your Sun domain's greater turning (destroy instead of turn)?", True):
            p.spend("greater_turning")
            greater = True
        r = dice.d20()
        check = r + p.mod("cha")
        if p.skill_ranks.get("Knowledge (religion)", 0) >= 5:
            check += 2
        max_hd = rules.turning_max_hd(check, lvl)
        dmg_roll = dice.roll("2d6")
        pool = dmg_roll.total + lvl + p.mod("cha")
        how = ("thrusts out an unholy symbol and commands the dead in the name of"
               if negative else "presents a holy symbol and calls upon")
        ui.out(f"{p.name} {how} {p.deity or 'the divine'}!", ("byellow",))
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
            if negative:
                if lvl >= 2 * hd:
                    self.command_undead(p, m)
                else:
                    m.add_effect(Effect("Rebuked", ROUNDS_PER_MINUTE, tags=["turned"]))
                    ui.good(f"  {m.name} is REBUKED and cowers in awe!")
                continue
            if lvl >= 2 * hd or greater:
                ui.good(f"  {m.name} crumbles to dust!")
                m.dead = True
                self.disengage_all(m)
            else:
                m.add_effect(Effect("Turned", ROUNDS_PER_MINUTE, tags=["turned"]))
                self.disengage_all(m, retreat=self.speed_of(m))
                ui.good(f"  {m.name} is TURNED and cowers away from the holy light!")
        if not any_turned:
            ui.out("  The undead resist the turning.")

    def command_undead(self, p, m) -> None:
        """An evil cleric takes control of a weak undead: it fights on their side."""
        self.disengage_all(m)
        self.monsters.remove(m)
        self.xp_monsters.append(m)
        m.owner = p
        m.summoned = False
        self.s(m).side = self.s(p).side
        self.companions.append(m)
        m.block = dict(m.block, morale=False)
        self.ui.good(f"  {m.name} bows its head: it is COMMANDED and now serves {p.name}!")

    def act_death_touch(self, x: CState) -> None:
        p = x.c
        ui = self.ui
        tgt = self._maneuver_target(p, [f for f in self.engaged_foes(p) if f.is_living()],
                                    "Touch whom?")
        if not tgt:
            return
        x.std = False
        p.spend("death_touch")
        if not touch_attack(ui, p, tgt, False, self):
            return
        r = dice.roll(f"{p.class_level('cleric')}d6")
        ui.roll(f"Death touch: {r.detail()} vs {tgt.name}'s {tgt.hp} hp")
        if "death" in tgt.immunities():
            ui.out(f"  {tgt.name} is warded against death.")
        elif r.total >= tgt.hp:
            ui.bad(f"  {tgt.name}'s heart stops. It falls dead!")
            tgt.damage = tgt.max_hp() + 10
            tgt.dead = True
            self.after_damage(tgt)
        else:
            ui.out(f"  {tgt.name} shudders but lives.")

    def act_ward(self, x: CState) -> None:
        p = x.c
        allies = [a for a in self.allies(p) if not a.dead]
        tgt = allies[0] if len(allies) == 1 else allies[self.ui.choose(
            "Ward whom?", [a.name for a in allies])]
        x.std = False
        protective_ward(self.ui, p, tgt)

    def act_flee(self, x: CState) -> None:
        p = x.c
        x.std = x.move = False
        if self.engaged_foes(p):
            self.provoke(p, "flees", movement=True)
        if p.conscious:
            self.disengage_all(p, retreat=2 * self.speed_of(p))
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
            if e.get("unidentified"):
                continue
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
            pool = [f for f in self.enemies(p) if p.uid not in self.st or self.clear_shot(p, f)]
            if not pool:
                ui.bad("No foe is in sight: walls block every line.")
                return None
            t = self._pick_target(p, pool)
            return [t] if t else None
        if kind == "enemies":
            foes = self.enemies(p)
            if not foes:
                return None
            n = min(sp["max_targets"], len(foes))
            if spell in grid.AREAS and p.uid in self.st:
                return self.pick_area(p, spell, foes, sp["max_targets"])
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
        from .magic import spell_range
        rng = spell_range(spell, getattr(p, "level", 1))
        for t in targets:
            if t is p or t.uid not in self.st or spell in grid.AREAS:
                continue
            d = self.distance(p, t)
            if rng == 5 and SPELLS[spell]["target"] in ("ally", "creature") and d > 5:
                # a touch spell on a friend: walk over if a move is left
                spot, cost, path = self.route(p, t) if self.s(t).side != x.side else \
                    self.route_to_ally(p, t)
                if spot is None or cost > self.speed_of(p) or not x.move:
                    ui.bad(f"{spell} needs a touch and {t.name} is {d} ft away"
                           + ("." if x.move else " (no move left)."))
                    return
                x.move = False
                x.moved = True
                ui.out(f"{p.name} hurries over to {t.name}.")
                if not self.travel(p, path):
                    x.std = False
                    return
            elif rng > 5 and d > rng:
                ui.bad(f"{t.name} is {d} ft away; {spell} reaches only {rng} ft. Move closer.")
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
        from .magic import MELEE_TOUCH
        if spell.startswith("Inflict") or spell in MELEE_TOUCH or spell in (
                "Bestow Curse", "Poison", "Slay Living", "Contagion") or (
                spell.startswith("Cure") and targets and targets[0].ctype == "undead"):
            t = targets[0]
            fam = getattr(p, "familiar", None)
            if (fam and not self.is_engaged(p, t) and
                    p.class_level("wizard") + p.class_level("sorcerer") >= 3 and
                    ui.confirm(f"Send {fam['name']} the {fam['kind']} to deliver the touch?",
                               True)):
                ui.out(f"{fam['name']} darts across the fight, carrying the spell to {t.name}!")
            elif not self.is_engaged(p, t):
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
