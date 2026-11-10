"""Skills (SRD 3.5). acp: armor check penalty applies (2 = double, Swim)."""

KNOWLEDGES = [
    "arcana", "architecture and engineering", "dungeoneering", "geography",
    "history", "local", "nature", "nobility and royalty", "religion", "the planes",
]

SKILLS = {
    "Appraise": {"ability": "int"},
    "Balance": {"ability": "dex", "acp": 1},
    "Bluff": {"ability": "cha"},
    "Climb": {"ability": "str", "acp": 1},
    "Concentration": {"ability": "con"},
    "Craft": {"ability": "int"},
    "Decipher Script": {"ability": "int", "trained": True},
    "Diplomacy": {"ability": "cha"},
    "Disable Device": {"ability": "int", "trained": True},
    "Disguise": {"ability": "cha"},
    "Escape Artist": {"ability": "dex", "acp": 1},
    "Forgery": {"ability": "int"},
    "Gather Information": {"ability": "cha"},
    "Handle Animal": {"ability": "cha", "trained": True},
    "Heal": {"ability": "wis"},
    "Hide": {"ability": "dex", "acp": 1},
    "Intimidate": {"ability": "cha"},
    "Jump": {"ability": "str", "acp": 1},
    "Listen": {"ability": "wis"},
    "Move Silently": {"ability": "dex", "acp": 1},
    "Open Lock": {"ability": "dex", "trained": True},
    "Perform": {"ability": "cha"},
    "Profession": {"ability": "wis", "trained": True},
    "Ride": {"ability": "dex"},
    "Search": {"ability": "int"},
    "Sense Motive": {"ability": "wis"},
    "Sleight of Hand": {"ability": "dex", "acp": 1, "trained": True},
    "Spellcraft": {"ability": "int", "trained": True},
    "Spot": {"ability": "wis"},
    "Survival": {"ability": "wis"},
    "Swim": {"ability": "str", "acp": 2},
    "Tumble": {"ability": "dex", "acp": 1, "trained": True},
    "Use Magic Device": {"ability": "cha", "trained": True},
    "Use Rope": {"ability": "dex"},
}
for _k in KNOWLEDGES:
    SKILLS[f"Knowledge ({_k})"] = {"ability": "int", "trained": True}

SKILL_ORDER = sorted(SKILLS)

# Synergy bonuses (+2 when you have 5+ ranks in the source skill)
SYNERGIES = [
    ("Bluff", "Diplomacy"), ("Bluff", "Intimidate"), ("Bluff", "Sleight of Hand"),
    ("Handle Animal", "Ride"), ("Jump", "Tumble"), ("Tumble", "Balance"),
    ("Tumble", "Jump"), ("Sense Motive", "Diplomacy"),
    ("Knowledge (arcana)", "Spellcraft"), ("Knowledge (religion)", "Knowledge (the planes)"),
    ("Knowledge (dungeoneering)", "Survival"), ("Knowledge (nature)", "Survival"),
    ("Knowledge (local)", "Gather Information"), ("Search", "Survival"),
    ("Survival", "Knowledge (nature)"), ("Use Rope", "Climb"), ("Escape Artist", "Use Rope"),
    ("Spellcraft", "Use Magic Device"), ("Decipher Script", "Use Magic Device"),
]
