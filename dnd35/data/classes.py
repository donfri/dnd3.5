"""Character classes (SRD 3.5), levels 1-5."""

from .skills import KNOWLEDGES

ALL_KNOWLEDGE = [f"Knowledge ({k})" for k in KNOWLEDGES]

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
            2: ["Uncanny Dodge"],
            3: ["Trap Sense +1"],
            4: ["Rage 2/day"],
            5: ["Improved Uncanny Dodge"],
        },
        "description": "A ferocious warrior who channels fury into raw power. High hit points, "
                       "rage for big damage.",
    },
    "cleric": {
        "name": "Cleric", "hd": 8, "bab": "average", "good_saves": ["fort", "will"],
        "skill_points": 2, "gold": "5d4x10",
        "class_skills": ["Concentration", "Craft", "Diplomacy", "Heal",
                         "Knowledge (arcana)", "Knowledge (history)", "Knowledge (religion)",
                         "Knowledge (the planes)", "Profession", "Spellcraft"],
        "weapon_prof": ["simple"], "armor_prof": ["light", "medium", "heavy", "shields"],
        "caster": "divine", "cast_ability": "wis", "prepared": True,
        "spells_per_day": {1: [3, 1], 2: [4, 2], 3: [4, 2, 1], 4: [5, 3, 2], 5: [5, 3, 2, 1]},
        "features": {
            1: ["Aura", "Spells", "Domains (2)", "Spontaneous Casting", "Turn Undead"],
        },
        "description": "A divine champion: heals allies, armored, turns undead, solid melee.",
    },
    "fighter": {
        "name": "Fighter", "hd": 10, "bab": "good", "good_saves": ["fort"],
        "skill_points": 2, "gold": "6d4x10",
        "class_skills": ["Climb", "Craft", "Handle Animal", "Intimidate", "Jump", "Ride",
                         "Swim"],
        "weapon_prof": ["simple", "martial"],
        "armor_prof": ["light", "medium", "heavy", "shields", "tower"],
        "bonus_feat_levels": [1, 2, 4],
        "features": {1: ["Bonus Feat"], 2: ["Bonus Feat"], 4: ["Bonus Feat"]},
        "description": "Master of arms and armor. The most feats, the best armor, great "
                       "attack bonus.",
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
        "spells_per_day": {4: [None, 0], 5: [None, 0]},
        "features": {
            1: ["1st Favored Enemy", "Track", "Wild Empathy"],
            2: ["Combat Style"],
            3: ["Endurance"],
            4: ["Animal Companion (not implemented)", "Spells"],
            5: ["2nd Favored Enemy"],
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
            1: ["Sneak Attack +1d6", "Trapfinding"],
            2: ["Evasion"],
            3: ["Sneak Attack +2d6", "Trap Sense +1"],
            4: ["Uncanny Dodge"],
            5: ["Sneak Attack +3d6"],
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
        "spells_per_day": {1: [5, 3], 2: [6, 4], 3: [6, 5], 4: [6, 6, 3], 5: [6, 6, 4]},
        "spells_known": {1: [4, 2], 2: [5, 2], 3: [5, 3], 4: [6, 3, 1], 5: [6, 4, 2]},
        "features": {1: ["Summon Familiar (flavor)", "Spells"]},
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
        "spells_per_day": {1: [3, 1], 2: [4, 2], 3: [4, 2, 1], 4: [4, 3, 2], 5: [4, 3, 2, 1]},
        "bonus_feat_levels": [5],
        "features": {1: ["Scribe Scroll", "Summon Familiar (flavor)", "Spellbook"],
                     5: ["Bonus Feat (metamagic/item creation)"]},
        "description": "Scholar of arcane magic. Fragile, but the widest choice of spells.",
    },
}

CLASS_ORDER = ["barbarian", "cleric", "fighter", "ranger", "rogue", "sorcerer", "wizard"]

ALIGNMENTS = ["Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral",
              "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"]

DEITIES = {
    "Pelor": {"alignment": "Neutral Good", "domains": ["Good", "Healing", "Strength"],
              "weapon": "heavy mace", "portfolio": "the sun, light, strength, healing"},
    "Heironeous": {"alignment": "Lawful Good", "domains": ["Good", "War"],
                   "weapon": "longsword", "portfolio": "valor, chivalry, justice"},
    "Kord": {"alignment": "Chaotic Good", "domains": ["Good", "Strength"],
             "weapon": "greatsword", "portfolio": "athletics, sport, brawling, courage"},
    "St. Cuthbert": {"alignment": "Lawful Neutral", "domains": ["Strength", "War"],
                     "weapon": "heavy mace", "portfolio": "retribution, common sense"},
    "Obad-Hai": {"alignment": "True Neutral", "domains": ["Healing", "Strength"],
                 "weapon": "quarterstaff", "portfolio": "nature, woodlands, hunting"},
}

DOMAINS = {
    "Good": {"power": "Cast good spells at +1 caster level.",
             "spells": {1: "Protection from Evil", 2: "Aid", 3: "Magic Circle against Evil"}},
    "Healing": {"power": "Cast healing (conjuration) spells at +1 caster level.",
                "spells": {1: "Cure Light Wounds", 2: "Cure Moderate Wounds",
                           3: "Cure Serious Wounds"}},
    "Strength": {"power": "Feat of Strength: once per day, gain an enhancement bonus to "
                          "Strength equal to your cleric level for 1 round.",
                 "spells": {1: "Enlarge Person", 2: "Bull's Strength", 3: "Magic Vestment"}},
    "War": {"power": "Free Martial Weapon Proficiency and Weapon Focus with your deity's "
                     "favored weapon.",
            "spells": {1: "Magic Weapon", 2: "Spiritual Weapon", 3: "Magic Vestment"}},
}

FAVORED_ENEMIES = ["goblinoid", "undead", "animal", "orc", "giant", "kobold", "vermin",
                   "aberration", "magical beast", "monstrous humanoid"]

STARTING_AGE = {  # base, (simple class dice, moderate, complex)
    "human": (15, "1d4", "1d6", "2d6"), "dwarf": (40, "3d6", "5d6", "7d6"),
    "elf": (110, "4d6", "6d6", "10d6"), "gnome": (40, "4d6", "6d6", "9d6"),
    "half-elf": (20, "1d6", "2d6", "3d6"), "half-orc": (14, "1d4", "1d6", "2d6"),
    "halfling": (20, "2d4", "3d6", "4d6"),
}
AGE_CATEGORY = {"barbarian": 0, "rogue": 0, "sorcerer": 0, "fighter": 1, "ranger": 1,
                "cleric": 2, "wizard": 2}
