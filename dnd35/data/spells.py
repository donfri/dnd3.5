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
    S("Daze", {"wizard": 0, "sorcerer": 0, "bard": 0}, "enchantment", "enemy",
      "A humanoid of 4 HD or less loses its next action (Will negates).",
      save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    S("Resistance", {"wizard": 0, "sorcerer": 0, "cleric": 0, "bard": 0, "druid": 0,
                    "paladin": 1}, "abjuration", "ally",
      "+1 resistance bonus on saving throws for 1 minute."),
    S("Detect Magic", {"wizard": 0, "sorcerer": 0, "cleric": 0, "bard": 0, "druid": 0}, "divination", "none",
      "Detect magical auras within 60 ft.", combat=False, utility=True),
    S("Light", {"wizard": 0, "sorcerer": 0, "cleric": 0, "bard": 0, "druid": 0}, "evocation", "none",
      "Object shines like a torch for 10 min/level.", combat=False, utility=True),
    S("Mage Hand", {"wizard": 0, "sorcerer": 0, "bard": 0}, "transmutation", "none",
      "Telekinetically move a 5-lb. object.", combat=False, utility=True),
    # ---------------------------------------------------------------- arcane 1
    S("Magic Missile", ARC(1), "evocation", "enemy",
      "1d4+1 force damage per missile, never misses. 1 missile, +1 per two levels above 1st "
      "(max 5).", desc_tags=["force"]),
    S("Sleep", {"wizard": 1, "sorcerer": 1, "bard": 1}, "enchantment", "enemies",
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
    S("Bull's Strength", {"wizard": 2, "sorcerer": 2, "cleric": 2, "druid": 2, "paladin": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Strength for 1 min/level."),
    S("Cat's Grace", {"wizard": 2, "sorcerer": 2, "bard": 2, "druid": 2, "ranger": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Dexterity for 1 min/level."),
    S("Bear's Endurance", {"wizard": 2, "sorcerer": 2, "cleric": 2, "druid": 2, "ranger": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Constitution for 1 min/level."),
    S("Blur", {"wizard": 2, "sorcerer": 2, "bard": 2}, "illusion", "ally",
      "Attacks against the subject have a 20% miss chance for 1 min/level."),
    # ---------------------------------------------------------------- arcane 3
    S("Fireball", ARC(3), "evocation", "enemies",
      "20-ft. radius burst: 1d6 fire per level (max 10d6), Reflex half. Allies fighting next "
      "to targets are caught too!", save=("reflex", "half"), desc_tags=["fire"],
      max_targets=8),
    S("Lightning Bolt", ARC(3), "evocation", "enemies",
      "120-ft. line: 1d6 electricity per level (max 10d6) to up to 3 foes in a line, Reflex "
      "half.", save=("reflex", "half"), desc_tags=["electricity"], max_targets=3),
    S("Haste", {"wizard": 3, "sorcerer": 3, "bard": 3}, "transmutation", "allies",
      "Party: +1 attack, +1 dodge AC and Reflex, one extra attack on a full attack, for 1 "
      "round/level."),
    # ---------------------------------------------------------------- divine 0
    S("Guidance", {"cleric": 0, "druid": 0}, "divination", "ally",
      "+1 competence bonus on the next attack roll, save, or skill check (1 minute)."),
    S("Virtue", {"cleric": 0, "druid": 0, "paladin": 1}, "transmutation", "ally", "Subject gains 1 temporary hp."),
    S("Cure Minor Wounds", {"cleric": 0, "druid": 0}, "conjuration", "ally", "Cures 1 point of damage.",
      desc_tags=["healing"]),
    # ---------------------------------------------------------------- divine 1
    S("Cure Light Wounds", {"cleric": 1, "bard": 1, "druid": 1, "paladin": 1, "ranger": 2}, "conjuration", "ally",
      "Cures 1d8 +1/level (max +5). Damages undead (Will half).", desc_tags=["healing"]),
    S("Inflict Light Wounds", {"cleric": 1}, "necromancy", "enemy",
      "Melee touch: 1d8 +1/level (max +5) damage (Will half). Heals undead.",
      save=("will", "half")),
    S("Bless", {"cleric": 1, "paladin": 1}, "enchantment", "allies",
      "Allies gain +1 morale bonus on attack rolls and saves vs fear for 1 min/level.",
      desc_tags=["mind-affecting"]),
    S("Shield of Faith", {"cleric": 1}, "abjuration", "ally",
      "+2 deflection bonus to AC (+1 per 6 levels) for 1 min/level."),
    S("Divine Favor", {"cleric": 1, "paladin": 1}, "evocation", "self",
      "+1 luck bonus on attack and damage rolls per 3 levels (max +3) for 1 minute."),
    S("Protection from Evil", {"cleric": 1, "wizard": 1, "sorcerer": 1, "paladin": 1}, "abjuration", "ally",
      "+2 deflection AC and +2 resistance on saves against evil creatures for 1 min/level.",
      desc_tags=["good"]),
    S("Magic Weapon", {"cleric": 1, "wizard": 1, "sorcerer": 1, "paladin": 1}, "transmutation", "ally",
      "Weapon gains +1 enhancement bonus on attack and damage for 1 min/level."),
    S("Doom", {"cleric": 1}, "necromancy", "enemy",
      "Target becomes shaken (-2 attacks, saves, checks) for 1 min/level (Will negates).",
      save=("will", "negates"), desc_tags=["fear", "mind-affecting"]),
    S("Longstrider", {"ranger": 1, "druid": 1}, "transmutation", "self",
      "+10 ft. enhancement bonus to speed for 1 hour/level."),
    S("Resist Energy", {"ranger": 1, "cleric": 2, "wizard": 2, "sorcerer": 2, "druid": 2,
                       "paladin": 2}, "abjuration",
      "ally", "Resist 10 fire for 10 min/level (resistance to fire assumed)."),
    # ---------------------------------------------------------------- divine 2
    S("Cure Moderate Wounds", {"cleric": 2, "bard": 2, "druid": 3, "ranger": 3}, "conjuration", "ally",
      "Cures 2d8 +1/level (max +10). Damages undead (Will half).", desc_tags=["healing"]),
    S("Inflict Moderate Wounds", {"cleric": 2}, "necromancy", "enemy",
      "Melee touch: 2d8 +1/level (max +10) damage (Will half).", save=("will", "half")),
    S("Aid", {"cleric": 2}, "enchantment", "ally",
      "+1 morale bonus on attacks and saves vs fear, plus 1d8+1/level (max +10) temporary hp, "
      "for 1 min/level.", desc_tags=["mind-affecting", "good"]),
    S("Spiritual Weapon", {"cleric": 2}, "evocation", "enemy",
      "A force weapon attacks a foe every round (BAB + Wis, 1d8 +1 per 3 levels) for 1 "
      "round/level.", sr=True, desc_tags=["force"]),
    S("Hold Person", {"cleric": 2, "wizard": 3, "sorcerer": 3, "bard": 2}, "enchantment", "enemy",
      "A humanoid is paralyzed for 1 round/level (Will negates; new save each round).",
      save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    # ---------------------------------------------------------------- divine 3
    S("Cure Serious Wounds", {"cleric": 3, "bard": 3, "druid": 4}, "conjuration", "ally",
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
    # ---------------------------------------------------------------- added in v2
    # cantrips
    S("Flare", {"wizard": 0, "sorcerer": 0, "bard": 0, "druid": 0}, "evocation", "enemy",
      "A burst of light dazzles one creature: -1 on attack rolls for 1 minute (Fort negates).",
      save=("fort", "negates"), desc_tags=["light"]),
    S("Prestidigitation", {"wizard": 0, "sorcerer": 0, "bard": 0}, "universal", "none",
      "Minor tricks: clean, warm, flavor, color or soil small things.", combat=False,
      utility=True),
    S("Know Direction", {"bard": 0, "druid": 0}, "divination", "none",
      "You instantly know which way is north.", combat=False, utility=True),
    # 1st
    S("Grease", {"wizard": 1, "sorcerer": 1, "bard": 1}, "conjuration", "enemies",
      "Slick grease under up to 3 foes: each must make a Reflex save or fall prone.",
      save=("ref", "negates"), sr=False, max_targets=3),
    S("Hideous Laughter", {"wizard": 2, "sorcerer": 2, "bard": 1}, "enchantment", "enemy",
      "Target collapses laughing: prone and helpless to act for 1 round/level (Will "
      "negates).", save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    S("Remove Fear", {"cleric": 1, "bard": 1}, "abjuration", "ally",
      "Ends fear effects and grants +4 morale on saves vs fear for 10 minutes."),
    S("Lesser Restoration", {"cleric": 2, "druid": 2, "paladin": 1}, "conjuration", "ally",
      "Heals 1d4 points of ability damage and removes fatigue.", desc_tags=["healing"]),
    S("Entangle", {"druid": 1, "ranger": 1}, "transmutation", "enemies",
      "Plants grab up to 6 foes: entangled (-2 attack, -4 Dex, can't move) for 1 min/level "
      "(Reflex negates; new Reflex save each round to break free).", save=("ref", "negates"),
      sr=False, max_targets=6),
    S("Produce Flame", {"druid": 1}, "evocation", "enemy",
      "Hurl a flame: ranged touch, 1d6 +1/level (max +5) fire.", sr=True, desc_tags=["fire"]),
    S("Shillelagh", {"druid": 1}, "transmutation", "self",
      "Your club or quarterstaff becomes +1 and deals damage as if two sizes larger "
      "(1 min/level)."),
    S("Magic Fang", {"druid": 1, "ranger": 1}, "transmutation", "ally",
      "Natural weapons and unarmed strikes get +1 on attack and damage (1 min/level)."),
    # 2nd
    S("Eagle's Splendor", {"wizard": 2, "sorcerer": 2, "bard": 2, "cleric": 2, "paladin": 2},
      "transmutation", "ally", "+4 enhancement bonus to Charisma for 1 min/level."),
    S("Owl's Wisdom", {"wizard": 2, "sorcerer": 2, "cleric": 2, "druid": 2, "paladin": 2,
                       "ranger": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Wisdom for 1 min/level."),
    S("Fox's Cunning", {"wizard": 2, "sorcerer": 2, "bard": 2}, "transmutation", "ally",
      "+4 enhancement bonus to Intelligence for 1 min/level."),
    S("Heroism", {"wizard": 3, "sorcerer": 3, "bard": 2}, "enchantment", "ally",
      "+2 morale bonus on attack rolls, saves and skill checks for 10 min/level.",
      desc_tags=["mind-affecting"]),
    S("Barkskin", {"druid": 2, "ranger": 2}, "transmutation", "ally",
      "+2 enhancement to natural armor (+1 per 3 levels above 3rd, max +5), 10 min/level."),
    S("Flaming Sphere", {"wizard": 2, "sorcerer": 2, "druid": 2}, "evocation", "enemy",
      "A rolling ball of fire hits a foe every round: 2d6 fire (Reflex negates), 1 round/"
      "level.", save=("ref", "negates"), desc_tags=["fire"]),
    S("Hold Animal", {"druid": 2, "ranger": 2}, "enchantment", "enemy",
      "An animal is paralyzed for 1 round/level (Will negates; new save each round).",
      save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    S("Sound Burst", {"cleric": 2, "bard": 2}, "evocation", "enemies",
      "Blast of sound on up to 4 foes: 1d8 sonic, and Fort save or stunned 1 round.",
      save=("fort", "partial"), desc_tags=["sonic"], max_targets=4),
    S("Remove Paralysis", {"cleric": 2, "paladin": 2}, "conjuration", "ally",
      "Frees a creature from paralysis and hold spells."),
    # 3rd
    S("Slow", {"wizard": 3, "sorcerer": 3, "bard": 3}, "transmutation", "enemies",
      "Up to 1 foe/level (max 6) is slowed: one action per turn, -1 attack, AC and Reflex, "
      "for 1 round/level (Will negates).", save=("will", "negates"), max_targets=6),
    S("Good Hope", {"bard": 3}, "enchantment", "allies",
      "Party: +2 morale bonus on attacks, damage, saves and skill checks for 1 min/level.",
      desc_tags=["mind-affecting"]),
    S("Displacement", {"wizard": 3, "sorcerer": 3, "bard": 3}, "illusion", "ally",
      "Attacks against the subject miss 50% of the time, 1 round/level."),
    S("Bestow Curse", {"cleric": 3, "wizard": 4, "sorcerer": 4}, "necromancy", "enemy",
      "Melee touch: -4 on attacks, saves and checks until removed (Will negates).",
      save=("will", "negates"), desc_tags=["curse"]),
    S("Fear", {"wizard": 4, "sorcerer": 4, "bard": 3}, "necromancy", "enemies",
      "Cone of terror on up to 4 foes: they flee in panic for 1 round/level (Will: shaken "
      "1 round instead).", save=("will", "partial"),
      desc_tags=["fear", "mind-affecting"], max_targets=4),
    S("Call Lightning", {"druid": 3}, "evocation", "enemy",
      "Call a 3d6 lightning bolt now (Reflex half), and another each round as a standard "
      "action: 1 bolt per level (max 10) over 1 min/level.", save=("ref", "half"),
      desc_tags=["electricity"]),
    S("Greater Magic Fang", {"druid": 3, "ranger": 3}, "transmutation", "ally",
      "Natural weapons and unarmed strikes get +1 per 4 levels (max +5) for 1 hour/level."),
    S("Poison", {"druid": 3, "cleric": 4}, "necromancy", "enemy",
      "Melee touch: 1d10 Constitution damage (Fort negates).", save=("fort", "negates"),
      desc_tags=["poison"]),
    S("Remove Disease", {"cleric": 3, "druid": 3, "ranger": 3}, "conjuration", "ally",
      "Cures all diseases the subject suffers from."),
    # 4th
    S("Cure Critical Wounds", {"cleric": 4, "bard": 4, "druid": 5}, "conjuration", "ally",
      "Cures 4d8 +1/level (max +20). Damages undead (Will half).", desc_tags=["healing"]),
    S("Freedom of Movement", {"cleric": 4, "bard": 4, "druid": 4, "ranger": 4}, "abjuration",
      "ally", "Frees the subject from paralysis, entangling and slow, and protects it from "
              "them (10 min/level)."),
    S("Restoration", {"cleric": 4, "paladin": 4}, "conjuration", "ally",
      "Heals all ability damage and removes fatigue and exhaustion."),
    S("Death Ward", {"cleric": 4, "druid": 5, "paladin": 4}, "necromancy", "ally",
      "Immunity to death spells and negative energy for 1 min/level."),
    S("Divine Power", {"cleric": 4}, "evocation", "self",
      "Attack as a fighter of your level, +6 Strength, and 1 temporary hp per level "
      "(1 round/level)."),
    S("Spell Immunity", {"cleric": 4}, "abjuration", "ally",
      "Simplified: +4 on saving throws against spells for 10 min/level."),
    S("Holy Smite", {"cleric_domain": 4}, "evocation", "enemies",
      "Holy power on up to 6 foes: evil ones take 1d8 per 2 levels (max 5d8) and are blinded "
      "1 round (Will half, not blinded); neutral ones take half; good ones are unharmed.",
      save=("will", "half"), desc_tags=["good"], max_targets=6),
    S("Hold Monster", {"wizard": 5, "sorcerer": 5, "bard": 4}, "enchantment", "enemy",
      "Any living creature is paralyzed for 1 round/level (Will negates; new save each "
      "round).", save=("will", "negates"), desc_tags=["mind-affecting", "compulsion"]),
    S("Shout", {"wizard": 4, "sorcerer": 4, "bard": 4}, "evocation", "enemies",
      "Deafening blast on up to 3 foes: 5d6 sonic (Fort half).", save=("fort", "half"),
      desc_tags=["sonic"], max_targets=3),
    S("Greater Invisibility", {"wizard": 4, "sorcerer": 4, "bard": 4}, "illusion", "ally",
      "Subject turns invisible even while attacking: +2 attack, foes miss 50% of the time "
      "(1 round/level)."),
    S("Ice Storm", {"wizard": 4, "sorcerer": 4, "druid": 4}, "evocation", "enemies",
      "Hail on up to 6 foes: 3d6 bludgeoning + 2d6 cold, no save.", desc_tags=["cold"],
      max_targets=6),
    S("Stoneskin", {"wizard": 4, "sorcerer": 4, "druid": 5}, "abjuration", "ally",
      "DR 10/adamantine until it has stopped 10 damage per level (max 150), 10 min/level."),
    S("Flame Strike", {"cleric": 5, "druid": 4}, "evocation", "enemies",
      "Divine fire on up to 3 foes: 1d6 per level (max 15d6), Reflex half.",
      save=("ref", "half"), desc_tags=["fire"], max_targets=3),
    # 5th
    S("Mass Cure Light Wounds", {"cleric": 5, "druid": 6, "bard": 5}, "conjuration", "allies",
      "Whole party: cures 1d8 +1/level (max +25).", desc_tags=["healing"]),
    S("Raise Dead", {"cleric": 5}, "conjuration", "ally",
      "Restores a dead ally to life (costs a 5,000 gp diamond; the raised hero loses half a "
      "level of experience). Out of combat only.", combat=False),
    S("Righteous Might", {"cleric": 5}, "transmutation", "self",
      "Grow to Large size: +4 Str, +4 Con, -2 Dex, +2 natural armor (1 round/level)."),
    S("Slay Living", {"cleric": 5}, "necromancy", "enemy",
      "Melee touch: the target dies (Fort save: 3d6 +1/level damage instead).",
      save=("fort", "partial"), desc_tags=["death"]),
    S("Dispel Evil", {"cleric": 5}, "abjuration", "self",
      "Simplified: +4 deflection AC and +4 on saves against evil creatures (1 round/level).",
      desc_tags=["good"]),
    S("Cone of Cold", {"wizard": 5, "sorcerer": 5}, "evocation", "enemies",
      "Cone of frost on up to 4 foes: 1d6 per level (max 15d6) cold, Reflex half.",
      save=("ref", "half"), desc_tags=["cold"], max_targets=4),
    S("Waves of Fatigue", {"wizard": 5, "sorcerer": 5}, "necromancy", "enemies",
      "Up to 4 living foes in a cone become fatigued (-2 Str and Dex), no save.",
      max_targets=4),
    S("Call Lightning Storm", {"druid": 5}, "evocation", "enemy",
      "As call lightning, but 5d6 per bolt and up to 15 bolts.", save=("ref", "half"),
      desc_tags=["electricity"]),
    # ---------------------------------------------------------------- added in v3
    S("Dispel Magic", {"wizard": 3, "sorcerer": 3, "cleric": 3, "bard": 3, "druid": 4,
                       "paladin": 3}, "abjuration", "creature",
      "Dispel check (d20 + caster level, max +10) vs 11 + caster level ends spells on one "
      "creature: an enemy's buffs or summons, or a hostile spell on a friend.", sr=False),
    S("Invisibility", {"wizard": 2, "sorcerer": 2, "bard": 2}, "illusion", "ally",
      "Subject turns invisible: +2 on its next attack, foes miss it 50% of the time. Ends "
      "when it attacks (1 min/level)."),
    S("Fly", {"wizard": 3, "sorcerer": 3}, "transmutation", "ally",
      "Subject flies for 1 min/level: it can reach flying foes and doesn't need to touch "
      "the ground."),
    S("Cause Fear", {"wizard": 1, "sorcerer": 1, "bard": 1, "cleric": 1}, "necromancy",
      "enemy", "A foe of 5 HD or less flees in fear for 1d4 rounds (Will: shaken 1 round).",
      save=("will", "partial"), desc_tags=["fear", "mind-affecting"]),
    S("Endure Elements", {"cleric": 1, "druid": 1, "paladin": 1, "ranger": 1, "wizard": 1,
                          "sorcerer": 1}, "abjuration", "ally",
      "Comfortable in any heat or cold for 24 hours.", combat=False),
    S("Entropic Shield", {"cleric": 1}, "abjuration", "self",
      "Ranged attacks against you miss 20% of the time (1 min/level)."),
    S("Shatter", {"cleric": 2, "wizard": 2, "sorcerer": 2, "bard": 2}, "evocation", "enemy",
      "Shatters a foe's nonmagical weapon (Will negates for the wielder).",
      save=("will", "negates"), desc_tags=["sonic"]),
    S("Inflict Serious Wounds", {"cleric": 3}, "necromancy", "enemy",
      "Melee touch: 3d8 +1/level (max +15) damage (Will half).", save=("will", "half")),
    S("Inflict Critical Wounds", {"cleric": 4}, "necromancy", "enemy",
      "Melee touch: 4d8 +1/level (max +20) damage (Will half).", save=("will", "half")),
    S("Protection from Energy", {"cleric": 3, "druid": 3, "ranger": 2, "wizard": 3,
                                 "sorcerer": 3}, "abjuration", "ally",
      "Absorbs up to 12 points of fire damage per level (max 120), 10 min/level."),
    S("Contagion", {"cleric": 3, "druid": 3, "wizard": 4, "sorcerer": 4}, "necromancy",
      "enemy", "Melee touch: a wasting disease deals 1d6 Constitution damage now and more each "
               "day (Fort negates).", save=("fort", "negates"), desc_tags=["disease"]),
    S("Animate Dead", {"cleric": 3, "wizard": 4, "sorcerer": 4}, "necromancy", "summon",
      "Raise a skeleton or zombie (one per 2 levels, up to 4) to fight for you this battle.",
      sr=False, desc_tags=["evil"]),
    S("Fire Shield", {"wizard": 4, "sorcerer": 4}, "evocation", "self",
      "Flames wreathe you: anyone who hits you in melee takes 1d6 +1/level (max +15) fire "
      "(1 round/level)."),
    S("Confusion", {"wizard": 4, "sorcerer": 4, "bard": 3}, "enchantment", "enemies",
      "Up to 4 foes become confused for 1 round/level: each turn they may babble, wander off, "
      "or attack whoever is nearest (Will negates).", save=("will", "negates"),
      desc_tags=["mind-affecting", "compulsion"], max_targets=4),
    # ---------------------------------------------------------------- 5th-9th level (v4)
    S("Greater Heroism", {"bard": 5, "wizard": 6, "sorcerer": 6}, "enchantment", "ally",
      "+4 morale on attacks, saves and skills, immunity to fear, and temporary hp equal to "
      "your caster level (max 20), 1 min/level.", desc_tags=["mind-affecting"]),
    S("Song of Discord", {"bard": 5}, "enchantment", "enemies",
      "Up to 4 foes turn on each other (Will negates) for 1 round/level.",
      save=("will", "negates"), desc_tags=["mind-affecting", "sonic"], max_targets=4),
    S("Greater Dispel Magic", {"bard": 5, "cleric": 6, "druid": 6, "wizard": 6,
                               "sorcerer": 6}, "abjuration", "creature",
      "Like dispel magic, but the check is d20 + caster level (max +20), and it tries every "
      "spell on the target.", sr=False),
    S("Mass Cure Moderate Wounds", {"bard": 6, "cleric": 6, "druid": 7}, "conjuration",
      "allies", "Whole party: cures 2d8 +1/level (max +30).", desc_tags=["healing"]),
    S("Heroes' Feast", {"bard": 6, "cleric": 6}, "conjuration", "allies",
      "A magical feast: the party gains 1d8 + half your level temporary hp, +1 morale on "
      "attacks and Will saves, and immunity to fear and poison for 12 hours.", combat=False),
    S("Mass Bull's Strength", {"wizard": 6, "sorcerer": 6, "cleric": 6, "druid": 6},
      "transmutation", "allies", "Party: +4 Strength for 1 min/level."),
    S("Mass Cat's Grace", {"wizard": 6, "sorcerer": 6, "bard": 6, "druid": 6},
      "transmutation", "allies", "Party: +4 Dexterity for 1 min/level."),
    S("Mass Bear's Endurance", {"wizard": 6, "sorcerer": 6, "cleric": 6, "druid": 6},
      "transmutation", "allies", "Party: +4 Constitution for 1 min/level."),
    S("Mass Owl's Wisdom", {"wizard": 6, "sorcerer": 6, "cleric": 6, "druid": 6},
      "transmutation", "allies", "Party: +4 Wisdom for 1 min/level."),
    S("Mass Eagle's Splendor", {"wizard": 6, "sorcerer": 6, "bard": 6, "cleric": 6},
      "transmutation", "allies", "Party: +4 Charisma for 1 min/level."),
    S("Chain Lightning", {"wizard": 6, "sorcerer": 6}, "evocation", "enemies",
      "Lightning arcs to up to 1 foe per level (max 8 here): 1d6 per level (max 20d6) to "
      "the first, half that to the others (Reflex half).", save=("ref", "half"),
      desc_tags=["electricity"], max_targets=8),
    S("Disintegrate", {"wizard": 6, "sorcerer": 6}, "transmutation", "enemy",
      "Ranged touch: 2d6 per level (max 40d6); a creature reduced to 0 hp is turned to dust "
      "(Fort: 5d6 instead).", save=("fort", "partial")),
    S("Globe of Invulnerability", {"wizard": 6, "sorcerer": 6}, "abjuration", "self",
      "Simplified: immune to enemy spells of 4th level or lower (1 round/level)."),
    S("Heal", {"cleric": 6, "druid": 7}, "conjuration", "ally",
      "Heals 10 hp per level (max 150) and cures ability damage, disease, fatigue, "
      "confusion, blindness and similar ills. Deals the same to undead (Will half).",
      desc_tags=["healing"]),
    S("Harm", {"cleric": 6}, "necromancy", "enemy",
      "Melee touch: 10 damage per level (max 150), but can't drop the target below 1 hp "
      "(Will half).", save=("will", "half")),
    S("Blade Barrier", {"cleric": 6}, "evocation", "enemies",
      "A wall of whirling blades cuts up to 4 foes: 1d6 per level (max 15d6), Reflex half.",
      save=("ref", "half"), sr=True, max_targets=4),
    S("Delayed Blast Fireball", {"wizard": 7, "sorcerer": 7}, "evocation", "enemies",
      "As fireball, but 1d6 per level (max 20d6).", save=("ref", "half"),
      desc_tags=["fire"], max_targets=8),
    S("Finger of Death", {"wizard": 7, "sorcerer": 7, "druid": 8}, "necromancy", "enemy",
      "The target dies (Fort save: 3d6 +1/level damage instead).", save=("fort", "partial"),
      desc_tags=["death"]),
    S("Power Word Blind", {"wizard": 7, "sorcerer": 7}, "enchantment", "enemy",
      "A creature with 200 hp or less is blinded (no save).", sr=True,
      desc_tags=["mind-affecting"]),
    S("Mordenkainen's Sword", {"wizard": 7, "sorcerer": 7}, "evocation", "enemy",
      "A blade of force attacks a foe every round (your level + 3 + Int, 4d6+3, crit 19-20) "
      "for 1 round/level.", sr=False, desc_tags=["force"]),
    S("Destruction", {"cleric": 7}, "necromancy", "enemy",
      "The target is slain and turned to ash (Fort save: 10d6 damage instead).",
      save=("fort", "partial"), desc_tags=["death"]),
    S("Holy Word", {"cleric_domain": 7, "cleric": 7}, "evocation", "enemies",
      "Evil foes are struck by a word of power: by Hit Dice they are deafened, blinded, "
      "paralyzed or killed (no save).", desc_tags=["good", "sonic"], max_targets=8),
    S("Mass Cure Serious Wounds", {"cleric": 7, "druid": 8}, "conjuration", "allies",
      "Whole party: cures 3d8 +1/level (max +35).", desc_tags=["healing"]),
    S("Resurrection", {"cleric": 7}, "conjuration", "ally",
      "Restores a dead ally to full health (10,000 gp diamond; the hero loses a quarter level "
      "of experience). Out of combat only.", combat=False),
    S("Fire Storm", {"cleric": 8, "druid": 7}, "evocation", "enemies",
      "A sheet of roaring flame on up to 6 foes: 1d6 per level (max 20d6), Reflex half.",
      save=("ref", "half"), desc_tags=["fire"], max_targets=6),
    S("Creeping Doom", {"druid": 7}, "conjuration", "enemies",
      "A carpet of biting insects swarms up to 4 foes: 2d6 a round for 1 round per level.",
      sr=False, max_targets=4),
    S("Sunbeam", {"druid": 7}, "evocation", "enemies",
      "Beams of sunlight: 4d6 (undead: 1d6 per level, max 20d6) and blinded on a failed "
      "Reflex save, to up to 4 foes.", save=("ref", "half"), desc_tags=["light"],
      max_targets=4),
    S("Horrid Wilting", {"wizard": 8, "sorcerer": 8}, "necromancy", "enemies",
      "Drains the water from up to 6 living foes: 1d6 per level (max 20d6), Fort half.",
      save=("fort", "half"), max_targets=6),
    S("Polar Ray", {"wizard": 8, "sorcerer": 8}, "evocation", "enemy",
      "Ranged touch: 1d6 per level (max 25d6) cold.", desc_tags=["cold"]),
    S("Power Word Stun", {"wizard": 8, "sorcerer": 8}, "enchantment", "enemy",
      "A creature with 150 hp or less is stunned (4d4 rounds under 50 hp, 2d4 under 100, "
      "1d4 under 150; no save).", desc_tags=["mind-affecting"]),
    S("Sunburst", {"wizard": 8, "sorcerer": 8, "druid": 8}, "evocation", "enemies",
      "A globe of searing light on up to 6 foes: 6d6 (undead 1d6 per level, max 25d6) and "
      "blinded (Reflex half and not blinded).", save=("ref", "half"), desc_tags=["light"],
      max_targets=6),
    S("Holy Aura", {"cleric": 8}, "abjuration", "allies",
      "Party: +4 deflection AC and +4 resistance on saves, spell resistance 25 against evil "
      "spells (simplified: +4 vs evil), 1 round/level.", desc_tags=["good"]),
    S("Mass Cure Critical Wounds", {"cleric": 8, "druid": 9}, "conjuration", "allies",
      "Whole party: cures 4d8 +1/level (max +40).", desc_tags=["healing"]),
    S("Meteor Swarm", {"wizard": 9, "sorcerer": 9}, "evocation", "enemies",
      "Four meteors: each foe struck takes 2d6 bludgeoning and 6d6 fire (Reflex half the "
      "fire); up to 4 foes.", save=("ref", "half"), desc_tags=["fire"], max_targets=4),
    S("Power Word Kill", {"wizard": 9, "sorcerer": 9}, "enchantment", "enemy",
      "A creature with 100 hp or less dies (no save).", desc_tags=["death", "mind-affecting"]),
    S("Wail of the Banshee", {"wizard": 9, "sorcerer": 9}, "necromancy", "enemies",
      "A deadly scream: up to 1 living foe per level (max 8 here) must make a Fortitude save "
      "or die.", save=("fort", "negates"), desc_tags=["death", "sonic"], max_targets=8),
    S("Mass Hold Monster", {"wizard": 9, "sorcerer": 9}, "enchantment", "enemies",
      "As hold monster on up to 6 foes.", save=("will", "negates"),
      desc_tags=["mind-affecting", "compulsion"], max_targets=6),
    S("Implosion", {"cleric": 9}, "evocation", "enemy",
      "A creature collapses in on itself and dies (Fort negates).", save=("fort", "negates"),
      desc_tags=["death"]),
    S("Mass Heal", {"cleric": 9}, "conjuration", "allies",
      "As heal, on the whole party.", desc_tags=["healing"]),
    S("True Resurrection", {"cleric": 9}, "conjuration", "ally",
      "Returns a dead ally to life with no loss of experience (25,000 gp diamond). Out of "
      "combat only.", combat=False),
    S("Storm of Vengeance", {"druid": 9, "cleric_domain": 9}, "conjuration", "enemies",
      "A storm cloud batters up to 8 foes: acid rain 1d6, then lightning 10d6 (Reflex half), "
      "then hail 5d6.", save=("ref", "half"), desc_tags=["electricity"], max_targets=8),
    S("Elemental Swarm", {"druid": 9}, "conjuration", "summon",
      "Summon three Large elementals to fight for you for 10 minutes per level.", sr=False),
]}

for _n, _r in [(6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX")]:
    SPELLS[f"Summon Monster {_r}"] = S(
        f"Summon Monster {_r}", {"wizard": _n, "sorcerer": _n, "cleric": _n,
                                 **({"bard": 6} if _n == 6 else {})},
        "conjuration", "summon",
        f"Call a creature from another plane to fight for you for 1 round/level "
        f"(level {_n} list).", sr=False)
    SPELLS[f"Summon Nature's Ally {_r}"] = S(
        f"Summon Nature's Ally {_r}", {"druid": _n}, "conjuration", "summon",
        f"Call a wild creature to fight for you for 1 round/level (level {_n} list).", sr=False)

# paladin and ranger spells for levels 11-20
for _name, _cls, _lvl in [("Prayer", "paladin", 3), ("Magic Circle against Evil", "paladin", 3),
                          ("Dispel Magic", "paladin", 3), ("Dispel Evil", "paladin", 4),
                          ("Cure Serious Wounds", "ranger", 4), ("Freedom of Movement",
                                                                  "paladin", 4)]:
    SPELLS[_name]["levels"].setdefault(_cls, _lvl)

for _n, _r in enumerate(["I", "II", "III", "IV", "V"], 1):
    SPELLS[f"Summon Monster {_r}"] = S(
        f"Summon Monster {_r}", {"wizard": _n, "sorcerer": _n, "cleric": _n, "bard": _n},
        "conjuration", "summon",
        f"Call a creature from another plane to fight for you for 1 round/level "
        f"(level {_n} list).", sr=False)
    SPELLS[f"Summon Nature's Ally {_r}"] = S(
        f"Summon Nature's Ally {_r}", {"druid": _n, "ranger": _n}, "conjuration", "summon",
        f"Call a wild animal to fight for you for 1 round/level (level {_n} list). Druids "
        f"can swap any prepared spell for this.", sr=False)


def spells_for(cls: str, level: int):
    return sorted(n for n, s in SPELLS.items() if s["levels"].get(cls) == level)
