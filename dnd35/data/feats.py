"""Feats (SRD 3.5 subset with implemented mechanics).

prereq keys: ability scores ("str": 13), "bab", "feats", "caster", "fighter_level",
"turn_undead", "proficient".
param: if set, the feat is taken with a parameter (weapon, skill, school).
"""

FEATS = {
    "Acrobatic": {"desc": "+2 Jump and Tumble.", "skills": {"Jump": 2, "Tumble": 2}},
    "Agile": {"desc": "+2 Balance and Escape Artist.",
              "skills": {"Balance": 2, "Escape Artist": 2}},
    "Alertness": {"desc": "+2 Listen and Spot.", "skills": {"Listen": 2, "Spot": 2}},
    "Animal Affinity": {"desc": "+2 Handle Animal and Ride.",
                        "skills": {"Handle Animal": 2, "Ride": 2}},
    "Athletic": {"desc": "+2 Climb and Swim.", "skills": {"Climb": 2, "Swim": 2}},
    "Deceitful": {"desc": "+2 Disguise and Forgery.", "skills": {"Disguise": 2, "Forgery": 2}},
    "Diligent": {"desc": "+2 Appraise and Decipher Script.",
                 "skills": {"Appraise": 2, "Decipher Script": 2}},
    "Investigator": {"desc": "+2 Gather Information and Search.",
                     "skills": {"Gather Information": 2, "Search": 2}},
    "Magical Aptitude": {"desc": "+2 Spellcraft and Use Magic Device.",
                         "skills": {"Spellcraft": 2, "Use Magic Device": 2}},
    "Negotiator": {"desc": "+2 Diplomacy and Sense Motive.",
                   "skills": {"Diplomacy": 2, "Sense Motive": 2}},
    "Nimble Fingers": {"desc": "+2 Disable Device and Open Lock.",
                       "skills": {"Disable Device": 2, "Open Lock": 2}},
    "Persuasive": {"desc": "+2 Bluff and Intimidate.", "skills": {"Bluff": 2, "Intimidate": 2}},
    "Self-Sufficient": {"desc": "+2 Heal and Survival.", "skills": {"Heal": 2, "Survival": 2}},
    "Stealthy": {"desc": "+2 Hide and Move Silently.", "skills": {"Hide": 2, "Move Silently": 2}},
    "Skill Focus": {"desc": "+3 on checks with the chosen skill.", "param": "skill"},

    "Great Fortitude": {"desc": "+2 on Fortitude saves."},
    "Iron Will": {"desc": "+2 on Will saves."},
    "Lightning Reflexes": {"desc": "+2 on Reflex saves."},
    "Toughness": {"desc": "+3 hit points."},
    "Endurance": {"desc": "+4 on checks to resist fatigue, cold, running, etc. (flavor)."},
    "Run": {"desc": "Run at x5 speed (flavor)."},
    "Improved Initiative": {"desc": "+4 on initiative checks.", "fighter": True},
    "Blind-Fight": {"desc": "Reroll miss chance from concealment once.", "fighter": True},
    "Combat Expertise": {"desc": "Option: take up to -5 on attacks (max BAB) for an equal "
                                 "dodge bonus to AC.", "prereq": {"int": 13}, "fighter": True},
    "Dodge": {"desc": "+1 dodge bonus to AC.", "prereq": {"dex": 13}, "fighter": True},
    "Mobility": {"desc": "+4 dodge bonus to AC against attacks of opportunity from moving.",
                 "prereq": {"dex": 13, "feats": ["Dodge"]}, "fighter": True},
    "Power Attack": {"desc": "Option: subtract up to your BAB from melee attacks and add it "
                             "to damage (x2 with two-handed weapons).",
                     "prereq": {"str": 13}, "fighter": True},
    "Cleave": {"desc": "When you drop a foe in melee, make an immediate extra attack against "
                       "another adjacent foe (1/round).",
               "prereq": {"str": 13, "feats": ["Power Attack"]}, "fighter": True},
    "Point Blank Shot": {"desc": "+1 attack and damage with ranged weapons within 30 ft.",
                         "fighter": True},
    "Precise Shot": {"desc": "No -4 penalty for shooting into melee.",
                     "prereq": {"feats": ["Point Blank Shot"]}, "fighter": True},
    "Rapid Shot": {"desc": "One extra ranged attack on a full attack; all attacks at -2.",
                   "prereq": {"dex": 13, "feats": ["Point Blank Shot"]}, "fighter": True},
    "Two-Weapon Fighting": {"desc": "Reduce two-weapon fighting penalties by 2 (main) / "
                                    "6 (off hand).", "prereq": {"dex": 15}, "fighter": True},
    "Weapon Finesse": {"desc": "Use Dex instead of Str for attacks with light weapons, "
                               "rapiers and natural weapons.", "prereq": {"bab": 1},
                       "fighter": True},
    "Weapon Focus": {"desc": "+1 on attack rolls with the chosen weapon.", "param": "weapon",
                     "prereq": {"bab": 1, "proficient": True}, "fighter": True},
    "Weapon Specialization": {"desc": "+2 damage with the chosen weapon.", "param": "weapon",
                              "prereq": {"fighter_level": 4, "feats": ["Weapon Focus"]},
                              "fighter": True, "fighter_only": True},
    "Improved Unarmed Strike": {"desc": "Unarmed strikes deal lethal damage and do not "
                                        "provoke.", "fighter": True},
    "Quick Draw": {"desc": "Draw a weapon as a free action.", "prereq": {"bab": 1},
                   "fighter": True},
    "Combat Casting": {"desc": "+4 on Concentration checks to cast defensively."},
    "Spell Focus": {"desc": "+1 to the save DC of spells from the chosen school.",
                    "param": "school"},
    "Extra Turning": {"desc": "Turn undead four more times per day.",
                      "prereq": {"turn_undead": True}},
    "Martial Weapon Proficiency": {"desc": "Proficiency with one martial weapon.",
                                   "param": "martial_weapon"},
    "Simple Weapon Proficiency": {"desc": "Proficiency with all simple weapons."},
    "Armor Proficiency (light)": {"desc": "No attack penalty from light armor."},
    "Armor Proficiency (medium)": {"desc": "No attack penalty from medium armor.",
                                   "prereq": {"feats": ["Armor Proficiency (light)"]}},
    "Armor Proficiency (heavy)": {"desc": "No attack penalty from heavy armor.",
                                  "prereq": {"feats": ["Armor Proficiency (medium)"]}},
    "Shield Proficiency": {"desc": "No attack penalty from shields."},
    "Track": {"desc": "Use Survival to follow tracks.", "hidden": True},
    "Scribe Scroll": {"desc": "Create scrolls of spells you know (downtime).",
                      "prereq": {"caster": 1}},
    "Brew Potion": {"desc": "Create potions of spells you know (downtime, flavor).",
                    "prereq": {"caster": 3}},
    "Empower Spell": {"desc": "Metamagic (flavor in this version).", "prereq": {"caster": 1},
                      "metamagic": True},
    "Spell Penetration": {"desc": "+2 on caster level checks to beat spell resistance."},
}

SPELL_SCHOOLS = ["abjuration", "conjuration", "divination", "enchantment", "evocation",
                 "illusion", "necromancy", "transmutation"]

FIGHTER_FEATS = sorted(k for k, v in FEATS.items() if v.get("fighter"))
