"""Weapons, armor, and gear (SRD 3.5). Prices in copper pieces (cp).

Weapon damage is listed for a Medium wielder; Small wielders scale it down.
"""

GP = 100
SP = 10


def _w(name, cat, prof, dmg, crit, mult, cost_gp, weight, dtype, hands, rng=0,
       ranged=False, thrown=False, finesse=False, ammo=None, **kw):
    d = {"kind": "weapon", "name": name, "category": cat, "prof": prof, "damage": dmg,
         "crit_range": crit, "crit_mult": mult, "cost": int(cost_gp * GP), "weight": weight,
         "dtype": dtype, "hands": hands, "range": rng, "ranged": ranged, "thrown": thrown,
         "finesse": finesse, "ammo": ammo}
    d.update(kw)
    return d


# hands: "light", "one", "two", "ranged"
WEAPONS = {
    # simple
    "unarmed strike": _w("Unarmed strike", "simple", "simple", "1d3", 20, 2, 0, 0, "B",
                         "light", nonlethal=True),
    "dagger": _w("Dagger", "simple", "simple", "1d4", 19, 2, 2, 1, "PS", "light", 10,
                 thrown=True),
    "light mace": _w("Light mace", "simple", "simple", "1d6", 20, 2, 5, 4, "B", "light"),
    "sickle": _w("Sickle", "simple", "simple", "1d6", 20, 2, 6, 2, "S", "light"),
    "club": _w("Club", "simple", "simple", "1d6", 20, 2, 0, 3, "B", "one", 10, thrown=True),
    "heavy mace": _w("Heavy mace", "simple", "simple", "1d8", 20, 2, 12, 8, "B", "one"),
    "morningstar": _w("Morningstar", "simple", "simple", "1d8", 20, 2, 8, 6, "BP", "one"),
    "shortspear": _w("Shortspear", "simple", "simple", "1d6", 20, 2, 1, 3, "P", "one", 20,
                     thrown=True),
    "quarterstaff": _w("Quarterstaff", "simple", "simple", "1d6", 20, 2, 0, 4, "B", "two"),
    "spear": _w("Spear", "simple", "simple", "1d8", 20, 3, 2, 6, "P", "two", 20, thrown=True),
    "light crossbow": _w("Light crossbow", "simple", "simple", "1d8", 19, 2, 35, 4, "P",
                         "ranged", 80, ranged=True, ammo="bolts"),
    "heavy crossbow": _w("Heavy crossbow", "simple", "simple", "1d10", 19, 2, 50, 8, "P",
                         "ranged", 120, ranged=True, ammo="bolts"),
    "javelin": _w("Javelin", "simple", "simple", "1d6", 20, 2, 1, 2, "P", "one", 30,
                  ranged=True, thrown=True),
    "sling": _w("Sling", "simple", "simple", "1d4", 20, 2, 0, 0, "B", "ranged", 50,
                ranged=True, ammo="sling bullets", sling=True),
    # martial
    "handaxe": _w("Handaxe", "martial", "martial", "1d6", 20, 3, 6, 3, "S", "light"),
    "light hammer": _w("Light hammer", "martial", "martial", "1d4", 20, 2, 1, 2, "B", "light",
                       20, thrown=True),
    "short sword": _w("Short sword", "martial", "martial", "1d6", 19, 2, 10, 2, "P", "light"),
    "throwing axe": _w("Throwing axe", "martial", "martial", "1d6", 20, 2, 8, 2, "S", "light",
                       10, thrown=True),
    "battleaxe": _w("Battleaxe", "martial", "martial", "1d8", 20, 3, 10, 6, "S", "one"),
    "flail": _w("Flail", "martial", "martial", "1d8", 20, 2, 8, 5, "B", "one"),
    "longsword": _w("Longsword", "martial", "martial", "1d8", 19, 2, 15, 4, "S", "one"),
    "rapier": _w("Rapier", "martial", "martial", "1d6", 18, 2, 20, 2, "P", "one",
                 finesse=True),
    "scimitar": _w("Scimitar", "martial", "martial", "1d6", 18, 2, 15, 4, "S", "one"),
    "warhammer": _w("Warhammer", "martial", "martial", "1d8", 20, 3, 12, 5, "B", "one"),
    "falchion": _w("Falchion", "martial", "martial", "2d4", 18, 2, 75, 8, "S", "two"),
    "greataxe": _w("Greataxe", "martial", "martial", "1d12", 20, 3, 20, 12, "S", "two"),
    "greatclub": _w("Greatclub", "martial", "martial", "1d10", 20, 2, 5, 8, "B", "two"),
    "greatsword": _w("Greatsword", "martial", "martial", "2d6", 19, 2, 50, 8, "S", "two"),
    "halberd": _w("Halberd", "martial", "martial", "1d10", 20, 3, 10, 12, "PS", "two"),
    "scythe": _w("Scythe", "martial", "martial", "2d4", 20, 4, 18, 10, "PS", "two"),
    "longbow": _w("Longbow", "martial", "martial", "1d8", 20, 3, 75, 3, "P", "ranged", 100,
                  ranged=True, ammo="arrows", bow=True),
    "shortbow": _w("Shortbow", "martial", "martial", "1d6", 20, 3, 30, 2, "P", "ranged", 60,
                   ranged=True, ammo="arrows", bow=True),
    # reach weapons (strike foes 10 ft. away)
    "longspear": _w("Longspear", "simple", "simple", "1d8", 20, 3, 5, 9, "P", "two", reach=True),
    "glaive": _w("Glaive", "martial", "martial", "1d10", 20, 3, 8, 10, "S", "two", reach=True),
    "guisarme": _w("Guisarme", "martial", "martial", "2d4", 20, 3, 9, 12, "S", "two",
                   reach=True, trip_bonus=2),
    "ranseur": _w("Ranseur", "martial", "martial", "2d4", 20, 3, 10, 12, "P", "two",
                  reach=True, disarm_bonus=2),
    "sap": _w("Sap", "martial", "martial", "1d6", 20, 2, 1, 2, "B", "light", nonlethal=True),
    # exotic
    "bastard sword": _w("Bastard sword", "exotic", "exotic", "1d10", 19, 2, 35, 6, "S", "one"),
    "dwarven waraxe": _w("Dwarven waraxe", "exotic", "exotic", "1d10", 20, 3, 30, 8, "S",
                         "one"),
    "spiked chain": _w("Spiked chain", "exotic", "exotic", "2d4", 20, 2, 25, 10, "P", "two",
                       reach=True, trip_bonus=2, disarm_bonus=2, finesse=True),
    "whip": _w("Whip", "exotic", "exotic", "1d3", 20, 2, 1, 2, "S", "one", reach=True,
               nonlethal=True, trip_bonus=2, disarm_bonus=2),
    "kama": _w("Kama", "exotic", "exotic", "1d6", 20, 2, 2, 2, "S", "light", trip_bonus=2),
    "nunchaku": _w("Nunchaku", "exotic", "exotic", "1d6", 20, 2, 2, 2, "B", "light",
                   disarm_bonus=2),
    "siangham": _w("Siangham", "exotic", "exotic", "1d6", 20, 2, 3, 1, "P", "light"),
    # monster / special weapons
    "greatclub (large)": _w("Greatclub", "martial", "martial", "2d8", 20, 2, 5, 16, "B", "two"),
}

# name -> "shortbow" etc. Proficiency names used by classes
SPECIFIC_PROF = {"hand crossbow": [], "sap": [], "rapier": ["rapier"], "shortbow": ["shortbow"],
                 "short sword": ["short sword"], "club": ["club"], "dagger": ["dagger"],
                 "heavy crossbow": ["heavy crossbow"], "light crossbow": ["light crossbow"],
                 "quarterstaff": ["quarterstaff"], "longsword": ["longsword"],
                 "longbow": ["longbow"]}


def _a(name, cat, bonus, maxdex, acp, asf, cost_gp, weight, speed_reduce=True):
    return {"kind": "armor" if cat not in ("shield", "tower") else "shield", "name": name,
            "category": cat, "ac": bonus, "max_dex": maxdex, "acp": acp, "asf": asf,
            "cost": int(cost_gp * GP), "weight": weight,
            "speed_reduce": speed_reduce and cat in ("medium", "heavy")}


ARMOR = {
    "padded": _a("Padded armor", "light", 1, 8, 0, 5, 5, 10),
    "leather": _a("Leather armor", "light", 2, 6, 0, 10, 10, 15),
    "studded leather": _a("Studded leather", "light", 3, 5, -1, 15, 25, 20),
    "chain shirt": _a("Chain shirt", "light", 4, 4, -2, 20, 100, 25),
    "hide": _a("Hide armor", "medium", 3, 4, -3, 20, 15, 25),
    "scale mail": _a("Scale mail", "medium", 4, 3, -4, 25, 50, 30),
    "chainmail": _a("Chainmail", "medium", 5, 2, -5, 30, 150, 40),
    "breastplate": _a("Breastplate", "medium", 5, 3, -4, 25, 200, 30),
    "splint mail": _a("Splint mail", "heavy", 6, 0, -7, 40, 200, 45),
    "banded mail": _a("Banded mail", "heavy", 6, 1, -6, 35, 250, 35),
    "half-plate": _a("Half-plate", "heavy", 7, 0, -7, 40, 600, 50),
    "full plate": _a("Full plate", "heavy", 8, 1, -6, 35, 1500, 50),
    "buckler": _a("Buckler", "shield", 1, None, -1, 5, 15, 5),
    "light wooden shield": _a("Light wooden shield", "shield", 1, None, -1, 5, 3, 5),
    "light steel shield": _a("Light steel shield", "shield", 1, None, -1, 5, 9, 6),
    "heavy wooden shield": _a("Heavy wooden shield", "shield", 2, None, -2, 15, 7, 10),
    "heavy steel shield": _a("Heavy steel shield", "shield", 2, None, -2, 15, 20, 15),
    "tower shield": _a("Tower shield", "tower", 4, 2, -10, 50, 30, 45),
}


def _g(name, cost_cp, weight, desc="", **kw):
    d = {"kind": "gear", "name": name, "cost": cost_cp, "weight": weight, "desc": desc}
    d.update(kw)
    return d


GEAR = {
    "backpack": _g("Backpack", 2 * GP, 2),
    "bedroll": _g("Bedroll", 1 * SP, 5),
    "rations": _g("Trail rations (1 day)", 5 * SP, 1, "Food. Also handy for distracting "
                  "hungry animals.", stack=True),
    "waterskin": _g("Waterskin", 1 * GP, 4),
    "rope": _g("Hempen rope (50 ft.)", 1 * GP, 10, "+2 on Climb checks when used to climb.",
               skill_bonus={"Climb": 2}),
    "torch": _g("Torch", 1, 1, "Bright light 20 ft. for 1 hour.", stack=True),
    "flint and steel": _g("Flint and steel", 1 * GP, 0),
    "thieves' tools": _g("Thieves' tools", 30 * GP, 1, "Required for Disable Device/Open "
                         "Lock without -2 penalty."),
    "masterwork thieves' tools": _g("Masterwork thieves' tools", 100 * GP, 2,
                                    "+2 circumstance bonus to Disable Device and Open Lock.",
                                    skill_bonus={"Disable Device": 2, "Open Lock": 2},
                                    counts_as="thieves' tools"),
    "healer's kit": _g("Healer's kit", 50 * GP, 1, "+2 circumstance bonus on Heal checks "
                       "(10 uses).", skill_bonus={"Heal": 2}),
    "holy symbol": _g("Wooden holy symbol", 1 * GP, 0, "Divine focus."),
    "spell component pouch": _g("Spell component pouch", 5 * GP, 2),
    "spellbook": _g("Spellbook", 15 * GP, 3),
    "crowbar": _g("Crowbar", 2 * GP, 5, "+2 circumstance bonus on Strength checks to force "
                  "doors or chests."),
    "arrows": _g("Arrows", 1 * GP, 3, "Sold in bundles of 20.", stack=True, ammo_count=20),
    "bolts": _g("Crossbow bolts", 1 * GP, 1, "Sold in bundles of 10.", stack=True, ammo_count=10),
    "sling bullets": _g("Sling bullets", 1 * SP, 5, "Sold in bundles of 10.", stack=True, ammo_count=10),
    "lantern": _g("Hooded lantern", 7 * GP, 2),
    "oil": _g("Flask of oil", 1 * SP, 1, stack=True),
    "grappling hook": _g("Grappling hook", 1 * GP, 4),
    "silver holy symbol": _g("Silver holy symbol", 25 * GP, 1, "Divine focus."),
    "iron key": _g("Iron key", 0, 0, "A heavy key stamped with an ember."),
    "lighthouse key": _g("Lighthouse key", 0, 0, "Old Corwin's spare key to the Lantern."),
    "postern key": _g("Postern key", 0, 0, "A greasy key to Greyfang Keep's postern gate."),
    "ember sigil": _g("Ember Sigil", 0, 1, "A warm bronze disc bearing the mark of the Ember "
                      "King."),
}

# consumables - use effects resolved in magic.py
CONSUMABLES = {
    "potion of cure light wounds": {"kind": "consumable", "name": "Potion of cure light wounds",
                                    "cost": 50 * GP, "weight": 0.1, "stack": True,
                                    "use": "spell", "spell": "Cure Light Wounds", "cl": 1,
                                    "desc": "Heals 1d8+1."},
    "potion of cure moderate wounds": {"kind": "consumable",
                                       "name": "Potion of cure moderate wounds",
                                       "cost": 300 * GP, "weight": 0.1, "stack": True,
                                       "use": "spell", "spell": "Cure Moderate Wounds", "cl": 3,
                                       "desc": "Heals 2d8+3."},
    "potion of bull's strength": {"kind": "consumable", "name": "Potion of bull's strength",
                                  "cost": 300 * GP, "weight": 0.1, "stack": True, "use": "spell",
                                  "spell": "Bull's Strength", "cl": 3,
                                  "desc": "+4 Strength for 3 minutes."},
    "potion of shield of faith": {"kind": "consumable", "name": "Potion of shield of faith",
                                  "cost": 50 * GP, "weight": 0.1, "stack": True, "use": "spell",
                                  "spell": "Shield of Faith", "cl": 1,
                                  "desc": "+2 deflection bonus to AC for 1 minute."},
    "scroll of magic missile": {"kind": "consumable", "name": "Scroll of magic missile",
                                "cost": 25 * GP, "weight": 0, "stack": True, "use": "scroll",
                                "spell": "Magic Missile", "cl": 1, "list": "arcane",
                                "desc": "Arcane scroll."},
    "scroll of sleep": {"kind": "consumable", "name": "Scroll of sleep", "cost": 25 * GP,
                        "weight": 0, "stack": True, "use": "scroll", "spell": "Sleep", "cl": 1,
                        "list": "arcane", "desc": "Arcane scroll."},
    "scroll of cure light wounds": {"kind": "consumable", "name": "Scroll of cure light wounds",
                                    "cost": 25 * GP, "weight": 0, "stack": True,
                                    "use": "scroll", "spell": "Cure Light Wounds", "cl": 1,
                                    "list": "divine", "desc": "Divine scroll."},
    "scroll of bless": {"kind": "consumable", "name": "Scroll of bless", "cost": 25 * GP,
                        "weight": 0, "stack": True, "use": "scroll", "spell": "Bless", "cl": 1,
                        "list": "divine", "desc": "Divine scroll."},
    "alchemist's fire": {"kind": "consumable", "name": "Alchemist's fire", "cost": 20 * GP,
                         "weight": 1, "stack": True, "use": "splash", "damage": "1d6",
                         "dtype": "fire", "desc": "Thrown splash weapon: 1d6 fire, ranged "
                                                  "touch, 10 ft. increment."},
    "holy water": {"kind": "consumable", "name": "Holy water", "cost": 25 * GP, "weight": 1,
                   "stack": True, "use": "splash", "damage": "2d4", "dtype": "holy",
                   "only_vs": ["undead"], "desc": "Thrown splash weapon: 2d4 to undead."},
    "potion of cure serious wounds": {"kind": "consumable",
                                      "name": "Potion of cure serious wounds",
                                      "cost": 750 * GP, "weight": 0.1, "stack": True,
                                      "use": "spell", "spell": "Cure Serious Wounds", "cl": 5,
                                      "desc": "Heals 3d8+5."},
    "potion of lesser restoration": {"kind": "consumable",
                                     "name": "Potion of lesser restoration",
                                     "cost": 300 * GP, "weight": 0.1, "stack": True,
                                     "use": "spell", "spell": "Lesser Restoration", "cl": 3,
                                     "desc": "Heals 1d4 ability damage, removes fatigue."},
    "scroll of fireball": {"kind": "consumable", "name": "Scroll of fireball",
                           "cost": 375 * GP, "weight": 0, "stack": True, "use": "scroll",
                           "spell": "Fireball", "cl": 5, "list": "arcane",
                           "desc": "Arcane scroll (5d6 fireball)."},
    "scroll of cure serious wounds": {"kind": "consumable",
                                      "name": "Scroll of cure serious wounds",
                                      "cost": 375 * GP, "weight": 0, "stack": True,
                                      "use": "scroll", "spell": "Cure Serious Wounds", "cl": 5,
                                      "list": "divine", "desc": "Divine scroll."},
    "scroll of remove disease": {"kind": "consumable", "name": "Scroll of remove disease",
                                 "cost": 375 * GP, "weight": 0, "stack": True, "use": "scroll",
                                 "spell": "Remove Disease", "cl": 5, "list": "divine",
                                 "desc": "Divine scroll."},
    "antitoxin": {"kind": "consumable", "name": "Antitoxin", "cost": 50 * GP, "weight": 0,
                  "stack": True, "use": "antitoxin",
                  "desc": "+5 alchemical bonus on Fort saves vs poison for 1 hour."},
}

# magic items and other special equipment
MAGIC = {
    "ring of protection +1": {"kind": "ring", "name": "Ring of protection +1",
                              "cost": 2000 * GP, "weight": 0,
                              "bonuses": [("ac", "deflection", 1)],
                              "desc": "+1 deflection bonus to AC."},
    "cloak of resistance +1": {"kind": "cloak", "name": "Cloak of resistance +1",
                               "cost": 1000 * GP, "weight": 1,
                               "bonuses": [("saves", "resistance", 1)],
                               "desc": "+1 resistance bonus on all saving throws."},
    "amulet of natural armor +1": {"kind": "amulet", "name": "Amulet of natural armor +1",
                                   "cost": 2000 * GP, "weight": 0,
                                   "bonuses": [("ac", "natural_enh", 1)],
                                   "desc": "+1 enhancement bonus to natural armor."},
}


def _wi(kind, name, gp, bonuses, desc, weight=0):
    return {"kind": kind, "name": name, "cost": gp * GP, "weight": weight, "bonuses": bonuses,
            "desc": desc}


MAGIC.update({
    "ring of protection +2": _wi("ring", "Ring of protection +2", 8000,
                                 [("ac", "deflection", 2)], "+2 deflection bonus to AC."),
    "cloak of resistance +2": _wi("cloak", "Cloak of resistance +2", 4000,
                                  [("saves", "resistance", 2)],
                                  "+2 resistance bonus on all saving throws.", 1),
    "amulet of natural armor +2": _wi("amulet", "Amulet of natural armor +2", 8000,
                                      [("ac", "natural_enh", 2)],
                                      "+2 enhancement bonus to natural armor."),
    "bracers of armor +1": _wi("bracers", "Bracers of armor +1", 1000, [("ac", "armor", 1)],
                               "+1 armor bonus to AC (doesn't stack with armor; monks love "
                               "these).", 1),
    "bracers of armor +2": _wi("bracers", "Bracers of armor +2", 4000, [("ac", "armor", 2)],
                               "+2 armor bonus to AC (doesn't stack with armor).", 1),
    "gauntlets of ogre power": _wi("gloves", "Gauntlets of ogre power", 4000,
                                   [("str", "enhancement", 2)],
                                   "+2 enhancement bonus to Strength.", 4),
    "gloves of dexterity +2": _wi("gloves", "Gloves of Dexterity +2", 4000,
                                  [("dex", "enhancement", 2)],
                                  "+2 enhancement bonus to Dexterity."),
    "headband of intellect +2": _wi("head", "Headband of intellect +2", 4000,
                                    [("int", "enhancement", 2)],
                                    "+2 enhancement bonus to Intelligence."),
    "periapt of wisdom +2": _wi("amulet", "Periapt of Wisdom +2", 4000,
                                [("wis", "enhancement", 2)],
                                "+2 enhancement bonus to Wisdom (neck slot)."),
    "cloak of charisma +2": _wi("cloak", "Cloak of Charisma +2", 4000,
                                [("cha", "enhancement", 2)],
                                "+2 enhancement bonus to Charisma.", 1),
    "amulet of health +2": _wi("amulet", "Amulet of health +2", 4000,
                               [("con", "enhancement", 2)],
                               "+2 enhancement bonus to Constitution (neck slot)."),
    "belt of giant strength +4": _wi("belt", "Belt of giant strength +4", 16000,
                                     [("str", "enhancement", 4)],
                                     "+4 enhancement bonus to Strength.", 1),
    "amulet of mighty fists +1": _wi("amulet", "Amulet of mighty fists +1", 6000,
                                     [("natural_weapon_enh", "enhancement", 1)],
                                     "+1 on attack and damage with unarmed strikes and "
                                     "natural weapons."),
})

# higher-level versions of the worn items (+3 to +6)
for _n in (3, 4, 5):
    MAGIC[f"ring of protection +{_n}"] = _wi("ring", f"Ring of protection +{_n}",
                                            2000 * _n * _n, [("ac", "deflection", _n)],
                                            f"+{_n} deflection bonus to AC.")
    MAGIC[f"cloak of resistance +{_n}"] = _wi("cloak", f"Cloak of resistance +{_n}",
                                             1000 * _n * _n, [("saves", "resistance", _n)],
                                             f"+{_n} resistance bonus on all saves.", 1)
for _n in (3, 4):
    MAGIC[f"amulet of natural armor +{_n}"] = _wi(
        "amulet", f"Amulet of natural armor +{_n}", 2000 * _n * _n,
        [("ac", "natural_enh", _n)], f"+{_n} enhancement bonus to natural armor.")
for _n in (4, 6):
    MAGIC[f"bracers of armor +{_n}"] = _wi("bracers", f"Bracers of armor +{_n}",
                                          1000 * _n * _n, [("ac", "armor", _n)],
                                          f"+{_n} armor bonus to AC.", 1)
    for _key, _kind, _ab, _nm in (("gloves of dexterity", "gloves", "dex", "Gloves of Dexterity"),
                                  ("headband of intellect", "head", "int",
                                   "Headband of intellect"),
                                  ("periapt of wisdom", "amulet", "wis", "Periapt of Wisdom"),
                                  ("cloak of charisma", "cloak", "cha", "Cloak of Charisma"),
                                  ("amulet of health", "amulet", "con", "Amulet of health")):
        MAGIC[f"{_key} +{_n}"] = _wi(_kind, f"{_nm} +{_n}", 1000 * _n * _n,
                                    [(_ab, "enhancement", _n)],
                                    f"+{_n} enhancement bonus to {_ab.upper()}.")
MAGIC["belt of giant strength +6"] = _wi("belt", "Belt of giant strength +6", 36000,
                                         [("str", "enhancement", 6)],
                                         "+6 enhancement bonus to Strength.", 1)
MAGIC["amulet of mighty fists +3"] = _wi("amulet", "Amulet of mighty fists +3", 54000,
                                         [("natural_weapon_enh", "enhancement", 3)],
                                         "+3 on attack and damage with unarmed strikes and "
                                         "natural weapons.")

# wands, staffs and metamagic rods
def _wand(spell, cl, gp, lvl_note=""):
    return {"kind": "wand", "name": f"Wand of {spell.lower()}" + lvl_note, "cost": gp * GP,
            "weight": 0, "spell": spell, "cl": cl, "charges": 50,
            "desc": f"Spell trigger: casts {spell} (caster level {cl}). 50 charges. Needs the "
                    f"spell on your class list, or Use Magic Device DC 20."}


MAGIC.update({
    "wand of cure light wounds": _wand("Cure Light Wounds", 1, 750),
    "wand of magic missile": _wand("Magic Missile", 1, 750),
    "wand of magic missile (cl 5)": _wand("Magic Missile", 5, 3750, " (3 missiles)"),
    "wand of cure moderate wounds": _wand("Cure Moderate Wounds", 3, 4500),
    "wand of scorching ray": _wand("Scorching Ray", 3, 4500),
    "wand of hold person": _wand("Hold Person", 3, 4500),
    "wand of bull's strength": _wand("Bull's Strength", 3, 4500),
    "wand of barkskin": _wand("Barkskin", 3, 4500),
    "wand of fireball": _wand("Fireball", 5, 11250),
    "wand of lightning bolt": _wand("Lightning Bolt", 5, 11250),
    "wand of cure serious wounds": _wand("Cure Serious Wounds", 5, 11250),
    "staff of fire": {"kind": "staff", "name": "Staff of fire", "cost": 17750 * GP,
                      "weight": 5, "cl": 8, "charges": 50,
                      "spells": [["Burning Hands", 1], ["Fireball", 1], ["Flaming Sphere", 1]],
                      "desc": "Casts burning hands, flaming sphere or fireball (1 charge "
                              "each). Uses your caster level if it's higher than 8."},
    "staff of healing": {"kind": "staff", "name": "Staff of healing", "cost": 27750 * GP,
                         "weight": 5, "cl": 8, "charges": 50,
                         "spells": [["Lesser Restoration", 1], ["Cure Serious Wounds", 1],
                                    ["Remove Disease", 1], ["Remove Fear", 1]],
                         "desc": "Casts lesser restoration, cure serious wounds, remove "
                                 "disease or remove fear (1 charge each)."},
    "lesser rod of extend spell": {"kind": "rod", "name": "Lesser rod of extend spell",
                                   "cost": 3000 * GP, "weight": 5, "metamagic": "Extend Spell",
                                   "max_level": 3,
                                   "desc": "3/day: extend a spell of 3rd level or lower "
                                           "without using a higher slot."},
    "lesser rod of empower spell": {"kind": "rod", "name": "Lesser rod of empower spell",
                                    "cost": 9000 * GP, "weight": 5,
                                    "metamagic": "Empower Spell", "max_level": 3,
                                    "desc": "3/day: empower a spell of 3rd level or lower "
                                            "without using a higher slot."},
    "lesser rod of maximize spell": {"kind": "rod", "name": "Lesser rod of maximize spell",
                                     "cost": 14000 * GP, "weight": 5,
                                     "metamagic": "Maximize Spell", "max_level": 3,
                                     "desc": "3/day: maximize a spell of 3rd level or lower "
                                             "without using a higher slot."},
})

# where each kind of worn item goes
WORN_SLOTS = {"ring": ["ring", "ring2"], "cloak": ["cloak"], "amulet": ["amulet"],
              "bracers": ["wrists"], "gloves": ["hands"], "head": ["head"], "belt": ["belt"]}
WORN_KINDS = set(WORN_SLOTS)
EQUIPPABLE_KINDS = {"weapon", "armor", "shield"} | WORN_KINDS


def make_item(item_id: str, qty: int = 1, **overrides) -> dict:
    """Instantiate an inventory entry. Supports prefixes like 'masterwork longsword'
    and '+1 longsword'."""
    base_id = item_id
    enh = 0
    mw = False
    if any(item_id in t for t in (WEAPONS, ARMOR, GEAR, CONSUMABLES, MAGIC)):
        pass
    elif item_id.startswith("+") and " " in item_id:
        enh = int(item_id[1:item_id.index(" ")])
        base_id = item_id[item_id.index(" ") + 1:]
        mw = True
    elif item_id.startswith("masterwork "):
        base_id = item_id[len("masterwork "):]
        mw = True
    if not any(base_id in t for t in (WEAPONS, ARMOR, GEAR, CONSUMABLES, MAGIC)):
        raise KeyError(f"Unknown item: {item_id}")
    entry = {"id": base_id, "qty": qty}
    if mw:
        entry["masterwork"] = True
    if enh:
        entry["enhancement"] = enh
    entry.update(overrides)
    return entry


def item_data(entry: dict) -> dict:
    iid = entry["id"]
    for table in (WEAPONS, ARMOR, GEAR, CONSUMABLES, MAGIC):
        if iid in table:
            d = dict(table[iid])
            break
    else:
        raise KeyError(iid)
    if entry.get("masterwork"):
        d["masterwork"] = True
        if d["kind"] == "weapon":
            d["cost"] += 300 * GP
        elif d["kind"] in ("armor", "shield"):
            d["cost"] += 150 * GP
            d["acp"] = min(0, d["acp"] + 1)
    if entry.get("enhancement"):
        d["enhancement"] = entry["enhancement"]
        e = entry["enhancement"]
        d["cost"] += (2000 if d["kind"] == "weapon" else 1000) * e * e * GP
    if entry.get("small"):
        d["small"] = True
    return d


def item_name(entry: dict) -> str:
    d = item_data(entry)
    name = d["name"]
    if entry.get("enhancement"):
        name = f"{name} +{entry['enhancement']}"
    elif entry.get("masterwork"):
        name = f"Masterwork {name[0].lower()}{name[1:]}"
    if entry.get("custom_name"):
        name = entry["custom_name"]
    if d["kind"] in ("wand", "staff"):
        name += f" ({charges_left(entry)} charges)"
    return name


def charges_left(entry: dict) -> int:
    d = item_data(entry)
    return entry.get("charges", d.get("charges", 0))


SHOP_STOCK = {
    "general": ["backpack", "bedroll", "rations", "waterskin", "rope", "torch",
                "flint and steel", "thieves' tools", "masterwork thieves' tools", "healer's kit",
                "holy symbol", "spell component pouch", "spellbook", "crowbar", "arrows",
                "bolts", "sling bullets", "lantern", "oil", "grappling hook",
                "alchemist's fire", "antitoxin"],
    "weapons": [k for k in WEAPONS if k not in ("unarmed strike", "greatclub (large)")],
    "armor": list(ARMOR),
    "temple": ["potion of cure light wounds", "potion of cure moderate wounds",
               "potion of cure serious wounds", "potion of lesser restoration",
               "potion of shield of faith", "holy water", "scroll of cure light wounds",
               "scroll of bless", "scroll of cure serious wounds", "scroll of remove disease",
               "silver holy symbol"],
    "magic": ["scroll of magic missile", "scroll of sleep", "scroll of fireball",
              "potion of bull's strength", "wand of cure light wounds",
              "wand of magic missile", "wand of magic missile (cl 5)",
              "wand of cure moderate wounds", "wand of scorching ray", "wand of hold person",
              "wand of bull's strength", "wand of barkskin", "wand of fireball",
              "wand of lightning bolt", "wand of cure serious wounds", "staff of fire",
              "staff of healing", "lesser rod of extend spell", "lesser rod of empower spell",
              "lesser rod of maximize spell"],
    "fine": ["+1 bastard sword", "+1 dwarven waraxe", "+1 spiked chain", "+1 kama",
             "masterwork longsword", "masterwork rapier", "masterwork greataxe",
             "masterwork longbow", "+1 longsword", "+1 rapier", "+1 greataxe",
             "+1 greatsword", "+1 battleaxe", "+1 warhammer", "+1 heavy mace",
             "+1 morningstar", "+1 longbow", "+1 shortbow", "+1 quarterstaff",
             "+1 chain shirt", "+1 studded leather", "+1 breastplate", "+1 full plate",
             "+1 heavy steel shield", "ring of protection +1", "cloak of resistance +1",
             "amulet of natural armor +1", "potion of cure moderate wounds",
             "+2 longsword", "+2 rapier", "+2 greataxe", "+2 greatsword", "+2 longbow",
             "+2 quarterstaff", "+2 scimitar", "+2 heavy mace", "+2 chain shirt",
             "+2 breastplate", "+2 full plate", "+2 heavy steel shield",
             "ring of protection +2", "cloak of resistance +2", "amulet of natural armor +2",
             "bracers of armor +1", "bracers of armor +2", "amulet of mighty fists +1",
             "gauntlets of ogre power", "gloves of dexterity +2", "headband of intellect +2",
             "periapt of wisdom +2", "cloak of charisma +2", "amulet of health +2",
             "belt of giant strength +4",
             "+3 longsword", "+3 greatsword", "+3 greataxe", "+3 rapier", "+3 longbow",
             "+3 full plate", "+3 chain shirt", "+3 heavy steel shield",
             "+4 longsword", "+4 greatsword", "+4 longbow", "+4 full plate",
             "+5 longsword", "+5 greatsword", "+5 longbow", "+5 full plate",
             "ring of protection +3", "ring of protection +4", "ring of protection +5",
             "cloak of resistance +3", "cloak of resistance +4", "cloak of resistance +5",
             "amulet of natural armor +3", "amulet of natural armor +4",
             "bracers of armor +4", "bracers of armor +6", "belt of giant strength +6",
             "gloves of dexterity +4", "gloves of dexterity +6", "headband of intellect +4",
             "headband of intellect +6", "periapt of wisdom +4", "periapt of wisdom +6",
             "cloak of charisma +4", "cloak of charisma +6", "amulet of health +4",
             "amulet of health +6", "amulet of mighty fists +3"],
}
