"""Item creation (downtime in town): Brew Potion, Scribe Scroll, Craft Wand, Craft
Wondrous Item, Craft Magic Arms and Armor.

SRD rules, lightly simplified: the crafter pays half the market price in gold and
1/25 of it in XP (never enough to lose a level), and it takes one day per 1,000 gp of
market price. The crafter must be able to cast the spell involved (or meet the
item's caster level for wondrous items and magic arms).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from . import rules
from .data.classes import CLASSES
from .data.items import ARMOR, CONSUMABLES, GP, MAGIC, WEAPONS, item_data, item_name, make_item
from .data.spells import SPELLS

# caster level needed for each wondrous item (SRD values, rounded)
WONDROUS_CL = {"ring of protection": 5, "cloak of resistance": 5, "amulet of natural armor": 5,
               "amulet of mighty fists": 5, "gauntlets of ogre power": 6,
               "belt of giant strength": 8, "gloves of dexterity": 8,
               "headband of intellect": 8, "periapt of wisdom": 8, "cloak of charisma": 8,
               "amulet of health": 8, "bracers of armor": 7}


def _can_cast(ch, spell: str) -> bool:
    lv = SPELLS[spell]["levels"]
    for cls in ch.caster_classes():
        if cls in lv and lv[cls] in ch.spells_per_day(cls):
            if CLASSES[cls].get("prepared"):
                if cls == "wizard" and spell not in ch.spellbook:
                    continue
                return True
            if spell in ch.spells_known.get(lv[cls], []):
                return True
    return False


def best_cl(ch) -> int:
    return max([ch.caster_level(c) for c in ch.caster_classes()] or [0])


def craftable(ch) -> List[Tuple[str, str]]:
    """(item id, why) a character can make."""
    feats = ch.feat_list()
    out = []
    cl = best_cl(ch)
    for key, d in CONSUMABLES.items():
        sp = d.get("spell")
        if not sp:
            continue
        if d["use"] == "scroll" and "Scribe Scroll" in feats and _can_cast(ch, sp):
            out.append((key, "Scribe Scroll"))
        if d["use"] == "spell" and "Brew Potion" in feats and _can_cast(ch, sp) \
                and min(SPELLS[sp]["levels"].values()) <= 3:
            out.append((key, "Brew Potion"))
    for key, d in MAGIC.items():
        if d["kind"] == "wand" and "Craft Wand" in feats and _can_cast(ch, d["spell"]) \
                and cl >= d["cl"]:
            out.append((key, "Craft Wand"))
        if d["kind"] in ("ring", "cloak", "amulet", "bracers", "gloves", "head", "belt") \
                and "Craft Wondrous Item" in feats:
            base = key.rsplit(" +", 1)[0]
            need = WONDROUS_CL.get(base, 8)
            if base == "bracers of armor":
                need = max(need, 2 * int(key.rsplit("+", 1)[1]))
            if cl >= need:
                out.append((key, "Craft Wondrous Item"))
    if "Craft Magic Arms and Armor" in feats:
        for n in range(1, 6):
            if cl >= 3 * n:
                out.append((f"+{n}", "Craft Magic Arms and Armor"))
    return out


def price_gp(item_id: str) -> int:
    return item_data(make_item(item_id))["cost"] // GP


def craft(ui, ch, item_id: str, gs=None) -> bool:
    market = price_gp(item_id)
    gold = market // 2
    xp = max(1, market // 25)
    days = max(1, market // 1000)
    floor = rules.xp_for_level(ch.level)
    if ch.cp < gold * GP:
        ui.bad(f"{ch.name} needs {gold:,} gp in materials (has {rules.money_str(ch.cp)}).")
        return False
    if ch.xp - xp < floor:
        ui.bad(f"Crafting this would cost {xp:,} XP, more than {ch.name} can spare without "
               f"losing a level.")
        return False
    if not ui.confirm(f"Make {item_name(make_item(item_id))}: {gold:,} gp, {xp:,} XP and "
                      f"{days} day(s) of work?", True):
        return False
    ch.cp -= gold * GP
    ch.xp -= xp
    if gs is not None:
        gs.pass_time(days * 24 * 60, ui)
    entry = ch.add_item(make_item(item_id))
    ui.good(f"After {days} day(s) of careful work, {ch.name} finishes "
            f"{item_name(entry)}.")
    return True


def enchant_menu(ui, ch, n_max: int, gs=None) -> None:
    """Craft Magic Arms and Armor: upgrade a weapon, armor or shield the crafter owns."""
    gear = [e for e in ch.inventory if item_data(e)["kind"] in ("weapon", "armor", "shield")
            and e["id"] in (*WEAPONS, *ARMOR) and e["id"] != "unarmed strike"]
    if not gear:
        ui.out("No weapon, armor or shield to enchant.")
        return
    i = ui.choose("Enchant which item?", [item_name(e) for e in gear], allow_cancel=True)
    if i is None:
        return
    e = gear[i]
    cur = e.get("enhancement", 0)
    opts = [n for n in range(cur + 1, n_max + 1)]
    if not opts:
        ui.out("That's already as strong as you can make it.")
        return
    j = ui.choose("Raise it to?", [f"+{n}" for n in opts], allow_cancel=True)
    if j is None:
        return
    n = opts[j]
    new = make_item(f"+{n} {e['id']}")
    old_price = item_data(e)["cost"] // GP
    market = item_data(new)["cost"] // GP - old_price
    gold, xp, days = market // 2, max(1, market // 25), max(1, market // 1000)
    if ch.cp < gold * GP or ch.xp - xp < rules.xp_for_level(ch.level):
        ui.bad(f"Not enough gold ({gold:,} gp) or spare XP ({xp:,}) for that.")
        return
    if not ui.confirm(f"Enchant to +{n}: {gold:,} gp, {xp:,} XP, {days} day(s)?", True):
        return
    ch.cp -= gold * GP
    ch.xp -= xp
    if gs is not None:
        gs.pass_time(days * 24 * 60, ui)
    e["masterwork"] = True
    e["enhancement"] = n
    ui.good(f"{ch.name}'s work is done: {item_name(e)}.")


def craft_menu(ui, party, gs=None) -> None:
    crafters = [p for p in party if not p.dead and craftable(p)]
    if not crafters:
        ui.out("No one in the party has an item creation feat they can use.")
        return
    ch = crafters[0] if len(crafters) == 1 else crafters[ui.choose(
        "Who works?", [p.name for p in crafters])]
    with ui.acting(ch.player):
        items = craftable(ch)
        kinds = sorted({why for _, why in items})
        k = ui.choose("Make what?", kinds, allow_cancel=True)
        if k is None:
            return
        kind = kinds[k]
        if kind == "Craft Magic Arms and Armor":
            enchant_menu(ui, ch, max(n for n in range(1, 6) if best_cl(ch) >= 3 * n), gs)
            return
        pool = sorted({iid for iid, why in items if why == kind},
                      key=lambda iid: (price_gp(iid), iid))
        j = ui.choose("Which item?", [f"{item_name(make_item(iid))} (market "
                                      f"{price_gp(iid):,} gp)" for iid in pool],
                      allow_cancel=True)
        if j is None:
            return
        craft(ui, ch, pool[j], gs)


def can_anyone_craft(party) -> Optional[bool]:
    return any(not p.dead and craftable(p) for p in party)
