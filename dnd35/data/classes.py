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
                   9: [None, 1, 0], 10: [None, 1, 1], 11: [None, 1, 1, 0],
                   12: [None, 1, 1, 1], 13: [None, 1, 1, 1], 14: [None, 2, 1, 1, 0],
                   15: [None, 2, 1, 1, 1], 16: [None, 2, 2, 1, 1], 17: [None, 2, 2, 2, 1],
                   18: [None, 3, 2, 2, 1], 19: [None, 3, 3, 3, 2], 20: [None, 3, 3, 3, 3]}
CLERIC_DAY.update({11: [6, 5, 4, 4, 3, 2, 1], 12: [6, 5, 4, 4, 3, 3, 2],
                   13: [6, 5, 5, 4, 4, 3, 2, 1], 14: [6, 5, 5, 4, 4, 3, 3, 2],
                   15: [6, 5, 5, 5, 4, 4, 3, 2, 1], 16: [6, 5, 5, 5, 4, 4, 3, 3, 2],
                   17: [6, 5, 5, 5, 5, 4, 4, 3, 2, 1], 18: [6, 5, 5, 5, 5, 4, 4, 3, 3, 2],
                   19: [6, 5, 5, 5, 5, 5, 4, 4, 3, 3], 20: [6, 5, 5, 5, 5, 5, 4, 4, 4, 4]})
WIZARD_DAY.update({11: [4, 4, 4, 4, 3, 2, 1], 12: [4, 4, 4, 4, 3, 3, 2],
                   13: [4, 4, 4, 4, 4, 3, 2, 1], 14: [4, 4, 4, 4, 4, 3, 3, 2],
                   15: [4, 4, 4, 4, 4, 4, 3, 2, 1], 16: [4, 4, 4, 4, 4, 4, 3, 3, 2],
                   17: [4, 4, 4, 4, 4, 4, 4, 3, 2, 1], 18: [4, 4, 4, 4, 4, 4, 4, 3, 3, 2],
                   19: [4, 4, 4, 4, 4, 4, 4, 4, 3, 3], 20: [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]})
SORC_DAY.update({11: [6, 6, 6, 6, 6, 5, 3], 12: [6, 6, 6, 6, 6, 6, 4],
                 13: [6, 6, 6, 6, 6, 6, 5, 3], 14: [6, 6, 6, 6, 6, 6, 6, 4],
                 15: [6, 6, 6, 6, 6, 6, 6, 5, 3], 16: [6, 6, 6, 6, 6, 6, 6, 6, 4],
                 17: [6, 6, 6, 6, 6, 6, 6, 6, 5, 3], 18: [6, 6, 6, 6, 6, 6, 6, 6, 6, 4],
                 19: [6, 6, 6, 6, 6, 6, 6, 6, 6, 6], 20: [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]})
SORC_KNOWN.update({11: [9, 5, 5, 4, 3, 2, 1], 12: [9, 5, 5, 4, 3, 3, 2],
                   13: [9, 5, 5, 4, 4, 3, 2, 1], 14: [9, 5, 5, 4, 4, 3, 3, 2],
                   15: [9, 5, 5, 4, 4, 4, 3, 2, 1], 16: [9, 5, 5, 4, 4, 4, 3, 3, 2],
                   17: [9, 5, 5, 4, 4, 4, 3, 3, 2, 1], 18: [9, 5, 5, 4, 4, 4, 3, 3, 3, 2],
                   19: [9, 5, 5, 4, 4, 4, 3, 3, 3, 3], 20: [9, 5, 5, 4, 4, 4, 3, 3, 3, 3]})
BARD_DAY.update({11: [3, 3, 3, 3, 1], 12: [3, 3, 3, 3, 2], 13: [3, 3, 3, 3, 2, 0],
                 14: [4, 3, 3, 3, 3, 1], 15: [4, 4, 3, 3, 3, 2], 16: [4, 4, 4, 3, 3, 2, 0],
                 17: [4, 4, 4, 4, 3, 3, 1], 18: [4, 4, 4, 4, 4, 3, 2],
                 19: [4, 4, 4, 4, 4, 4, 3], 20: [4, 4, 4, 4, 4, 4, 4]})
BARD_KNOWN.update({11: [6, 4, 4, 4, 3], 12: [6, 4, 4, 4, 4], 13: [6, 4, 4, 4, 4, 2],
                   14: [6, 4, 4, 4, 4, 3], 15: [6, 4, 4, 4, 4, 3], 16: [6, 5, 4, 4, 4, 4, 2],
                   17: [6, 5, 5, 4, 4, 4, 3], 18: [6, 5, 5, 5, 4, 4, 3],
                   19: [6, 5, 5, 5, 5, 4, 4], 20: [6, 5, 5, 5, 5, 5, 4]})

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
            11: ["Greater Rage (+6 Str/Con, +3 Will)"], 12: ["Rage 4/day", "Trap Sense +4"],
            13: ["Damage Reduction 3/-"], 14: ["Indomitable Will (+4 vs enchantment in rage)"],
            15: ["Trap Sense +5"], 16: ["Rage 5/day", "Damage Reduction 4/-"],
            17: ["Tireless Rage"], 18: ["Trap Sense +6"], 19: ["Damage Reduction 5/-"],
            20: ["Mighty Rage (+8 Str/Con, +4 Will)", "Rage 6/day"],
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
            8: ["Inspire Courage +2"], 9: ["Inspire Greatness"],
            12: ["Song of Freedom (flavor)"], 14: ["Inspire Courage +3"],
            15: ["Inspire Heroics (+4 saves and dodge AC to an ally)"],
            18: ["Mass Suggestion (flavor)"], 20: ["Inspire Courage +4"],
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
            11: ["Wild Shape (Tiny forms)"], 12: ["Wild Shape (plants)"],
            13: ["A Thousand Faces (flavor)"], 14: ["Wild Shape 5/day"],
            15: ["Timeless Body", "Wild Shape (Huge)"], 16: ["Wild Shape (elemental 1/day)"],
            18: ["Wild Shape 6/day", "Elemental 2/day"],
            20: ["Elemental 3/day (Huge elementals)"],
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
        "bonus_feat_levels": [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "features": {lv: ["Bonus Feat"] for lv in (1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20)},
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
            11: ["Diamond Body (immune to poison)", "Greater Flurry (2 extra attacks)"],
            12: ["Abundant Step (flavor)", "Fast Movement +40", "Unarmed 2d6"],
            13: ["Diamond Soul (spell resistance 10 + level)"],
            15: ["Quivering Palm (1/week)", "Fast Movement +50"],
            16: ["Ki Strike (adamantine)", "Unarmed 2d8"],
            17: ["Timeless Body", "Tongue of the Sun and Moon"],
            18: ["Fast Movement +60"], 19: ["Empty Body (flavor)"],
            20: ["Perfect Self (DR 10/magic)", "Unarmed 2d10"],
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
            10: ["Smite Evil 3/day"], 12: ["Remove Disease 3/week"],
            15: ["Smite Evil 4/day", "Remove Disease 4/week"], 18: ["Remove Disease 5/week"],
            20: ["Smite Evil 5/day"],
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
            11: ["Combat Style Mastery"], 13: ["Camouflage (flavor)"],
            15: ["4th Favored Enemy"], 17: ["Hide in Plain Sight (flavor)"],
            20: ["5th Favored Enemy"],
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
            10: ["Special Ability"], 11: ["Sneak Attack +6d6"], 12: ["Trap Sense +4"],
            13: ["Sneak Attack +7d6", "Special Ability"], 15: ["Sneak Attack +8d6",
                                                                "Trap Sense +5"],
            16: ["Special Ability"], 17: ["Sneak Attack +9d6"], 18: ["Trap Sense +6"],
            19: ["Sneak Attack +10d6", "Special Ability"],
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
        "bonus_feat_levels": [5, 10, 15, 20],
        "features": {1: ["Scribe Scroll", "Familiar", "Spellbook"],
                     5: ["Bonus Feat (metamagic/item creation)"],
                     10: ["Bonus Feat (metamagic/item creation)"],
                     15: ["Bonus Feat (metamagic/item creation)"],
                     20: ["Bonus Feat (metamagic/item creation)"]},
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
    if rule == "evil":
        return "Evil" in alignment
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

MONK_UNARMED = {"medium": {1: "1d6", 4: "1d8", 8: "1d10", 12: "2d6", 16: "2d8", 20: "2d10"},
                "small": {1: "1d4", 4: "1d6", 8: "1d8", 12: "1d10", 16: "2d6", 20: "2d8"}}

ROGUE_SPECIALS = {
    "improved evasion": "Improved evasion: half damage even when you fail a Reflex save.",
    "crippling strike": "Crippling strike: your sneak attacks also deal 2 Strength damage.",
    "defensive roll": "Defensive roll: once per day, when a blow would drop you, a Reflex "
                      "save (DC = damage) halves it.",
    "slippery mind": "Slippery mind: reroll a failed save against enchantment.",
    "opportunist": "Opportunist: once per round, an attack of opportunity against a foe an "
                   "ally just hit.",
    "skill mastery": "Skill mastery: take 10 on skill checks even under pressure (flavor).",
}
METAL_ARMOR = {"chain shirt", "scale mail", "chainmail", "breastplate", "splint mail",
               "banded mail", "half-plate", "full plate", "light steel shield",
               "heavy steel shield"}

# domain spells for levels 6-9 (closest implemented spell where the SRD one isn't here)
for _d, _sp in {
    "Good": ["Blade Barrier", "Holy Word", "Holy Aura", "Summon Monster IX"],
    "Healing": ["Heal", "Mass Cure Serious Wounds", "Mass Cure Critical Wounds", "Mass Heal"],
    "Strength": ["Stoneskin", "Mass Bull's Strength", "Mass Bear's Endurance",
                 "Mordenkainen's Sword"],
    "War": ["Blade Barrier", "Power Word Blind", "Power Word Stun", "Power Word Kill"],
    "Animal": ["Mass Cat's Grace", "Summon Nature's Ally VII", "Summon Nature's Ally VIII",
               "Summon Nature's Ally IX"],
    "Chaos": ["Song of Discord", "Power Word Blind", "Holy Aura", "Summon Monster IX"],
    "Death": ["Harm", "Destruction", "Horrid Wilting", "Wail of the Banshee"],
    "Destruction": ["Harm", "Disintegrate", "Horrid Wilting", "Implosion"],
    "Evil": ["Harm", "Destruction", "Horrid Wilting", "Summon Monster IX"],
    "Fire": ["Delayed Blast Fireball", "Fire Storm", "Sunburst", "Elemental Swarm"],
    "Knowledge": ["Greater Dispel Magic", "Power Word Blind", "Mass Hold Monster",
                  "Power Word Kill"],
    "Law": ["Greater Dispel Magic", "Holy Word", "Holy Aura", "Summon Monster IX"],
    "Luck": ["Mass Eagle's Splendor", "Greater Heroism", "Holy Aura", "Mass Heal"],
    "Magic": ["Greater Dispel Magic", "Mordenkainen's Sword", "Polar Ray", "Meteor Swarm"],
    "Protection": ["Globe of Invulnerability", "Holy Aura", "Mass Bear's Endurance",
                   "Mass Heal"],
    "Sun": ["Delayed Blast Fireball", "Sunbeam", "Sunburst", "Meteor Swarm"],
    "Travel": ["Greater Dispel Magic", "Greater Heroism", "Mass Cat's Grace",
               "Mass Hold Monster"],
    "Trickery": ["Mass Eagle's Splendor", "Song of Discord", "Power Word Stun",
                 "Mass Hold Monster"],
}.items():
    DOMAINS[_d]["spells"].update(dict(zip((6, 7, 8, 9), _sp)))

# ---------------------------------------------------------------- prestige classes (DMG)
PRESTIGE = {
    "eldritch knight": {
        "name": "Eldritch Knight", "hd": 6, "bab": "good", "good_saves": ["fort"],
        "skill_points": 2, "max_level": 10, "progression": {"arcane": range(2, 11)},
        "class_skills": ["Climb", "Concentration", "Craft", "Decipher Script", "Jump",
                         "Knowledge (arcana)", "Knowledge (nobility and royalty)", "Ride",
                         "Sense Motive", "Spellcraft", "Swim"],
        "weapon_prof": [], "armor_prof": [],
        "features": {1: ["Bonus fighter feat"], 2: ["+1 level of arcane spellcasting (2-10)"]},
        "requires": "Proficiency with all martial weapons; able to cast 3rd-level arcane "
                    "spells.",
        "description": "Blade and spell together: fighter's attack bonus, a wizard's spells.",
    },
    "mystic theurge": {
        "name": "Mystic Theurge", "hd": 4, "bab": "poor", "good_saves": ["will"],
        "skill_points": 2, "max_level": 10,
        "progression": {"arcane": range(1, 11), "divine": range(1, 11)},
        "class_skills": ["Concentration", "Craft", "Decipher Script", "Knowledge (arcana)",
                         "Knowledge (religion)", "Profession", "Sense Motive", "Spellcraft"],
        "weapon_prof": [], "armor_prof": [],
        "features": {1: ["+1 level of arcane AND divine spellcasting"]},
        "requires": "Able to cast 2nd-level arcane and 2nd-level divine spells; Knowledge "
                    "(arcana) 6 ranks, Knowledge (religion) 6 ranks.",
        "description": "Advances both an arcane and a divine spellcasting class.",
    },
    "arcane trickster": {
        "name": "Arcane Trickster", "hd": 4, "bab": "poor", "good_saves": ["ref", "will"],
        "skill_points": 4, "max_level": 10, "progression": {"arcane": range(1, 11)},
        "class_skills": ["Appraise", "Balance", "Climb", "Concentration", "Craft",
                         "Decipher Script", "Disable Device", "Escape Artist",
                         "Gather Information", "Hide", "Jump", "Knowledge (arcana)", "Listen",
                         "Move Silently", "Open Lock", "Profession", "Search",
                         "Sleight of Hand", "Spellcraft", "Spot", "Swim", "Tumble", "Use Rope"],
        "weapon_prof": [], "armor_prof": [],
        "features": {1: ["+1 level of arcane spellcasting"], 2: ["Sneak attack +1d6"],
                     4: ["Sneak attack +2d6"], 6: ["Sneak attack +3d6"],
                     8: ["Sneak attack +4d6"], 10: ["Sneak attack +5d6"]},
        "requires": "Nonlawful; Disable Device 7, Escape Artist 7, Knowledge (arcana) 4; "
                    "sneak attack +2d6; able to cast 3rd-level arcane spells.",
        "description": "Rogue-wizard: arcane spells and ever more sneak attack.",
        "alignment": "nonlawful",
    },
    "dwarven defender": {
        "name": "Dwarven Defender", "hd": 12, "bab": "good", "good_saves": ["fort", "will"],
        "skill_points": 2, "max_level": 10,
        "class_skills": ["Craft", "Listen", "Sense Motive", "Spot"],
        "weapon_prof": ["simple", "martial"],
        "armor_prof": ["light", "medium", "heavy", "shields"],
        "features": {1: ["AC bonus +1", "Defensive stance 1/day"], 2: ["Uncanny dodge"],
                     3: ["Defensive stance 2/day"], 4: ["AC bonus +2", "Trap sense +1"],
                     5: ["Defensive stance 3/day"], 6: ["DR 3/-", "Improved uncanny dodge"],
                     7: ["AC bonus +3", "Defensive stance 4/day"],
                     8: ["Mobile defense", "Trap sense +2"], 9: ["Defensive stance 5/day"],
                     10: ["AC bonus +4", "DR 6/-"]},
        "requires": "Dwarf; lawful; base attack +7; Dodge, Endurance and Toughness.",
        "description": "An immovable wall: big hit points, dodge AC, a defensive stance.",
        "alignment": "lawful",
    },
    "duelist": {
        "name": "Duelist", "hd": 10, "bab": "good", "good_saves": ["ref"],
        "skill_points": 4, "max_level": 10,
        "class_skills": ["Balance", "Bluff", "Escape Artist", "Jump", "Listen", "Perform",
                         "Sense Motive", "Spot", "Tumble"],
        "weapon_prof": ["simple", "martial"], "armor_prof": [],
        "features": {1: ["Canny defense (Int to AC, unarmored)"],
                     2: ["Improved reaction +2"], 4: ["Grace (+2 Reflex)"],
                     5: ["Precise strike +1d6"], 7: ["Elaborate parry"],
                     8: ["Improved reaction +4"], 9: ["Deflect arrows"],
                     10: ["Precise strike +2d6"]},
        "requires": "Base attack +6; Dodge, Mobility, Weapon Finesse; Perform 2, Tumble 5.",
        "description": "A nimble, unarmored blade: Int to AC and precise, deadly thrusts.",
    },
    "arcane archer": {
        "name": "Arcane Archer", "hd": 8, "bab": "good", "good_saves": ["fort", "ref"],
        "skill_points": 4, "max_level": 10,
        "class_skills": ["Craft", "Hide", "Listen", "Move Silently", "Ride", "Spot",
                         "Survival", "Use Rope"],
        "weapon_prof": ["simple", "martial"], "armor_prof": ["light", "medium", "shields"],
        "features": {1: ["Enhance arrow +1"], 3: ["Enhance arrow +2"],
                     5: ["Enhance arrow +3"], 7: ["Enhance arrow +4"],
                     8: ["Hail of arrows (1/day)"], 9: ["Enhance arrow +5"],
                     10: ["Arrow of death (1/day)"]},
        "requires": "Elf or half-elf; base attack +6; Point Blank Shot, Precise Shot, Weapon "
                    "Focus (longbow or shortbow); able to cast 1st-level arcane spells.",
        "description": "Elven archer-mage: every arrow becomes magic, ending in arrows of "
                       "death.",
    },
    "assassin": {
        "name": "Assassin", "hd": 6, "bab": "average", "good_saves": ["ref"],
        "skill_points": 4, "max_level": 10,
        "class_skills": ["Balance", "Bluff", "Climb", "Craft", "Decipher Script", "Diplomacy",
                         "Disable Device", "Disguise", "Escape Artist", "Forgery",
                         "Gather Information", "Hide", "Intimidate", "Jump", "Listen",
                         "Move Silently", "Open Lock", "Search", "Sense Motive",
                         "Sleight of Hand", "Spot", "Swim", "Tumble", "Use Magic Device",
                         "Use Rope"],
        "weapon_prof": ["simple", "hand crossbow", "rapier", "sap", "shortbow", "short sword"],
        "armor_prof": ["light"],
        "features": {1: ["Sneak attack +1d6", "Death attack"], 2: ["Uncanny dodge"],
                     3: ["Sneak attack +2d6"], 5: ["Sneak attack +3d6",
                                                  "Improved uncanny dodge"],
                     7: ["Sneak attack +4d6"], 9: ["Sneak attack +5d6"]},
        "requires": "Evil; Disguise 4, Hide 8, Move Silently 8.",
        "description": "Killer for hire: sneak attacks and the dreaded death attack. "
                       "(Assassin spells aren't included.)",
        "alignment": "evil",
    },
}
for _k, _v in PRESTIGE.items():
    _v["prestige"] = True
    _v.setdefault("gold", "0d4")
CLASSES.update(PRESTIGE)
