"""Gaining levels: hit points, skills, feats, class features, spells.

Every step works interactively (ui given, auto=False) or automatically using a
recommended build (auto=True), which is how pregenerated characters and the
"let the GM build it" option are made.
"""
from __future__ import annotations

from typing import List, Optional

from . import dice, rules
from .character import Character
from .companions import choose_companion, choose_familiar
from .data.classes import (CLASSES, CLASS_ORDER, DEITIES, DOMAINS, FAVORED_ENEMIES,
                           alignment_allowed, domain_allowed)
from .data.feats import FEATS, SPELL_SCHOOLS
from .data.items import WEAPONS
from .data.skills import SKILL_ORDER
from .data.spells import SPELLS, spells_for
from .ui import c

RECOMMENDED = {
    "barbarian": {
        "abilities": ["str", "con", "dex", "wis", "cha", "int"],
        "skills": ["Climb", "Jump", "Listen", "Intimidate", "Survival", "Swim"],
        "feats": ["Power Attack", "Cleave", "Weapon Focus (greataxe)", "Toughness",
                  "Improved Initiative", "Great Cleave", "Iron Will",
                  "Improved Critical (greataxe)"],
        "weapon": "greataxe",
    },
    "bard": {
        "abilities": ["cha", "dex", "con", "int", "wis", "str"],
        "skills": ["Perform", "Diplomacy", "Concentration", "Tumble", "Listen", "Bluff",
                   "Sense Motive", "Use Magic Device", "Spellcraft", "Gather Information",
                   "Knowledge (local)", "Knowledge (history)"],
        "feats": ["Weapon Finesse", "Improved Initiative", "Combat Casting", "Dodge",
                  "Extra Music", "Toughness", "Lightning Reflexes"],
        "weapon": "rapier",
        "spells": {0: ["Daze", "Flare", "Detect Magic", "Light", "Resistance", "Mage Hand",
                       "Prestidigitation", "Know Direction"],
                   1: ["Cure Light Wounds", "Sleep", "Grease", "Hideous Laughter",
                       "Remove Fear"],
                   2: ["Heroism", "Hold Person", "Cure Moderate Wounds", "Sound Burst",
                       "Cat's Grace", "Blur"],
                   3: ["Haste", "Good Hope", "Slow", "Cure Serious Wounds", "Displacement"],
                   4: ["Cure Critical Wounds", "Hold Monster", "Shout",
                       "Greater Invisibility"]},
    },
    "cleric": {
        "abilities": ["wis", "con", "str", "cha", "dex", "int"],
        "skills": ["Concentration", "Heal", "Knowledge (religion)", "Spellcraft", "Diplomacy"],
        "feats": ["Combat Casting", "Improved Initiative", "Extra Turning", "Toughness",
                  "Iron Will", "Craft Wondrous Item"],
        "deity": "Pelor", "domains": ["Healing", "Strength"], "weapon": "heavy mace",
    },
    "druid": {
        "abilities": ["wis", "con", "dex", "str", "int", "cha"],
        "skills": ["Concentration", "Knowledge (nature)", "Survival", "Spellcraft", "Heal",
                   "Listen", "Spot", "Handle Animal"],
        "feats": ["Improved Initiative", "Natural Spell", "Combat Casting", "Toughness",
                  "Iron Will"],
        "weapon": "scimitar",
    },
    "fighter": {
        "abilities": ["str", "con", "dex", "wis", "int", "cha"],
        "skills": ["Climb", "Jump", "Intimidate", "Swim", "Ride"],
        "feats": ["Power Attack", "Weapon Focus (longsword)", "Cleave", "Dodge",
                  "Weapon Specialization (longsword)", "Improved Initiative", "Toughness",
                  "Mobility", "Great Cleave", "Greater Weapon Focus (longsword)",
                  "Improved Critical (longsword)", "Spring Attack", "Combat Reflexes",
                  "Iron Will"],
        "weapon": "longsword",
    },
    "monk": {
        "abilities": ["wis", "dex", "str", "con", "int", "cha"],
        "skills": ["Tumble", "Jump", "Balance", "Climb", "Listen", "Spot", "Move Silently",
                   "Hide", "Concentration", "Escape Artist", "Sense Motive"],
        "feats": ["Dodge", "Improved Initiative", "Weapon Focus (unarmed strike)", "Mobility",
                  "Spring Attack", "Toughness", "Lightning Reflexes"],
        "bonus": {1: "Stunning Fist", 2: "Deflect Arrows", 6: "Improved Trip"},
        "weapon": "quarterstaff",
    },
    "paladin": {
        "abilities": ["str", "cha", "con", "wis", "dex", "int"],
        "skills": ["Diplomacy", "Sense Motive", "Heal", "Concentration", "Ride",
                   "Knowledge (religion)"],
        "feats": ["Power Attack", "Weapon Focus (longsword)", "Cleave", "Improved Initiative",
                  "Extra Smiting", "Toughness", "Iron Will", "Great Cleave"],
        "weapon": "longsword",
    },
    "ranger": {
        "abilities": ["dex", "str", "wis", "con", "int", "cha"],
        "skills": ["Hide", "Move Silently", "Listen", "Spot", "Survival", "Search", "Heal",
                   "Climb", "Knowledge (nature)", "Use Rope"],
        "feats": ["Point Blank Shot", "Precise Shot", "Weapon Focus (longbow)",
                  "Improved Initiative", "Toughness", "Improved Critical (longbow)",
                  "Iron Will"],
        "favored_enemy": "goblinoid", "style": "archery", "weapon": "longbow",
    },
    "rogue": {
        "abilities": ["dex", "int", "con", "wis", "cha", "str"],
        "skills": ["Disable Device", "Open Lock", "Search", "Spot", "Listen", "Hide",
                   "Move Silently", "Tumble", "Use Magic Device", "Bluff", "Sense Motive",
                   "Diplomacy", "Climb", "Balance", "Escape Artist", "Jump"],
        "feats": ["Weapon Finesse", "Dodge", "Improved Initiative", "Mobility",
                  "Weapon Focus (rapier)", "Combat Reflexes", "Improved Critical (rapier)",
                  "Lightning Reflexes"],
        "weapon": "rapier",
    },
    "sorcerer": {
        "abilities": ["cha", "dex", "con", "int", "wis", "str"],
        "skills": ["Concentration", "Spellcraft", "Knowledge (arcana)", "Bluff"],
        "feats": ["Improved Initiative", "Toughness", "Combat Casting",
                  "Spell Focus (evocation)", "Iron Will", "Spell Penetration"],
        "spells": {0: ["Ray of Frost", "Acid Splash", "Daze", "Disrupt Undead", "Detect Magic",
                       "Light", "Resistance", "Mage Hand", "Flare"],
                   1: ["Magic Missile", "Sleep", "Mage Armor", "Shield", "Burning Hands",
                       "Color Spray", "Grease"],
                   2: ["Scorching Ray", "Blur", "Melf's Acid Arrow", "Cat's Grace",
                       "Flaming Sphere"],
                   3: ["Fireball", "Haste", "Lightning Bolt", "Slow"],
                   4: ["Stoneskin", "Greater Invisibility", "Ice Storm"],
                   5: ["Cone of Cold", "Hold Monster"]},
    },
    "wizard": {
        "abilities": ["int", "dex", "con", "wis", "cha", "str"],
        "skills": ["Concentration", "Spellcraft", "Knowledge (arcana)", "Knowledge (religion)",
                   "Knowledge (dungeoneering)", "Decipher Script", "Knowledge (history)"],
        "feats": ["Improved Initiative", "Toughness", "Spell Focus (evocation)",
                  "Combat Casting", "Iron Will", "Spell Penetration"],
        "spells": {1: ["Magic Missile", "Sleep", "Mage Armor", "Shield", "Color Spray",
                       "Burning Hands", "Grease", "Ray of Enfeeblement", "True Strike",
                       "Enlarge Person", "Protection from Evil", "Magic Weapon"],
                   2: ["Scorching Ray", "Melf's Acid Arrow", "Blur", "Bull's Strength",
                       "Cat's Grace", "Bear's Endurance", "Resist Energy", "Flaming Sphere",
                       "Hideous Laughter", "Fox's Cunning"],
                   3: ["Fireball", "Haste", "Lightning Bolt", "Slow", "Hold Person",
                       "Displacement", "Heroism"],
                   4: ["Stoneskin", "Greater Invisibility", "Ice Storm", "Shout", "Fear",
                       "Bestow Curse"],
                   5: ["Cone of Cold", "Hold Monster", "Waves of Fatigue"]},
    },
}

PREP_PRIORITY = {
    "cleric": {0: ["Guidance", "Resistance", "Virtue", "Cure Minor Wounds", "Light"],
               1: ["Bless", "Shield of Faith", "Divine Favor", "Doom", "Cure Light Wounds"],
               2: ["Aid", "Spiritual Weapon", "Bull's Strength", "Hold Person",
                   "Cure Moderate Wounds"],
               3: ["Prayer", "Searing Light", "Magic Vestment", "Cure Serious Wounds"],
               4: ["Divine Power", "Freedom of Movement", "Cure Critical Wounds",
                   "Death Ward"],
               5: ["Flame Strike", "Righteous Might", "Mass Cure Light Wounds",
                   "Slay Living"]},
    "druid": {0: ["Flare", "Guidance", "Resistance", "Virtue", "Cure Minor Wounds"],
              1: ["Produce Flame", "Entangle", "Cure Light Wounds", "Magic Fang"],
              2: ["Barkskin", "Flaming Sphere", "Bull's Strength", "Owl's Wisdom"],
              3: ["Call Lightning", "Cure Moderate Wounds", "Greater Magic Fang", "Poison"],
              4: ["Flame Strike", "Ice Storm", "Cure Serious Wounds"],
              5: ["Call Lightning Storm", "Stoneskin", "Cure Critical Wounds"]},
    "wizard": {0: ["Ray of Frost", "Acid Splash", "Daze", "Disrupt Undead", "Resistance"],
               1: ["Magic Missile", "Sleep", "Mage Armor", "Shield", "Color Spray"],
               2: ["Scorching Ray", "Melf's Acid Arrow", "Blur", "Flaming Sphere"],
               3: ["Fireball", "Haste", "Slow"],
               4: ["Stoneskin", "Greater Invisibility", "Ice Storm", "Shout"],
               5: ["Cone of Cold", "Hold Monster"]},
    "paladin": {1: ["Divine Favor", "Bless", "Cure Light Wounds", "Protection from Evil"],
                2: ["Bull's Strength", "Eagle's Splendor", "Owl's Wisdom"]},
    "ranger": {1: ["Entangle", "Magic Fang", "Longstrider"],
               2: ["Barkskin", "Cure Light Wounds", "Cat's Grace"]},
}

MONK_BONUS_FEATS = {1: ["Stunning Fist", "Improved Grapple"],
                    2: ["Deflect Arrows", "Combat Reflexes"],
                    6: ["Improved Trip", "Improved Disarm"]}
CASTER_BONUS_FEATS = ["Extend Spell", "Empower Spell", "Brew Potion", "Craft Wondrous Item",
                      "Craft Magic Arms and Armor", "Maximize Spell", "Quicken Spell",
                      "Spell Penetration"]

ABILITY_INCREASE_LEVELS = (4, 8, 12, 16, 20)
FEAT_LEVELS = (1, 3, 6, 9, 12, 15, 18)


# ---------------------------------------------------------------- feats
def feat_param_options(ch: Character, feat: str) -> List[str]:
    p = FEATS[feat].get("param")
    if p == "weapon":
        opts = []
        for wid, w in WEAPONS.items():
            if wid in ("greatclub (large)",):
                continue
            info = {"wid": wid, "category": w["category"]}
            if ch.is_proficient(info):
                opts.append(wid)
        return opts
    if p == "skill":
        return SKILL_ORDER
    if p == "school":
        return SPELL_SCHOOLS
    if p == "exotic_weapon":
        return [k for k, w in WEAPONS.items() if w["category"] == "exotic"]
    if p == "martial_weapon":
        return [k for k, w in WEAPONS.items() if w["category"] == "martial"
                and k != "greatclub (large)"]
    return []


def feat_eligible(ch: Character, feat: str, param: Optional[str] = None,
                  fighter_bonus: bool = False) -> bool:
    info = FEATS.get(feat)
    if not info or info.get("hidden"):
        return False
    if fighter_bonus and not info.get("fighter"):
        return False
    full = f"{feat} ({param})" if param else feat
    have = ch.feat_list()
    if full in have and feat not in ("Toughness", "Extra Turning", "Extra Smiting",
                                      "Extra Music"):
        return False
    pre = info.get("prereq", {})
    for ab in rules.ABILITIES:
        if ab in pre and (ch.ability(ab) or 0) < pre[ab]:
            return False
    if ch.bab() < pre.get("bab", 0):
        return False
    for f in pre.get("feats", []):
        if f == "Weapon Focus" and param:
            if f"Weapon Focus ({param})" not in have:
                return False
        elif f not in have and not any(h.startswith(f + " (") for h in have):
            return False
    if pre.get("fighter_level") and ch.class_level("fighter") < pre["fighter_level"]:
        return False
    if pre.get("caster"):
        if not any(ch.caster_level(c) >= pre["caster"] for c in ch.caster_classes()):
            return False
    if pre.get("turn_undead") and ch.turn_per_day() < 1:
        return False
    if pre.get("wild_shape") and ch.class_level("druid") < 5:
        return False
    if pre.get("smite") and not ch.class_level("paladin"):
        return False
    if pre.get("music") and not ch.class_level("bard"):
        return False
    if info.get("param") and param is None:
        return bool(feat_param_options(ch, feat))
    if pre.get("proficient") and param:
        if not ch.is_proficient({"wid": param, "category": WEAPONS.get(param, {}).get("category")}):
            return False
    return True


def choose_feat(ch: Character, ui, auto: bool, fighter_bonus: bool = False,
                label: str = "feat") -> Optional[str]:
    rec = RECOMMENDED.get(ch.class_levels[-1] if ch.class_levels else "fighter", {})
    if auto:
        for f in rec.get("feats", []) + list(FEATS):
            base, param = (f.split(" (")[0], f.split(" (")[1][:-1]) if " (" in f else (f, None)
            if base not in FEATS or FEATS[base].get("metamagic"):
                continue
            if FEATS[base].get("param") and not param:
                continue
            if f in ch.feat_list():
                continue
            if feat_eligible(ch, base, param, fighter_bonus):
                ch.feats.append(f)
                return f
        return None
    names = [f for f in sorted(FEATS) if feat_eligible(ch, f, None, fighter_bonus)]
    if not names:
        ui.warn("No eligible feats.")
        return None
    ui.sub(f"Choose a {label} for {ch.name}")
    rec_list = [f.split(" (")[0] for f in rec.get("feats", [])]
    opts = []
    for f in names:
        star = c(" (recommended)", "green") if f in rec_list else ""
        opts.append(f"{f}: {FEATS[f]['desc']}{star}")
    while True:
        i = ui.choose("Feat #", opts)
        feat = names[i]
        param = None
        if FEATS[feat].get("param"):
            popts = [p for p in feat_param_options(ch, feat) if feat_eligible(ch, feat, p,
                                                                                fighter_bonus)]
            if not popts:
                ui.bad("No valid choices for that feat.")
                continue
            j = ui.choose(f"Choose {FEATS[feat]['param'].replace('_', ' ')}", popts,
                          allow_cancel=True)
            if j is None:
                continue
            param = popts[j]
        full = f"{feat} ({param})" if param else feat
        ch.feats.append(full)
        ui.good(f"{ch.name} gains the feat: {full}")
        return full


# ---------------------------------------------------------------- skills
def allocate_skills(ch: Character, points: int, ui, auto: bool) -> None:
    lvl = ch.level
    rec = RECOMMENDED.get(ch.class_levels[-1], {}).get("skills", [])

    def cost(sk):
        return 1 if ch.is_class_skill(sk) else 2

    def room(sk):
        return ch.max_ranks(sk, lvl) - ch.skill_ranks.get(sk, 0)

    if auto:
        order = list(rec) + [s for s in SKILL_ORDER if ch.is_class_skill(s) and s not in rec]
        progress = True
        while points > 0 and progress:
            progress = False
            for sk in order:
                if points <= 0:
                    break
                if ch.is_class_skill(sk) and room(sk) >= 1:
                    ch.skill_ranks[sk] = ch.skill_ranks.get(sk, 0) + 1
                    points -= 1
                    progress = True
        return
    ui.sub(f"{ch.name}: spend {points} skill points (level {lvl})")
    ui.out("Class skills (*): 1 point = 1 rank, max ranks = level + 3. Cross-class "
           "skills: 1 point = 1/2 rank, max ranks = (level + 3) / 2.")
    ui.out("Enter allocations like '3 4' (skill #3, 4 points) or '3 4, 7 2'. 'auto' fills "
           "recommended skills, 'list' re-shows the list, 'done' keeps leftovers (lost).")
    while points > 0:
        rows = []
        for i, sk in enumerate(SKILL_ORDER, 1):
            star = "*" if ch.is_class_skill(sk) else " "
            r = ch.skill_ranks.get(sk, 0)
            mx = ch.max_ranks(sk, lvl)
            recmark = "+" if sk in rec else " "
            rows.append(f"{i:>2}{star}{recmark}{sk[:26]:<26} {r:>4g}/{mx:<4g}")
        for i in range(0, len(rows), 2):
            ui.out("  " + "   ".join(rows[i:i + 2]))
        ui.out(f"  (* class skill, + recommended)   Points left: {c(points, 'bold', 'bgreen')}")
        raw = ui.ask("Allocate").strip().lower()
        if raw == "auto":
            allocate_skills(ch, points, ui, True)
            return
        if raw == "done":
            if ui.confirm(f"Discard {points} unspent points?", False):
                return
            continue
        if raw in ("list", ""):
            continue
        try:
            for chunk in raw.split(","):
                a, b = chunk.split()
                idx, pts = int(a) - 1, int(b)
                sk = SKILL_ORDER[idx]
                if pts <= 0 or pts > points:
                    raise ValueError("not enough points")
                ranks = pts / cost(sk)
                if ranks > room(sk) + 1e-9:
                    raise ValueError(f"{sk}: max ranks would be exceeded")
                ch.skill_ranks[sk] = ch.skill_ranks.get(sk, 0) + ranks
                points -= pts
                ui.good(f"  {sk} now {ch.skill_ranks[sk]:g} ranks")
        except (ValueError, IndexError) as e:
            ui.bad(f"Couldn't apply that: {e}")


# ---------------------------------------------------------------- class features
def choose_deity_domains(ch: Character, ui, auto: bool) -> None:
    rec = RECOMMENDED["cleric"]

    def legal(deity):
        return [d for d in DEITIES[deity]["domains"] if domain_allowed(d, ch.alignment)]

    if auto:
        if not ch.deity or len(legal(ch.deity)) < 2:
            ch.deity = rec["deity"] if len(legal(rec["deity"])) >= 2 else next(
                n for n in DEITIES if len(legal(n)) >= 2)
        doms = legal(ch.deity)
        ch.domains = [d for d in rec["domains"] if d in doms][:2]
        for d in doms:
            if len(ch.domains) < 2 and d not in ch.domains:
                ch.domains.append(d)
    else:
        names = [n for n in DEITIES if len(legal(n)) >= 2]
        ui.sub("Choose a deity")
        i = ui.choose("Deity #", [f"{n} ({DEITIES[n]['alignment']}): "
                                  f"{DEITIES[n]['portfolio']}; domains "
                                  f"{', '.join(legal(n))}; favored weapon "
                                  f"{DEITIES[n]['weapon']}" for n in names])
        ch.deity = names[i]
        doms = legal(ch.deity)
        if len(doms) <= 2:
            ch.domains = list(doms)
            ui.out(f"Domains: {', '.join(ch.domains)}")
        else:
            ui.sub("Choose two domains")
            picks = []
            while len(picks) < 2:
                rest = [d for d in doms if d not in picks]
                j = ui.choose(f"Domain #{len(picks) + 1}",
                              [f"{d}: {DOMAINS[d]['power']}" for d in rest])
                picks.append(rest[j])
            ch.domains = picks
    # channel energy: good clerics turn undead and cure; evil clerics rebuke and inflict
    if "Evil" in ch.alignment:
        ch.energy = "negative"
    elif "Good" in ch.alignment or auto:
        ch.energy = "positive"
    else:
        ch.energy = ["positive", "negative"][ui.choose(
            "A neutral cleric chooses how to channel energy",
            ["Positive energy: turn undead, convert spells into cure spells",
             "Negative energy: rebuke and command undead, convert spells into inflict spells"],
            default=0)]


SCHOOL_TEXT = {"abjuration": "wards and protection", "conjuration": "summoning and acid",
               "divination": "knowledge (only one school prohibited)",
               "enchantment": "charms and sleep", "evocation": "fire, lightning and force",
               "illusion": "blur, invisibility and color spray",
               "necromancy": "life and death", "transmutation": "haste and buffs"}


def choose_specialty(ch: Character, ui, auto: bool) -> None:
    """Wizard school specialization: +1 spell slot per level for that school, two
    prohibited schools (one for divination)."""
    if auto:
        return
    opts = ["Generalist (no specialty, no prohibited schools)"] + [
        f"Specialist: {sch} ({SCHOOL_TEXT[sch]})" for sch in SPELL_SCHOOLS]
    i = ui.choose("Specialize in a school of magic?", opts, default=0)
    if i == 0:
        return
    ch.specialty = SPELL_SCHOOLS[i - 1]
    rest = [sch for sch in SPELL_SCHOOLS if sch not in (ch.specialty, "divination")]
    need = 1 if ch.specialty == "divination" else 2
    ui.out(f"Choose {need} prohibited school(s): you can never cast those spells.")
    while len(ch.prohibited) < need:
        left = [sch for sch in rest if sch not in ch.prohibited]
        ch.prohibited.append(left[ui.choose(f"Prohibited school #{len(ch.prohibited) + 1}",
                                            left)])
    ui.good(f"{ch.name} specializes in {ch.specialty}; prohibited: "
            f"{', '.join(ch.prohibited)}.")


def choose_favored_enemy(ch: Character, ui, auto: bool) -> None:
    if ch.favored_enemies:
        # 5th level: +2 to one existing favored enemy
        if auto:
            ch.favored_enemies[0]["bonus"] += 2
        else:
            j = ui.choose("Increase which favored enemy by +2?",
                          [f"{f['type']} (+{f['bonus']})" for f in ch.favored_enemies])
            ch.favored_enemies[j]["bonus"] += 2
    taken = {f["type"] for f in ch.favored_enemies}
    opts = [t for t in FAVORED_ENEMIES if t not in taken]
    if auto:
        rec = RECOMMENDED["ranger"]["favored_enemy"]
        t = rec if rec in opts else opts[0]
    else:
        ui.sub("Choose a favored enemy (+2 damage and +2 on some skills against them)")
        ui.out("Tip: this adventure features goblinoids and undead.")
        t = opts[ui.choose("Favored enemy #", opts)]
    ch.favored_enemies.append({"type": t, "bonus": 2})


def choose_combat_style(ch: Character, ui, auto: bool) -> None:
    if auto:
        ch.combat_style = RECOMMENDED["ranger"]["style"]
        return
    ui.sub("Choose a ranger combat style")
    i = ui.choose("Style #", ["Archery (bonus Rapid Shot)",
                              "Two-weapon combat (bonus Two-Weapon Fighting)"])
    ch.combat_style = ["archery", "two-weapon"][i]


def learn_spells(ch: Character, cls: str, ui, auto: bool, first: bool) -> None:
    if cls == "wizard":
        if first:
            ch.spellbook = [sp for sp in spells_for("wizard", 0)
                            if SPELLS[sp]["school"] not in ch.prohibited]
            n = 3 + max(0, ch.mod("int"))
            pool_levels = [1]
        else:
            n = 2
            pool_levels = [l for l in ch.spells_per_day("wizard") if l >= 1]
        for _ in range(n):
            pool = [s for l in pool_levels for s in spells_for("wizard", l)
                    if s not in ch.spellbook and SPELLS[s]["school"] not in ch.prohibited]
            if not pool:
                break
            if auto:
                prio = [s for l in sorted(pool_levels, reverse=True)
                        for s in RECOMMENDED["wizard"]["spells"].get(l, [])]
                pick = next((s for s in prio if s in pool), pool[0])
            else:
                ui.sub(f"Add a spell to {ch.name}'s spellbook")
                from .sheet import spell_description
                pick = pool[ui.choose("Spell #", [spell_description(s) for s in pool])]
            ch.spellbook.append(pick)
            if not auto:
                ui.good(f"Learned {pick}.")
    elif CLASSES[cls].get("spells_known"):
        lvl = min(ch.caster_class_level(cls), rules.MAX_LEVEL)
        known_table = CLASSES[cls]["spells_known"][lvl]
        for sl, n in enumerate(known_table):
            have = ch.spells_known.setdefault(sl, [])
            while len(have) < n:
                pool = [s for s in spells_for(cls, sl) if s not in have]
                if not pool:
                    break
                if auto:
                    prio = RECOMMENDED[cls]["spells"].get(sl, [])
                    pick = next((s for s in prio if s in pool), pool[0])
                else:
                    ui.sub(f"Choose a level-{sl} spell known for {ch.name} "
                           f"({len(have) + 1}/{n})")
                    from .sheet import spell_description
                    pick = pool[ui.choose("Spell #", [spell_description(s) for s in pool])]
                have.append(pick)


# ---------------------------------------------------------------- spell preparation
def prepare_spells(ch: Character, ui, auto: bool = False, keep_ok: bool = True) -> None:
    for cls in ch.caster_classes():
        if not CLASSES[cls].get("prepared"):
            continue
        per = ch.spells_per_day(cls)
        dom = ch.domain_slots() if cls == "cleric" else {}
        old = ch.prepared.get(cls, {})
        old_ok = old and all(len([s for s in old.get(sl, []) if not s.get("domain")]) == n
                             for sl, n in per.items())
        if not auto and old_ok and keep_ok:
            summary = "; ".join(f"L{sl}: " + ", ".join(s["spell"] for s in old.get(sl, []))
                                for sl in sorted(per))
            ui.out(f"{ch.name}'s current {CLASSES[cls]['name']} spells: {summary}")
            if ui.confirm("Keep the same spells prepared?", True):
                ch.reset_spells()
                continue
        new = {}
        for sl in sorted(per):
            pool = (sorted(s for s in ch.spellbook if SPELLS[s]["levels"].get("wizard") == sl)
                    if cls == "wizard" else spells_for(cls, sl))
            if not pool:
                continue
            n = per[sl]
            if auto:
                prio = [s for s in PREP_PRIORITY.get(cls, {}).get(sl, []) if s in pool] or pool
                picks = [prio[i % len(prio)] for i in range(n)]
            else:
                ui.sub(f"{ch.name}: prepare {n} level-{sl} {CLASSES[cls]['name']} spell(s)")
                from .sheet import spell_description
                for i, s in enumerate(pool, 1):
                    ui.out(f"  {i:>2}. {spell_description(s)}")
                while True:
                    raw = ui.ask(f"Enter {n} numbers (repeats allowed), or 'auto'")
                    if raw.strip().lower() == "auto":
                        prio = [s for s in PREP_PRIORITY.get(cls, {}).get(sl, [])
                                if s in pool] or pool
                        picks = [prio[i % len(prio)] for i in range(n)]
                        break
                    try:
                        idx = [int(x) - 1 for x in raw.replace(",", " ").split()]
                        if len(idx) == n and all(0 <= i < len(pool) for i in idx):
                            picks = [pool[i] for i in idx]
                            break
                    except ValueError:
                        pass
                    ui.bad(f"Please enter exactly {n} numbers from the list.")
            if cls == "wizard" and ch.specialty and picks and not any(
                    SPELLS[p]["school"] == ch.specialty for p in picks):
                spec = [p for p in pool if SPELLS[p]["school"] == ch.specialty]
                if spec:   # the specialist's bonus slot must hold a specialty spell
                    picks[-1] = spec[0]
                    if ui and not auto:
                        ui.out(f"  (Bonus specialist slot: {spec[0]}.)")
            slots = [{"spell": p, "used": False} for p in picks]
            if sl in dom:
                dspells = ch.domain_spells(sl)
                if auto or len(dspells) == 1:
                    ds = dspells[0]
                else:
                    ds = dspells[ui.choose(f"Domain spell for level {sl}", dspells)]
                slots.append({"spell": ds, "used": False, "domain": True})
            new[sl] = slots
        ch.prepared[cls] = new


# ---------------------------------------------------------------- hit points
def gain_hp(ch: Character, cls: str, ui, auto: bool, method: str = "ask") -> int:
    hd = CLASSES[cls]["hd"]
    if ch.level == 1 or method == "max":
        roll = hd
        msg = f"Maximum hit points on d{hd} = {hd}"
    elif auto or method == "average":
        roll = hd // 2 + 1
        msg = f"Average hit points on d{hd} = {roll}"
    else:
        choice = ui.choose(f"Hit points for this level (d{hd})",
                           [f"Roll 1d{hd}", f"Take the average ({hd // 2 + 1})"], default=0)
        if choice == 0:
            roll = dice.die(hd)
            msg = f"Rolled d{hd}: {roll}"
        else:
            roll = hd // 2 + 1
            msg = f"Took average: {roll}"
    ch.hp_rolls.append(roll)
    if ui and not auto:
        ui.out(f"  {msg} {ch.mod('con'):+d} Con")
    return roll


# ---------------------------------------------------------------- prestige classes
def _casts_level(ch: Character, kind: str, level: int) -> bool:
    return any(CLASSES[c].get("caster") == kind and
               max(ch.spells_per_day(c) or {0: 0}) >= level for c in ch.classes()
               if not CLASSES[c].get("prestige"))


def prestige_eligible(ch: Character, cls: str) -> bool:
    """DMG requirements (slightly simplified) for each prestige class."""
    r = ch.skill_ranks
    feats = ch.feat_list()
    if not alignment_allowed(cls, ch.alignment):
        return False
    if cls == "eldritch knight":
        return "martial" in ch.proficiencies() and _casts_level(ch, "arcane", 3)
    if cls == "mystic theurge":
        return (_casts_level(ch, "arcane", 2) and _casts_level(ch, "divine", 2)
                and r.get("Knowledge (arcana)", 0) >= 6 and r.get("Knowledge (religion)", 0) >= 6)
    if cls == "arcane trickster":
        return (r.get("Disable Device", 0) >= 7 and r.get("Escape Artist", 0) >= 7
                and r.get("Knowledge (arcana)", 0) >= 4 and ch.sneak_attack_dice() >= 2
                and _casts_level(ch, "arcane", 3))
    if cls == "dwarven defender":
        return (ch.race == "dwarf" and ch.bab() >= 7
                and all(f in feats for f in ("Dodge", "Endurance", "Toughness")))
    if cls == "duelist":
        return (ch.bab() >= 6 and all(f in feats for f in ("Dodge", "Mobility",
                                                           "Weapon Finesse"))
                and r.get("Perform", 0) >= 2 and r.get("Tumble", 0) >= 5)
    if cls == "arcane archer":
        return (ch.race in ("elf", "half-elf") and ch.bab() >= 6
                and "Point Blank Shot" in feats and "Precise Shot" in feats
                and any(f in feats for f in ("Weapon Focus (longbow)", "Weapon Focus (shortbow)"))
                and _casts_level(ch, "arcane", 1))
    if cls == "assassin":
        return (r.get("Disguise", 0) >= 4 and r.get("Hide", 0) >= 8
                and r.get("Move Silently", 0) >= 8)
    return False


def _prestige_progress(ch: Character, cls: str, clvl: int, ui, auto: bool) -> None:
    prog = CLASSES[cls].get("progression") or {}
    for kind, levels in prog.items():
        key = f"{cls}:{kind}"
        if key not in ch.prestige_target:
            opts = [c for c in ch.classes() if CLASSES[c].get("caster") == kind
                    and not CLASSES[c].get("prestige")]
            if not opts:
                continue
            if auto or len(opts) == 1:
                tgt = max(opts, key=ch.class_level)
            else:
                tgt = opts[ui.choose(f"{CLASSES[cls]['name']} advances which {kind} class?",
                                     [CLASSES[o]["name"] for o in opts])]
            ch.prestige_target[key] = tgt
        if clvl in levels:
            tgt = ch.prestige_target[key]
            if tgt == "wizard" or CLASSES[tgt].get("spells_known"):
                learn_spells(ch, tgt, ui, auto, False)
            if ui and not auto:
                ui.good(f"{ch.name}'s {CLASSES[tgt]['name']} spellcasting advances "
                        f"(now as a level {ch.caster_class_level(tgt)} caster).")


# ---------------------------------------------------------------- main entry
def gain_level(ch: Character, cls: str, ui=None, auto: bool = False,
               hp_method: str = "ask") -> None:
    first = ch.level == 0
    first_in_class = ch.class_level(cls) == 0
    before_spells = {c: dict(ch.spells_per_day(c)) for c in ch.caster_classes()}
    rec_cls = cls if cls in RECOMMENDED else (ch.class_levels[0] if ch.class_levels
                                              else "fighter")
    ch.class_levels.append(cls)
    lvl = ch.level
    clvl = ch.class_level(cls)
    if ui and not auto:
        ui.header(f"{ch.name} becomes level {lvl} ({CLASSES[cls]['name']} {clvl})")
    # ability increase
    if lvl in ABILITY_INCREASE_LEVELS:
        if auto:
            ab = RECOMMENDED[rec_cls]["abilities"][0]
        else:
            ui.sub("Ability score increase (+1)")
            opts = [f"{rules.ABILITY_NAMES[a]} ({ch.ability(a)})" for a in rules.ABILITIES]
            ab = rules.ABILITIES[ui.choose("Increase which ability?", opts)]
        ch.ability_increases.append(ab)
    gain_hp(ch, cls, ui, auto, hp_method)
    # class features needing choices
    if cls == "cleric" and first_in_class:
        choose_deity_domains(ch, ui, auto)
    if cls == "ranger" and clvl in (1, 5, 10, 15, 20):
        choose_favored_enemy(ch, ui, auto)
    if cls == "ranger" and clvl == 2:
        choose_combat_style(ch, ui, auto)
    if ((cls == "druid" and clvl == 1) or (cls == "ranger" and clvl == 4)) \
            and not ch.companion:
        choose_companion(ch, ui, auto)
    if cls in ("wizard", "sorcerer") and first_in_class and not ch.familiar:
        choose_familiar(ch, ui, auto)
    if cls == "wizard" and first_in_class:
        choose_specialty(ch, ui, auto)
    if cls == "rogue" and clvl in (10, 13, 16, 19):
        from .data.classes import ROGUE_SPECIALS
        opts = [k for k in ROGUE_SPECIALS if k not in ch.rogue_specials]
        if auto:
            pick = next(k for k in ("improved evasion", "crippling strike", "defensive roll",
                                    "slippery mind", "opportunist", "skill mastery")
                        if k in opts)
        else:
            pick = opts[ui.choose("Rogue special ability", [ROGUE_SPECIALS[k] for k in opts])]
        ch.rogue_specials.append(pick)
    if cls == "paladin" and clvl == 5 and not ch.mount:
        ch.mount = {"kind": "heavy warhorse", "name": "Valor" if auto else (
            ui.ask("Name your celestial warhorse", "Valor").strip() or "Valor"),
            "damage": 0, "dead": False}
        if ui and not auto:
            ui.good(f"A shining warhorse, {ch.mount['name']}, answers {ch.name}'s call.")
    # skills
    pts = ch.skill_points_for_level(cls, first)
    allocate_skills(ch, pts, ui, auto)
    # feats
    if lvl in FEAT_LEVELS:
        choose_feat(ch, ui, auto)
    if first and ch.race_data.get("bonus_feat"):
        choose_feat(ch, ui, auto, label="human bonus feat")
    if clvl in CLASSES[cls].get("bonus_feat_levels", []):
        if cls == "fighter":
            choose_feat(ch, ui, auto, fighter_bonus=True, label="fighter bonus feat")
        elif cls == "monk":
            # monks ignore prerequisites for their bonus feats
            opts = [f for f in MONK_BONUS_FEATS[clvl] if f not in ch.feats] or \
                MONK_BONUS_FEATS[clvl]
            if auto:
                pick = RECOMMENDED["monk"]["bonus"][clvl]
                pick = pick if pick in opts else opts[0]
            else:
                from .data.feats import FEATS as _F
                pick = opts[ui.choose("Monk bonus feat", [f"{o}: {_F[o]['desc']}"
                                                          for o in opts])]
            ch.feats.append(pick)
        else:
            # wizard 5th/10th: metamagic / item creation (mostly flavor here)
            opts = [o for o in CASTER_BONUS_FEATS if o not in ch.feats] or ["Spell Penetration"]
            if auto:
                ch.feats.append(opts[0])
            else:
                ch.feats.append(opts[ui.choose("Wizard bonus feat", opts)])
    if cls == "eldritch knight" and clvl == 1:
        choose_feat(ch, ui, auto, fighter_bonus=True, label="eldritch knight bonus feat")
    if CLASSES[cls].get("prestige"):
        _prestige_progress(ch, cls, clvl, ui, auto)
    # spells
    if cls == "wizard" or CLASSES[cls].get("spells_known"):
        learn_spells(ch, cls, ui, auto, first_in_class)
    after = {c: dict(ch.spells_per_day(c)) for c in ch.caster_classes()}
    if after and after != before_spells:
        prepare_spells(ch, ui, auto, keep_ok=False)
    if ui and not auto:
        ui.good(f"{ch.name} is now level {lvl}! HP {ch.max_hp()}, BAB {ch.bab():+d}.")


def level_up_interactive(ch: Character, ui, heroic: bool = False) -> None:
    with ui.acting(ch.player):
        _level_up_interactive(ch, ui, heroic)


def _level_up_interactive(ch: Character, ui, heroic: bool = False) -> None:
    while ch.can_level_up():
        if not ui.confirm(f"{ch.name} can advance to level {ch.level + 1}. Level up now?", True):
            return
        current = [k for k in ch.classes()
                   if ch.class_level(k) < CLASSES[k].get("max_level", 99)]
        opts = [f"{CLASSES[k]['name']} (continue, level {ch.class_level(k) + 1})"
                for k in current]
        others = [k for k in CLASS_ORDER if k not in ch.classes()
                  and alignment_allowed(k, ch.alignment)]
        from .data.classes import PRESTIGE
        others += [k for k in PRESTIGE if k not in ch.classes() and prestige_eligible(ch, k)]
        opts += [f"{CLASSES[k]['name']} ("
                 f"{'prestige class' if CLASSES[k].get('prestige') else 'multiclass'})"
                 for k in others]
        i = ui.choose("Advance in which class?", opts, default=0)
        cls = (current + others)[i]
        auto = ui.choose("How should the choices be made?",
                         ["I'll choose everything", "Use the recommended build (auto)"],
                         default=0) == 1
        gain_level(ch, cls, ui, auto=auto, hp_method="max" if heroic else "ask")
        if auto:
            ui.good(f"{ch.name} is now level {ch.level}! HP {ch.max_hp()}, "
                    f"BAB {ch.bab():+d}.")
