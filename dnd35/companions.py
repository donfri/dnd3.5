"""Animal companions (druids, rangers) and familiars (wizards, sorcerers).

A companion is a real combatant on the party's side, advanced by its master's
effective druid level (SRD table: bonus HD, natural armor, Str/Dex, evasion,
multiattack). Its owner's player commands it in combat. Familiars stay safely
with their master and grant the SRD master bonuses plus Alertness.
"""
from __future__ import annotations

import random
from typing import Optional

from .data.monsters import COMPANIONS, FAMILIARS, MONSTERS
from .monster import Monster

COMPANION_NAMES = ["Ash", "Bramble", "Cinder", "Fang", "Grey", "Moss", "Rook", "Shadow",
                   "Thistle", "Wick"]
FAMILIAR_NAMES = ["Pip", "Hoot", "Nib", "Quill", "Smudge", "Whisker", "Ink", "Button"]

# effective druid level -> (bonus HD, natural armor adj, Str/Dex adj)
ADVANCE = [(9, 6, 6, 3), (6, 4, 4, 2), (3, 2, 2, 1), (1, 0, 0, 0)]


def effective_level(ch) -> int:
    lvl = ch.class_level("druid")
    if ch.class_level("ranger") >= 4:
        lvl += ch.class_level("ranger") // 2
    return lvl


def companion_options(ch):
    eff = effective_level(ch)
    return [k for k, (need, _) in COMPANIONS.items() if eff >= need]


class Companion(Monster):
    """A Monster that fights for the party."""

    def __init__(self, kind: str, name: str, eff: int):
        need, minus = COMPANIONS[kind]
        lvl = max(1, eff - minus)
        bonus_hd, nat, strdex = next((b, n, s) for th, b, n, s in ADVANCE if lvl >= th)
        base = MONSTERS[kind]
        hd = base["hd"] + bonus_hd
        ab = dict(base["abilities"])
        ab["str"] += strdex
        ab["dex"] += strdex
        feats = list(base.get("feats", []))
        if lvl >= 9 and len(base.get("natural_attacks", [])) > 1:
            feats.append("Multiattack")
        good = 2 + hd // 2
        overrides = {"hd": hd, "bab": hd * 3 // 4, "abilities": ab,
                     "natural": base.get("natural", 0) + nat, "feats": feats,
                     "base_saves": (good, good, hd // 3), "evil": False, "morale": False}
        super().__init__(kind, name=name, roll_hp=False, overrides=overrides)
        self.kind = kind
        self.companion_level = lvl
        self.block["desc"] = f"{name} the {base['name'].lower()}, an animal companion."

    def has_evasion(self) -> bool:
        return self.companion_level >= 3

    def immunities(self):
        return list(super().immunities())


MOUNT_ADVANCE = [(15, 8, 10, 4), (11, 6, 8, 3), (8, 4, 6, 2), (5, 2, 4, 1)]


class Mount(Monster):
    """A paladin's celestial warhorse."""

    def __init__(self, name: str, plevel: int):
        bonus_hd, nat, strb = next((b, n, st) for th, b, n, st in MOUNT_ADVANCE
                                   if plevel >= th)
        base = MONSTERS["heavy warhorse"]
        hd = base["hd"] + bonus_hd
        ab = dict(base["abilities"])
        ab["str"] += strb
        good = 2 + hd // 2
        super().__init__("heavy warhorse", name=name, roll_hp=False, overrides={
            "hd": hd, "bab": hd * 3 // 4, "abilities": ab,
            "natural": base["natural"] + nat, "base_saves": (good, good, hd // 3),
            "evil": False, "morale": False})
        self.kind = "heavy warhorse"
        self.block["desc"] = f"{name}, a paladin's celestial warhorse."

    def has_evasion(self) -> bool:
        return True

    def has_improved_evasion(self) -> bool:
        return True


def mount_creature(ch) -> Optional[Mount]:
    data = getattr(ch, "mount", None)
    if not data or ch.class_level("paladin") < 5 or getattr(ch, "fallen", False):
        return None
    key = (ch.class_level("paladin"), data["name"])
    inst = getattr(ch, "_mount_inst", None)
    if inst is None or getattr(ch, "_mount_key", None) != key:
        inst = Mount(data["name"], ch.class_level("paladin"))
        inst.damage = data.get("damage", 0)
        inst.dead = data.get("dead", False)
        inst.owner = ch
        ch._mount_inst = inst
        ch._mount_key = key
    return inst


def companion_creature(ch) -> Optional[Companion]:
    """The (cached) companion creature for this character, or None."""
    data = getattr(ch, "companion", None)
    if not data:
        return None
    eff = effective_level(ch)
    if eff < 1:
        return None
    key = (data["kind"], eff, data["name"])
    inst = getattr(ch, "_companion_inst", None)
    if inst is None or getattr(ch, "_companion_key", None) != key:
        inst = Companion(data["kind"], data["name"], eff)
        inst.damage = data.get("damage", 0)
        inst.dead = data.get("dead", False)
        inst.owner = ch
        ch._companion_inst = inst
        ch._companion_key = key
    return inst


def sync_companion(ch) -> None:
    inst = getattr(ch, "_companion_inst", None)
    if inst is not None and ch.companion:
        ch.companion["damage"] = inst.damage
        ch.companion["dead"] = inst.dead
    m = getattr(ch, "_mount_inst", None)
    if m is not None and getattr(ch, "mount", None):
        ch.mount["damage"] = m.damage
        ch.mount["dead"] = m.dead


def all_companions(ch):
    out = []
    for c in (companion_creature(ch), mount_creature(ch)):
        if c is not None:
            out.append(c)
    return out


def choose_companion(ch, ui, auto: bool) -> None:
    opts = companion_options(ch)
    if not opts:
        return
    if auto:
        kind = opts[0]
        name = random.choice(COMPANION_NAMES)
    else:
        ui.sub(f"Choose {ch.name}'s animal companion")
        labels = []
        for k in opts:
            m = MONSTERS[k]
            atk = ", ".join(f"{a['name']} {a['damage']}" for a in m["natural_attacks"])
            labels.append(f"{m['name']}: {m['desc']} ({atk}; speed {m['speed']} ft.)")
        kind = opts[ui.choose("Companion", labels)]
        name = ui.ask("Its name", random.choice(COMPANION_NAMES)).strip() or "Companion"
    ch.companion = {"kind": kind, "name": name, "damage": 0, "dead": False}
    ch._companion_inst = None
    if ui and not auto:
        ui.good(f"{name} the {MONSTERS[kind]['name'].lower()} joins {ch.name}.")


def choose_familiar(ch, ui, auto: bool) -> None:
    opts = list(FAMILIARS)
    if auto:
        kind = "toad" if ch.class_level("sorcerer") else "owl"
        name = random.choice(FAMILIAR_NAMES)
    else:
        ui.sub(f"Summon {ch.name}'s familiar")
        kind = opts[ui.choose("Familiar", [f"{k.title()}: {FAMILIARS[k][2]}" for k in opts])]
        name = ui.ask("Its name", random.choice(FAMILIAR_NAMES)).strip() or "Familiar"
    ch.familiar = {"kind": kind, "name": name}
    if ui and not auto:
        ui.good(f"{name} the {kind} appears in a puff of smoke.")


def familiar_bonus(ch, stat: str):
    fam = getattr(ch, "familiar", None)
    if not fam:
        return []
    key, val, _ = FAMILIARS[fam["kind"]]
    if key == stat:
        return [("familiar", val, f"familiar ({fam['kind']})")]
    return []


def rest_companion(ui, ch) -> None:
    m = mount_creature(ch)
    if m is not None:
        if m.dead:
            ui.out(f"{ch.name} prays at dawn, and {m.name} returns from the celestial "
                   f"realms, whole again.")
            ch.mount.update(damage=0, dead=False)
            ch._mount_inst = None
        else:
            m.damage = 0
            m.effects = []
            sync_companion(ch)
    inst = companion_creature(ch)
    if inst is None:
        return
    if inst.dead:
        old = ch.companion
        ui.out(f"{ch.name} spends the night in prayer; at dawn a new "
               f"{MONSTERS[old['kind']]['name'].lower()} pads out of the wild to join them.")
        ch.companion = {"kind": old["kind"], "name": old["name"] + " II"
                        if not old["name"].endswith(" II") else old["name"],
                        "damage": 0, "dead": False}
        ch._companion_inst = None
        return
    inst.heal(inst.hit_dice() * 1)
    inst.effects = [e for e in inst.effects if e.duration is None]
    sync_companion(ch)


def companion_line(ch) -> Optional[str]:
    inst = companion_creature(ch)
    if inst is None:
        return None
    if inst.dead:
        return f"Animal companion: {inst.name} (dead; a new one comes after a night's rest)"
    return (f"Animal companion: {inst.name} the {MONSTERS[inst.kind]['name'].lower()} "
            f"({inst.hit_dice()} HD) - {inst.statline().split(': ', 1)[1]}")


def mount_line(ch) -> Optional[str]:
    m = mount_creature(ch)
    if m is None:
        return None
    if m.dead:
        return f"Special mount: {m.name} (fallen; returns after a night's rest)"
    return (f"Special mount: {m.name}, celestial heavy warhorse ({m.hit_dice()} HD) - "
            f"{m.statline().split(': ', 1)[1]}")


def familiar_line(ch) -> Optional[str]:
    fam = getattr(ch, "familiar", None)
    if not fam:
        return None
    return (f"Familiar: {fam['name']} the {fam['kind']} ({FAMILIARS[fam['kind']][2]}; "
            f"Alertness while it's near)")


__all__ = ["Companion", "companion_creature", "choose_companion", "choose_familiar",
           "familiar_bonus", "rest_companion", "companion_line", "familiar_line",
           "effective_level", "sync_companion", "mount_creature", "all_companions",
           "mount_line"]
