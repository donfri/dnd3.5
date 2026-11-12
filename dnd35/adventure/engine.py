"""The computer GM: exploration, skill checks, traps, encounters, rest, town.

Adventures are plain data (see ember_barrow.py): rooms with exits, features
(things to do), traps, and encounters. Features run small effect scripts.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .. import dice, rules
from ..character import Character
from ..combat import Combat, award_xp
from ..data.items import item_data, item_name, make_item
from ..effects import Effect, ROUNDS_PER_MINUTE
from ..levelup import level_up_interactive, prepare_spells
from ..abilities import ability_menu, has_usable
from ..companions import rest_companion
from ..crafting import can_anyone_craft, craft_menu
from ..magic import cast_out_of_combat, heal, saving_throw
from ..monster import Monster
from ..sheet import render, short_status
from ..shop import inventory_menu, shop_menu
from ..ui import QuitGame, c

SAVE_DIR = os.environ.get("DND35_SAVE_DIR") or os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saves")


class GameOver(Exception):
    def __init__(self, result: str):
        super().__init__(result)
        self.result = result


class GameState:
    def __init__(self, adventure, party: List[Character], settings: Optional[dict] = None):
        self.adv = adventure
        self.party = party
        self.room = adventure.START
        self.flags: set = set()
        self.rooms: Dict[str, dict] = {}
        self.minutes = 8 * 60  # day 1, 8:00 am
        self.settings = settings or {"heroic": False}
        self.sneaking = False
        self.journal: List[str] = []
        self.light_minutes = 0          # how long the party's torch/lantern/light lasts
        self.attitudes: Dict[str, str] = {}

    # ------------------------------------------------------------ helpers
    def rs(self, room_id: Optional[str] = None) -> dict:
        rid = room_id or self.room
        return self.rooms.setdefault(rid, {"visited": False, "used": [], "found_traps": [],
                                           "disabled_traps": [], "revealed": [],
                                           "attempts": {}, "unlocked": []})

    def living(self) -> List[Character]:
        return [p for p in self.party if not p.dead]

    def able(self) -> List[Character]:
        return [p for p in self.party if p.conscious]

    def party_level(self) -> int:
        alive = self.living() or self.party
        return max(1, round(sum(p.level for p in alive) / len(alive)))

    def time_str(self) -> str:
        day = self.minutes // (24 * 60) + 1
        h, m = divmod(self.minutes % (24 * 60), 60)
        return f"Day {day}, {h:02d}:{m:02d}"

    def pass_time(self, minutes: int, ui=None) -> None:
        self.minutes += minutes
        if self.light_minutes > 0:
            self.light_minutes = max(0, self.light_minutes - minutes)
            if self.light_minutes == 0 and ui:
                ui.warn("Your light gutters and goes out.")
        rounds = minutes * ROUNDS_PER_MINUTE
        for p in self.party:
            msgs = p.tick(rounds)
            if ui:
                for msg in msgs:
                    ui.out(f"  {msg}", ("dim",))

    def note(self, text: str) -> None:
        self.journal.append(f"[{self.time_str()}] {text}")

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        return {"adventure": self.adv.ID, "party": [p.to_dict() for p in self.party],
                "room": self.room, "flags": sorted(self.flags), "rooms": self.rooms,
                "minutes": self.minutes, "settings": self.settings,
                "sneaking": self.sneaking, "journal": self.journal,
                "light_minutes": self.light_minutes, "attitudes": self.attitudes}

    @classmethod
    def from_dict(cls, d: dict, adventure) -> "GameState":
        gs = cls(adventure, [Character.from_dict(p) for p in d["party"]], d.get("settings"))
        gs.room = d["room"]
        gs.flags = set(d.get("flags", []))
        gs.rooms = d.get("rooms", {})
        gs.minutes = d.get("minutes", 480)
        gs.sneaking = d.get("sneaking", False)
        gs.journal = d.get("journal", [])
        gs.light_minutes = d.get("light_minutes", 0)
        gs.attitudes = d.get("attitudes", {})
        return gs


def save_game(gs: GameState, name: str) -> str:
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(gs.to_dict(), f, indent=1)
    return path


def list_saves() -> List[str]:
    if not os.path.isdir(SAVE_DIR):
        return []
    files = [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    files.sort(key=lambda n: os.path.getmtime(os.path.join(SAVE_DIR, n + ".json")),
               reverse=True)
    return files


def load_game(name: str, adventure=None) -> GameState:
    """Load a save. The adventure is taken from the save file itself."""
    from . import get
    with open(os.path.join(SAVE_DIR, f"{name}.json")) as f:
        d = json.load(f)
    return GameState.from_dict(d, get(d.get("adventure", "")) if adventure is None
                               or d.get("adventure") not in (None, adventure.ID)
                               else adventure)


def save_info(name: str) -> str:
    """One-line description of a save for menus."""
    from . import get
    try:
        with open(os.path.join(SAVE_DIR, f"{name}.json")) as f:
            d = json.load(f)
        adv = get(d.get("adventure", ""))
        heroes = ", ".join(f"{p['name']} (L{len(p.get('class_levels', []))})"
                           for p in d.get("party", []) if not p.get("dead"))
        room = adv.ROOMS.get(d.get("room"), {}).get("name", "")
        return f"{name}: {adv.TITLE} - {room} - {heroes}"
    except (OSError, ValueError, KeyError):
        return name


# ================================================================ the GM
class GM:
    def __init__(self, ui, gs: GameState):
        self.ui = ui
        self.gs = gs
        self.adv = gs.adv
        if hasattr(ui, "game_state"):
            ui.game_state = gs  # lets the web page show party / journal tabs

    # ------------------------------------------------------------ checks
    def check_bonus(self, ch: Character, skill: str) -> Optional[int]:
        if skill.startswith("best:"):
            vals = [self.check_bonus(ch, sk) for sk in skill[5:].split("|")]
            vals = [v for v in vals if v is not None]
            return max(vals) if vals else None
        if skill.startswith("ability:"):
            return ch.mod(skill.split(":")[1])
        if skill == "Wild Empathy":
            lvl = ch.class_level("ranger") + ch.class_level("druid")
            if not lvl:
                return None
            return lvl + ch.mod("cha")
        if not ch.can_use_skill(skill):
            if skill == "Handle Animal":
                return ch.mod("cha")
            return None
        return ch.skill_total(skill)

    def skill_label(self, skill: str) -> str:
        if skill.startswith("best:"):
            return " or ".join(skill[5:].split("|"))
        if skill.startswith("ability:"):
            return rules.ABILITY_NAMES[skill.split(":")[1]] + " check"
        return skill

    def roll_check(self, ch: Character, skill: str, dc: Optional[int], take: Optional[int] = None,
                   extra: int = 0, show_dc: bool = True) -> int:
        bonus = self.check_bonus(ch, skill)
        if bonus is None:
            self.ui.roll(f"{ch.name} can't attempt {skill} untrained.")
            return -99
        bonus += extra
        if take:
            r = take
            how = f"takes {take}"
        else:
            r = dice.d20()
            how = f"d20={r}"
        total = r + bonus
        dctxt = f" vs DC {dc}" if (dc is not None and show_dc) else ""
        ok = "" if dc is None else (" -> success" if total >= dc else " -> failure")
        self.ui.roll(f"{ch.name} {self.skill_label(skill)}: {how} {bonus:+d} = {total}{dctxt}{ok}")
        return total

    def pick_hero(self, prompt: str, skill: Optional[str] = None,
                  heroes: Optional[List[Character]] = None) -> Optional[Character]:
        heroes = heroes or self.gs.able()
        if not heroes:
            return None
        if len(heroes) == 1:
            return heroes[0]
        opts = []
        for h in heroes:
            if skill:
                b = self.check_bonus(h, skill)
                opts.append(f"{h.name} ({self.skill_label(skill)} "
                            f"{'untrained' if b is None else f'{b:+d}'})")
            else:
                opts.append(h.name)
        i = self.ui.choose(prompt, opts, allow_cancel=True)
        return None if i is None else heroes[i]

    # ------------------------------------------------------------ conditions
    def met(self, req: Optional[dict], actor=None) -> bool:
        if not req:
            return True
        gs = self.gs
        if "flag" in req and req["flag"] not in gs.flags:
            return False
        if "flags" in req and not all(f in gs.flags for f in req["flags"]):
            return False
        if "not_flag" in req and req["not_flag"] in gs.flags:
            return False
        if "enc_cleared" in req and not self.enc_done(req["enc_cleared"]):
            return False
        if "enc_active" in req and self.enc_done(req["enc_active"]):
            return False
        if "has_item" in req and not any(p.has_item(req["has_item"]) for p in gs.living()):
            return False
        if "class" in req and not any(p.class_level(req["class"]) for p in gs.able()):
            return False
        return True

    def enc_done(self, enc_id: str) -> bool:
        return f"enc:{enc_id}" in self.gs.flags

    # ------------------------------------------------------------ effects
    def run(self, effects: List[dict], actor: Optional[Character] = None) -> None:
        for eff in effects or []:
            if not self.gs.able():
                return
            self.run_one(eff, actor)

    def run_one(self, eff: dict, actor: Optional[Character]) -> None:
        ui, gs = self.ui, self.gs
        do = eff["do"]
        if do == "text":
            ui.gm(eff["text"])
        elif do == "say":
            ui.para(f"{eff['who']}: “{eff['text']}”", ("bmagenta",))
        elif do == "xp":
            alive = gs.living()
            for p in alive:
                p.xp += eff["amount"]
            ui.good(f"Each hero gains {eff['amount']} XP" +
                    (f" ({eff['why']})." if eff.get("why") else "."))
            self.level_notice()
        elif do == "gold":
            alive = gs.living()
            total = eff["gp"] * 100
            each, rem = divmod(total, len(alive))
            for p in alive:
                p.cp += each
            alive[0].cp += rem
            ui.good(f"The party finds {eff['gp']} gp (split: {rules.money_str(each)} each).")
        elif do == "item":
            to = actor or (gs.living()[0] if gs.living() else None)
            if len(gs.living()) > 1 and not eff.get("to_actor"):
                to = self.pick_hero(f"Who takes the {item_name(make_item(eff['id']))}?") or to
            entry = to.add_item(make_item(eff["id"], eff.get("qty", 1)))
            ui.good(f"{to.name} takes {item_name(entry)}" +
                    (f" x{eff.get('qty')}" if eff.get("qty", 1) > 1 else "") + ".")
        elif do == "items_each":
            for p in gs.living():
                p.add_item(eff["id"], eff.get("qty", 1))
            ui.good(f"Each hero receives {item_name(make_item(eff['id']))} x{eff.get('qty', 1)}.")
        elif do == "remove_item":
            for p in gs.living():
                e = p.find_item(eff["id"])
                if e:
                    e.pop("slot", None)
                    p.remove_item(e, e["qty"])
                    break
        elif do == "flag":
            gs.flags.add(eff["name"])
        elif do == "unflag":
            gs.flags.discard(eff["name"])
        elif do == "journal":
            gs.note(eff["text"])
            ui.out(c(f"[Journal] {eff['text']}", "dim"))
        elif do == "damage":
            targets = gs.able() if eff.get("who") == "all" else [actor or gs.able()[0]]
            for t in targets:
                r = dice.roll(eff["dice"])
                amt = r.total
                sv = eff.get("save")
                if sv:
                    kind, dc, mode = sv
                    if saving_throw(ui, t, kind, dc, eff.get("tags", ["trap"])):
                        if mode == "half":
                            amt = 0 if (kind == "ref" and t.has_evasion()) else amt // 2
                        else:
                            amt = 0
                if amt:
                    ui.roll(f"Damage: {r.detail()}" + (" (halved)" if amt != r.total else ""))
                    dealt, note = t.take_damage(amt, eff.get("dtype", ""), magic=True)
                    ui.bad(f"{t.name} takes {dealt} damage ({t.hp}/{t.max_hp()} hp)."
                           + (f" {note}" if note else ""))
                    if t.dead:
                        ui.bad(f"{t.name} has died!")
                    elif t.hp < 0:
                        ui.bad(f"{t.name} is dying!")
                else:
                    ui.good(f"{t.name} avoids harm.")
        elif do == "ability_damage":
            t = actor or gs.able()[0]
            kind, dc = eff["save"]
            if not saving_throw(ui, t, kind, dc, eff.get("tags", ["poison"])):
                amt = dice.roll(eff["dice"]).total
                t.ability_damage[eff["ability"]] = t.ability_damage.get(eff["ability"], 0) + amt
                ui.bad(f"{t.name} takes {amt} {eff['ability'].upper()} damage!")
        elif do == "buff":
            targets = gs.living() if eff.get("who", "all") == "all" else [actor]
            for t in targets:
                t.add_effect(Effect(eff["name"], eff.get("duration"), eff.get("mods", []),
                                    eff.get("tags", [])))
            ui.good(f"The party gains: {eff['name']}.")
        elif do == "heal_all":
            for p in gs.living():
                p.damage = 0
                p.stable = False
            ui.good("Everyone is fully healed.")
        elif do == "fight":
            self.start_encounter(eff["enc"], surprise=eff.get("surprise"))
        elif do == "stealth_fight":
            self.stealth_approach(eff["enc"])
        elif do == "resolve_enc":
            self.resolve_encounter(eff["enc"], eff.get("xp", True), eff.get("factor", 1.0))
        elif do == "remove_monster":
            st = gs.rs(eff.get("room"))
            rem = st.setdefault("enc_mods", {}).setdefault(eff["enc"], {})
            rem["remove"] = rem.get("remove", 0) + eff.get("count", 1)
        elif do == "add_monster":
            st = gs.rs(eff.get("room"))
            rem = st.setdefault("enc_mods", {}).setdefault(eff["enc"], {})
            rem.setdefault("add", []).append(eff["key"])
        elif do == "reveal_exit":
            gs.rs(eff.get("room")).setdefault("revealed", []).append(eff["exit"])
            ui.good("A new way forward is revealed!")
        elif do == "unlock_exit":
            gs.rs(eff.get("room")).setdefault("unlocked", []).append(eff["exit"])
        elif do == "goto":
            self.enter(eff["room"])
        elif do == "shop":
            markup = eff.get("markup", 1.0)
            key = f"haggle:{eff['name']}:{gs.minutes // 1440}"
            if key not in gs.flags and ui.confirm("Haggle with the shopkeeper first? "
                                                  "(Diplomacy DC 20: 10% off today)", False):
                gs.flags.add(key)
                h = self.pick_hero("Who haggles?", "Diplomacy")
                if h and self.roll_check(h, "Diplomacy", 20) >= 20:
                    gs.flags.add(key + ":won")
                    ui.good("The shopkeeper sighs and knocks 10% off everything.")
                else:
                    ui.out("The shopkeeper isn't budging.")
            if key + ":won" in gs.flags:
                markup *= 0.9
            shop_menu(ui, gs.living(), eff["name"], eff["sections"], markup)
        elif do == "rest":
            self.rest(eff.get("cost_sp", 0), safe=eff.get("safe", True))
        elif do == "temple":
            self.temple_services()
        elif do == "rumors":
            self.rumors(actor)
        elif do == "recruit":
            self.recruit()
        elif do == "riddle":
            self.riddle(eff)
        elif do in ("swim", "exposure", "fall"):
            self.hazard(eff)
        elif do == "diplomacy":
            self.diplomacy(eff, actor)
        elif do == "paladin_falls":
            for p in gs.living():
                if p.class_level("paladin") and not p.fallen:
                    p.fallen = True
                    ui.bad(f"{p.name} has broken the paladin's code and FALLS: no smiting, "
                           f"no lay on hands, no spells, no mount, until atonement.")
        elif do == "end_adventure":
            raise GameOver("victory")
        elif do == "custom":
            getattr(self.adv, eff["fn"])(self, actor, eff)
        else:
            ui.warn(f"(unknown effect {do})")

    def level_notice(self) -> None:
        for p in self.gs.living():
            if p.can_level_up():
                self.ui.warn(f"{p.name} can level up! Choose 'Level up' from the menu.")

    # ------------------------------------------------------------ features
    def features(self) -> List[dict]:
        room = self.adv.ROOMS[self.gs.room]
        st = self.gs.rs()
        out = []
        for f in room.get("features", []):
            if f.get("once") and f["id"] in st["used"]:
                continue
            if not self.met(f.get("requires")):
                continue
            out.append(f)
        return out

    def do_feature(self, f: dict) -> None:
        ui, gs = self.ui, self.gs
        st = gs.rs()
        chk = f.get("check")
        if f.get("intro"):
            ui.gm(f["intro"])
        if not chk:
            if f.get("once"):
                st["used"].append(f["id"])
            self.run(f.get("effects", []), gs.able()[0] if gs.able() else None)
            return
        skill, dc = chk["skill"], chk["dc"]
        who = chk.get("who", "choose")
        attempts = st["attempts"].setdefault(f["id"], [])
        heroes = [h for h in gs.able() if chk.get("retry", True) or h.name not in attempts]
        if not heroes:
            ui.out("Everyone has already tried that.")
            return
        success = False
        actor = None
        if who == "each":
            need = chk.get("need", "all")
            results = []
            for h in heroes:
                results.append((h, self.roll_check(h, skill, dc, extra=chk.get("bonus", 0)) >= dc))
            oks = [r for _, r in results]
            success = all(oks) if need == "all" else any(oks)
            actor = next((h for h, r in results if (r if success else not r)), heroes[0])
        else:
            actor = self.pick_hero(chk.get("prompt", f"Who attempts it? ({self.skill_label(skill)} DC "
                                   f"{dc if chk.get('show_dc', True) else '?'})"), skill, heroes)
            if actor is None:
                return
            take = None
            if chk.get("take10_ok") and ui.confirm("Take 10 (no rush, average result)?", True):
                take = 10
            total = self.roll_check(actor, skill, dc, take, extra=chk.get("bonus", 0),
                                    show_dc=chk.get("show_dc", True))
            success = total >= dc
            if not chk.get("retry", True):
                attempts.append(actor.name)
            if not success and total <= dc - 5 and f.get("fail_by_5"):
                if f.get("once_on_fail"):
                    st["used"].append(f["id"])
                self.run(f["fail_by_5"], actor)
                return
        if success:
            if f.get("once", True):
                st["used"].append(f["id"])
            self.run(f.get("success", []), actor)
        else:
            if f.get("once_on_fail"):
                st["used"].append(f["id"])
            self.run(f.get("failure", [{"do": "text", "text": "Nothing comes of it."}]), actor)

    # ------------------------------------------------------------ encounters
    def build_monsters(self, enc_id: str) -> List[Monster]:
        enc = self.adv.ENCOUNTERS[enc_id]
        gs = self.gs
        saved = gs.rs(enc.get("room")).get("enc_left", {}).get(enc_id)
        mons = []
        if saved is not None:
            for s in saved:
                m = Monster(s["key"], s.get("base_name"), roll_hp=False,
                            overrides=enc.get("overrides", {}).get(s["key"]))
                m._max_hp = s["max_hp"]
                m.damage = s["damage"]
                m.base_name = s.get("base_name")
                mons.append(m)
            return mons
        keys = list(enc["monsters"])
        extra = max(0, len(gs.living()) - 2)
        for _ in range(extra):
            keys += enc.get("per_extra_hero", [])
        mods = gs.rs(enc.get("room")).get("enc_mods", {}).get(enc_id, {})
        keys += mods.get("add", [])
        for _ in range(mods.get("remove", 0)):
            if len(keys) > 1:
                keys.pop()
        names = enc.get("names", {})
        for k in keys:
            nm = names.get(k)
            m = Monster(k, nm, overrides=enc.get("overrides", {}).get(k))
            m.base_name = nm
            mons.append(m)
        return mons

    def start_encounter(self, enc_id: str, surprise: Optional[str] = None) -> None:
        ui, gs = self.ui, self.gs
        if self.enc_done(enc_id):
            return
        enc = self.adv.ENCOUNTERS[enc_id]
        mons = self.build_monsters(enc_id)
        surprised = []
        if surprise == "party":
            surprised = list(gs.able())
        elif surprise == "monsters":
            surprised = list(mons)
        elif enc.get("ambush") and surprise is None:
            ui.gm(enc.get("ambush_text", "Something stirs in the shadows..."))
            hide = max(m.skill_total("Hide") for m in mons) + dice.d20()
            ui.roll(f"The foes are hiding (Hide {hide}).")
            for p in gs.able():
                if self.roll_check(p, "Spot", hide, show_dc=False) < hide:
                    surprised.append(p)
            if surprised:
                ui.bad(", ".join(p.name for p in surprised) + " didn't see it coming!")
            else:
                ui.good("You spot the ambush in time!")
        if enc.get("text"):
            ui.gm(enc["text"])
        combat = Combat(ui, gs.party, mons, surprised, can_flee=enc.get("can_flee", True),
                        title=enc.get("title", "COMBAT"), dark=self.in_darkness(),
                        terrain=self.battle_terrain(enc))
        result = combat.run()
        award_xp(ui, gs.party, combat.xp_monsters, gs.party_level())
        gs.pass_time(1, ui)
        if result == "victory":
            gs.flags.add(f"enc:{enc_id}")
            gs.rs(enc.get("room")).get("enc_left", {}).pop(enc_id, None)
            self.run(enc.get("after", []))
            self.aftercare()
        elif result == "fled":
            left = [m for m in mons if not m.dead and not combat.s(m).fled]
            gs.rs(enc.get("room")).setdefault("enc_left", {})[enc_id] = [
                {"key": m.key, "base_name": getattr(m, "base_name", None),
                 "max_hp": m._max_hp, "damage": m.damage} for m in left]
            if not left:
                gs.flags.add(f"enc:{enc_id}")
            for p in gs.party:
                if p.hp < 0 and not p.dead:
                    ui.bad(f"{p.name} was left behind... and the foes show no mercy.")
                    p.dead = True
            back = enc.get("flee_to") or self.adv.ROOMS[gs.room].get("flee_to")
            ui.gm("You run for your lives!")
            if back:
                gs.room = back
        else:
            raise GameOver("defeat")

    def stealth_approach(self, enc_id: str) -> None:
        ui, gs = self.ui, self.gs
        mons = self.build_monsters(enc_id)
        listen = max(m.skill_total("Listen") for m in mons) + dice.d20()
        ui.out("The party creeps forward...")
        ok = True
        for p in gs.able():
            if self.roll_check(p, "Move Silently", listen, show_dc=False) < listen:
                ok = False
        if ok:
            ui.good("You reach them unnoticed! You get a surprise round.")
            self.start_encounter(enc_id, surprise="monsters")
        else:
            ui.bad("Someone's armor clanks. They hear you coming!")
            self.start_encounter(enc_id, surprise="none")

    def resolve_encounter(self, enc_id: str, xp: bool, factor: float = 1.0) -> None:
        gs = self.gs
        if self.enc_done(enc_id):
            return
        gs.flags.add(f"enc:{enc_id}")
        if xp:
            mons = self.build_monsters(enc_id)
            total = sum(rules.xp_award(gs.party_level(), m.cr) for m in mons)
            each = int(total * factor) // max(1, len(gs.living()))
            for p in gs.living():
                p.xp += each
            self.ui.good(f"Encounter overcome! Each hero earns {each} XP.")
            self.level_notice()

    def aftercare(self) -> None:
        """After a fight: tend to dying friends."""
        ui, gs = self.ui, self.gs
        for p in gs.party:
            while p.hp < 0 and not p.dead and not p.stable:
                helpers = gs.able()
                if not helpers:
                    r = dice.percent()
                    if r <= 10:
                        p.stable = True
                        ui.good(f"{p.name} stabilizes on their own.")
                    else:
                        p.damage += 1
                        p.check_death()
                        if p.dead:
                            ui.bad(f"{p.name} bleeds out and dies.")
                    continue
                ui.bad(f"{p.name} is dying ({p.hp} hp)!")
                opts = ["Heal check to stabilize (DC 15)"]
                casts = [(h, cst) for h in helpers for cst in h.available_casts()
                         if cst["spell"].startswith("Cure")]
                pots = [(h, e) for h in helpers for e in h.inventory
                        if e["id"].startswith("potion of cure")]
                for h, cst in casts:
                    opts.append(f"{h.name} casts {cst['spell']}")
                for h, e in pots:
                    opts.append(f"{h.name} uses {item_name(e)}")
                i = ui.choose("What do you do?", opts)
                if i == 0:
                    h = self.pick_hero("Who tends the wounds?", "Heal") or helpers[0]
                    if self.roll_check(h, "Heal", 15) >= 15:
                        p.stable = True
                        ui.good(f"{p.name} is stable.")
                    else:
                        p.damage += 1
                        p.check_death()
                        ui.bad(f"{p.name} loses more blood ({p.hp})." if not p.dead else
                               f"{p.name} dies.")
                elif i <= len(casts):
                    h, cst = casts[i - 1]
                    from ..magic import cast_spell, caster_cl, caster_dc
                    h.expend(cst)
                    cast_spell(ui, h, cst["spell"], [p], caster_cl(h, cst), caster_dc(h, cst))
                else:
                    h, e = pots[i - 1 - len(casts)]
                    from ..magic import cast_spell
                    d = item_data(e)
                    h.remove_item(e, 1)
                    cast_spell(ui, p, d["spell"], [p], d.get("cl", 1), 11)
        if not gs.able():
            raise GameOver("defeat")

    # ------------------------------------------------------------ traps
    def trap_state(self, trap_id: str) -> str:
        st = self.gs.rs()
        if trap_id in st["disabled_traps"]:
            return "disabled"
        if trap_id in st["found_traps"]:
            return "found"
        return "hidden"

    def search_room(self) -> None:
        ui, gs = self.ui, self.gs
        room = self.adv.ROOMS[gs.room]
        st = gs.rs()
        ui.out("The party searches the area carefully (taking 20; about 2 minutes)...")
        gs.pass_time(2, ui)
        found_any = False
        seers = [h for h in gs.able() if not self.in_darkness()
                 or "darkvision" in h.race_data["vision"]]
        if not seers:
            ui.bad("It's too dark to search without a light.")
            return
        for h in seers:
            total = self.roll_check(h, "Search", None, take=20)
            for tid, trap in room.get("traps", {}).items():
                if tid in st["found_traps"] or tid in st["disabled_traps"]:
                    continue
                if not self.met(trap.get("requires")):
                    continue
                dc = trap["search_dc"]
                if dc > 20 and not h.class_level("rogue"):
                    continue
                if total >= dc:
                    st["found_traps"].append(tid)
                    ui.warn(f"{h.name} finds a trap: {trap['name']}! {trap.get('found_text', '')}")
                    found_any = True
            for ex_id, ex in room.get("exits", {}).items():
                hid = ex.get("hidden")
                if hid and hid.get("search_dc") and ex_id not in st["revealed"]:
                    if total >= hid["search_dc"] and self.met(hid.get("requires")):
                        st["revealed"].append(ex_id)
                        ui.good(f"{h.name} discovers {hid.get('found_text', 'a hidden passage')}!")
                        found_any = True
            for sec in room.get("secrets", []):
                if sec["id"] in st["used"] or not self.met(sec.get("requires")):
                    continue
                if total >= sec["search_dc"]:
                    st["used"].append(sec["id"])
                    found_any = True
                    self.run(sec["effects"], h)
        if not found_any:
            ui.out("You find nothing new.")
        self.wandering_check(0.1)

    def passive_checks(self) -> None:
        ui, gs = self.ui, self.gs
        room = self.adv.ROOMS[gs.room]
        st = gs.rs()
        for h in gs.able():
            if h.race_data.get("stonecunning"):
                for tid, trap in room.get("traps", {}).items():
                    if trap.get("stone") and tid not in st["found_traps"] and \
                            tid not in st["disabled_traps"]:
                        r = dice.d20()
                        tot = r + h.skill_total("Search") + 2
                        if tot >= trap["search_dc"]:
                            st["found_traps"].append(tid)
                            ui.warn(f"{h.name}'s dwarven stonecunning notices something "
                                    f"odd about the floor: {trap['name']}!")
            if h.race in ("elf",) or h.race_data.get("auto_secret_door"):
                for ex_id, ex in room.get("exits", {}).items():
                    hid = ex.get("hidden")
                    if hid and hid.get("search_dc") and ex_id not in st["revealed"]:
                        r = dice.d20()
                        if r + h.skill_total("Search") >= hid["search_dc"]:
                            st["revealed"].append(ex_id)
                            ui.good(f"{h.name}'s elven eyes catch the outline of "
                                    f"{hid.get('found_text', 'a secret door')}!")

    def disable_trap(self, tid: str) -> None:
        ui, gs = self.ui, self.gs
        trap = self.adv.ROOMS[gs.room]["traps"][tid]
        dc = trap["disable_dc"]
        h = self.pick_hero(f"Who tries to disable the {trap['name']}? (DC {dc})",
                           "Disable Device")
        if h is None:
            return
        if not h.can_use_skill("Disable Device"):
            ui.bad(f"{h.name} has no idea how (Disable Device is trained only).")
            return
        if dc > 20 and not h.class_level("rogue"):
            ui.bad("Only a rogue's trapfinding can handle a trap this intricate.")
            return
        take10 = ui.confirm("Take 10 (careful, steady work)?", True)
        gs.pass_time(2, ui)
        total = self.roll_check(h, "Disable Device", dc, 10 if take10 else None)
        if total >= dc:
            gs.rs()["disabled_traps"].append(tid)
            ui.good(f"{h.name} disables the {trap['name']}.")
            if trap.get("xp"):
                self.run([{"do": "xp", "amount": trap["xp"], "why": "trap disarmed"}])
        elif total <= dc - 5:
            ui.bad("Something goes click...")
            self.trigger_trap(tid, h)
        else:
            ui.out("No luck yet; you can try again.")

    def trigger_trap(self, tid: str, victim: Character) -> None:
        ui, gs = self.ui, self.gs
        trap = self.adv.ROOMS[gs.room]["traps"][tid]
        ui.gm(trap.get("trigger_text", "A trap springs!"))
        self.run(trap["effects"], victim)
        if trap.get("one_shot"):
            gs.rs()["disabled_traps"].append(tid)
        else:
            if tid not in gs.rs()["found_traps"]:
                gs.rs()["found_traps"].append(tid)
        if not gs.able():
            raise GameOver("defeat")

    # ------------------------------------------------------------ movement
    def exits(self) -> List[tuple]:
        room = self.adv.ROOMS[self.gs.room]
        st = self.gs.rs()
        out = []
        for ex_id, ex in room.get("exits", {}).items():
            if ex.get("hidden") and ex_id not in st["revealed"]:
                continue
            if not self.met(ex.get("requires")):
                continue
            out.append((ex_id, ex))
        return out

    def try_exit(self, ex_id: str, ex: dict) -> None:
        ui, gs = self.ui, self.gs
        st = gs.rs()
        blocked = ex.get("blocked_by")
        if blocked and not self.enc_done(blocked):
            ui.bad(ex.get("blocked_text", "Your way is blocked by enemies!"))
            return
        lock = ex.get("lock")
        if lock and ex_id not in st["unlocked"]:
            if not self.handle_lock(ex_id, ex, lock):
                return
        trap_id = ex.get("trap")
        if trap_id and self.trap_state(trap_id) != "disabled":
            trap = self.adv.ROOMS[gs.room]["traps"][trap_id]
            if self.trap_state(trap_id) == "found":
                opts = ["Try to disable it (Disable Device)",
                        trap.get("bypass_label", "Carefully get past it"), "Stay here"]
                if trap.get("no_disable"):
                    opts[0] = "(can't be disabled)"
                i = ui.choose(f"The {trap['name']} lies in your path.", opts)
                if i == 0 and trap.get("no_disable"):
                    ui.out("That won't work here.")
                    return
                if i == 0:
                    self.disable_trap(trap_id)
                    return
                if i == 2:
                    return
                if trap.get("bypass"):
                    ok = True
                    for h in gs.able():
                        chk = trap["bypass"]
                        if self.roll_check(h, chk["skill"], chk["dc"]) < chk["dc"]:
                            ui.bad(f"{h.name} slips!")
                            self.trigger_trap(trap_id, h)
                            ok = False
                            break
                    if not ok:
                        return
                else:
                    ui.out("You edge around it carefully.")
            else:
                leader = gs.able()[0]
                self.trigger_trap(trap_id, leader)
                return
        if ex.get("text"):
            ui.gm(ex["text"])
        self.run(ex.get("effects", []))
        self.enter(ex["to"])

    def handle_lock(self, ex_id: str, ex: dict, lock: dict) -> bool:
        ui, gs = self.ui, self.gs
        if lock.get("key") and any(p.has_item(lock["key"]) for p in gs.living()):
            ui.good(f"The {item_name(make_item(lock['key']))} turns in the lock.")
            gs.rs()["unlocked"].append(ex_id)
            return True
        ui.out(lock.get("text", "The way is locked."))
        opts = []
        if lock.get("open_dc"):
            opts.append(f"Pick the lock (Open Lock DC {lock['open_dc']})")
        if lock.get("break_dc"):
            opts.append(f"Force it (Strength check DC {lock['break_dc']})")
        opts.append("Leave it")
        i = ui.choose("What now?", opts)
        label = opts[i]
        if label.startswith("Pick"):
            h = self.pick_hero("Who picks the lock?", "Open Lock")
            if not h:
                return False
            take = 20 if ui.confirm("Take 20 (spend 2 minutes, best possible result)?",
                                    True) else None
            if take:
                gs.pass_time(2, ui)
                self.wandering_check(0.05)
            if self.roll_check(h, "Open Lock", lock["open_dc"], take) >= lock["open_dc"]:
                ui.good("Click! The lock opens.")
                gs.rs()["unlocked"].append(ex_id)
                return True
            ui.bad("The lock resists.")
        elif label.startswith("Force"):
            h = self.pick_hero("Who tries to force it?", "ability:str")
            if not h:
                return False
            bonus = 2 if h.has_item("crowbar") else 0
            tot = self.roll_check(h, "ability:str", lock["break_dc"], extra=bonus)
            if tot >= lock["break_dc"]:
                ui.good("With a splintering crash, it gives way!")
                gs.rs()["unlocked"].append(ex_id)
                if lock.get("noise_enc"):
                    self.run([{"do": "flag", "name": "alarm"}])
                return True
            ui.bad("It holds fast. (The noise echoes...)")
            self.wandering_check(0.15)
        return False

    def enter(self, room_id: str) -> None:
        ui, gs = self.ui, self.gs
        gs.room = room_id
        room = self.adv.ROOMS[room_id]
        st = gs.rs()
        first = not st["visited"]
        st["visited"] = True
        gs.pass_time(room.get("travel_minutes", 1), ui)
        self.autosave()
        ui.header(room["name"])
        if first and room.get("first"):
            ui.gm(room["first"])
        ui.gm(room["desc"])
        if room.get("dark"):
            self.ensure_light()
        self.passive_checks()
        self.run(room.get("on_enter", []))
        if first:
            self.run(room.get("on_first_enter", []))
        for enc_id in room.get("encounters_enter", []):
            if not self.enc_done(enc_id) and self.met(self.adv.ENCOUNTERS[enc_id].get("requires")):
                if gs.sneaking and not self.adv.ENCOUNTERS[enc_id].get("ambush"):
                    self.stealth_approach(enc_id)
                else:
                    self.start_encounter(enc_id)
                if gs.room != room_id:
                    return

    def battle_terrain(self, enc: dict) -> str:
        """Battlefield theme: the encounter's own, else one that fits the room."""
        from ..grid import theme_for
        return enc.get("terrain") or theme_for(self.adv.ROOMS.get(self.gs.room, {}))

    # ------------------------------------------------------------ light & darkness
    def in_darkness(self) -> bool:
        room = self.adv.ROOMS[self.gs.room]
        return bool(room.get("dark")) and self.gs.light_minutes <= 0

    def ensure_light(self) -> None:
        ui, gs = self.ui, self.gs
        if gs.light_minutes > 0:
            return
        for p in gs.able():
            caster = next((c for c in p.available_casts() if c["spell"] == "Light"), None)
            if caster:
                p.expend(caster)
                gs.light_minutes = 10 * max(1, p.caster_level(caster["class"]))
                ui.out(f"{p.name} casts light on a pebble; it glows like a torch.")
                return
        for p in gs.living():
            lamp = p.find_item("lantern")
            oil = p.find_item("oil")
            if lamp and oil:
                p.remove_item(oil, 1)
                gs.light_minutes = 6 * 60
                ui.out(f"{p.name} fills and lights the lantern (6 hours of light).")
                return
            torch = p.find_item("torch")
            if torch:
                p.remove_item(torch, 1)
                gs.light_minutes = 60
                ui.out(f"{p.name} lights a torch (1 hour of light).")
                return
        blind = [p.name for p in gs.able() if "darkvision" not in p.race_data["vision"]]
        if blind:
            ui.bad("It's pitch dark and you have no light! " + ", ".join(blind) +
                   " can't see a thing (blind in a fight: 50% miss chance, -2 AC). "
                   "Buy torches, a lantern and oil, or bring a light spell.")

    # ------------------------------------------------------------ hazards & talking
    def hazard(self, eff: dict) -> None:
        ui, gs = self.ui, self.gs
        kind = eff["do"]
        for p in gs.able():
            if kind == "swim":
                total = self.roll_check(p, "Swim", eff["dc"])
                if total >= eff["dc"]:
                    continue
                if any(q.has_item("rope") for q in gs.living()) and total >= eff["dc"] - 5:
                    ui.out(f"  A rope from the others hauls {p.name} through.")
                    continue
                amt = dice.roll("1d6").total
                p.take_nonlethal(amt)
                ui.bad(f"  {p.name} goes under and swallows water ({amt} nonlethal damage).")
                if total <= eff["dc"] - 5:
                    r = dice.roll("2d6").total
                    p.take_nonlethal(r)
                    ui.bad(f"  {p.name} is nearly drowned ({r} more)!")
            elif kind == "exposure":
                if p.get_effect("Endure Elements") or eff.get("type", "cold") in p.immunities():
                    ui.out(f"  {p.name} is comfortable (endure elements).")
                    continue
                if not saving_throw(ui, p, "fort", eff["dc"], [], f"{eff.get('type', 'cold')} "
                                                                   f"exposure"):
                    amt = dice.roll(eff.get("dice", "1d6")).total
                    p.take_nonlethal(amt)
                    ui.bad(f"  The {eff.get('type', 'cold')} saps {p.name} ({amt} nonlethal "
                           f"damage).")
            elif kind == "fall":
                feet = eff["feet"]
                if p.skill_total("Jump") + dice.d20() >= 15 or \
                        (p.can_use_skill("Tumble") and p.skill_total("Tumble") + dice.d20() >= 15):
                    feet = max(0, feet - 10)
                n = min(20, feet // 10)
                if n:
                    r = dice.roll(f"{n}d6")
                    dealt, _ = p.take_damage(r.total, "", magic=True)
                    ui.bad(f"  {p.name} falls {eff['feet']} ft. and takes {dealt} damage.")
        if gs.able() and all(not p.conscious for p in gs.living()):
            raise GameOver("defeat")

    ATTITUDES = ["hostile", "unfriendly", "indifferent", "friendly", "helpful"]
    DIPLOMACY_DC = {("hostile", "unfriendly"): 20, ("hostile", "indifferent"): 25,
                    ("hostile", "friendly"): 35, ("hostile", "helpful"): 50,
                    ("unfriendly", "indifferent"): 15, ("unfriendly", "friendly"): 25,
                    ("unfriendly", "helpful"): 40, ("indifferent", "friendly"): 15,
                    ("indifferent", "helpful"): 30, ("friendly", "helpful"): 20}

    def diplomacy(self, eff: dict, actor) -> None:
        """Shift an NPC's attitude (SRD Diplomacy table). One try per NPC per day."""
        ui, gs = self.ui, self.gs
        npc = eff["npc"]
        cur = gs.attitudes.get(npc, eff.get("start", "indifferent"))
        goal = eff["goal"]
        A = self.ATTITUDES
        if A.index(cur) >= A.index(goal):
            self.run(eff.get("success", []), actor)
            return
        day_key = f"diplo:{npc}:{gs.minutes // 1440}"
        if day_key in gs.flags:
            ui.out(f"{npc} won't be talked around again today.")
            return
        gs.flags.add(day_key)
        h = self.pick_hero(f"Who talks to {npc}? ({cur} -> {goal}, Diplomacy)", "Diplomacy")
        if h is None:
            return
        total = self.roll_check(h, "Diplomacy", None) + eff.get("bonus", 0)
        best = cur
        for att in A[A.index(cur) + 1:]:
            if total >= self.DIPLOMACY_DC[(cur, att)]:
                best = att
        gs.attitudes[npc] = best
        ui.out(f"{npc} is now {best}." if best != cur else f"{npc} remains {cur}.")
        if A.index(best) >= A.index(goal):
            self.run(eff.get("success", []), h)
        else:
            self.run(eff.get("failure", []), h)

    # ------------------------------------------------------------ rest
    def rest(self, cost_sp: int = 0, safe: bool = True) -> None:
        ui, gs = self.ui, self.gs
        if cost_sp:
            total = cost_sp * 10 * len(gs.living())
            if sum(p.cp for p in gs.living()) < total:
                ui.bad("You can't afford the rooms.")
                return
            remaining = total
            for p in sorted(gs.living(), key=lambda p: -p.cp):
                take = min(p.cp, remaining)
                p.cp -= take
                remaining -= take
            ui.out(f"You pay {rules.money_str(total)} for rooms and a hot meal.")
        if not safe:
            room = self.adv.ROOMS[gs.room]
            if room.get("no_rest"):
                ui.bad(room.get("no_rest_text", "This is no place to rest."))
                return
            unfinished = [e for e in room.get("encounters_enter", []) if not self.enc_done(e)]
            if unfinished:
                ui.bad("Not with enemies nearby!")
                return
            ui.out("You set a watch and try to sleep...")
            if self.wandering_check(self.adv.REST_ENCOUNTER_CHANCE, resting=True):
                ui.out("After the fight you manage to finish resting.")
        gs.pass_time(8 * 60, ui)
        ui.header("A NIGHT'S REST")
        for p in gs.party:
            if p.dead:
                continue
            if p.hp < 0:
                p.stable = True
            healed = p.heal(p.level * (2 if cost_sp else 1))
            for ab in list(p.ability_damage):
                p.ability_damage[ab] -= 1
                if p.ability_damage[ab] <= 0:
                    del p.ability_damage[ab]
            p.daily = {}
            p.temp_hp = 0
            p.nonlethal = 0
            p.effects = [e for e in p.effects if e.duration is None and "fatigued" not in e.tags
                         and "prone" not in e.tags]
            ui.out(f"{p.name} recovers {healed} hp ({p.hp}/{p.max_hp()})."
                   + ("  (A soft bed doubles natural healing.)" if cost_sp else ""))
            self.disease_check(p)
            self.drain_check(p)
            p.reset_spells()
            rest_companion(ui, p)
        for p in gs.living():
            if p.caster_classes():
                with ui.acting(p.player):
                    prepare_spells(p, ui)
        if self.adv.ROOMS[gs.room].get("dark"):
            self.ensure_light()
        for p in gs.living():
            if p.can_level_up():
                level_up_interactive(p, ui, gs.settings.get("heroic", False))

    def disease_check(self, p: Character) -> None:
        ui = self.ui
        for a in list(p.afflictions):
            if saving_throw(ui, p, "fort", a["dc"], ["disease"], a["name"]):
                a["successes"] = a.get("successes", 0) + 1
                if a["successes"] >= 2:
                    p.afflictions.remove(a)
                    ui.good(f"{p.name} has fought off {a['name']}.")
            else:
                a["successes"] = 0
                for ab in a["abilities"]:
                    amt = dice.roll(a["damage"]).total
                    p.ability_damage[ab] = p.ability_damage.get(ab, 0) + amt
                    ui.bad(f"{a['name']}: {p.name} takes {amt} {ab.upper()} damage.")

    def wandering_check(self, chance: float, resting: bool = False) -> bool:
        gs = self.gs
        room = self.adv.ROOMS[gs.room]
        if room.get("town") or not room.get("wandering", True):
            return False
        if dice.percent() > chance * 100:
            return False
        options = [w for w in self.adv.WANDERING if self.met(w.get("requires"))]
        if not options:
            return False
        w = dice.choice(options)
        self.ui.warn(w["text"])
        mons = [Monster(k) for k in w["monsters"]]
        surprised = list(gs.able()) if resting and dice.percent() <= 50 else []
        combat = Combat(self.ui, gs.party, mons, surprised, title="WANDERING MONSTERS",
                        terrain=self.battle_terrain({}))
        result = combat.run()
        award_xp(self.ui, gs.party, combat.xp_monsters, gs.party_level())
        if result == "defeat":
            raise GameOver("defeat")
        self.aftercare()
        return True

    # ------------------------------------------------------------ town services
    def temple_services(self) -> None:
        ui, gs = self.ui, self.gs
        while True:
            opts = ["Buy potions, holy water and scrolls",
                    "Healing: cure light wounds cast on a hero (10 gp)",
                    "Healing: cure moderate wounds (60 gp)",
                    "Lesser restoration: heal all ability damage on one hero (60 gp)",
                    "Remove disease (150 gp)"]
            if any(getattr(p, "fallen", False) for p in gs.living()):
                opts.append("Atonement: restore a fallen paladin's oath (450 gp)")
            if any(p.get_effect("Negative levels") for p in gs.living()):
                opts.append("Restoration: remove life drain from one hero (380 gp)")
            dead = [p for p in gs.party if p.dead]
            if dead:
                opts.append("Raise dead: return a fallen hero to life (5,450 gp)")
            opts.append("Leave the shrine")
            i = ui.choose(getattr(self.adv, "TEMPLE_GREETING",
                                  "Sister Elowen, the priestess of Pelor, smiles. 'How may "
                                  "the Dawnfather help?'"), opts)
            if i == 0:
                shop_menu(ui, gs.living(), getattr(self.adv, "TEMPLE_NAME", "Shrine of Pelor"),
                          ["temple"])
            elif i in (1, 2):
                cost = 10 if i == 1 else 60
                who = self.pick_hero("Who is healed?", heroes=gs.living())
                if who is None:
                    continue
                payer = self._payer(cost)
                if not payer:
                    continue
                payer.cp -= cost * 100
                amt = dice.roll("1d8+1" if i == 1 else "2d8+3").total
                heal(ui, who, amt)
            elif i == 3:
                who = self.pick_hero("Who?", heroes=gs.living())
                if who and who.ability_damage and self._payer(60):
                    self._payer(60).cp -= 6000
                    who.ability_damage = {}
                    ui.good(f"{who.name}'s strength returns.")
                elif who:
                    ui.out("Nothing to restore.")
            elif i == 4:
                who = self.pick_hero("Who?", heroes=gs.living())
                if who and who.afflictions and self._payer(150):
                    self._payer(150).cp -= 15000
                    who.afflictions = []
                    ui.good(f"{who.name} is cured of disease.")
                elif who:
                    ui.out(f"{who.name} isn't sick.")
            elif opts[i].startswith("Atonement"):
                fallen = [p for p in gs.living() if getattr(p, "fallen", False)]
                who = fallen[0] if len(fallen) == 1 else self.pick_hero("Who?", heroes=fallen)
                payer = who and self._payer(450)
                if payer:
                    payer.cp -= 450 * 100
                    who.fallen = False
                    ui.good(f"{who.name} kneels through a night of prayer. At dawn, their "
                            f"oath burns bright again.")
            elif opts[i].startswith("Restoration"):
                drained = [p for p in gs.living() if p.get_effect("Negative levels")]
                who = drained[0] if len(drained) == 1 else self.pick_hero("Who?", heroes=drained)
                payer = who and self._payer(380)
                if payer:
                    payer.cp -= 380 * 100
                    who.remove_effect("Negative levels")
                    who.ability_damage = {}
                    ui.good(f"Warm light floods {who.name}; the cold of the grave is gone.")
            elif opts[i].startswith("Raise dead"):
                dead = [p for p in gs.party if p.dead]
                who = dead[0] if len(dead) == 1 else self.pick_hero("Raise whom?", heroes=dead)
                payer = who and self._payer(5450)
                if payer:
                    payer.cp -= 5450 * 100
                    ui.gm(f"The priests lay {who.name} on the altar and pray through the "
                          f"night, crushing a flawless diamond into the holy oil...")
                    from ..magic import raise_dead
                    raise_dead(ui, who)
            else:
                return

    def familiar_scout(self) -> None:
        ui, gs = self.ui, self.gs
        owner = next(p for p in gs.living() if p.familiar and p.conscious)
        fam = owner.familiar
        exits = self.exits()
        i = ui.choose(f"Where does {fam['name']} the {fam['kind']} go?",
                      [f"{ex_id}: {ex['label']}" for ex_id, ex in exits], allow_cancel=True)
        if i is None:
            return
        ex_id, ex = exits[i]
        room = self.adv.ROOMS[ex["to"]]
        gs.pass_time(5, ui)
        ui.out(f"{fam['name']} slips away {ex_id} and comes back a few minutes later, sharing "
               f"what it saw through your empathic link:")
        seen = []
        encs = [e for e, d in self.adv.ENCOUNTERS.items() if d.get("room") == ex["to"]]
        for enc_id in dict.fromkeys(room.get("encounters_enter", []) + encs):
            if not self.enc_done(enc_id):
                mons = self.adv.ENCOUNTERS[enc_id]["monsters"]
                from ..data.monsters import MONSTERS
                names = {}
                for k in mons:
                    names[MONSTERS[k]["name"]] = names.get(MONSTERS[k]["name"], 0) + 1
                seen.append(", ".join(f"{n}x {k}" if n > 1 else k for k, n in names.items()))
        ui.gm(f"{room['name']}: {room['desc']}")
        if seen:
            ui.warn("Danger waiting there: " + "; ".join(seen) + ".")
        else:
            ui.good("Nothing hostile waiting there, as far as it could tell.")
        if dice.percent() <= 10:
            ui.bad(f"Something nearly caught {fam['name']}; it comes back shaking.")

    def drain_check(self, p) -> None:
        """Each day a drained hero tries to shake off each negative level (Fort save)."""
        e = p.get_effect("Negative levels")
        if not e:
            return
        n, dc = e.data.get("n", 0), e.data.get("dc", 14)
        kept = 0
        for _ in range(n):
            if not saving_throw(self.ui, p, "fort", dc, [], "negative level"):
                kept += 1
        p.remove_effect("Negative levels")
        if kept:
            p.add_effect(Effect("Negative levels", None,
                                [("attack", "untyped", -kept), ("saves", "untyped", -kept),
                                 ("skills", "untyped", -kept), ("max_hp", "untyped", -5 * kept)],
                                data={"n": kept, "dc": dc}))
            self.ui.warn(f"{p.name} still carries {kept} negative level(s). Rest again, or "
                         f"have a temple cast restoration.")
        else:
            self.ui.good(f"{p.name} shakes off the life drain.")

    def _payer(self, gp: int) -> Optional[Character]:
        rich = [p for p in self.gs.living() if p.cp >= gp * 100]
        if not rich:
            self.ui.bad(f"No one has {gp} gp. (Use 'Give money' in a shop to pool funds.)")
            return None
        if len(rich) == 1:
            return rich[0]
        return self.pick_hero("Who pays?", heroes=rich)

    def rumors(self, actor: Optional[Character]) -> None:
        ui, gs = self.ui, self.gs
        day = gs.minutes // (24 * 60)
        key = f"rumors_day_{day}"
        if key in gs.flags:
            ui.out("You've already worked the common room today. Try again tomorrow.")
            return
        gs.flags.add(key)
        h = self.pick_hero("Who mingles and asks around? (Gather Information)",
                           "Gather Information")
        if not h:
            return
        gs.pass_time(60, ui)
        tot = self.roll_check(h, "Gather Information", None)
        got = 0
        for dc, text in self.adv.RUMORS:
            if tot >= dc and f"rumor:{text[:12]}" not in gs.flags:
                gs.flags.add(f"rumor:{text[:12]}")
                ui.para(f"Rumor: {text}", ("bmagenta",))
                gs.note(f"Rumor: {text}")
                got += 1
                if got >= 2:
                    break
        if not got:
            ui.out("You hear nothing new (or nothing true).")

    def recruit(self) -> None:
        ui, gs = self.ui, self.gs
        from ..creation import choose_pregen, create_character
        from ..levelup import gain_level
        lvl = gs.party_level()
        dead = [p for p in gs.party if p.dead]
        if len(gs.living()) >= 4:
            ui.out("Your party is already full (4 heroes).")
            return
        if not dead and not ui.confirm("Add another hero to the party (fights get tougher "
                                       "too)?", False):
            return
        player = ui.ask("Who will play the new hero?", dead[0].player if dead else "")
        i = ui.choose("New hero", ["Create a new character", "Choose a ready-made hero"])
        with ui.acting(player):
            if i == 0:
                ch = create_character(ui, player, start_level=lvl)
            else:
                ch = choose_pregen(ui, player, [])
            cls = ch.class_levels[0]
            while ch.level < lvl:
                gain_level(ch, cls, ui, auto=True)
            ch.xp = rules.xp_for_level(ch.level)
            prepare_spells(ch, ui, auto=True)
        if gs.settings.get("heroic"):
            from ..game import make_heroic
            make_heroic(ch)
        if dead and ui.confirm(f"Replace {dead[0].name} (who rests in the village churchyard)?",
                               True):
            gs.party.remove(dead[0])
        gs.party.append(ch)
        ui.good(f"{ch.name} joins the party!")

    def riddle(self, eff: dict) -> None:
        ui = self.ui
        ui.para(eff["riddle"], ("bold", "byellow"))
        h = self.pick_hero("Who speaks the answer aloud?")
        if not h:
            return
        ans = ui.ask("Your answer").strip().lower()
        words = set(ans.replace(".", " ").replace("!", " ").split())
        if any(a in words or a == ans for a in eff["answers"]):
            self.run(eff["success"], h)
        else:
            self.run(eff["failure"], h)

    # ------------------------------------------------------------ main menu loop
    def autosave(self) -> None:
        """Saved after entering an area and after every action, one file per table."""
        try:
            save_game(self.gs, getattr(self.ui, "autosave_name", "autosave"))
        except OSError:
            pass

    def loop(self) -> None:
        gs = self.gs
        self.enter(gs.room) if not gs.rs()["visited"] else self.describe_brief()
        while True:
            if not gs.able():
                raise GameOver("defeat")
            self.turn_menu()
            if gs.able():
                self.autosave()

    def describe_brief(self) -> None:
        room = self.adv.ROOMS[self.gs.room]
        self.ui.header(room["name"])
        self.ui.gm(room["desc"])

    def turn_menu(self) -> None:
        ui, gs = self.ui, self.gs
        room = self.adv.ROOMS[gs.room]
        ui.out()
        ui.out(c(f"[{room['name']} | {gs.time_str()}]", "yellow") + "  " +
               "  ".join(short_status(p) for p in gs.party))
        opts: List[tuple] = []
        for f in self.features():
            opts.append((c(f["label"], "bcyan"), "feature", f))
        for ex_id, ex in self.exits():
            extra = ""
            tid = ex.get("trap")
            if tid and self.trap_state(tid) == "found":
                extra = c(" [TRAP]", "bred")
            if ex.get("lock") and ex_id not in gs.rs()["unlocked"]:
                extra += c(" [locked]", "yellow")
            opts.append((f"Go {ex_id}: {ex['label']}{extra}", "exit", (ex_id, ex)))
        if not room.get("town"):
            opts.append(("Search the area (traps, secret doors, loot)", "search", None))
            opts.append((f"Sneaking: {'ON' if gs.sneaking else 'off'} (Move Silently when "
                         f"entering new areas to gain surprise)", "sneak", None))
        if any(p.level < rules.MAX_LEVEL and p.can_level_up() for p in gs.living()):
            opts.append((c("Level up!", "bgreen", "bold"), "levelup", None))
        opts.append(("Character sheet", "sheet", None))
        if not getattr(ui, "has_party_tab", False):
            # the web page manages gear from each hero's sheet in the Party tab
            opts.append(("Inventory & equipment", "inv", None))
        opts.append(("Cast a spell (healing, buffs)", "cast", None))
        if not room.get("town") and any(p.familiar and p.conscious for p in gs.living()) \
                and self.exits():
            opts.append(("Send a familiar to scout ahead", "scout", None))
        if room.get("town") and can_anyone_craft(gs.living()):
            opts.append(("Craft magic items (downtime: days pass)", "craft", None))
        if has_usable(gs.living()):
            opts.append(("Use a class ability (lay on hands, wild shape...)", "ability", None))
        if not room.get("town"):
            opts.append(("Rest for 8 hours (heal, regain spells; may attract wanderers)",
                         "rest", None))
        opts += [("Look around again", "look", None), ("Journal & quest notes", "journal", None),
                 ("Save game", "save", None), ("Help / rules summary", "help", None),
                 ("Quit (offers to save)", "quit", None)]
        group_of = {"feature": "Actions", "exit": "Travel", "search": "Explore",
                    "sneak": "Explore", "rest": "Explore", "levelup": "Party",
                    "sheet": "Party", "inv": "Party", "cast": "Party", "ability": "Party",
                    "scout": "Explore", "craft": "Party"}
        i = ui.choose("What do you do?", [o[0] for o in opts],
                      groups=[group_of.get(o[1], "Game") for o in opts])
        _, kind, data = opts[i]
        if kind == "feature":
            self.do_feature(data)
        elif kind == "exit":
            self.try_exit(*data)
        elif kind == "search":
            self.search_room()
        elif kind == "sneak":
            gs.sneaking = not gs.sneaking
            ui.out("The party moves " + ("stealthily." if gs.sneaking else "normally."))
        elif kind == "levelup":
            for p in gs.living():
                if p.can_level_up():
                    level_up_interactive(p, ui, gs.settings.get("heroic", False))
        elif kind == "sheet":
            who = self.pick_hero("Whose sheet?", heroes=gs.party)
            if who:
                ui.out(render(who))
                ui.pause()
        elif kind == "inv":
            inventory_menu(ui, gs.living())
        elif kind == "cast":
            cast_out_of_combat(ui, gs.party)
        elif kind == "craft":
            craft_menu(ui, gs.living(), gs)
        elif kind == "scout":
            self.familiar_scout()
        elif kind == "ability":
            ability_menu(ui, gs.living())
        elif kind == "rest":
            self.rest(safe=False)
        elif kind == "look":
            ui.gm(room["desc"])
        elif kind == "journal":
            ui.sub("Journal")
            for line in gs.journal[-20:] or ["(empty)"]:
                ui.out("  " + line)
        elif kind == "save":
            name = ui.ask("Save name", "save1")
            safe = "".join(ch for ch in name if ch.isalnum() or ch in "-_") or "save1"
            save_game(gs, safe)
            ui.good(f"Saved as '{safe}'.")
        elif kind == "help":
            from ..game import HELP_TEXT
            ui.para(HELP_TEXT)
        elif kind == "quit":
            if ui.confirm("Save before quitting?", True):
                save_game(gs, "quicksave")
                ui.good("Saved as 'quicksave'.")
            raise QuitGame()
