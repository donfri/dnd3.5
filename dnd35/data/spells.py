"""Spells (SRD 3.5 subset). Mechanics live in dnd35/magic.py keyed by name.

target: "enemy" (one hostile), "enemies" (choose several), "ally" (one ally incl. self),
        "allies" (whole party), "self", "none" (utility / flavor).
"""


def S(name, levels, school, target, desc, save=None, sr=True, desc_tags=(), combat=True,
      utility=False, max_targets=1):
    return {"name": name, "levels": levels, "school": school, "target": target, "desc": desc,
            "save": save, "sr": sr, "tags": set(desc_tags), "combat": combat,
            "utility": utility, "max_targets": max_targets}


ARC = lambda lvl: {"wizard": lvl, "sorcerer": lvl}  # noqa: E731

SPELLS = {s["name"]: s for s in [
    # ---------------------------------------------------------------- arcane 0
    S("Acid Splash", ARC(0), "conjuration", "enemy",
      "Ranged touch attack: 1d3 acid damage.", sr=False, desc_tags=["acid"]),
    S("Ray of Frost", ARC(0), "evocation", "enemy",
      "Ranged touch attack: 1d3 cold damage.", desc_tags=["cold"]),
    S("Disrupt Undead", ARC(0), "necromancy", "enemy",
      "Ranged touch attack: 1d6 damage to one undead."),
    S("Daze", ARC(0), "enchantment", "enemy",
      "A humanoid of 4 HD or less loses its next action (Will negates).",
      save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    S("Resistance", {"wizard": 0, "sorcerer": 0, "cleric": 0}, "abjuration", "ally",
      "+1 resistance bonus on saving throws for 1 minute."),
    S("Detect Magic", {"wizard": 0, "sorcerer": 0, "cleric": 0}, "divination", "none",
      "Detect magical auras within 60 ft.", combat=False, utility=True),
    S("Light", {"wizard": 0, "sorcerer": 0, "cleric": 0}, "evocation", "none",
      "Object shines like a torch for 10 min/level.", combat=False, utility=True),
    S("Mage Hand", ARC(0), "transmutation", "none",
      "Telekinetically move a 5-lb. object.", combat=False, utility=True),
    # ---------------------------------------------------------------- arcane 1
    S("Magic Missile", ARC(1), "evocation", "enemy",
      "1d4+1 force damage per missile, never misses. 1 missile, +1 per two levels above 1st "
      "(max 5).", desc_tags=["force"]),
    S("Sleep", ARC(1), "enchantment", "enemies",
      "Puts 4 HD of living creatures (weakest first) into magical slumber (Will negates).",
      save=("will", "negates"), desc_tags=["mind-affecting", "sleep", "compulsion"],
      max_targets=6),
    S("Color Spray", ARC(1), "illusion", "enemies",
      "Cone of colors: creatures of 2 HD or less are knocked unconscious, 3-4 HD blinded, "
      "others stunned 1 round (Will negates).", save=("will", "negates"),
      desc_tags=["mind-affecting", "pattern"], max_targets=3),
    S("Burning Hands", ARC(1), "evocation", "enemies",
      "Cone of flame: 1d4 fire per level (max 5d4) to up to 3 adjacent foes (Reflex half).",
      save=("reflex", "half"), desc_tags=["fire"], max_targets=3),
    S("Mage Armor", ARC(1), "conjuration", "ally",
      "+4 armor bonus to AC for 1 hour/level.", desc_tags=["force"]),
    S("Shield", ARC(1), "abjuration", "self",
      "+4 shield bonus to AC for 1 minute/level; blocks magic missile.", desc_tags=["force"]),
    S("Ray of Enfeeblement", ARC(1), "necromancy", "enemy",
      "Ranged touch: target takes a 1d6 Strength penalty (+1 per two levels, max +5)."),
    S("True Strike", ARC(1), "divination", "self",
      "+20 insight bonus on your next attack roll this round or next."),
    S("Enlarge Person", {"wizard": 1, "sorcerer": 1, "cleric_domain": 1}, "transmutation",
      "ally", "Humanoid becomes Large: +2 Str, -2 Dex, -1 attack/AC, bigger weapon damage "
              "for 1 min/level."),
    # ---------------------------------------------------------------- arcane 2
    S("Scorching Ray", ARC(2), "evocation", "enemy",
      "Ranged touch: 4d6 fire damage.", desc_tags=["fire"]),
    S("Melf's Acid Arrow", ARC(2), "conjuration", "enemy",
      "Ranged touch: 2d4 acid now and 2d4 for 1 more round (per 3 levels).", sr=False,
      desc_tags=["acid"]),
    S("Bull's Strength", {"wizard": 2, "sorcerer": 2, "cleric": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Strength for 1 min/level."),
    S("Cat's Grace", {"wizard": 2, "sorcerer": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Dexterity for 1 min/level."),
    S("Bear's Endurance", {"wizard": 2, "sorcerer": 2, "cleric": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Constitution for 1 min/level."),
    S("Blur", ARC(2), "illusion", "ally",
      "Attacks against the subject have a 20% miss chance for 1 min/level."),
    # ---------------------------------------------------------------- arcane 3
    S("Fireball", ARC(3), "evocation", "enemies",
      "20-ft. radius burst: 1d6 fire per level (max 10d6), Reflex half. Allies fighting next "
      "to targets are caught too!", save=("reflex", "half"), desc_tags=["fire"],
      max_targets=8),
    S("Lightning Bolt", ARC(3), "evocation", "enemies",
      "120-ft. line: 1d6 electricity per level (max 10d6) to up to 3 foes in a line, Reflex "
      "half.", save=("reflex", "half"), desc_tags=["electricity"], max_targets=3),
    S("Haste", ARC(3), "transmutation", "allies",
      "Party: +1 attack, +1 dodge AC and Reflex, one extra attack on a full attack, for 1 "
      "round/level."),
    # ---------------------------------------------------------------- divine 0
    S("Guidance", {"cleric": 0}, "divination", "ally",
      "+1 competence bonus on the next attack roll, save, or skill check (1 minute)."),
    S("Virtue", {"cleric": 0}, "transmutation", "ally", "Subject gains 1 temporary hp."),
    S("Cure Minor Wounds", {"cleric": 0}, "conjuration", "ally", "Cures 1 point of damage.",
      desc_tags=["healing"]),
    # ---------------------------------------------------------------- divine 1
    S("Cure Light Wounds", {"cleric": 1, "ranger": 1}, "conjuration", "ally",
      "Cures 1d8 +1/level (max +5). Damages undead (Will half).", desc_tags=["healing"]),
    S("Inflict Light Wounds", {"cleric": 1}, "necromancy", "enemy",
      "Melee touch: 1d8 +1/level (max +5) damage (Will half). Heals undead.",
      save=("will", "half")),
    S("Bless", {"cleric": 1}, "enchantment", "allies",
      "Allies gain +1 morale bonus on attack rolls and saves vs fear for 1 min/level.",
      desc_tags=["mind-affecting"]),
    S("Shield of Faith", {"cleric": 1}, "abjuration", "ally",
      "+2 deflection bonus to AC (+1 per 6 levels) for 1 min/level."),
    S("Divine Favor", {"cleric": 1}, "evocation", "self",
      "+1 luck bonus on attack and damage rolls per 3 levels (max +3) for 1 minute."),
    S("Protection from Evil", {"cleric": 1, "wizard": 1, "sorcerer": 1}, "abjuration", "ally",
      "+2 deflection AC and +2 resistance on saves against evil creatures for 1 min/level.",
      desc_tags=["good"]),
    S("Magic Weapon", {"cleric": 1, "wizard": 1, "sorcerer": 1}, "transmutation", "ally",
      "Weapon gains +1 enhancement bonus on attack and damage for 1 min/level."),
    S("Doom", {"cleric": 1}, "necromancy", "enemy",
      "Target becomes shaken (-2 attacks, saves, checks) for 1 min/level (Will negates).",
      save=("will", "negates"), desc_tags=["fear", "mind-affecting"]),
    S("Longstrider", {"ranger": 1}, "transmutation", "self",
      "+10 ft. enhancement bonus to speed for 1 hour/level."),
    S("Resist Energy", {"ranger": 1, "cleric": 2, "wizard": 2, "sorcerer": 2}, "abjuration",
      "ally", "Resist 10 fire for 10 min/level (resistance to fire assumed)."),
    # ---------------------------------------------------------------- divine 2
    S("Cure Moderate Wounds", {"cleric": 2}, "conjuration", "ally",
      "Cures 2d8 +1/level (max +10). Damages undead (Will half).", desc_tags=["healing"]),
    S("Inflict Moderate Wounds", {"cleric": 2}, "necromancy", "enemy",
      "Melee touch: 2d8 +1/level (max +10) damage (Will half).", save=("will", "half")),
    S("Aid", {"cleric": 2}, "enchantment", "ally",
      "+1 morale bonus on attacks and saves vs fear, plus 1d8+1/level (max +10) temporary hp, "
      "for 1 min/level.", desc_tags=["mind-affecting", "good"]),
    S("Spiritual Weapon", {"cleric": 2}, "evocation", "enemy",
      "A force weapon attacks a foe every round (BAB + Wis, 1d8 +1 per 3 levels) for 1 "
      "round/level.", sr=True, desc_tags=["force"]),
    S("Hold Person", {"cleric": 2, "wizard": 3, "sorcerer": 3}, "enchantment", "enemy",
      "A humanoid is paralyzed for 1 round/level (Will negates; new save each round).",
      save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    # ---------------------------------------------------------------- divine 3
    S("Cure Serious Wounds", {"cleric": 3}, "conjuration", "ally",
      "Cures 3d8 +1/level (max +15). Damages undead (Will half).", desc_tags=["healing"]),
    S("Prayer", {"cleric": 3}, "enchantment", "allies",
      "Allies +1 luck on attacks, damage, saves, checks; enemies -1 (1 round/level).",
      desc_tags=["mind-affecting"]),
    S("Searing Light", {"cleric": 3}, "evocation", "enemy",
      "Ranged touch: 1d8 per two levels (max 5d8); 1d6/level vs undead.",
      desc_tags=["light"]),
    S("Magic Vestment", {"cleric": 3}, "transmutation", "ally",
      "Armor or shield gains +1 enhancement per 4 levels (max +5) for 1 hour/level."),
    S("Magic Circle against Evil", {"cleric": 3, "wizard": 3, "sorcerer": 3}, "abjuration",
      "allies", "As protection from evil, on the whole party, 10 min/level.",
      desc_tags=["good"]),
]}


def spells_for(cls: str, level: int):
    return sorted(n for n, s in SPELLS.items() if s["levels"].get(cls) == level)
