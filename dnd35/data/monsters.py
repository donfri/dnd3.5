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
    "constrictor snake": {
        "name": "Constrictor snake", "type": "animal", "size": "medium",
        "hd": 3, "hit_die": 8, "bab": 2, "base_saves": (4, 6, 2), "cr": 2,
        "abilities": {"str": 17, "dex": 17, "con": 13, "int": 1, "wis": 12, "cha": 2},
        "natural": 2, "speed": 20,
        "natural_attacks": [{"name": "bite", "damage": "1d3", "dtype": "P", "primary": True,
                             "grab": True}],
        "constrict": "1d3+4", "skills": {"Hide": 10, "Listen": 7, "Spot": 7},
        "feats": ["Alertness", "Toughness"], "vision": "scent", "savage": True,
        "desc": "A thick-bodied snake as long as a wagon. It bites to hold, then squeezes.",
    },
    "giant constrictor snake": {
        "name": "Giant constrictor snake", "type": "animal", "size": "huge",
        "hd": 11, "hit_die": 8, "bab": 8, "base_saves": (8, 10, 4), "cr": 5,
        "abilities": {"str": 25, "dex": 17, "con": 13, "int": 1, "wis": 12, "cha": 2},
        "natural": 4, "speed": 20,
        "natural_attacks": [{"name": "bite", "damage": "1d8", "dtype": "P", "primary": True,
                             "grab": True}],
        "constrict": "1d8+10", "skills": {"Hide": 10, "Listen": 9, "Spot": 9},
        "feats": ["Alertness", "Toughness"], "vision": "scent", "savage": True,
        "desc": "A snake as thick as a barrel, long enough to crush an ox in its coils.",
    },
    "rat swarm": {
        "name": "Rat swarm", "type": "animal", "size": "tiny",
        "hd": 4, "hit_die": 8, "bab": 3, "base_saves": (4, 6, 2), "cr": 2,
        "abilities": {"str": 2, "dex": 15, "con": 10, "int": 2, "wis": 12, "cha": 2},
        "natural": 0, "speed": 15, "morale": False,
        "natural_attacks": [{"name": "swarm", "damage": "1d6", "dtype": "P", "primary": True}],
        "swarm": {"damage": "1d6", "dc": 12},
        "skills": {"Hide": 14, "Listen": 6, "Spot": 7}, "feats": ["Alertness"],
        "vision": "low-light, scent", "savage": True,
        "desc": "A squealing carpet of hundreds of rats. Blades barely thin it; fire and "
                "blast spells do the job.",
    },
    "basilisk": {
        "name": "Basilisk", "type": "magical beast", "size": "medium",
        "hd": 6, "hit_die": 10, "bab": 6, "base_saves": (9, 4, 3), "cr": 5,
        "abilities": {"str": 15, "dex": 8, "con": 15, "int": 2, "wis": 12, "cha": 11},
        "natural": 7, "speed": 20,
        "natural_attacks": [{"name": "bite", "damage": "1d8", "dtype": "P", "primary": True}],
        "gaze": {"dc": 13, "range": 30},
        "skills": {"Hide": 0, "Listen": 7, "Spot": 7}, "feats": ["Alertness", "Blind-Fight"],
        "vision": "darkvision 60 ft., low-light",
        "desc": "An eight-legged reptile with dull scales and pale, glowing eyes. "
                "Meet its gaze and you turn to stone.",
    },
    "elephant": {
        "name": "Elephant", "type": "animal", "size": "huge",
        "hd": 11, "hit_die": 8, "bab": 8, "base_saves": (12, 7, 6), "cr": 7,
        "abilities": {"str": 30, "dex": 10, "con": 21, "int": 2, "wis": 13, "cha": 7},
        "natural": 7, "speed": 40,
        "natural_attacks": [{"name": "slam", "damage": "2d6", "dtype": "B", "primary": True},
                            {"name": "stamp", "damage": "2d6", "dtype": "B",
                             "primary": False},
                            {"name": "stamp", "damage": "2d6", "dtype": "B",
                             "primary": False}],
        "trample": {"damage": "2d8+15", "dc": 25},
        "skills": {"Listen": 12, "Spot": 10}, "feats": ["Alertness", "Endurance"],
        "vision": "low-light, scent",
        "desc": "A maddened bull elephant, tusks lowered. It doesn't go around you.",
    },
    "tyrannosaurus": {
        "name": "Tyrannosaurus", "type": "animal", "size": "huge",
        "hd": 18, "hit_die": 8, "bab": 13, "base_saves": (16, 12, 8), "cr": 8,
        "abilities": {"str": 28, "dex": 12, "con": 21, "int": 2, "wis": 15, "cha": 10},
        "natural": 5, "speed": 40,
        "natural_attacks": [{"name": "bite", "damage": "3d6", "dtype": "P", "primary": True,
                             "grab": True}],
        "swallow": "2d8+8", "skills": {"Hide": -2, "Listen": 14, "Spot": 14},
        "feats": ["Alertness", "Run", "Toughness", "Track"], "vision": "low-light, scent",
        "savage": True,
        "desc": "A towering two-legged lizard with a head the size of a cart and teeth "
                "like daggers. It swallows prey whole.",
    },
}

# ---------------------------------------------------------------- wild shape forms
# Druids take the physical scores, size, natural armor, speed and attacks of these.
MONSTERS.update({
    "black bear": {
        # MM: AC 13, claw +6 (1d4+4) x2, bite +1 (1d6+2)
        "name": "Black Bear", "type": "animal", "size": "medium",
        "hd": 3, "hit_die": 8, "bab": 2, "base_saves": (5, 4, 2), "cr": 2,
        "abilities": {"str": 19, "dex": 13, "con": 15, "int": 2, "wis": 12, "cha": 6},
        "natural": 2, "speed": 40,
        "natural_attacks": [{"name": "claw", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "claw", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "1d6", "dtype": "P",
                             "primary": False}],
        "skills": {"Climb": 4, "Listen": 4, "Spot": 4, "Swim": 8},
        "feats": ["Endurance", "Run"], "vision": "low-light, scent",
        "desc": "A shaggy black bear, all muscle and claws.",
    },
    "leopard": {
        # MM: AC 15, bite +6 (1d6+3), claw +1 (1d3+1) x2
        "name": "Leopard", "type": "animal", "size": "medium",
        "hd": 3, "hit_die": 8, "bab": 2, "base_saves": (4, 7, 2), "cr": 2,
        "abilities": {"str": 16, "dex": 19, "con": 15, "int": 2, "wis": 12, "cha": 6},
        "natural": 1, "speed": 40,
        "natural_attacks": [{"name": "bite", "damage": "1d6", "dtype": "P", "primary": True},
                            {"name": "claw", "damage": "1d3", "dtype": "S", "primary": False},
                            {"name": "claw", "damage": "1d3", "dtype": "S",
                             "primary": False}],
        "skills": {"Balance": 12, "Climb": 11, "Hide": 8, "Jump": 11, "Listen": 6,
                   "Move Silently": 8, "Spot": 6},
        "feats": ["Alertness", "Weapon Finesse"], "vision": "low-light, scent",
        "desc": "A spotted great cat, low and coiled to spring.",
    },
    "brown bear": {
        # MM: Large, AC 15, claw +11 (1d8+8) x2, bite +6 (2d6+4)
        "name": "Brown Bear", "type": "animal", "size": "large",
        "hd": 6, "hit_die": 8, "bab": 4, "base_saves": (8, 6, 3), "cr": 4,
        "abilities": {"str": 27, "dex": 13, "con": 19, "int": 2, "wis": 12, "cha": 6},
        "natural": 5, "speed": 40,
        "natural_attacks": [{"name": "claw", "damage": "1d8", "dtype": "S", "primary": True},
                            {"name": "claw", "damage": "1d8", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "2d6", "dtype": "P",
                             "primary": False}],
        "skills": {"Listen": 4, "Spot": 7, "Swim": 12},
        "feats": ["Endurance", "Run", "Track"], "vision": "low-light, scent",
        "desc": "A towering brown bear that blots out the light behind it.",
    },
    "dire wolf": {
        # MM: Large, AC 14, bite +11 (1d8+10), trip
        "name": "Dire Wolf", "type": "animal", "size": "large",
        "hd": 6, "hit_die": 8, "bab": 4, "base_saves": (8, 7, 6), "cr": 3,
        "abilities": {"str": 25, "dex": 15, "con": 17, "int": 2, "wis": 12, "cha": 10},
        "natural": 3, "speed": 50,
        "natural_attacks": [{"name": "bite", "damage": "1d8", "dtype": "P", "primary": True,
                             "str_mult": 1.5, "trip": True}],
        "skills": {"Hide": 0, "Listen": 7, "Move Silently": 4, "Spot": 7, "Survival": 2},
        "feats": ["Alertness", "Run", "Track", "Weapon Focus (bite)"],
        "vision": "low-light, scent",
        "desc": "A wolf as big as a horse, with a mouth full of yellow knives.",
    },
})

MONSTERS.update({
    "riding dog": {
        # MM: AC 16, bite +3 (1d6+3), trip
        "name": "Riding Dog", "type": "animal", "size": "medium",
        "hd": 2, "hit_die": 8, "bab": 1, "base_saves": (5, 5, 1), "cr": 1,
        "abilities": {"str": 15, "dex": 15, "con": 15, "int": 2, "wis": 12, "cha": 6},
        "natural": 4, "speed": 40,
        "natural_attacks": [{"name": "bite", "damage": "1d6", "dtype": "P", "primary": True,
                             "str_mult": 1.5, "trip": True}],
        "skills": {"Jump": 8, "Listen": 5, "Spot": 5, "Swim": 3, "Survival": 1},
        "feats": ["Alertness", "Track"], "vision": "low-light, scent",
        "desc": "A big, loyal war dog in a studded collar.",
    },
    "eagle": {
        # MM: Small, AC 14, talons +3 (1d4) x2, bite -2 (1d4)
        "name": "Eagle", "type": "animal", "size": "small",
        "hd": 1, "hit_die": 8, "bab": 0, "base_saves": (3, 4, 2), "cr": 1 / 2,
        "abilities": {"str": 10, "dex": 15, "con": 12, "int": 2, "wis": 14, "cha": 6},
        "natural": 1, "speed": 80,
        "natural_attacks": [{"name": "talon", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "talon", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "1d4", "dtype": "P",
                             "primary": False}],
        "skills": {"Listen": 2, "Spot": 14}, "feats": ["Alertness", "Weapon Finesse"],
        "vision": "low-light",
        "desc": "A keen-eyed eagle with a wingspan wider than a man is tall.",
    },
})

# ---------------------------------------------------------------- the Thornwood Fen (6-8)
MONSTERS.update({
    "troll": {
        # MM: Large, AC 16, claw +9 (1d6+6) x2, bite +4 (1d6+3), rend 2d6+9, regen 5
        "name": "Troll", "type": "giant", "size": "large",
        "hd": 6, "hit_die": 8, "bab": 4, "base_saves": (5, 2, 2), "cr": 5,
        "abilities": {"str": 23, "dex": 14, "con": 23, "int": 6, "wis": 9, "cha": 6},
        "natural": 5, "speed": 30,
        "natural_attacks": [{"name": "claw", "damage": "1d6", "dtype": "S", "primary": True},
                            {"name": "claw", "damage": "1d6", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "1d6", "dtype": "P",
                             "primary": False}],
        "rend": "2d6+9", "regeneration": {"amount": 5, "bypass": ["fire", "acid"]},
        "skills": {"Listen": 5, "Spot": 6}, "feats": ["Alertness", "Iron Will", "Track"],
        "vision": "darkvision 90 ft., low-light, scent", "evil": True,
        "desc": "A gangly green giant with rubbery skin and long clawed arms. Its wounds "
                "close as you watch. Only fire or acid stops it for good.",
    },
    "wight": {
        # MM: AC 15, slam +3 (1d4+1 plus energy drain)
        "name": "Wight", "type": "undead", "size": "medium",
        "hd": 4, "hit_die": 12, "bab": 2, "base_saves": (1, 1, 4), "cr": 3,
        "abilities": {"str": 12, "dex": 12, "con": None, "int": 11, "wis": 13, "cha": 15},
        "natural": 4, "speed": 30,
        "natural_attacks": [{"name": "slam", "damage": "1d4", "dtype": "B", "primary": True,
                             "drain": {"dc": 14}}],
        "skills": {"Hide": 8, "Listen": 7, "Move Silently": 16, "Spot": 7},
        "feats": ["Alertness", "Blind-Fight"], "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A grave-gaunt corpse with burning eyes. Its touch drains the life from you.",
    },
    "gargoyle": {
        # MM: AC 16, claw +6 (1d4+2) x2, bite +4 (1d6+1), gore +4 (1d6+1), DR 10/magic
        "name": "Gargoyle", "type": "monstrous humanoid", "size": "medium",
        "hd": 4, "hit_die": 8, "bab": 4, "base_saves": (5, 6, 4), "cr": 4,
        "abilities": {"str": 15, "dex": 14, "con": 18, "int": 6, "wis": 11, "cha": 7},
        "natural": 4, "speed": 40,
        "natural_attacks": [{"name": "claw", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "claw", "damage": "1d4", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "1d6", "dtype": "P", "primary": False},
                            {"name": "gore", "damage": "1d6", "dtype": "P",
                             "primary": False}],
        "dr": [(10, "magic")], "skills": {"Hide": 7, "Listen": 4, "Spot": 4},
        "feats": ["Multiattack", "Toughness"], "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A winged stone horror that was a statue a moment ago. Ordinary weapons "
                "glance off it; magic ones bite.",
    },
    "owlbear": {
        # MM: Large, AC 15, claw +7 (1d6+5) x2, bite +2 (1d8+2), improved grab
        "name": "Owlbear", "type": "magical beast", "size": "large",
        "hd": 5, "hit_die": 10, "bab": 5, "base_saves": (9, 5, 2), "cr": 4,
        "abilities": {"str": 21, "dex": 12, "con": 21, "int": 2, "wis": 12, "cha": 10},
        "natural": 5, "speed": 30,
        "natural_attacks": [{"name": "claw", "damage": "1d6", "dtype": "S", "primary": True,
                             "grab": True},
                            {"name": "claw", "damage": "1d6", "dtype": "S", "primary": True},
                            {"name": "bite", "damage": "1d8", "dtype": "P",
                             "primary": False}],
        "skills": {"Listen": 8, "Spot": 8}, "feats": ["Alertness", "Toughness", "Track"],
        "vision": "darkvision 60 ft., low-light, scent", "savage": True,
        "desc": "A furious bear-sized beast with an owl's hooked beak and huge round eyes. "
                "If it gets hold of you, it squeezes.",
    },
    "dire boar": {
        # MM: Large, AC 15, gore +12 (1d8+12)
        "name": "Dire Boar", "type": "animal", "size": "large",
        "hd": 7, "hit_die": 8, "bab": 5, "base_saves": (8, 5, 6), "cr": 4,
        "abilities": {"str": 27, "dex": 10, "con": 17, "int": 2, "wis": 13, "cha": 8},
        "natural": 6, "speed": 40,
        "natural_attacks": [{"name": "gore", "damage": "1d8", "dtype": "S", "primary": True,
                             "str_mult": 1.5}],
        "skills": {"Listen": 8, "Spot": 8}, "feats": ["Alertness", "Endurance", "Iron Will"],
        "vision": "low-light, scent",
        "desc": "A boar the size of an ox, black-bristled, with tusks like scythes.",
    },
    "lizardfolk": {
        # MM: AC 15 (17 with shield), club +2 (1d6+1), javelin +1 (1d6+1)
        "name": "Lizardfolk", "type": "humanoid", "subtypes": ["reptilian"],
        "size": "medium", "hd": 2, "hit_die": 8, "bab": 1, "base_saves": (1, 3, 0),
        "cr": 1,
        "abilities": {"str": 13, "dex": 10, "con": 13, "int": 9, "wis": 10, "cha": 10},
        "natural": 5, "shield": "heavy wooden shield", "weapons": ["club", "javelin"],
        "speed": 30, "skills": {"Balance": 4, "Jump": 5, "Swim": 2},
        "feats": ["Multiattack"], "vision": "-",
        "desc": "A scaled marsh-warrior with a hide shield and a heavy club, its eyes dull "
                "and glassy, as if it's dreaming.",
    },
    "green hag": {
        # MM: AC 22, claw +13 (1d4+4) x2, weakness (2d4 Str, Fort DC 16)
        "name": "Green Hag", "type": "monstrous humanoid", "size": "medium",
        "hd": 9, "hit_die": 8, "bab": 9, "base_saves": (4, 7, 7), "cr": 5,
        "abilities": {"str": 19, "dex": 12, "con": 12, "int": 13, "wis": 13, "cha": 14},
        "natural": 11, "speed": 30,
        "natural_attacks": [{"name": "claw", "damage": "1d4", "dtype": "S", "primary": True,
                             "ability_damage": {"ability": "str", "damage": "2d4", "dc": 16,
                                                "name": "weakness"}},
                            {"name": "claw", "damage": "1d4", "dtype": "S",
                             "primary": True}],
        "sr": 18,
        "skills": {"Concentration": 7, "Hide": 9, "Listen": 11, "Spot": 11, "Swim": 12},
        "feats": ["Alertness", "Blind-Fight", "Combat Casting", "Great Fortitude"],
        "vision": "darkvision 90 ft.", "evil": True,
        "desc": "A stooped crone with mossy skin, lank green hair, and black iron nails. Her "
                "touch withers strength away.",
    },
})

# ---------------------------------------------------------------- monsters with special powers
MONSTERS.update({
    "hell hound": {
        # MM: AC 16, bite +5 (1d8+1 plus 1d6 fire), breath 2d6 fire (Ref DC 13)
        "name": "Hell Hound", "type": "outsider", "subtypes": ["evil", "fire"],
        "size": "medium", "hd": 4, "hit_die": 8, "bab": 4, "base_saves": (4, 4, 4), "cr": 3,
        "abilities": {"str": 13, "dex": 13, "con": 13, "int": 6, "wis": 10, "cha": 6},
        "natural": 5, "speed": 40,
        "natural_attacks": [{"name": "bite", "damage": "1d8", "dtype": "P", "primary": True,
                             "extra_damage": ["1d6", "fire"]}],
        "breath": {"dice": "2d6", "dtype": "fire", "dc": 13, "save": "ref", "targets": 2,
                   "recharge": "2d4", "text": "breathes a cone of fire",
                   "area": ("cone", 10)},
        "immune": ["fire"], "vulnerable": ["cold"],
        "skills": {"Hide": 13, "Listen": 7, "Move Silently": 13, "Spot": 7, "Survival": 7},
        "feats": ["Improved Initiative", "Run", "Track"], "vision": "darkvision 60 ft.",
        "evil": True,
        "desc": "A rust-red hound with smoke curling from its jaws and eyes like coals.",
    },
    "shadow": {
        # MM: incorporeal, AC 13, incorporeal touch +3 (1d6 Strength damage)
        "name": "Shadow", "type": "undead", "size": "medium", "hd": 3, "hit_die": 12,
        "bab": 1, "base_saves": (1, 1, 3), "cr": 3,
        "abilities": {"str": None, "dex": 14, "con": None, "int": 6, "wis": 12, "cha": 13},
        "natural": 0, "deflection": 1, "speed": 30, "fly": 40, "incorporeal": True,
        "natural_attacks": [{"name": "incorporeal touch", "damage": "0", "dtype": "",
                             "primary": True, "touch": True, "finesse": True,
                             "no_damage": True,
                             "ability_damage": {"ability": "str", "damage": "1d6",
                                                "nosave": True, "name": "shadow touch"}}],
        "skills": {"Hide": 8, "Listen": 7, "Search": 4, "Spot": 7},
        "feats": ["Alertness", "Dodge"], "vision": "darkvision 60 ft.", "evil": True,
        "mindless": False,
        "desc": "A patch of darkness shaped like a man that slides along the walls. "
                "Ordinary weapons pass right through it; its touch saps your strength.",
    },
    "wraith": {
        # MM: incorporeal, AC 15, incorporeal touch +5 (1d4 + 1d6 Con drain, Fort DC 14)
        "name": "Wraith", "type": "undead", "size": "medium", "hd": 5, "hit_die": 12,
        "bab": 2, "base_saves": (1, 1, 4), "cr": 5,
        "abilities": {"str": None, "dex": 16, "con": None, "int": 14, "wis": 14, "cha": 15},
        "natural": 0, "deflection": 2, "speed": 30, "fly": 60, "incorporeal": True,
        "natural_attacks": [{"name": "incorporeal touch", "damage": "1d4", "dtype": "",
                             "primary": True, "touch": True, "finesse": True,
                             "ability_damage": {"ability": "con", "damage": "1d6", "dc": 14,
                                                "name": "wraith's chill"}}],
        "skills": {"Hide": 11, "Intimidate": 10, "Listen": 12, "Search": 10, "Spot": 12},
        "feats": ["Alertness", "Blind-Fight", "Combat Reflexes", "Improved Initiative"],
        "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A cowled shape of living shadow with two pinpoints of red light for eyes.",
    },
    "mummy": {
        # MM: AC 20, slam +11 (1d6+10 plus mummy rot), despair, DR 5/-
        "name": "Mummy", "type": "undead", "size": "medium", "hd": 8, "hit_die": 12,
        "bab": 4, "base_saves": (2, 2, 6), "cr": 5,
        "abilities": {"str": 24, "dex": 10, "con": None, "int": 6, "wis": 14, "cha": 15},
        "natural": 10, "speed": 20, "bonus_hp": 3,
        "natural_attacks": [{"name": "slam", "damage": "1d6", "dtype": "B", "primary": True,
                             "str_mult": 1.5,
                             "disease": {"name": "mummy rot", "dc": 16, "damage": "1d6",
                                         "ability": "con", "incubation": 1}}],
        "fear_aura": {"dc": 16, "effect": "paralyzed", "duration": "1d4",
                      "text": "The mummy's gaze falls on you, and dread seizes your limbs"},
        "dr": [(5, "-")], "vulnerable": ["fire"],
        "skills": {"Hide": 7, "Listen": 8, "Move Silently": 7, "Spot": 8},
        "feats": ["Alertness", "Great Fortitude", "Toughness"],
        "vision": "darkvision 60 ft.", "evil": True,
        "desc": "A towering corpse in rotting linen, its eyes burning with hatred.",
    },
    "wyvern": {
        # MM: Large dragon, AC 18, sting +10 (1d6+4 plus poison), bite +8 (2d8+4)
        "name": "Wyvern", "type": "dragon", "size": "large", "hd": 7, "hit_die": 12,
        "bab": 7, "base_saves": (5, 5, 5), "cr": 6,
        "abilities": {"str": 19, "dex": 12, "con": 15, "int": 6, "wis": 12, "cha": 9},
        "natural": 8, "speed": 20, "fly": 60, "flyby": True,
        "natural_attacks": [{"name": "sting", "damage": "1d6", "dtype": "P", "primary": True,
                             "poison": {"dc": 17, "ability": "con", "damage": "2d6",
                                        "name": "wyvern venom"}},
                            {"name": "bite", "damage": "2d8", "dtype": "P",
                             "primary": False}],
        "immune": ["sleep", "paralysis"],
        "skills": {"Hide": 7, "Listen": 13, "Move Silently": 11, "Spot": 16},
        "feats": ["Ability Focus", "Alertness", "Flyby Attack"],
        "vision": "darkvision 60 ft., low-light, scent", "evil": True,
        "desc": "A great grey-brown wyvern, wings snapping, its barbed tail arched to sting.",
    },
    "ogre mage": {
        # MM: Large giant, AC 18, greatsword +7 (3d6+7), cone of cold, regen 5, SR 19
        "name": "Ogre Mage", "type": "giant", "size": "large", "hd": 5, "hit_die": 8,
        "bab": 3, "base_saves": (4, 1, 1), "cr": 8,
        "abilities": {"str": 21, "dex": 10, "con": 17, "int": 14, "wis": 14, "cha": 17},
        "natural": 5, "armor": "chain shirt", "weapons": ["greatsword", "longbow"],
        "speed": 40, "fly": 40, "sr": 19,
        "regeneration": {"amount": 5, "bypass": ["fire", "acid"]},
        "slas": [{"spell": "Cone of Cold", "cl": 9, "dc": 18, "uses": 1},
                 {"spell": "Sleep", "cl": 9, "dc": 14, "uses": 1},
                 {"spell": "Invisibility", "cl": 9, "uses": 1, "self": True}],
        "skills": {"Concentration": 11, "Listen": 10, "Spellcraft": 10, "Spot": 10},
        "feats": ["Combat Expertise", "Improved Initiative"],
        "vision": "darkvision 90 ft., low-light", "evil": True,
        "desc": "A blue-skinned giant with ivory horns, fine robes over chain, and a "
                "greatsword. Cold magic crackles around its fingers.",
    },
    "juvenile white dragon": {
        # MM: Large dragon, AC 21, bite +16 (2d6+4), breath 4d6 cold (Ref DC 18)
        "name": "Juvenile White Dragon", "type": "dragon", "subtypes": ["cold"],
        "size": "large", "hd": 12, "hit_die": 12, "bab": 12, "base_saves": (8, 8, 8),
        "cr": 6,
        "abilities": {"str": 19, "dex": 10, "con": 15, "int": 8, "wis": 11, "cha": 8},
        "natural": 12, "speed": 60, "fly": 150,
        "natural_attacks": [{"name": "bite", "damage": "2d6", "dtype": "P", "primary": True},
                            {"name": "claw", "damage": "1d8", "dtype": "S", "primary": False},
                            {"name": "claw", "damage": "1d8", "dtype": "S",
                             "primary": False}],
        "breath": {"dice": "4d6", "dtype": "cold", "dc": 18, "save": "ref", "targets": 3,
                   "recharge": "1d4", "text": "breathes a freezing cone of ice and frost",
                   "area": ("cone", 40)},
        "immune": ["cold", "sleep", "paralysis"], "vulnerable": ["fire"],
        "skills": {"Hide": 5, "Listen": 12, "Search": 10, "Spot": 12, "Swim": 19},
        "feats": ["Alertness", "Hover", "Improved Initiative", "Power Attack"],
        "vision": "darkvision 120 ft., blindsense", "evil": True,
        "desc": "A white dragon the size of a cart-horse, frost smoking from its nostrils.",
    },
})

MONSTERS["heavy warhorse"] = {
    # MM: Large animal, AC 14, hoof +6 (1d6+4) x2, bite +1 (1d4+2)
    "name": "Heavy Warhorse", "type": "animal", "size": "large", "hd": 4, "hit_die": 8,
    "bab": 3, "base_saves": (4, 4, 1), "cr": 2,
    "abilities": {"str": 18, "dex": 13, "con": 17, "int": 6, "wis": 13, "cha": 6},
    "natural": 4, "speed": 50,
    "natural_attacks": [{"name": "hoof", "damage": "1d6", "dtype": "B", "primary": True},
                        {"name": "hoof", "damage": "1d6", "dtype": "B", "primary": True},
                        {"name": "bite", "damage": "1d4", "dtype": "P", "primary": False}],
    "skills": {"Listen": 5, "Spot": 4}, "feats": ["Endurance", "Run"],
    "vision": "low-light, scent",
    "desc": "A great white warhorse with intelligent eyes and a coat that seems to glow.",
}

def _elemental(name, ab, natural, slam, speed, desc, extra=None, **kw):
    d = {"name": f"Large {name} Elemental", "type": "elemental", "subtypes": [name.lower()],
         "size": "large", "hd": 8, "hit_die": 8, "bab": 6, "cr": 5,
         "abilities": dict(zip(("str", "dex", "con", "int", "wis", "cha"), ab)),
         "natural": natural, "speed": speed,
         "natural_attacks": [{"name": "slam", "damage": slam, "dtype": "B", "primary": True,
                              **({"extra_damage": extra} if extra else {})},
                             {"name": "slam", "damage": slam, "dtype": "B", "primary": True,
                              **({"extra_damage": extra} if extra else {})}],
         "immune": ["poison", "sleep", "paralysis", "stun", "mind-affecting"],
         "mindless": False, "skills": {"Listen": 7, "Spot": 7}, "feats": ["Power Attack"],
         "vision": "darkvision 60 ft.", "desc": desc}
    d.update(kw)
    return d


MONSTERS.update({
    "large air elemental": _elemental("Air", (18, 25, 16, 6, 11, 11), 4, "2d6", 30,
                                      "A howling column of wind with a vague, angry face.",
                                      fly=100, base_saves=(4, 8, 2)),
    "large earth elemental": _elemental("Earth", (25, 8, 19, 6, 11, 11), 10, "2d8", 20,
                                        "A hulking mass of stone and soil that shakes the "
                                        "ground.", base_saves=(8, 2, 2)),
    "large fire elemental": _elemental("Fire", (16, 25, 16, 6, 11, 11), 4, "2d6", 50,
                                       "A roaring pillar of living flame.", ["1d8", "fire"],
                                       base_saves=(4, 8, 2), vulnerable=["cold"]),
    "large water elemental": _elemental("Water", (24, 14, 19, 6, 11, 11), 7, "2d10", 20,
                                        "A surging wave that rises up with grasping arms.",
                                        base_saves=(8, 4, 2)),
})
MONSTERS["large fire elemental"]["immune"] = MONSTERS["large fire elemental"]["immune"] + [
    "fire"]

# Animal companions: key -> (minimum effective druid level, levels subtracted)
COMPANIONS = {
    "wolf": (1, 0), "riding dog": (1, 0), "eagle": (1, 0),
    "black bear": (4, 3), "leopard": (4, 3),
}

# Familiars: what the master gains (plus Alertness while it's near)
FAMILIARS = {
    "bat": ("skill:Listen", 3, "+3 on Listen checks"),
    "cat": ("skill:Move Silently", 3, "+3 on Move Silently checks"),
    "hawk": ("skill:Spot", 3, "+3 on Spot checks in bright light"),
    "lizard": ("skill:Climb", 3, "+3 on Climb checks"),
    "owl": ("skill:Spot", 3, "+3 on Spot checks in shadows"),
    "rat": ("save_fort", 2, "+2 on Fortitude saves"),
    "raven": ("skill:Appraise", 3, "+3 on Appraise checks (and it can talk)"),
    "snake": ("skill:Bluff", 3, "+3 on Bluff checks"),
    "toad": ("hp", 3, "+3 hit points"),
    "weasel": ("save_ref", 2, "+2 on Reflex saves"),
}

WILD_SHAPES = {  # key: minimum druid level
    "wolf": 5, "black bear": 5, "leopard": 5, "brown bear": 8, "dire wolf": 8,
}
ELEMENTAL_SHAPES = {"large air elemental": 16, "large earth elemental": 16,
                    "large fire elemental": 16, "large water elemental": 16}


# ---------------------------------------------------------------- bestiary, part 3
def _sv(hd, good):
    """Base saves from Hit Dice: good = 2 + HD/2, poor = HD/3. good is e.g. "FR"."""
    return tuple(2 + hd // 2 if k in good else hd // 3 for k in "FRW")


def _a(name, damage, dtype, primary=True, **special):
    return dict({"name": name, "damage": damage, "dtype": dtype, "primary": primary}, **special)


def _mon(name, mtype, size, hd, hit_die, bab, good, cr, ab, natural, speed, desc, **kw):
    d = {"name": name, "type": mtype, "size": size, "hd": hd, "hit_die": hit_die, "bab": bab,
         "base_saves": _sv(hd, good), "cr": cr,
         "abilities": dict(zip(("str", "dex", "con", "int", "wis", "cha"), ab)),
         "natural": natural, "speed": speed, "skills": {"Listen": 4, "Spot": 4},
         "feats": [], "vision": "darkvision 60 ft.", "desc": desc}
    d.update(kw)
    return d


_PAR = {"dc": 15, "duration": "1d4+1"}
MONSTERS.update({
    # ---- people
    "human bandit": _mon(
        "Bandit", "humanoid", "medium", 1, 8, 1, "F", 0.5, (13, 11, 12, 10, 9, 8), 0, 30,
        "A hard-eyed outlaw in patched leather.", armor="studded leather",
        weapons=["short sword", "light crossbow"], vision="normal", morale=True),
    "dark acolyte": _mon(
        "Dark acolyte", "humanoid", "medium", 3, 8, 2, "FW", 3, (12, 10, 12, 10, 15, 12), 0, 20,
        "A robed priest of some hungry god, a black iron mace in hand.",
        armor="chain shirt", shield="light wooden shield", weapons=["heavy mace"],
        vision="normal", evil=True,
        slas=[{"spell": "Cause Fear", "cl": 3, "dc": 13, "uses": 2},
              {"spell": "Hold Person", "cl": 3, "dc": 14, "uses": 1}]),
    "hobgoblin warcaster": _mon(
        "Hobgoblin warcaster", "humanoid", "medium", 3, 4, 1, "W", 3, (10, 14, 12, 15, 10, 10),
        0, 30, "A hobgoblin in a soot-stained coat, fingers already sketching fire.",
        subtypes=["goblinoid"], weapons=["quarterstaff"], evil=True,
        slas=[{"spell": "Magic Missile", "cl": 3, "dc": 13, "uses": 3},
              {"spell": "Burning Hands", "cl": 3, "dc": 13, "uses": 2}]),
    "minotaur": _mon(
        "Minotaur", "monstrous humanoid", "large", 6, 8, 6, "RW", 4, (19, 10, 15, 7, 10, 8), 5,
        30, "A bull-headed brute hefting an axe as long as you are tall.",
        weapons=["greataxe"], evil=True),
    "medusa": _mon(
        "Medusa", "monstrous humanoid", "medium", 6, 8, 6, "RW", 7, (10, 15, 12, 12, 13, 15),
        3, 30, "A veiled woman with a nest of hissing snakes for hair. Don't meet her eyes.",
        weapons=["shortbow", "dagger"], gaze={"dc": 15, "range": 30}, evil=True,
        natural_attacks=[_a("snakes", "1d4", "P", False, poison={
            "dc": 14, "ability": "str", "damage": "1d6", "name": "medusa venom"})]),
    # ---- giants
    "ettin": _mon("Ettin", "giant", "large", 10, 8, 7, "F", 6, (23, 8, 15, 6, 10, 11), 7, 30,
                  "A two-headed giant, each head arguing with the other about who gets to "
                  "hit you.", armor="hide", weapons=["morningstar", "javelin"], evil=True),
    "hill giant": _mon("Hill giant", "giant", "large", 12, 8, 9, "F", 7,
                       (25, 8, 19, 6, 10, 7), 9, 30,
                       "A slab-muscled giant in stinking hides, swinging a tree trunk.",
                       armor="hide", weapons=["greatclub", "javelin"], evil=True),
    "stone giant": _mon("Stone giant", "giant", "large", 14, 8, 10, "F", 8,
                        (27, 15, 19, 10, 12, 11), 11, 30,
                        "A grey, hairless giant with skin like weathered granite.",
                        armor="hide", weapons=["greatclub", "javelin"]),
    "frost giant": _mon("Frost giant", "giant", "large", 14, 8, 10, "F", 9,
                        (29, 9, 21, 10, 14, 11), 9, 40,
                        "A blue-skinned giant with an icicle beard and a rime-crusted axe.",
                        subtypes=["cold"], armor="chain shirt", weapons=["greataxe"],
                        immune=["cold"], vulnerable=["fire"], evil=True),
    "fire giant": _mon("Fire giant", "giant", "large", 15, 8, 11, "F", 10,
                       (31, 9, 21, 10, 14, 11), 8, 30,
                       "A coal-black giant with hair of flame, armored in blackened plate.",
                       subtypes=["fire"], armor="half-plate", weapons=["greatsword"],
                       immune=["fire"], vulnerable=["cold"], evil=True),
    # ---- undead
    "ghast": _mon("Ghast", "undead", "medium", 4, 12, 2, "W", 3, (17, 17, None, 13, 14, 16), 4,
                  30, "A ghoul gone worse: bloated, clever, and stinking of the grave.",
                  natural_attacks=[_a("bite", "1d8", "P", paralysis=_PAR),
                                   _a("claw", "1d4", "S", False, paralysis=_PAR),
                                   _a("claw", "1d4", "S", False, paralysis=_PAR)],
                  evil=True, savage=True),
    "ogre zombie": _mon("Ogre zombie", "undead", "large", 8, 12, 4, "W", 3,
                        (23, 6, None, None, 10, 1), 5, 30,
                        "A dead ogre, grey and sagging, that has not stopped walking.",
                        weapons=["greatclub"], dr=[(5, "S")], mindless=True,
                        single_actions=True, immune=["mind-affecting"], evil=True),
    "vampire spawn": _mon("Vampire spawn", "undead", "medium", 4, 12, 2, "W", 4,
                          (16, 14, None, 13, 13, 14), 3, 30,
                          "Pale, quick and smiling, with too many teeth in the smile.",
                          natural_attacks=[_a("slam", "1d6", "B", drain={"dc": 14})],
                          dr=[(5, "magic")], evil=True),
    "spectre": _mon("Spectre", "undead", "medium", 7, 12, 3, "W", 7,
                    (None, 16, None, 14, 14, 15), 0, 40,
                    "A hateful, translucent figure that still wears the face it died with.",
                    deflection=2, fly=80, incorporeal=True, evil=True,
                    natural_attacks=[_a("incorporeal touch", "1d8", "", touch=True,
                                        finesse=True, drain={"dc": 15})]),
    # ---- animals
    "boar": _mon("Boar", "animal", "medium", 3, 8, 2, "FR", 2, (15, 10, 17, 2, 13, 4), 6, 40,
                 "A bristling wild boar with yellow tusks and no fear at all.",
                 natural_attacks=[_a("gore", "1d8", "P", str_mult=1.5)], savage=True,
                 vision="low-light, scent"),
    "wolverine": _mon("Wolverine", "animal", "medium", 3, 8, 2, "FR", 2,
                      (14, 15, 19, 2, 12, 10), 2, 30,
                      "Forty pounds of teeth and bad temper.",
                      natural_attacks=[_a("claw", "1d4", "S"), _a("claw", "1d4", "S"),
                                       _a("bite", "1d6", "P", False)], savage=True,
                      vision="low-light, scent"),
    "crocodile": _mon("Crocodile", "animal", "medium", 3, 8, 2, "FR", 2,
                      (19, 12, 17, 1, 12, 2), 4, 20,
                      "A log with eyes, until it moves.",
                      natural_attacks=[_a("bite", "1d8", "P", str_mult=1.5, grab=True)],
                      vision="low-light"),
    "giant crocodile": _mon("Giant crocodile", "animal", "huge", 7, 8, 5, "FR", 4,
                            (27, 12, 19, 1, 12, 2), 7, 20,
                            "A crocodile as long as a river barge.",
                            natural_attacks=[_a("bite", "2d8", "P", str_mult=1.5, grab=True)],
                            vision="low-light"),
    "lion": _mon("Lion", "animal", "large", 5, 8, 3, "FR", 3, (21, 17, 15, 2, 12, 6), 3, 40,
                 "A tawny lion, shoulders rolling as it paces.",
                 natural_attacks=[_a("claw", "1d4", "S"), _a("claw", "1d4", "S"),
                                  _a("bite", "1d8", "P", False, grab=True)],
                 vision="low-light, scent"),
    "tiger": _mon("Tiger", "animal", "large", 6, 8, 4, "FR", 4, (23, 15, 17, 2, 12, 6), 3, 40,
                  "Stripes in the tall grass, and then four hundred pounds of cat.",
                  natural_attacks=[_a("claw", "1d8", "S", grab=True), _a("claw", "1d8", "S"),
                                   _a("bite", "2d6", "P", False)],
                  vision="low-light, scent"),
    "dire ape": _mon("Dire ape", "animal", "large", 5, 8, 3, "FR", 3,
                     (22, 15, 14, 2, 12, 7), 4, 30,
                     "A shaggy ape twice the size of a man, beating its chest.",
                     natural_attacks=[_a("claw", "1d6", "S"), _a("claw", "1d6", "S"),
                                      _a("bite", "1d8", "P", False)], rend="2d6+9",
                     vision="low-light, scent"),
    "dire bear": _mon("Dire bear", "animal", "large", 12, 8, 9, "FR", 7,
                      (31, 13, 19, 2, 12, 10), 7, 40,
                      "A cave bear from an older age, as tall at the shoulder as a horse.",
                      natural_attacks=[_a("claw", "2d4", "S", grab=True), _a("claw", "2d4", "S"),
                                       _a("bite", "2d8", "P", False)],
                      vision="low-light, scent"),
    "dire tiger": _mon("Dire tiger", "animal", "large", 16, 8, 12, "FR", 8,
                       (27, 15, 17, 2, 12, 10), 6, 40,
                       "A sabre-toothed cat the size of an ox.",
                       natural_attacks=[_a("claw", "2d4", "S", grab=True), _a("claw", "2d4", "S"),
                                        _a("bite", "2d6", "P", False)],
                       vision="low-light, scent"),
    # ---- vermin
    "large monstrous spider": _mon(
        "Large monstrous spider", "vermin", "large", 4, 8, 3, "F", 2,
        (15, 17, 12, None, 10, 2), 1, 30, "A spider the size of a pony, eyes like wet beads.",
        natural_attacks=[_a("bite", "1d8", "P", poison={
            "dc": 13, "ability": "str", "damage": "1d6", "name": "spider venom"})],
        mindless=True, immune=["mind-affecting"]),
    "giant wasp": _mon(
        "Giant wasp", "vermin", "large", 5, 8, 3, "F", 3, (18, 12, 14, None, 13, 11), 4, 20,
        "A wasp as big as a hound, its drone rattling your teeth.", fly=60,
        natural_attacks=[_a("sting", "1d3", "P", str_mult=1.5, poison={
            "dc": 14, "ability": "dex", "damage": "1d6", "name": "wasp venom"})],
        mindless=True, immune=["mind-affecting"]),
    "giant scorpion": _mon(
        "Giant scorpion", "vermin", "large", 5, 8, 3, "F", 3, (19, 10, 14, None, 10, 2), 6, 50,
        "A scorpion as long as a wagon, claws clacking.",
        natural_attacks=[_a("claw", "1d6", "B", grab=True), _a("claw", "1d6", "B"),
                         _a("sting", "1d6", "P", False, poison={
                             "dc": 14, "ability": "con", "damage": "1d4",
                             "name": "scorpion venom"})],
        constrict="1d6+4", mindless=True, immune=["mind-affecting"]),
    # ---- beasts and horrors
    "giant eagle": _mon("Giant eagle", "magical beast", "large", 4, 10, 4, "FR", 3,
                        (18, 17, 12, 10, 14, 10), 3, 10,
                        "A noble eagle with a twenty-foot wingspan.", fly=80,
                        natural_attacks=[_a("claw", "1d6", "S"), _a("claw", "1d6", "S"),
                                         _a("bite", "1d8", "P", False)],
                        vision="low-light"),
    "griffon": _mon("Griffon", "magical beast", "large", 7, 10, 7, "FR", 4,
                    (18, 15, 16, 5, 13, 8), 6, 30,
                    "Half lion, half eagle, all appetite. It likes horses best.", fly=80,
                    natural_attacks=[_a("bite", "2d6", "P"), _a("claw", "1d4", "S", False),
                                     _a("claw", "1d4", "S", False)]),
    "ankheg": _mon("Ankheg", "magical beast", "large", 3, 10, 3, "FR", 3,
                   (21, 10, 17, 1, 13, 6), 8, 30,
                   "A burrowing insect-thing the size of a cart, mandibles dripping acid.",
                   natural_attacks=[_a("bite", "2d6", "P", str_mult=1.5, grab=True,
                                       extra_damage=["1d4", "acid"])]),
    "cockatrice": _mon("Cockatrice", "magical beast", "small", 5, 10, 5, "FR", 3,
                       (6, 17, 11, 2, 13, 9), 0, 20,
                       "A scrawny rooster with a lizard's tail and bat wings. Its peck turns "
                       "flesh to stone.", fly=60,
                       natural_attacks=[_a("bite", "1d4", "P", finesse=True,
                                           petrify={"dc": 12})]),
    "winter wolf": _mon("Winter wolf", "magical beast", "large", 6, 10, 6, "FR", 5,
                        (18, 13, 16, 9, 13, 10), 5, 50,
                        "A white wolf the size of a horse, breath smoking with cold.",
                        subtypes=["cold"], immune=["cold"], vulnerable=["fire"], evil=True,
                        natural_attacks=[_a("bite", "1d8", "P", str_mult=1.5, trip=True,
                                            extra_damage=["1d6", "cold"])],
                        breath={"dice": "4d6", "dtype": "cold", "dc": 16, "save": "ref",
                                "targets": 2, "recharge": "1d4",
                                "text": "breathes a cone of killing frost",
                                "area": ("cone", 15)}),
    "chimera": _mon("Chimera", "magical beast", "large", 9, 10, 9, "FR", 7,
                    (19, 13, 17, 4, 13, 10), 9, 30,
                    "A lion's body with three heads: lion, goat, and a red dragon that is "
                    "already drawing breath.", fly=50, evil=True,
                    natural_attacks=[_a("bite", "2d6", "P"), _a("bite", "1d8", "P", False),
                                     _a("gore", "1d8", "P", False), _a("claw", "1d6", "S", False),
                                     _a("claw", "1d6", "S", False)],
                    breath={"dice": "3d8", "dtype": "fire", "dc": 17, "save": "ref",
                            "targets": 3, "recharge": "1d4", "text": "breathes a cone of fire",
                            "area": ("cone", 20)}),
    "bulette": _mon("Bulette", "magical beast", "huge", 9, 10, 9, "FR", 7,
                    (27, 15, 20, 2, 13, 6), 12, 40,
                    "An armored land shark that erupts out of the ground under your feet.",
                    natural_attacks=[_a("bite", "2d8", "P"), _a("claw", "2d6", "S", False),
                                     _a("claw", "2d6", "S", False)], savage=True),
    "carrion crawler": _mon(
        "Carrion crawler", "aberration", "large", 3, 8, 2, "W", 4, (14, 15, 14, 1, 15, 6), 6, 30,
        "A pale segmented worm with a fringe of twitching tentacles around its mouth.",
        natural_attacks=[_a("tentacle", "0", "", no_damage=True, touch=True,
                            paralysis={"dc": 13, "duration": "2d4"}),
                         _a("tentacle", "0", "", no_damage=True, touch=True,
                            paralysis={"dc": 13, "duration": "2d4"}),
                         _a("bite", "1d4", "P", False)]),
    "ettercap": _mon("Ettercap", "aberration", "medium", 5, 8, 3, "W", 3,
                     (14, 17, 13, 6, 15, 8), 1, 30,
                     "A hunched, pot-bellied spider-man with venom beading on its fangs.",
                     natural_attacks=[_a("bite", "1d8", "P", poison={
                         "dc": 15, "ability": "dex", "damage": "1d6", "name": "ettercap venom"}),
                                      _a("claw", "1d3", "S", False), _a("claw", "1d3", "S", False)],
                     evil=True),
    "gelatinous cube": _mon(
        "Gelatinous cube", "ooze", "large", 4, 10, 3, "", 3, (10, 1, 26, None, 1, 1), 0, 15,
        "A ten-foot block of clear jelly filling the passage, bones drifting inside it.",
        natural_attacks=[_a("slam", "1d6", "B", extra_damage=["1d6", "acid"],
                            paralysis={"dc": 20, "duration": "3d6"})],
        mindless=True, immune=["mind-affecting", "sleep", "paralysis", "electricity"]),
    "ochre jelly": _mon(
        "Ochre jelly", "ooze", "large", 6, 10, 4, "", 5, (15, 1, 22, None, 1, 1), 0, 10,
        "A heaving yellow-brown slime that eats flesh and leaves the bones.",
        natural_attacks=[_a("slam", "2d4", "B", extra_damage=["1d4", "acid"], grab=True)],
        constrict="2d4+3", mindless=True,
        immune=["mind-affecting", "sleep", "paralysis"]),
    "treant": _mon("Treant", "plant", "huge", 7, 8, 5, "F", 8, (29, 8, 21, 12, 16, 12), 13, 30,
                   "An ancient oak that has decided to walk, and is not pleased with you.",
                   natural_attacks=[_a("slam", "2d6", "B"), _a("slam", "2d6", "B")],
                   dr=[(10, "S")], vulnerable=["fire"],
                   immune=["mind-affecting", "sleep", "paralysis"], vision="low-light"),
    # ---- dragons
    "young black dragon": _mon(
        "Young black dragon", "dragon", "medium", 10, 12, 10, "FRW", 5,
        (15, 10, 15, 10, 11, 10), 9, 60,
        "A gaunt, horned dragon the color of a tar pit, dripping swamp water.", fly=150,
        subtypes=["water"], immune=["acid", "sleep", "paralysis"], evil=True,
        natural_attacks=[_a("bite", "1d8", "P"), _a("claw", "1d6", "S", False),
                         _a("claw", "1d6", "S", False)],
        breath={"dice": "6d4", "dtype": "acid", "dc": 17, "save": "ref", "targets": 3,
                "recharge": "1d4", "text": "spits a hissing line of acid",
                "area": ("line", 60)}),
    "young red dragon": _mon(
        "Young red dragon", "dragon", "large", 13, 12, 13, "FRW", 7,
        (21, 10, 15, 12, 13, 12), 12, 40,
        "Scarlet scales, a furnace glow in its throat, and the certainty that you are prey.",
        fly=150, subtypes=["fire"], immune=["fire", "sleep", "paralysis"],
        vulnerable=["cold"], evil=True,
        natural_attacks=[_a("bite", "2d6", "P"), _a("claw", "1d8", "S", False),
                         _a("claw", "1d8", "S", False)],
        breath={"dice": "6d10", "dtype": "fire", "dc": 18, "save": "ref", "targets": 3,
                "recharge": "1d4", "text": "breathes a roaring cone of fire",
                "area": ("cone", 40)}),
})

# true base saves for the round-4 monsters
for _k, (_hd, _good) in {"constrictor snake": (3, "FR"), "giant constrictor snake": (11, "FR"),
                         "rat swarm": (4, "FR"), "basilisk": (6, "FR"), "elephant": (11, "FR"),
                         "tyrannosaurus": (18, "FR")}.items():
    MONSTERS[_k]["base_saves"] = _sv(_hd, _good)
