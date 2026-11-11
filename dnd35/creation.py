"""Character creation, starting equipment, and pregenerated heroes."""
from __future__ import annotations

from typing import List, Optional

from . import dice, rules
from .character import Character
from .data.classes import (AGE_CATEGORY, ALIGNMENTS, CLASS_ORDER, CLASSES, DEITIES,
                           STARTING_AGE, alignment_allowed)
from .data.items import GP
from .data.races import RACE_ORDER, RACES
from .levelup import RECOMMENDED, gain_level, prepare_spells
from .sheet import render
from .ui import c

ELITE_ARRAY = [15, 14, 13, 12, 10, 8]
# DMG "character wealth by level" (minus the 1st-level kit), to spend in town
LEVEL_WEALTH_GP = {2: 900, 3: 2700, 4: 5400, 5: 9000, 6: 13000, 7: 19000, 8: 27000,
                   9: 36000, 10: 49000, 11: 66000, 12: 88000, 13: 110000, 14: 150000,
                   15: 200000, 16: 260000, 17: 340000, 18: 440000, 19: 580000, 20: 760000}
POINT_BUY_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6, 15: 8, 16: 10, 17: 13,
                  18: 16}

COMMON_GEAR = [("backpack", 1), ("rations", 2), ("flint and steel", 1), ("torch", 2)]

KITS = {
    "barbarian": {"equip": ["studded leather", "greataxe"],
                  "carry": [("shortbow", 1), ("arrows", 20), ("dagger", 1), ("javelin", 2)],
                  "gold": "2d4"},
    "bard": {"equip": ["studded leather", "rapier"],
             "carry": [("shortbow", 1), ("arrows", 20), ("dagger", 1)],
             "gold": "3d4"},
    "druid": {"equip": ["hide", "heavy wooden shield", "scimitar"],
              "carry": [("sling", 1), ("sling bullets", 10), ("quarterstaff", 1),
                        ("healer's kit", 1)],
              "gold": "1d4"},
    "monk": {"equip": [],
             "carry": [("quarterstaff", 1), ("sling", 1), ("sling bullets", 10)],
             "gold": "1d4"},
    "paladin": {"equip": ["scale mail", "heavy steel shield", "longsword"],
                "carry": [("javelin", 2), ("holy symbol", 1)],
                "gold": "2d4"},
    "cleric": {"equip": ["scale mail", "heavy wooden shield", "heavy mace"],
               "carry": [("light crossbow", 1), ("bolts", 10), ("holy symbol", 1),
                         ("healer's kit", 1)],
               "gold": "1d4"},
    "fighter": {"equip": ["scale mail", "heavy wooden shield", "longsword"],
                "carry": [("shortbow", 1), ("arrows", 20), ("dagger", 1), ("javelin", 2)],
                "gold": "2d4"},
    "ranger": {"equip": ["studded leather", "longsword"],
               "carry": [("longbow", 1), ("arrows", 40), ("short sword", 1)],
               "gold": "2d4"},
    "rogue": {"equip": ["leather", "rapier"],
              "carry": [("shortbow", 1), ("arrows", 20), ("dagger", 2), ("thieves' tools", 1)],
              "gold": "2d4"},
    "sorcerer": {"equip": ["quarterstaff"],
                 "carry": [("light crossbow", 1), ("bolts", 20), ("dagger", 1),
                           ("spell component pouch", 1)],
                 "gold": "3d4"},
    "wizard": {"equip": ["quarterstaff"],
               "carry": [("light crossbow", 1), ("bolts", 20), ("dagger", 1),
                         ("spell component pouch", 1), ("spellbook", 1)],
               "gold": "3d4"},
}


def apply_kit(ch: Character, cls: str) -> None:
    kit = KITS[cls]
    # cleric of War gets their deity's weapon
    equip = list(kit["equip"])
    if cls == "cleric" and "War" in ch.domains and ch.deity in DEITIES:
        equip[-1] = DEITIES[ch.deity]["weapon"]
    for iid in equip:
        e = ch.add_item(iid)
        ch.equip(e)
    gear = COMMON_GEAR
    if ch.base_size == "small":
        gear = [(i, min(q, 2) if i == "rations" else (1 if i == "torch" else q))
                for i, q in COMMON_GEAR]
    for iid, qty in kit["carry"] + gear:
        if (ch.base_size == "small" and iid == "rope") or qty <= 0:
            continue
        ch.add_item(iid, qty)
    ch.cp += dice.roll(kit["gold"]).total * GP


def roll_starting_gold(cls: str) -> int:
    gold = CLASSES[cls]["gold"]
    mult = 10 if "x10" in gold else 1
    return dice.roll(gold.replace("x10", "")).total * mult * GP


def random_physical(ch: Character, cls: str) -> None:
    base, simple, moderate, complex_ = STARTING_AGE[ch.race]
    cat = AGE_CATEGORY.get(cls, 0)
    ch.age = base + dice.roll([simple, moderate, complex_][cat]).total
    hbase, hmod = ch.race_data["height"]
    wbase, wmod = ch.race_data["weight"]
    hroll = dice.roll(hmod).total
    if ch.gender.lower().startswith("f"):
        hbase -= 2 if ch.base_size == "medium" else 2
        wbase -= 30 if ch.base_size == "medium" else 5
    inches = hbase + hroll
    ch.height = f"{inches // 12}' {inches % 12}\""
    ch.weight = f"{wbase + hroll * dice.roll(wmod).total} lb."


# ---------------------------------------------------------------- abilities
def _assign(ui, values: List[int], ch: Character, cls: Optional[str]) -> None:
    remaining = sorted(values, reverse=True)
    rec = RECOMMENDED.get(cls, {}).get("abilities", rules.ABILITIES)
    ui.out(f"Assign these scores: {', '.join(map(str, remaining))}")
    if cls and ui.confirm(f"Auto-assign them in the recommended order for a "
                          f"{CLASSES[cls]['name']} ({', '.join(a.upper() for a in rec)})?",
                          True):
        for ab, v in zip(rec, remaining):
            ch.base_abilities[ab] = v
        return
    for ab in rules.ABILITIES:
        opts = [str(v) for v in remaining]
        racial = ch.race_data["ability_adj"].get(ab, 0)
        note = f" (racial {racial:+d})" if racial else ""
        i = ui.choose(f"{rules.ABILITY_NAMES[ab]}{note} gets which score?", opts)
        ch.base_abilities[ab] = remaining.pop(i)


def roll_abilities(ui, ch: Character, cls: Optional[str]) -> None:
    while True:
        method = ui.choose("How do you want to generate ability scores?", [
            "Roll 4d6, drop the lowest, six times (classic)",
            "Elite array: 15, 14, 13, 12, 10, 8",
            "Point buy (25 points, all scores start at 8)",
        ], default=0)
        if method == 0:
            while True:
                rolls = []
                for _ in range(6):
                    total, ds = dice.roll_4d6_drop_lowest()
                    rolls.append(total)
                    ui.roll(f"4d6 {ds} -> drop {ds[-1]} = {total}")
                mods = sum(rules.ability_mod(r) for r in rolls)
                if mods <= 0 or max(rolls) <= 13:
                    ui.warn("Those scores are too weak to play (total modifier <= 0 or no "
                            "score above 13); rerolling as per the PHB.")
                    continue
                if ui.confirm(f"Keep these scores ({', '.join(map(str, sorted(rolls, reverse=True)))})"
                              f"?", True):
                    break
            _assign(ui, rolls, ch, cls)
            return
        if method == 1:
            _assign(ui, list(ELITE_ARRAY), ch, cls)
            return
        if point_buy(ui, ch):
            return


def point_buy(ui, ch: Character) -> bool:
    scores = {a: 8 for a in rules.ABILITIES}
    budget = 25
    ui.out("Costs: 9=1 10=2 11=3 12=4 13=5 14=6 15=8 16=10 17=13 18=16")
    while True:
        spent = sum(POINT_BUY_COST[v] for v in scores.values())
        ui.out("  " + "  ".join(f"{a.upper()} {scores[a]}" for a in rules.ABILITIES)
               + f"   points left: {budget - spent}")
        raw = ui.ask("Set a score like 'str 16', 'done' when finished, 'back' to cancel")
        raw = raw.strip().lower()
        if raw == "back":
            return False
        if raw == "done":
            if spent > budget:
                ui.bad("Over budget!")
                continue
            for a in rules.ABILITIES:
                ch.base_abilities[a] = scores[a]
            return True
        try:
            a, v = raw.split()
            v = int(v)
            if a not in scores or v not in POINT_BUY_COST:
                raise ValueError
            old = scores[a]
            scores[a] = v
            if sum(POINT_BUY_COST[x] for x in scores.values()) > budget:
                scores[a] = old
                ui.bad("That would exceed 25 points.")
        except ValueError:
            ui.bad("Format: 'dex 14' with a score from 8 to 18.")


# ---------------------------------------------------------------- creation
def create_character(ui, player: str = "", start_level: int = 1) -> Character:
    ui.header("CHARACTER CREATION")
    ui.sub("Race")
    races = [k for k in RACE_ORDER]
    i = ui.choose("Choose a race", [
        f"{RACES[r]['name']:<9} " + "; ".join(RACES[r]['traits'][:2]) +
        (" | " + ", ".join(f"{k.upper()} {v:+d}" for k, v in RACES[r]['ability_adj'].items())
         if RACES[r]['ability_adj'] else "")
        for r in races])
    race = races[i]
    ui.sub("Class")
    j = ui.choose("Choose a class", [
        f"{CLASSES[k]['name']:<9} d{CLASSES[k]['hd']}, {CLASSES[k]['skill_points']} skill "
        f"pts: {CLASSES[k]['description']}" for k in CLASS_ORDER])
    cls = CLASS_ORDER[j]
    name = ""
    while not name:
        name = ui.ask("Character name").strip()
    ch = Character(name, race, player)
    ch.gender = ui.ask("Gender (optional)", "").strip()

    ui.sub("Ability scores")
    roll_abilities(ui, ch, cls)
    ui.out("Final scores: " + "  ".join(
        f"{a.upper()} {ch.ability(a)} ({rules.ability_mod(ch.ability(a)):+d})"
        for a in rules.ABILITIES))

    ui.sub("Alignment")
    allowed = [a for a in ALIGNMENTS if alignment_allowed(cls, a)]
    if len(allowed) < len(ALIGNMENTS):
        ui.out(f"(A {CLASSES[cls]['name'].lower()} must be "
               f"{CLASSES[cls].get('alignment', 'any')}.)")
    k = ui.choose("Alignment", allowed, default=allowed.index("Neutral Good")
                  if "Neutral Good" in allowed else 0)
    ch.alignment = allowed[k]

    auto = ui.choose("How do you want to make the level-by-level choices (skills, feats, "
                     "spells)?", ["I'll choose everything myself",
                                  "Use the recommended build (fast)"], default=0) == 1
    for _ in range(start_level):
        gain_level(ch, cls, ui, auto=auto, hp_method="average" if auto else "ask")
    ch.xp = rules.xp_for_level(ch.level)
    random_physical(ch, cls)

    ui.sub("Starting equipment")
    e = ui.choose("Equipment", ["Take the standard class kit (quick)",
                                f"Roll starting gold ({CLASSES[cls]['gold']} gp) and shop"],
                  default=0)
    if e == 0:
        apply_kit(ch, cls)
    else:
        ch.cp = roll_starting_gold(cls)
        ch.add_item("backpack")
        if cls == "wizard":
            ch.add_item("spellbook")
        if cls == "paladin" or cls == "cleric":
            ch.add_item("holy symbol")
        ui.out(f"{ch.name} has {rules.money_str(ch.cp)} to spend.")
        from .shop import shop_menu
        shop_menu(ui, [ch], "Outfitter's Market", ["general", "weapons", "armor", "temple"])
    if start_level > 1:
        ch.cp += LEVEL_WEALTH_GP.get(start_level, 0) * GP
        ui.out(f"Higher-level start: +{rules.money_str(ch.cp)} total wealth to spend in town.")
    prepare_spells(ch, ui, auto=auto, keep_ok=False)
    ui.out(render(ch))
    ui.pause()
    return ch


# ---------------------------------------------------------------- pregens
PREGENS = {
    "thorgar": {"name": "Thorgar Ironbrow", "race": "dwarf", "cls": "fighter",
                "alignment": "Lawful Good", "gender": "Male",
                "abilities": {"str": 15, "dex": 13, "con": 14, "int": 10, "wis": 12, "cha": 8},
                "blurb": "Dwarf fighter: scale mail, shield, longsword. Tough as an anvil."},
    "lyra": {"name": "Lyra Vaelith", "race": "elf", "cls": "wizard",
             "alignment": "Chaotic Good", "gender": "Female",
             "abilities": {"str": 8, "dex": 14, "con": 13, "int": 15, "wis": 12, "cha": 10},
             "blurb": "Elf wizard: magic missile, sleep, mage armor. Fragile but powerful."},
    "pip": {"name": "Pip Underbough", "race": "halfling", "cls": "rogue",
            "alignment": "Chaotic Good", "gender": "Male",
            "abilities": {"str": 10, "dex": 15, "con": 13, "int": 14, "wis": 12, "cha": 8},
            "blurb": "Halfling rogue: sneak attack, traps, locks, quick rapier."},
    "aldric": {"name": "Brother Aldric", "race": "human", "cls": "cleric",
               "alignment": "Neutral Good", "gender": "Male",
               "abilities": {"str": 13, "dex": 10, "con": 14, "int": 8, "wis": 15, "cha": 12},
               "blurb": "Human cleric of Pelor: heals, turns undead, heavy mace and shield."},
    "kesh": {"name": "Kesh Bloodtusk", "race": "half-orc", "cls": "barbarian",
             "alignment": "Chaotic Neutral", "gender": "Female",
             "abilities": {"str": 15, "dex": 13, "con": 14, "int": 10, "wis": 12, "cha": 8},
             "blurb": "Half-orc barbarian: greataxe and rage. Hits like a falling tree."},
    "faelin": {"name": "Faelin Thornwood", "race": "half-elf", "cls": "ranger",
               "alignment": "Neutral Good", "gender": "Male",
               "abilities": {"str": 13, "dex": 15, "con": 12, "int": 10, "wis": 14, "cha": 8},
               "blurb": "Half-elf ranger: longbow archer, tracker, hates goblinoids."},
    "sable": {"name": "Sable Ashveil", "race": "human", "cls": "sorcerer",
              "alignment": "Neutral Good", "gender": "Female",
              "abilities": {"str": 8, "dex": 14, "con": 13, "int": 10, "wis": 12, "cha": 15},
              "blurb": "Human sorcerer: fewer spells known, more spells per day."},
    "wren": {"name": "Wren Tallowsong", "race": "half-elf", "cls": "bard",
             "alignment": "Chaotic Good", "gender": "Female",
             "abilities": {"str": 10, "dex": 14, "con": 12, "int": 13, "wis": 8, "cha": 15},
             "blurb": "Half-elf bard: songs of courage, healing magic, a silver tongue."},
    "moss": {"name": "Old Moss", "race": "gnome", "cls": "druid",
             "alignment": "True Neutral", "gender": "Male",
             "abilities": {"str": 10, "dex": 13, "con": 14, "int": 12, "wis": 15, "cha": 8},
             "blurb": "Gnome druid: entangling plants, fire and lightning; becomes a bear at "
                      "5th level."},
    "jin": {"name": "Brother Jin", "race": "human", "cls": "monk",
            "alignment": "Lawful Neutral", "gender": "Male",
            "abilities": {"str": 13, "dex": 14, "con": 12, "int": 10, "wis": 15, "cha": 8},
            "blurb": "Human monk: fast, unarmored, flurries of blows and stunning fists."},
    "elowen": {"name": "Dame Elowen", "race": "human", "cls": "paladin",
               "alignment": "Lawful Good", "gender": "Female",
               "abilities": {"str": 15, "dex": 10, "con": 13, "int": 8, "wis": 12, "cha": 14},
               "blurb": "Human paladin: heavy armor, smites evil, heals with a touch."},
}


def build_pregen(key: str, player: str = "", level: int = 1) -> Character:
    p = PREGENS[key]
    ch = Character(p["name"], p["race"], player)
    ch.alignment = p["alignment"]
    ch.gender = p["gender"]
    ch.base_abilities = dict(p["abilities"])
    for _ in range(level):
        gain_level(ch, p["cls"], None, auto=True)
    ch.xp = rules.xp_for_level(ch.level)
    random_physical(ch, p["cls"])
    apply_kit(ch, p["cls"])
    ch.cp += LEVEL_WEALTH_GP.get(level, 0) * GP
    if p["cls"] == "ranger":
        bow = ch.find_item("longbow")
        if bow:
            ch.equip(bow)
    prepare_spells(ch, None, auto=True)
    return ch


def choose_pregen(ui, player: str, taken: List[str], level: int = 1) -> Character:
    keys = [k for k in PREGENS if k not in taken]
    i = ui.choose("Choose a hero", [f"{c(PREGENS[k]['name'], 'bold')}: {PREGENS[k]['blurb']}"
                                    for k in keys])
    key = keys[i]
    taken.append(key)
    ch = build_pregen(key, player, level=level)
    ui.out(render(ch))
    if ui.confirm(f"Rename {ch.name}?", False):
        nm = ui.ask("New name").strip()
        if nm:
            ch.name = nm
    return ch
