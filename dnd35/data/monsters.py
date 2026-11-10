"""Monster stat blocks (SRD 3.5 Monster Manual creatures plus a few custom ones).

Numbers are derived by the same rules engine the PCs use; the comments note the
Monster Manual line each block reproduces.
"""

MONSTERS = {
    "goblin": {
        # Goblin, 1st-level warrior: AC 15, morningstar +2 (1d6), javelin +3 (1d4)
        "name": "Goblin", "type": "humanoid", "subtypes": ["goblinoid"], "size": "small",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 3,
        "abilities": {"str": 11, "dex": 13, "con": 12, "int": 10, "wis": 9, "cha": 6},
        "armor": "leather", "shield": "light wooden shield", "natural": 0,
        "weapons": ["morningstar", "javelin"], "speed": 30,
        "skills": {"Hide": 5, "Listen": 2, "Move Silently": 5, "Ride": 4, "Spot": 2},
        "feats": ["Alertness"], "vision": "darkvision 60 ft.", "alignment": "Neutral Evil",
        "morale": True, "evil": True,
        "desc": "A flat-faced, red-eyed humanoid barely three feet tall, clad in greasy "
                "leather.",
    },
    "goblin archer": {
        "name": "Goblin Archer", "type": "humanoid", "subtypes": ["goblinoid"], "size": "small",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 3,
        "abilities": {"str": 11, "dex": 13, "con": 12, "int": 10, "wis": 9, "cha": 6},
        "armor": "leather", "natural": 0, "weapons": ["shortbow", "dagger"], "speed": 30,
        "skills": {"Hide": 5, "Listen": 2, "Move Silently": 5, "Spot": 2},
        "feats": ["Alertness"], "vision": "darkvision 60 ft.", "prefers_ranged": True,
        "morale": True, "evil": True,
        "desc": "A goblin with a crude shortbow, keeping its distance.",
    },
    "hobgoblin": {
        # AC 15, longsword +2 (1d8+1/19-20), javelin +2 (1d6+1)
        "name": "Hobgoblin", "type": "humanoid", "subtypes": ["goblinoid"], "size": "medium",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 2,
        "abilities": {"str": 13, "dex": 13, "con": 14, "int": 10, "wis": 9, "cha": 8},
        "armor": "studded leather", "shield": "light wooden shield",
        "weapons": ["longsword", "javelin"], "speed": 30,
        "skills": {"Hide": 3, "Listen": 2, "Move Silently": 3, "Spot": 2},
        "feats": ["Alertness"], "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A burly, disciplined goblinoid with dark orange skin and a well-kept "
                "longsword.",
    },
    "bugbear": {
        # AC 17, morningstar +5 (1d8+2), javelin +3 (1d6+2)
        "name": "Bugbear", "type": "humanoid", "subtypes": ["goblinoid"], "size": "medium",
        "hd": 3, "hit_die": 8, "bab": 2, "base_saves": (1, 3, 1), "cr": 2,
        "abilities": {"str": 15, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 9},
        "armor": "leather", "shield": "light wooden shield", "natural": 3,
        "weapons": ["morningstar", "javelin"], "speed": 30,
        "skills": {"Climb": 3, "Hide": 4, "Listen": 4, "Move Silently": 6, "Spot": 4},
        "feats": ["Alertness", "Weapon Focus (morningstar)"], "vision": "darkvision 60 ft.",
        "evil": True,
        "desc": "A hulking, hairy goblinoid seven feet tall, moving with surprising quiet.",
    },
    "kobold": {
        "name": "Kobold", "type": "humanoid", "subtypes": ["reptilian"], "size": "small",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 4,
        "abilities": {"str": 9, "dex": 13, "con": 10, "int": 10, "wis": 9, "cha": 8},
        "armor": "leather", "natural": 1, "weapons": ["spear", "sling"], "speed": 30,
        "skills": {"Hide": 6, "Listen": 2, "Move Silently": 2, "Search": 2, "Spot": 2},
        "feats": ["Alertness"], "vision": "darkvision 60 ft.", "morale": True, "evil": True,
        "desc": "A scaly, dog-like little humanoid with a spear.",
    },
    "orc": {
        # AC 13, falchion +4 (2d4+4/18-20), javelin +1 (1d6+3)
        "name": "Orc", "type": "humanoid", "subtypes": ["orc"], "size": "medium",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 2,
        "abilities": {"str": 17, "dex": 11, "con": 12, "int": 8, "wis": 7, "cha": 6},
        "armor": "studded leather", "weapons": ["falchion", "javelin"], "speed": 30,
        "skills": {"Listen": 1, "Spot": 1}, "feats": ["Alertness"],
        "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A brutish grey-skinned warrior with a heavy falchion.",
    },
    "dire rat": {
        # AC 15, bite +4 (1d4 plus disease)
        "name": "Dire Rat", "type": "animal", "size": "small",
        "hd": 1, "hit_die": 8, "bab": 0, "base_saves": (2, 2, 2), "cr": 1 / 3,
        "abilities": {"str": 10, "dex": 17, "con": 12, "int": 1, "wis": 12, "cha": 4},
        "natural": 1, "speed": 40,
        "natural_attacks": [{"name": "bite", "damage": "1d4", "dtype": "P", "primary": True,
                             "disease": {"name": "filth fever", "dc": 11, "damage": "1d3",
                                         "abilities": ["dex", "con"]}}],
        "skills": {"Climb": 11, "Hide": 8, "Listen": 4, "Move Silently": 4, "Spot": 4,
                   "Swim": 11},
        "feats": ["Alertness", "Weapon Finesse"], "vision": "low-light, scent",
        "desc": "A filthy rat the size of a small dog, with yellow teeth.",
    },
    "wolf": {
        # AC 14, bite +3 (1d6+1), trip
        "name": "Wolf", "type": "animal", "size": "medium",
        "hd": 2, "hit_die": 8, "bab": 1, "base_saves": (3, 3, 0), "cr": 1,
        "abilities": {"str": 13, "dex": 15, "con": 15, "int": 2, "wis": 12, "cha": 6},
        "natural": 2, "speed": 50,
        "natural_attacks": [{"name": "bite", "damage": "1d6", "dtype": "P", "primary": True,
                             "trip": True}],
        "skills": {"Hide": 2, "Listen": 3, "Move Silently": 3, "Spot": 3, "Survival": 1},
        "feats": ["Track", "Weapon Focus (bite)"], "vision": "low-light, scent",
        "desc": "A lean grey wolf, hackles raised.",
    },
    "human skeleton": {
        # AC 15, scimitar +1 (1d6+1/18-20), DR 5/bludgeoning
        "name": "Skeleton", "type": "undead", "size": "medium",
        "hd": 1, "hit_die": 12, "bab": 0, "base_saves": (0, 0, 2), "cr": 1 / 3,
        "abilities": {"str": 13, "dex": 13, "con": None, "int": None, "wis": 10, "cha": 1},
        "shield": "heavy steel shield", "natural": 2, "weapons": ["scimitar"], "speed": 30,
        "dr": [(5, "B")], "immune": ["cold"], "feats": ["Improved Initiative"],
        "vision": "darkvision 60 ft.", "evil": True, "mindless": True,
        "desc": "A clattering human skeleton with a rusted scimitar and a battered shield.",
    },
    "human zombie": {
        # AC 11, slam +2 (1d6+1), DR 5/slashing, single actions only
        "name": "Zombie", "type": "undead", "size": "medium",
        "hd": 2, "hit_die": 12, "bab": 1, "base_saves": (0, 0, 3), "cr": 1 / 2,
        "abilities": {"str": 12, "dex": 8, "con": None, "int": None, "wis": 10, "cha": 1},
        "natural": 2, "speed": 30,
        "natural_attacks": [{"name": "slam", "damage": "1d6", "dtype": "B", "primary": True,
                             "str_mult": 1.5}],
        "dr": [(5, "S")], "feats": ["Toughness"], "single_actions": True,
        "vision": "darkvision 60 ft.", "evil": True, "mindless": True,
        "desc": "A shambling corpse in rotted burial wrappings.",
    },
    "ghoul": {
        # AC 14, bite +2 (1d6+1 plus paralysis), 2 claws +0 (1d3 plus paralysis)
        "name": "Ghoul", "type": "undead", "size": "medium",
        "hd": 2, "hit_die": 12, "bab": 1, "base_saves": (0, 0, 3), "cr": 1,
        "abilities": {"str": 13, "dex": 15, "con": None, "int": 13, "wis": 14, "cha": 12},
        "natural": 2, "speed": 30,
        "natural_attacks": [
            {"name": "bite", "damage": "1d6", "dtype": "P", "primary": True,
             "paralysis": {"dc": 12, "duration": "1d4+1"}},
            {"name": "claw", "damage": "1d3", "dtype": "S", "primary": False,
             "paralysis": {"dc": 12, "duration": "1d4+1"}},
            {"name": "claw", "damage": "1d3", "dtype": "S", "primary": False,
             "paralysis": {"dc": 12, "duration": "1d4+1"}},
        ],
        "feats": ["Multiattack"], "skills": {"Hide": 7, "Move Silently": 7, "Spot": 7,
                                             "Listen": 7},
        "vision": "darkvision 60 ft.", "evil": True, "savage": True,
        "desc": "A gaunt, grey-skinned corpse with a long tongue and black claws.",
    },
    "ember husk": {
        # Custom: the Ember King's guardian
        "name": "The Ember King's Husk", "type": "undead", "subtypes": ["fire"],
        "size": "medium", "hd": 4, "hit_die": 12, "bab": 2, "base_saves": (1, 1, 4), "cr": 3,
        "abilities": {"str": 16, "dex": 10, "con": None, "int": 8, "wis": 12, "cha": 14},
        "natural": 5, "speed": 30,
        "natural_attacks": [
            {"name": "burning slam", "damage": "1d8", "dtype": "B", "primary": True,
             "extra_damage": ("1d6", "fire")},
        ],
        "immune": ["fire"], "vulnerable": ["cold"],
        "special": {"ember_burst": {"damage": "2d6", "dtype": "fire", "dc": 13,
                                    "recharge": 3}},
        "skills": {"Listen": 6, "Spot": 6}, "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A charred, crowned corpse whose ribs glow like a banked forge. Embers drift "
                "from its jaw with every rasping breath.",
    },
    # ---------------------------------------------------------------- added for more adventures
    "gnoll": {
        # AC 15, battleaxe +3 (1d8+2/x3), shortbow +1 (1d6/x3)
        "name": "Gnoll", "type": "humanoid", "subtypes": ["gnoll"], "size": "medium",
        "hd": 2, "hit_die": 8, "bab": 1, "base_saves": (3, 0, 0), "cr": 1,
        "abilities": {"str": 15, "dex": 10, "con": 13, "int": 8, "wis": 11, "cha": 8},
        "armor": "leather", "shield": "heavy steel shield", "natural": 1,
        "weapons": ["battleaxe", "shortbow"], "speed": 30,
        "skills": {"Listen": 2, "Spot": 3}, "feats": ["Power Attack"],
        "vision": "darkvision 60 ft.", "evil": True, "morale": True,
        "desc": "A hyena-headed humanoid, seven feet of mangy fur and yellow teeth.",
    },
    "ogre": {
        # Large: AC 16, greatclub +8 (2d8+7), javelin +1 (1d8+5)
        "name": "Ogre", "type": "giant", "size": "large",
        "hd": 4, "hit_die": 8, "bab": 3, "base_saves": (4, 1, 1), "cr": 3,
        "abilities": {"str": 21, "dex": 8, "con": 15, "int": 6, "wis": 10, "cha": 7},
        "armor": "hide", "natural": 5, "weapons": ["greatclub", "javelin"], "speed": 30,
        "skills": {"Climb": 5, "Listen": 2, "Spot": 2},
        "feats": ["Toughness", "Weapon Focus (greatclub)"],
        "vision": "darkvision 60 ft., low-light", "evil": True,
        "desc": "A ten-foot brute with warty grey skin, wearing badly cured hides.",
    },
    "worg": {
        # AC 14, bite +7 (1d6+4) plus trip
        "name": "Worg", "type": "magical beast", "size": "medium",
        "hd": 4, "hit_die": 10, "bab": 4, "base_saves": (4, 4, 1), "cr": 2,
        "abilities": {"str": 17, "dex": 15, "con": 15, "int": 6, "wis": 14, "cha": 10},
        "natural": 2, "speed": 50,
        "natural_attacks": [{"name": "bite", "damage": "1d6", "dtype": "P", "primary": True,
                             "str_mult": 1.5, "trip": True}],
        "skills": {"Hide": 4, "Listen": 6, "Move Silently": 6, "Spot": 6, "Survival": 2},
        "feats": ["Alertness", "Track"], "vision": "darkvision 60 ft., scent", "evil": True,
        "desc": "A wolf the size of a pony, with clever, hateful eyes.",
    },
    "monstrous spider": {
        # Medium monstrous spider: AC 14, bite +4 (1d6 plus poison)
        "name": "Giant Spider", "type": "vermin", "size": "medium",
        "hd": 2, "hit_die": 8, "bab": 1, "base_saves": (3, 0, 0), "cr": 1,
        "abilities": {"str": 11, "dex": 17, "con": 12, "int": None, "wis": 10, "cha": 2},
        "natural": 1, "speed": 30,
        "natural_attacks": [{"name": "bite", "damage": "1d6", "dtype": "P", "primary": True,
                             "poison": {"dc": 12, "ability": "str", "damage": "1d4",
                                        "name": "spider venom"}}],
        "skills": {"Climb": 11, "Hide": 7, "Jump": 0, "Spot": 4},
        "feats": ["Weapon Finesse"], "vision": "darkvision 60 ft., tremorsense",
        "mindless": True, "immune": ["mind-affecting"],
        "desc": "A hairy spider as big as a large dog, mandibles glistening.",
    },
    "smuggler": {
        # Human warrior 1: AC 14, short sword +2 (1d6+1/19-20), light crossbow +2 (1d8)
        "name": "Smuggler", "type": "humanoid", "subtypes": ["human"], "size": "medium",
        "hd": 1, "hit_die": 8, "bab": 1, "base_saves": (2, 0, 0), "cr": 1 / 2,
        "abilities": {"str": 13, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 9},
        "armor": "studded leather", "weapons": ["short sword", "light crossbow"],
        "speed": 30, "skills": {"Listen": 1, "Spot": 1, "Swim": 5}, "feats": ["Alertness"],
        "evil": True, "morale": True,
        "desc": "A weathered sailor with a short sword and a crossbow, eyes like a gull's.",
    },
    "captain merrow": {
        # Human fighter 3: AC 17, rapier +6 (1d6+2/18-20), light crossbow +5 (1d8/19-20)
        "name": "Captain Ilsa Merrow", "type": "humanoid", "subtypes": ["human"],
        "size": "medium", "hd": 3, "hit_die": 10, "bab": 3, "base_saves": (3, 1, 1), "cr": 3,
        "abilities": {"str": 12, "dex": 15, "con": 13, "int": 12, "wis": 10, "cha": 14},
        "armor": "chain shirt", "weapons": ["masterwork rapier", "light crossbow"],
        "speed": 30, "bonus_hp": 3,
        "skills": {"Bluff": 6, "Listen": 2, "Spot": 4, "Swim": 7},
        "feats": ["Weapon Finesse", "Weapon Focus (rapier)", "Dodge", "Mobility"],
        "evil": True,
        "desc": "A tall woman in a salt-stained captain's coat, rapier drawn, smiling like "
                "she has already won.",
    },
}
