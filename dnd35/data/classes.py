"""Character classes (SRD 3.5), levels 1-10."""

from .skills import KNOWLEDGES

ALL_KNOWLEDGE = [f"Knowledge ({k})" for k in KNOWLEDGES]

# spells per day by class level: list index = spell level; None = can't cast that level yet
CLERIC_DAY = {1: [3, 1], 2: [4, 2], 3: [4, 2, 1], 4: [5, 3, 2], 5: [5, 3, 2, 1],
              6: [5, 3, 3, 2], 7: [6, 4, 3, 2, 1], 8: [6, 4, 3, 3, 2], 9: [6, 4, 4, 3, 2, 1],
              10: [6, 4, 4, 3, 3, 2]}
WIZARD_DAY = {1: [3, 1], 2: [4, 2], 3: [4, 2, 1], 4: [4, 3, 2], 5: [4, 3, 2, 1],
              6: [4, 3, 3, 2], 7: [4, 4, 3, 2, 1], 8: [4, 4, 3, 3, 2], 9: [4, 4, 4, 3, 2, 1],
              10: [4, 4, 4, 3, 3, 2]}
SORC_DAY = {1: [5, 3], 2: [6, 4], 3: [6, 5], 4: [6, 6, 3], 5: [6, 6, 4], 6: [6, 6, 5, 3],
            7: [6, 6, 6, 4], 8: [6, 6, 6, 5, 3], 9: [6, 6, 6, 6, 4], 10: [6, 6, 6, 6, 5, 3]}
SORC_KNOWN = {1: [4, 2], 2: [5, 2], 3: [5, 3], 4: [6, 3, 1], 5: [6, 4, 2], 6: [7, 4, 2, 1],
              7: [7, 5, 3, 2], 8: [8, 5, 3, 2, 1], 9: [8, 5, 4, 3, 2], 10: [9, 5, 4, 3, 2, 1]}
BARD_DAY = {1: [2], 2: [3, 0], 3: [3, 1], 4: [3, 2, 0], 5: [3, 3, 1], 6: [3, 3, 2],
            7: [3, 3, 2, 0], 8: [3, 3, 3, 1], 9: [3, 3, 3, 2], 10: [3, 3, 3, 2, 0]}
BARD_KNOWN = {1: [4], 2: [5, 2], 3: [6, 3], 4: [6, 3, 2], 5: [6, 4, 3], 6: [6, 4, 3],
              7: [6, 4, 4, 2], 8: [6, 4, 4, 3], 9: [6, 4, 4, 3], 10: [6, 4, 4, 4, 2]}
HALF_CASTER_DAY = {4: [None, 0], 5: [None, 0], 6: [None, 1], 7: [None, 1], 8: [None, 1, 0],
                   9: [None, 1, 0], 10: [None, 1, 1]}

CLASSES = {
    "barbarian": {
        "name": "Barbarian", "hd": 12, "bab": "good", "good_saves": ["fort"],
        "skill_points": 4, "gold": "4d4x10",
        "class_skills": ["Climb", "Craft", "Handle Animal", "Intimidate", "Jump", "Listen",
                         "Ride", "Survival", "Swim"],
        "weapon_prof": ["simple", "martial"], "armor_prof": ["light", "medium", "shields"],
        "alignment": "nonlawful",
        "features": {
            1: ["Fast Movement (+10 ft.)", "Illiteracy", "Rage 1/day"],
            2: ["Uncanny Dodge"], 3: ["Trap Sense +1"], 4: ["Rage 2/day"],
            5: ["Improved Uncanny Dodge"], 6: ["Trap Sense +2"], 7: ["Damage Reduction 1/-"],
            8: ["Rage 3/day"], 9: ["Trap Sense +3"], 10: ["Damage Reduction 2/-"],
        },
        "description": "A ferocious warrior who channels fury into raw power. High hit points, "
                       "rage for big damage.",
    },
    "bard": {
        "name": "Bard", "hd": 6, "bab": "average", "good_saves": ["ref", "will"],
        "skill_points": 6, "gold": "4d4x10",
        "class_skills": ["Appraise", "Balance", "Bluff", "Climb", "Concentration", "Craft",
                         "Decipher Script", "Diplomacy", "Disguise", "Escape Artist",
                         "Gather Information", "Hide", "Jump", "Listen", "Move Silently",
                         "Perform", "Profession", "Sense Motive", "Sleight of Hand",
                         "Spellcraft", "Swim", "Tumble", "Use Magic Device"] + ALL_KNOWLEDGE,
        "weapon_prof": ["simple", "longsword", "rapier", "sap", "short sword", "shortbow",
                        "whip"],
        "armor_prof": ["light", "shields"], "alignment": "nonlawful",
        "caster": "arcane", "cast_ability": "cha", "prepared": False,
        "light_armor_casting": True,
        "spells_per_day": BARD_DAY, "spells_known": BARD_KNOWN,
        "features": {
            1: ["Bardic Music (inspire courage +1)", "Bardic Knowledge", "Countersong",
                "Fascinate"],
            3: ["Inspire Competence"], 6: ["Suggestion (flavor)"],
            8: ["Inspire Courage +2"], 9: ["Inspire Greatness (flavor)"],
        },
        "description": "Jack of all trades: songs that inspire the party, healing and "
                       "charm magic, lots of skills.",
    },
    "cleric": {
        "name": "Cleric", "hd": 8, "bab": "average", "good_saves": ["fort", "will"],
        "skill_points": 2, "gold": "5d4x10",
        "class_skills": ["Concentration", "Craft", "Diplomacy", "Heal",
                         "Knowledge (arcana)", "Knowledge (history)", "Knowledge (religion)",
                         "Knowledge (the planes)", "Profession", "Spellcraft"],
        "weapon_prof": ["simple"], "armor_prof": ["light", "medium", "heavy", "shields"],
        "caster": "divine", "cast_ability": "wis", "prepared": True,
        "spells_per_day": CLERIC_DAY,
        "features": {
            1: ["Aura", "Spells", "Domains (2)", "Spontaneous Casting", "Turn Undead"],
        },
        "description": "A divine champion: heals allies, armored, turns undead, solid melee.",
    },
    "druid": {
        "name": "Druid", "hd": 8, "bab": "average", "good_saves": ["fort", "will"],
        "skill_points": 4, "gold": "2d4x10",
        "class_skills": ["Concentration", "Craft", "Diplomacy", "Handle Animal", "Heal",
                         "Knowledge (nature)", "Listen", "Profession", "Ride", "Spellcraft",
                         "Spot", "Survival", "Swim"],
        "weapon_prof": ["club", "dagger", "quarterstaff", "scimitar", "sickle", "shortspear",
                        "sling", "spear"],
        "armor_prof": ["light", "medium", "shields"], "alignment": "neutral",
        "no_metal_armor": True,
        "caster": "divine", "cast_ability": "wis", "prepared": True,
        "spells_per_day": CLERIC_DAY,
        "features": {
            1: ["Animal Companion", "Nature Sense", "Wild Empathy"],
            2: ["Woodland Stride"], 3: ["Trackless Step"], 4: ["Resist Nature's Lure"],
            5: ["Wild Shape 1/day"], 6: ["Wild Shape 2/day"], 7: ["Wild Shape 3/day"],
            8: ["Wild Shape (Large forms)"], 9: ["Venom Immunity"], 10: ["Wild Shape 4/day"],
        },
        "description": "Nature priest: healing and storm magic, an animal friend, and at 5th "
                       "level turns into beasts.",
    },
    "fighter": {
        "name": "Fighter", "hd": 10, "bab": "good", "good_saves": ["fort"],
        "skill_points": 2, "gold": "6d4x10",
        "class_skills": ["Climb", "Craft", "Handle Animal", "Intimidate", "Jump", "Ride",
                         "Swim"],
        "weapon_prof": ["simple", "martial"],
        "armor_prof": ["light", "medium", "heavy", "shields", "tower"],
        "bonus_feat_levels": [1, 2, 4, 6, 8, 10],
        "features": {1: ["Bonus Feat"], 2: ["Bonus Feat"], 4: ["Bonus Feat"],
                     6: ["Bonus Feat"], 8: ["Bonus Feat"], 10: ["Bonus Feat"]},
        "description": "Master of arms and armor. The most feats, the best armor, great "
                       "attack bonus.",
    },
    "monk": {
        "name": "Monk", "hd": 8, "bab": "average", "good_saves": ["fort", "ref", "will"],
        "skill_points": 4, "gold": "5d4",
        "class_skills": ["Balance", "Climb", "Concentration", "Craft", "Diplomacy",
                         "Escape Artist", "Hide", "Jump", "Knowledge (arcana)",
                         "Knowledge (religion)", "Listen", "Move Silently", "Perform",
                         "Profession", "Sense Motive", "Spot", "Swim", "Tumble"],
        "weapon_prof": ["club", "light crossbow", "heavy crossbow", "dagger", "handaxe",
                        "javelin", "kama", "nunchaku", "quarterstaff", "siangham", "sling",
                        "unarmed strike"],
        "armor_prof": [], "alignment": "lawful",
        "bonus_feat_levels": [1, 2, 6],
        "features": {
            1: ["AC Bonus (Wis)", "Flurry of Blows", "Unarmed Strike", "Bonus Feat"],
            2: ["Bonus Feat", "Evasion"], 3: ["Fast Movement +10", "Still Mind"],
            4: ["Ki Strike (magic)", "Slow Fall (flavor)"], 5: ["Purity of Body"],
            6: ["Bonus Feat", "Fast Movement +20"], 7: ["Wholeness of Body"],
            9: ["Improved Evasion", "Fast Movement +30"], 10: ["Ki Strike (lawful)"],
        },
        "description": "Unarmed martial artist: fast, hard to hit, flurries of blows, "
                       "great saves. No armor.",
    },
    "paladin": {
        "name": "Paladin", "hd": 10, "bab": "good", "good_saves": ["fort"],
        "skill_points": 2, "gold": "6d4x10",
        "class_skills": ["Concentration", "Craft", "Diplomacy", "Handle Animal", "Heal",
                         "Knowledge (nobility and royalty)", "Knowledge (religion)",
                         "Profession", "Ride", "Sense Motive"],
        "weapon_prof": ["simple", "martial"],
        "armor_prof": ["light", "medium", "heavy", "shields"],
        "alignment": "lawful good",
        "caster": "divine", "cast_ability": "wis", "prepared": True, "caster_level_half": True,
        "spells_per_day": HALF_CASTER_DAY,
        "features": {
            1: ["Aura of Good", "Detect Evil", "Smite Evil 1/day"],
            2: ["Divine Grace (Cha to saves)", "Lay on Hands"],
            3: ["Aura of Courage (immune to fear)", "Divine Health (immune to disease)"],
            4: ["Turn Undead", "Spells"], 5: ["Smite Evil 2/day", "Special Mount (flavor)"],
            6: ["Remove Disease 1/week"], 9: ["Remove Disease 2/week"],
            10: ["Smite Evil 3/day"],
        },
        "description": "Holy warrior: heavy armor, smites evil, heals with a touch, shrugs "
                       "off fear and disease.",
    },
    "ranger": {
        "name": "Ranger", "hd": 8, "bab": "good", "good_saves": ["fort", "ref"],
        "skill_points": 6, "gold": "6d4x10",
        "class_skills": ["Climb", "Concentration", "Craft", "Handle Animal", "Heal", "Hide",
                         "Jump", "Knowledge (dungeoneering)", "Knowledge (geography)",
                         "Knowledge (nature)", "Listen", "Move Silently", "Profession", "Ride",
                         "Search", "Spot", "Survival", "Swim", "Use Rope"],
        "weapon_prof": ["simple", "martial"], "armor_prof": ["light", "shields"],
        "caster": "divine", "cast_ability": "wis", "prepared": True, "caster_level_half": True,
        "spells_per_day": HALF_CASTER_DAY,
        "features": {
            1: ["1st Favored Enemy", "Track", "Wild Empathy"],
            2: ["Combat Style"], 3: ["Endurance"],
            4: ["Animal Companion", "Spells"], 5: ["2nd Favored Enemy"],
            6: ["Improved Combat Style"], 7: ["Woodland Stride"], 8: ["Swift Tracker"],
            9: ["Evasion"], 10: ["3rd Favored Enemy"],
        },
        "description": "Skilled hunter and tracker. Favored enemies, two-weapon or archery "
                       "style, great at skills.",
    },
    "rogue": {
        "name": "Rogue", "hd": 6, "bab": "average", "good_saves": ["ref"],
        "skill_points": 8, "gold": "5d4x10",
        "class_skills": ["Appraise", "Balance", "Bluff", "Climb", "Craft", "Decipher Script",
                         "Diplomacy", "Disable Device", "Disguise", "Escape Artist", "Forgery",
                         "Gather Information", "Hide", "Intimidate", "Jump",
                         "Knowledge (local)", "Listen", "Move Silently", "Open Lock", "Perform",
                         "Profession", "Search", "Sense Motive", "Sleight of Hand", "Spot",
                         "Swim", "Tumble", "Use Magic Device", "Use Rope"],
        "weapon_prof": ["simple", "hand crossbow", "rapier", "sap", "shortbow", "short sword"],
        "armor_prof": ["light"],
        "features": {
            1: ["Sneak Attack +1d6", "Trapfinding"], 2: ["Evasion"],
            3: ["Sneak Attack +2d6", "Trap Sense +1"], 4: ["Uncanny Dodge"],
            5: ["Sneak Attack +3d6"], 6: ["Trap Sense +2"], 7: ["Sneak Attack +4d6"],
            8: ["Improved Uncanny Dodge"], 9: ["Sneak Attack +5d6", "Trap Sense +3"],
            10: ["Special Ability: Improved Evasion"],
        },
        "description": "Skill expert and backstabber: sneak attack, traps, locks, stealth.",
    },
    "sorcerer": {
        "name": "Sorcerer", "hd": 4, "bab": "poor", "good_saves": ["will"],
        "skill_points": 2, "gold": "3d4x10",
        "class_skills": ["Bluff", "Concentration", "Craft", "Knowledge (arcana)", "Profession",
                         "Spellcraft"],
        "weapon_prof": ["simple"], "armor_prof": [],
        "caster": "arcane", "cast_ability": "cha", "prepared": False,
        "spells_per_day": SORC_DAY, "spells_known": SORC_KNOWN,
        "features": {1: ["Familiar", "Spells"]},
        "description": "Innate arcane caster: fewer spells known, but casts them flexibly and "
                       "more often.",
    },
    "wizard": {
        "name": "Wizard", "hd": 4, "bab": "poor", "good_saves": ["will"],
        "skill_points": 2, "gold": "3d4x10",
        "class_skills": ["Concentration", "Craft", "Decipher Script", "Profession",
                         "Spellcraft"] + ALL_KNOWLEDGE,
        "weapon_prof": ["club", "dagger", "heavy crossbow", "light crossbow", "quarterstaff"],
        "armor_prof": [],
        "caster": "arcane", "cast_ability": "int", "prepared": True,
        "spells_per_day": WIZARD_DAY,
        "bonus_feat_levels": [5, 10],
        "features": {1: ["Scribe Scroll", "Familiar", "Spellbook"],
                     5: ["Bonus Feat (metamagic/item creation)"],
                     10: ["Bonus Feat (metamagic/item creation)"]},
        "description": "Scholar of arcane magic. Fragile, but the widest choice of spells.",
    },
}

CLASS_ORDER = ["barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger",
               "rogue", "sorcerer", "wizard"]

ALIGNMENTS = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral",
              "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]


def alignment_allowed(cls: str, alignment: str) -> bool:
    rule = CLASSES[cls].get("alignment", "any")
    if rule == "nonlawful":
        return not alignment.startswith("Lawful")
    if rule == "lawful":
        return alignment.startswith("Lawful")
    if rule == "lawful good":
        return alignment == "Lawful Good"
    if rule == "neutral":
        return "Neutral" in alignment
    return True


def _deity(align, domains, weapon, portfolio):
    return {"alignment": align, "domains": domains, "weapon": weapon, "portfolio": portfolio}


DEITIES = {
    "Boccob": _deity("True Neutral", ["Knowledge", "Magic", "Trickery"], "quarterstaff",
                     "magic, arcane knowledge, foresight"),
    "Corellon Larethian": _deity("Chaotic Good", ["Chaos", "Good", "Protection", "War"],
                                 "longsword", "elves, magic, music, arts"),
    "Ehlonna": _deity("Neutral Good", ["Animal", "Good", "Plant", "Sun"], "longsword",
                      "woodlands, forest creatures, fertility"),
    "Erythnul": _deity("Chaotic Evil", ["Chaos", "Evil", "Trickery", "War"], "morningstar",
                       "hate, envy, malice, panic, slaughter"),
    "Fharlanghn": _deity("True Neutral", ["Luck", "Protection", "Travel"], "quarterstaff",
                         "horizons, distance, travel, roads"),
    "Garl Glittergold": _deity("Neutral Good", ["Good", "Protection", "Trickery"],
                               "battleaxe", "gnomes, protection, humor, gemcutting"),
    "Gruumsh": _deity("Chaotic Evil", ["Chaos", "Evil", "Strength", "War"], "spear",
                      "orcs, conquest, survival, territory"),
    "Heironeous": _deity("Lawful Good", ["Good", "Law", "War"], "longsword",
                         "valor, chivalry, justice, honor"),
    "Hextor": _deity("Lawful Evil", ["Destruction", "Evil", "Law", "War"], "flail",
                     "tyranny, war, discord, massacres"),
    "Kord": _deity("Chaotic Good", ["Chaos", "Good", "Luck", "Strength"], "greatsword",
                   "athletics, sport, brawling, courage"),
    "Moradin": _deity("Lawful Good", ["Earth", "Good", "Law", "Protection"], "warhammer",
                      "dwarves, creation, smithing, protection"),
    "Nerull": _deity("Neutral Evil", ["Death", "Evil", "Trickery"], "scythe",
                     "death, darkness, murder, the underworld"),
    "Obad-Hai": _deity("True Neutral", ["Air", "Animal", "Earth", "Fire", "Plant", "Water"],
                       "quarterstaff", "nature, woodlands, freedom, hunting, beasts"),
    "Olidammara": _deity("Chaotic Neutral", ["Chaos", "Luck", "Trickery"], "rapier",
                         "music, revels, wine, rogues, humor, tricks"),
    "Pelor": _deity("Neutral Good", ["Good", "Healing", "Strength", "Sun"], "heavy mace",
                    "the sun, light, strength, healing"),
    "St. Cuthbert": _deity("Lawful Neutral", ["Destruction", "Law", "Protection", "Strength"],
                           "heavy mace", "retribution, common sense, wisdom, zeal"),
    "Vecna": _deity("Neutral Evil", ["Evil", "Knowledge", "Magic"], "dagger",
                    "destructive and evil secrets"),
    "Wee Jas": _deity("Lawful Neutral", ["Death", "Law", "Magic"], "dagger",
                      "death, magic, vanity, law"),
    "Yondalla": _deity("Lawful Good", ["Good", "Law", "Protection"], "short sword",
                       "halflings, protection, fertility"),
}


def _dom(power, spells, **kw):
    d = {"power": power, "spells": dict(enumerate(spells, 1))}
    d.update(kw)
    return d


# Domain spells use this game's closest spell where the SRD one isn't implemented.
DOMAINS = {
    "Good": _dom("Cast good spells at +1 caster level.",
                 ["Protection from Evil", "Aid", "Magic Circle against Evil", "Holy Smite",
                  "Dispel Evil"], forbid="Evil", cl_tag="good"),
    "Healing": _dom("Cast healing (conjuration) spells at +1 caster level.",
                    ["Cure Light Wounds", "Cure Moderate Wounds", "Cure Serious Wounds",
                     "Cure Critical Wounds", "Mass Cure Light Wounds"]),
    "Strength": _dom("Feat of Strength: once per day, gain an enhancement bonus to Strength "
                     "equal to your cleric level for 1 round.",
                     ["Enlarge Person", "Bull's Strength", "Magic Vestment", "Spell Immunity",
                      "Righteous Might"]),
    "War": _dom("Free Martial Weapon Proficiency and Weapon Focus with your deity's favored "
                "weapon.", ["Magic Weapon", "Spiritual Weapon", "Magic Vestment",
                            "Divine Power", "Flame Strike"]),
    "Animal": _dom("Knowledge (nature) is a class skill; you can speak with animals.",
                   ["Magic Fang", "Hold Animal", "Greater Magic Fang",
                    "Summon Nature's Ally IV", "Summon Nature's Ally V"],
                   skills=["Knowledge (nature)"]),
    "Chaos": _dom("Cast chaos spells at +1 caster level.",
                  ["Protection from Evil", "Shatter", "Magic Circle against Evil", "Confusion",
                   "Dispel Magic"], forbid="Law"),
    "Death": _dom("Death touch, once per day: touch a living foe and roll 1d6 per cleric "
                  "level. If the total is at least its current hit points, it dies.",
                  ["Cause Fear", "Inflict Moderate Wounds", "Animate Dead", "Death Ward",
                   "Slay Living"], use="death_touch"),
    "Destruction": _dom("Smite, once per day: +4 on one melee attack and + cleric level "
                        "damage.", ["Inflict Light Wounds", "Shatter", "Contagion",
                                    "Inflict Critical Wounds", "Shout"], use="dsmite"),
    "Evil": _dom("Cast evil spells at +1 caster level.",
                 ["Cause Fear", "Hold Person", "Bestow Curse", "Poison", "Slay Living"],
                 forbid="Good", cl_tag="evil"),
    "Fire": _dom("Turn or destroy water creatures; rebuke fire creatures (flavor).",
                 ["Burning Hands", "Produce Flame", "Protection from Energy", "Fire Shield",
                  "Flame Strike"]),
    "Knowledge": _dom("All Knowledge skills are class skills.",
                      ["True Strike", "Fox's Cunning", "Dispel Magic", "Spell Immunity",
                       "Hold Monster"], skills=["Knowledge (arcana)", "Knowledge (history)",
                                                "Knowledge (local)", "Knowledge (nature)",
                                                "Knowledge (dungeoneering)",
                                                "Knowledge (geography)",
                                                "Knowledge (nobility and royalty)",
                                                "Knowledge (the planes)"]),
    "Law": _dom("Cast law spells at +1 caster level.",
                ["Protection from Evil", "Hold Person", "Magic Circle against Evil",
                 "Hold Monster", "Dispel Evil"], forbid="Chaos"),
    "Luck": _dom("Good fortune, once per day: reroll a failed saving throw.",
                 ["Entropic Shield", "Aid", "Protection from Energy", "Freedom of Movement",
                  "Spell Immunity"], use="good_fortune"),
    "Magic": _dom("Use arcane scrolls, wands and staffs as if they were on your list.",
                  ["Magic Missile", "Scorching Ray", "Dispel Magic", "Spell Immunity",
                   "Cone of Cold"]),
    "Protection": _dom("Protective ward, once per day: touch an ally to give a resistance "
                       "bonus equal to your cleric level on their next save.",
                       ["Shield of Faith", "Resist Energy", "Protection from Energy",
                        "Spell Immunity", "Stoneskin"], use="protective_ward"),
    "Sun": _dom("Greater turning, once per day: a turning that destroys every undead it "
                "would turn.", ["Endure Elements", "Flaming Sphere", "Searing Light",
                                "Fire Shield", "Flame Strike"], use="greater_turning"),
    "Travel": _dom("Survival is a class skill.",
                   ["Longstrider", "Cat's Grace", "Fly", "Freedom of Movement",
                    "Greater Invisibility"], skills=["Survival"]),
    "Trickery": _dom("Bluff, Disguise and Hide are class skills.",
                     ["Grease", "Invisibility", "Displacement", "Confusion",
                      "Greater Invisibility"], skills=["Bluff", "Disguise", "Hide"]),
}


def domain_allowed(domain: str, alignment: str) -> bool:
    forbid = DOMAINS.get(domain, {}).get("forbid")
    return domain in DOMAINS and not (forbid and forbid in alignment)


FAVORED_ENEMIES = ["goblinoid", "undead", "animal", "orc", "giant", "kobold", "vermin",
                   "gnoll", "magical beast", "human", "aberration", "monstrous humanoid"]

STARTING_AGE = {  # base, (simple class dice, moderate, complex)
    "human": (15, "1d4", "1d6", "2d6"), "dwarf": (40, "3d6", "5d6", "7d6"),
    "elf": (110, "4d6", "6d6", "10d6"), "gnome": (40, "4d6", "6d6", "9d6"),
    "half-elf": (20, "1d6", "2d6", "3d6"), "half-orc": (14, "1d4", "1d6", "2d6"),
    "halfling": (20, "2d4", "3d6", "4d6"),
}
AGE_CATEGORY = {"barbarian": 0, "rogue": 0, "sorcerer": 0, "bard": 1, "fighter": 1,
                "paladin": 1, "ranger": 1, "cleric": 2, "druid": 2, "monk": 2, "wizard": 2}

MONK_UNARMED = {"medium": {1: "1d6", 4: "1d8", 8: "1d10"},
                "small": {1: "1d4", 4: "1d6", 8: "1d8"}}
METAL_ARMOR = {"chain shirt", "scale mail", "chainmail", "breastplate", "splint mail",
               "banded mail", "half-plate", "full plate", "light steel shield",
               "heavy steel shield"}
