"""Player characters."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import rules
from . import companions as _comp
from .creature import Creature, weapon_info_from_entry, thrown_variant
from .data.classes import CLASSES, DEITIES, DOMAINS, METAL_ARMOR, MONK_UNARMED
from .data.feats import FEATS
from .data.items import (WEAPONS, WORN_SLOTS, item_clash, item_data, item_name, make_item,
                         stuck)
from .data.monsters import MONSTERS
from .data.races import RACES
from .data.skills import SKILLS, SYNERGIES
from .data.spells import SPELLS
from .effects import Effect

EQUIP_SLOTS = ["main", "off", "armor", "shield", "ring", "ring2", "cloak", "amulet", "wrists",
               "hands", "head", "belt"]
WORN = [sl for slots in WORN_SLOTS.values() for sl in slots]

INFLICT_BY_LEVEL = {1: "Inflict Light Wounds", 2: "Inflict Moderate Wounds",
                    3: "Inflict Serious Wounds", 4: "Inflict Critical Wounds"}
CURE_BY_LEVEL = {0: "Cure Minor Wounds", 1: "Cure Light Wounds", 2: "Cure Moderate Wounds",
                 3: "Cure Serious Wounds", 4: "Cure Critical Wounds",
                 5: "Mass Cure Light Wounds"}

SNA_BY_LEVEL = {i: f"Summon Nature's Ally {r}" for i, r in
                enumerate(["I", "II", "III", "IV", "V"], 1)}

SKILL_FEATS = {k: v["skills"] for k, v in FEATS.items() if "skills" in v}


class Character(Creature):
    is_pc = True

    def __init__(self, name: str, race: str, player: str = ""):
        super().__init__()
        self.name = name
        self.player = player
        self.race = race
        self.class_levels: List[str] = []
        self.base_abilities: Dict[str, int] = {a: 10 for a in rules.ABILITIES}
        self.ability_increases: List[str] = []
        self.hp_rolls: List[int] = []
        self.skill_ranks: Dict[str, float] = {}
        self.feats: List[str] = []
        self.alignment = "True Neutral"
        self.deity = ""
        self.domains: List[str] = []
        self.gender = ""
        self.age = 0
        self.height = ""
        self.weight = ""
        self.languages: List[str] = list(RACES[race]["languages"])
        self.favored_enemies: List[dict] = []  # {"type": "goblinoid", "bonus": 2}
        self.combat_style: Optional[str] = None
        self.spellbook: List[str] = []
        self.spells_known: Dict[int, List[str]] = {}
        self.prepared: Dict[str, Dict[int, List[dict]]] = {}
        self.spont_used: Dict[int, int] = {}
        self.inventory: List[dict] = []
        self.cp = 0
        self.xp = 0
        self.notes: List[str] = []
        self.power_attack = 0       # current Power Attack setting
        self.expertise = 0          # current Combat Expertise setting
        self.bonus_hp = 0           # heroic mode vigor
        self.companion: Optional[dict] = None   # animal companion {"kind", "name", ...}
        self.familiar: Optional[dict] = None    # {"kind", "name"}
        self.energy = "positive"     # clerics: channel positive (turn/cure) or negative
        self.specialty: Optional[str] = None    # wizard school specialization
        self.prohibited: List[str] = []
        self.mount: Optional[dict] = None       # paladin's special mount
        self.fallen = False                     # paladin who broke the code
        self.rogue_specials: List[str] = []     # rogue 10/13/16/19 special abilities
        self.prestige_target: Dict[str, str] = {}   # prestige class -> spellcasting class

    # ------------------------------------------------------------ basics
    @property
    def race_data(self) -> dict:
        return RACES[self.race]

    @property
    def level(self) -> int:
        return len(self.class_levels)

    def class_level(self, cls: str) -> int:
        return self.class_levels.count(cls)

    def classes(self) -> Dict[str, int]:
        c = Counter(self.class_levels)
        return {k: c[k] for k in dict.fromkeys(self.class_levels)}

    def class_summary(self) -> str:
        return " / ".join(f"{CLASSES[k]['name']} {v}" for k, v in self.classes().items())

    @property
    def base_size(self) -> str:  # type: ignore[override]
        form = self.wild_form()
        return form["size"] if form else self.race_data["size"]

    # ------------------------------------------------------------ wild shape
    def wild_form(self) -> Optional[dict]:
        for e in self.effects:
            if e.name == "Wild Shape":
                return MONSTERS.get(e.data.get("form"))
        return None

    @property
    def ctype(self) -> str:  # type: ignore[override]
        return "humanoid"

    @property
    def subtypes(self):  # type: ignore[override]
        return self.race_data.get("subtypes", []) + [self.race]

    @property
    def evil(self) -> bool:  # type: ignore[override]
        return "Evil" in self.alignment

    # ------------------------------------------------------------ hooks
    def base_ability_score(self, ab):
        if ab in ("str", "dex", "con"):
            form = self.wild_form()
            if form:
                return form["abilities"][ab]
        return (self.base_abilities[ab] + self.race_data["ability_adj"].get(ab, 0)
                + self.ability_increases.count(ab))

    def bab_base(self):
        return sum(rules.bab_for(CLASSES[c]["bab"], n) for c, n in self.classes().items())

    def base_save(self, kind):
        return sum(rules.base_save_for(kind in CLASSES[c]["good_saves"], n)
                   for c, n in self.classes().items())

    def hit_dice(self):
        return self.level

    def max_hp(self):
        conm = self.mod("con")
        total = sum(max(1, r + conm) for r in self.hp_rolls) + self.bonus_hp
        if self.has_feat("Toughness"):
            total += 3 * self.feat_list().count("Toughness")
        if self.familiar and self.familiar.get("kind") == "toad":
            total += 3
        total += self.bonus("max_hp")
        return max(1, total)

    def negative_levels(self) -> int:
        e = self.get_effect("Negative levels")
        return e.data.get("n", 0) if e else 0

    def companion_creature(self):
        return _comp.companion_creature(self)

    def companions_all(self):
        return _comp.all_companions(self)

    def feat_list(self) -> List[str]:
        out = list(self.feats)
        if self.class_level("ranger") >= 1:
            out.append("Track")
        if self.class_level("wizard") >= 1 and "Scribe Scroll" not in out:
            out.append("Scribe Scroll")
        if self.class_level("ranger") >= 2 and self.combat_style and self._light_or_no_armor():
            if self.combat_style == "archery":
                out.append("Rapid Shot")
            else:
                out.append("Two-Weapon Fighting")
        if self.class_level("ranger") >= 3:
            out.append("Endurance")
        if self.class_level("ranger") >= 6 and self.combat_style and self._light_or_no_armor():
            out.append("Manyshot" if self.combat_style == "archery"
                       else "Improved Two-Weapon Fighting")
        if self.class_level("ranger") >= 11 and self.combat_style and self._light_or_no_armor():
            out.append("Improved Precise Shot" if self.combat_style == "archery"
                       else "Greater Two-Weapon Fighting")
        if self.class_level("monk") >= 1 and "Improved Unarmed Strike" not in out:
            out.append("Improved Unarmed Strike")
        if self.class_level("duelist") >= 9 and "Deflect Arrows" not in out:
            out.append("Deflect Arrows")
        if self.familiar and "Alertness" not in out:
            out.append("Alertness")
        if "War" in self.domains and self.deity in DEITIES:
            w = DEITIES[self.deity]["weapon"]
            out.append(f"Weapon Focus ({w})")
        return out

    def _light_or_no_armor(self) -> bool:
        e = self.equipped("armor")
        return e is None or item_data(e)["category"] == "light"

    def monk_unarmored(self) -> bool:
        """Monk AC bonus, flurry and fast movement need no armor, no shield, light load."""
        if self.class_level("monk") < 1 or self.wild_form():
            return False
        if self.equipped("armor") or self.equipped("shield"):
            return False
        return self.load() == "light"

    # ------------------------------------------------------------ equipment
    def equipped(self, slot: str) -> Optional[dict]:
        for e in self.inventory:
            if e.get("slot") == slot:
                return e
        return None

    def encumbrance(self):
        """(max dex, check penalty) from carried load, or None if light."""
        load = self.load()
        if load == "medium":
            return 3, -3
        if load in ("heavy", "overloaded"):
            return 1, -6
        return None

    def max_dex_bonus(self):
        cap = super().max_dex_bonus()
        enc = self.encumbrance()
        if enc:
            cap = enc[0] if cap is None else min(cap, enc[0])
        return cap

    def armor_check_penalty(self):
        pen = super().armor_check_penalty()
        enc = self.encumbrance()
        if enc:
            pen = min(pen, enc[1])
        return pen

    def armor_data(self):
        e = self.equipped("armor")
        if not e or self.wild_form():
            return None
        d = item_data(e)
        eff = self.bonus("armor_enh")
        if eff:
            d["enhancement"] = max(d.get("enhancement", 0), eff)
        return d

    def shield_data(self):
        e = self.equipped("shield")
        return item_data(e) if e and not self.wild_form() else None

    def natural_armor(self):
        form = self.wild_form()
        return form.get("natural", 0) if form else 0

    def add_item(self, item_id_or_entry, qty: int = 1) -> dict:
        entry = make_item(item_id_or_entry, qty) if isinstance(item_id_or_entry, str) \
            else dict(item_id_or_entry)
        d = item_data(entry)
        if d.get("stack") or d["kind"] in ("consumable",) or entry["id"] in ("javelin",
                                                                             "dagger"):
            for e in self.inventory:
                if (e["id"] == entry["id"] and not e.get("slot") and
                        e.get("masterwork") == entry.get("masterwork") and
                        e.get("enhancement") == entry.get("enhancement")):
                    e["qty"] += entry.get("qty", qty)
                    return e
        entry.setdefault("qty", qty)
        self.inventory.append(entry)
        return entry

    def remove_item(self, entry: dict, qty: int = 1) -> None:
        entry["qty"] -= qty
        if entry["qty"] <= 0:
            self.inventory.remove(entry)

    def find_item(self, item_id: str) -> Optional[dict]:
        for e in self.inventory:
            if e["id"] == item_id:
                return e
        return None

    def has_item(self, item_id: str) -> bool:
        for e in self.inventory:
            if e["id"] == item_id:
                return True
            d = item_data(e)
            if d.get("counts_as") == item_id:
                return True
        return False

    def ammo_count(self, ammo: str) -> int:
        return sum(e["qty"] for e in self.inventory if e["id"] == ammo)

    def use_ammo(self, ammo: str) -> bool:
        e = self.find_item(ammo)
        if not e:
            return False
        self.remove_item(e, 1)
        return True

    def equip(self, entry: dict, slot: Optional[str] = None) -> str:
        if entry.get("unidentified"):
            return ("Nobody knows what that does yet. Have it identified in town, or let a "
                    "spellcaster study it.")
        d = item_data(entry)
        kind = d["kind"]
        if slot is None:
            if kind == "armor":
                slot = "armor"
            elif kind == "shield":
                slot = "shield"
            elif kind == "weapon":
                slot = "main"
            elif kind in WORN_SLOTS:
                slots = WORN_SLOTS[kind]
                slot = next((sl for sl in slots if not self.equipped(sl)), slots[0])
            else:
                return f"You can't equip {item_name(entry)}."
        if (kind in ("armor", "shield") and self.class_level("druid")
                and entry["id"] in METAL_ARMOR):
            return (f"{self.name} refuses to wear metal armor: it would cut a druid off from "
                    f"nature's magic.")
        # split stacks so only one is equipped
        if entry.get("qty", 1) > 1 and kind == "weapon":
            entry["qty"] -= 1
            entry = dict(entry, qty=1)
            entry.pop("slot", None)
            self.inventory.append(entry)
        old = self.equipped(slot)
        if old and stuck(old):
            other = next((sl for sl in WORN_SLOTS.get(kind, []) if sl != slot
                          and not (self.equipped(sl) and stuck(self.equipped(sl)))), None)
            if other is None:
                return (f"{item_name(old)} is cursed and won't come off, so there's no room "
                        f"for {item_name(entry)}.")
            slot = other
            old = self.equipped(slot)
        if old:
            old.pop("slot", None)
        if kind == "weapon" and slot == "main" and (d["hands"] == "two" or d.get("bow")):
            off = self.equipped("off")
            if off:
                off.pop("slot", None)
        if slot == "off":
            sh = self.equipped("shield")
            if sh:
                sh.pop("slot", None)
        if slot == "shield":
            off = self.equipped("off")
            if off:
                off.pop("slot", None)
        entry["slot"] = slot
        self._merge_stacks()
        it = d.get("intelligent")
        if it and slot in ("main", "off"):
            said = it["clash"] if item_clash(self.alignment, d) else it["greet"]
            extra = (" It resents you: -1 on attacks and saves while you hold it, and it "
                     "may balk in a fight.") if item_clash(self.alignment, d) else ""
            return f"{self.name} takes up {d['name']}. {said}{extra}"
        if d.get("cursed") and not entry.get("curse_known"):
            fake = item_name(entry)
            entry["curse_known"] = True
            return (f"{self.name} puts on the {fake[0].lower()}{fake[1:]}... and it tightens "
                    f"like a vice. It's CURSED: {item_name(entry)}! "
                    f"{d['desc'].split(': ', 1)[1]}")
        return f"{self.name} equips {item_name(entry)} ({slot})."

    def unequip(self, entry: dict) -> bool:
        if stuck(entry):
            return False
        entry.pop("slot", None)
        self._merge_stacks()
        return True

    def _merge_stacks(self):
        merged: List[dict] = []
        for e in self.inventory:
            if not e.get("slot"):
                for m in merged:
                    if (not m.get("slot") and m["id"] == e["id"]
                            and m.get("masterwork") == e.get("masterwork")
                            and m.get("enhancement") == e.get("enhancement")
                            and m.get("custom_name") == e.get("custom_name")
                            and m.get("charges") == e.get("charges")):
                        m["qty"] += e.get("qty", 1)
                        break
                else:
                    merged.append(e)
            else:
                merged.append(e)
        self.inventory = merged

    def total_weight(self) -> float:
        total = 0.0
        for e in self.inventory:
            d = item_data(e)
            w = d.get("weight", 0)
            if e["id"] in ("arrows",):
                w = 0.15
            elif e["id"] == "bolts":
                w = 0.1
            elif e["id"] == "sling bullets":
                w = 0.5
            if self.base_size == "small":
                if d["kind"] in ("weapon", "armor", "shield"):
                    w = w / 2
                elif e["id"] in ("backpack", "bedroll", "waterskin", "spellbook"):
                    w = w / 4
            total += w * e.get("qty", 1)
        return round(total, 1)

    def load(self) -> str:
        return rules.load_category(self.total_weight(), self.ability("str") or 0,
                                   self.base_size)

    def speed(self) -> int:
        form = self.wild_form()
        if form:
            return form.get("speed", 30) + self.bonus("speed")
        base = self.race_data["speed"]
        a = self.armor_data()
        if a and a.get("speed_reduce") and not self.race_data.get("speed_unaffected_by_armor"):
            base = 20 if base == 30 else 15
        if self.class_level("barbarian") >= 1 and not (a and a["category"] == "heavy"):
            base += 10
        if self.class_level("monk") >= 3 and self.monk_unarmored():
            base += 10 * (self.class_level("monk") // 3)
        base += self.bonus("speed")
        return base

    def natural_attacks(self) -> List[dict]:
        form = self.wild_form()
        out = []
        if not form:
            return out
        for nat in form.get("natural_attacks", []):
            w = {"name": nat["name"], "wid": nat["name"], "damage": nat["damage"],
                 "base_damage": nat["damage"], "crit_range": nat.get("crit_range", 20),
                 "crit_mult": nat.get("crit_mult", 2), "dtype": nat.get("dtype", "B"),
                 "ranged": False, "thrown": False, "light": False, "two_handed": False,
                 "natural": True, "primary": nat.get("primary", True), "special": nat,
                 "wielded": "main"}
            if "str_mult" in nat:
                w["str_mult"] = nat["str_mult"]
            elif len(form["natural_attacks"]) == 1:
                w["str_mult"] = 1.5
            out.append(w)
        return out

    def monk_unarmed(self) -> dict:
        w = weapon_info_from_entry(make_item("unarmed strike"), self.base_size)
        m = self.class_level("monk")
        table = MONK_UNARMED["small" if self.base_size == "small" else "medium"]
        w["damage"] = table[max(k for k in table if k <= m)]
        w["base_damage"] = MONK_UNARMED["medium"][max(k for k in table if k <= m)]
        w["nonlethal"] = False
        w["name"] = "Unarmed strike (monk)"
        w["wielded"] = "main"
        return w

    def weapon_enhancement(self, w: dict) -> int:
        enh = super().weapon_enhancement(w)
        aa = self.class_level("arcane archer")
        if aa and w.get("bow"):
            enh = max(enh, min(5, (aa + 1) // 2))
        return enh

    def weapon_infos(self) -> List[dict]:
        if self.wild_form():
            return self.natural_attacks()
        out = []
        if self.class_level("monk"):
            out.append(self.monk_unarmed())
        main = self.equipped("main")
        off = self.equipped("off")
        size = self.base_size
        if main:
            w = weapon_info_from_entry(main, size)
            w["wielded"] = "main"
            out.append(w)
            if w.get("throwable") and not w["ranged"]:
                out.append(dict(thrown_variant(w), wielded="main"))
        if off:
            w = weapon_info_from_entry(off, size)
            w["wielded"] = "off"
            out.append(w)
        seen = set()
        for e in self.inventory:
            if e.get("slot") or item_data(e)["kind"] != "weapon":
                continue
            key = (e["id"], e.get("enhancement"), e.get("masterwork"))
            if key in seen:
                continue
            seen.add(key)
            w = weapon_info_from_entry(e, size)
            w["wielded"] = None
            out.append(w)
            if w.get("throwable") and not w["ranged"]:
                out.append(dict(thrown_variant(w), wielded=None))
        if not out or not any(not w["ranged"] for w in out):
            un = weapon_info_from_entry(make_item("unarmed strike"), size)
            un["wielded"] = "main"
            out.append(un)
        return out

    # ------------------------------------------------------------ proficiency
    def proficiencies(self) -> set:
        profs = set()
        for c in self.classes():
            profs.update(CLASSES[c]["weapon_prof"])
        profs.update(self.race_data.get("auto_proficiency", []))
        if "martial" in profs:
            profs.update(self.race_data.get("weapon_familiarity", []))
        for f in self.feat_list():
            if f.startswith(("Martial Weapon Proficiency (", "Exotic Weapon Proficiency (")):
                profs.add(f[f.index("(") + 1:-1])
            if f == "Simple Weapon Proficiency":
                profs.add("simple")
        if "War" in self.domains and self.deity in DEITIES:
            profs.add(DEITIES[self.deity]["weapon"])
        return profs

    def is_proficient(self, w):
        if w.get("natural") or w.get("wid") == "unarmed strike":
            return True
        profs = self.proficiencies()
        wid = w.get("wid")
        cat = w.get("category") or WEAPONS.get(wid, {}).get("category")
        return cat in profs or wid in profs

    def armor_profs(self) -> set:
        profs = set()
        for c in self.classes():
            profs.update(CLASSES[c]["armor_prof"])
        for f in self.feat_list():
            if f.startswith("Armor Proficiency ("):
                profs.add(f[len("Armor Proficiency ("):-1])
            if f == "Shield Proficiency":
                profs.add("shields")
        return profs

    def armor_proficient(self, a):
        profs = self.armor_profs()
        cat = a["category"]
        if cat == "shield":
            return "shields" in profs
        if cat == "tower":
            return "tower" in profs
        return cat in profs

    # ------------------------------------------------------------ bonuses
    def static_bonuses(self, stat):
        out = []
        feats = self.feat_list()
        if stat == "save_fort" and "Great Fortitude" in feats:
            out.append(("untyped", 2, "Great Fortitude"))
        if stat == "save_will" and "Iron Will" in feats:
            out.append(("untyped", 2, "Iron Will"))
        if stat == "save_ref" and "Lightning Reflexes" in feats:
            out.append(("untyped", 2, "Lightning Reflexes"))
        if stat == "ac" and "Dodge" in feats:
            out.append(("dodge", 1, "Dodge"))
        if stat == "saves" and self.race_data.get("save_bonus_all"):
            out.append(("racial", self.race_data["save_bonus_all"], "racial"))
        if stat in ("attack", "saves"):
            for slot in ("main", "off"):
                e = self.equipped(slot)
                if e and item_clash(self.alignment, item_data(e)):
                    out.append(("untyped", -1, f"{item_name(e)} fights your grip"))
        for slot in WORN:
            e = self.equipped(slot)
            if e:
                for s, btype, val in item_data(e).get("bonuses", []):
                    if s == stat:
                        out.append((btype, val, item_name(e)))
        if stat == "ac" and self.class_level("monk") and self.monk_unarmored():
            val = max(0, self.mod("wis")) + self.class_level("monk") // 5
            if val:
                out.append(("monk", val, "monk AC bonus"))
        out += _comp.familiar_bonus(self, stat)
        dd = self.class_level("dwarven defender")
        if stat == "ac" and dd:
            out.append(("dodge", 1 + (dd - 1) // 3, "dwarven defender"))
        du = self.class_level("duelist")
        if du:
            if stat == "ac" and not self.equipped("armor") and not self.equipped("shield"):
                intb = min(max(0, self.mod("int")), du)
                if intb:
                    out.append(("canny", intb, "canny defense"))
            if stat == "init" and du >= 2:
                out.append(("untyped", 4 if du >= 8 else 2, "improved reaction"))
            if stat == "save_ref" and du >= 4:
                out.append(("competence", 2, "grace"))
        if stat == "saves" and self.class_level("paladin") >= 2 and not self.fallen:
            cha = self.mod("cha")
            if cha > 0:
                out.append(("divine_grace", cha, "divine grace"))
        return out

    def save_vs_tags(self, tags):
        out = []
        st = self.race_data.get("save_bonus_tags", {})
        for t in tags:
            if t in st:
                btype = "morale" if t == "fear" else "racial"
                out.append((btype, st[t], f"racial vs {t}"))
        if "trap" in tags:
            ts = self.trap_sense()
            if ts:
                out.append(("untyped", ts, "trap sense"))
        if "enchantment" in tags and self.class_level("monk") >= 3:
            out.append(("still_mind", 2, "still mind"))
        return out

    def trap_sense(self) -> int:
        return self.class_level("barbarian") // 3 + self.class_level("rogue") // 3 + \
            self.class_level("dwarven defender") // 4

    def immunities(self):
        out = []
        if self.class_level("paladin") >= 3 and not self.fallen:
            out += ["fear", "disease"]
        if self.class_level("monk") >= 5:
            out.append("disease")
        if self.class_level("druid") >= 9 or self.class_level("monk") >= 11:
            out.append("poison")
        form = self.wild_form()
        if form:
            out += list(form.get("immune", []))
        tg = self._effect_tags()
        if "fearless" in tg:
            out.append("fear")
        if "feasted" in tg:
            out.append("poison")
        if self.get_effect("Death Ward"):
            out += ["death", "negative"]
        if self.get_effect("Freedom of Movement"):
            out += ["paralysis", "entangle", "slow"]
        return out

    def dr(self):
        out = []
        b = self.class_level("barbarian")
        if b >= 7:
            out.append((1 + (b - 7) // 3, "-"))
        if self.class_level("monk") >= 20:
            out.append((10, "magic"))
        dd = self.class_level("dwarven defender")
        if dd >= 6:
            out.append((6 if dd >= 10 else 3, "-"))
        sk = self.get_effect("Stoneskin")
        if sk:
            out.insert(0, (min(10, sk.data.get("left", 10)), "adamantine"))
        return out

    def on_dr_absorbed(self, bypass, amount):
        if bypass == "adamantine":
            sk = self.get_effect("Stoneskin")
            if sk:
                sk.data["left"] = sk.data.get("left", 10) - amount
                if sk.data["left"] <= 0:
                    self.effects.remove(sk)

    def dodge_vs(self):
        return dict(self.race_data.get("dodge_vs", {}))

    def has_uncanny_dodge(self):
        return (self.class_level("barbarian") >= 2 or self.class_level("rogue") >= 4
                or self.class_level("dwarven defender") >= 2
                or self.class_level("assassin") >= 2)

    def has_improved_uncanny_dodge(self):
        return (self.class_level("barbarian") >= 5 or self.class_level("rogue") >= 8
                or self.class_level("dwarven defender") >= 6
                or self.class_level("assassin") >= 5)

    def _evasion_ok(self) -> bool:
        a = self.armor_data()
        return not a or a["category"] == "light"

    def has_evasion(self) -> bool:
        return self._evasion_ok() and (self.class_level("rogue") >= 2
                                       or self.class_level("monk") >= 2
                                       or self.class_level("ranger") >= 9)

    def has_improved_evasion(self) -> bool:
        return self._evasion_ok() and ("improved evasion" in self.rogue_specials
                                       or self.class_level("monk") >= 9)

    def spell_resistance(self) -> int:
        m = self.class_level("monk")
        return 10 + m if m >= 13 else 0

    def racial_attack_bonus(self, w, target):
        out = []
        if (w.get("thrown") or w.get("sling")) and self.race_data.get("thrown_attack"):
            out.append(("racial", self.race_data["thrown_attack"], "racial (thrown)"))
        if target is not None:
            for sub, val in self.race_data.get("attack_vs", {}).items():
                if sub in target.subtypes:
                    out.append(("racial", val, f"racial vs {sub}"))
                    break
        return out

    def damage_vs(self, target):
        out = []
        if target is not None:
            for fe in self.favored_enemies:
                if fe["type"] == target.ctype or fe["type"] in target.subtypes:
                    out.append(("untyped", fe["bonus"], f"favored enemy ({fe['type']})"))
                    break
        return out

    def sneak_attack_dice(self):
        r = self.class_level("rogue")
        a = self.class_level("assassin")
        return ((r + 1) // 2 if r else 0) + self.class_level("arcane trickster") // 2 + \
            ((a + 1) // 2 if a else 0)

    def has_twf_style(self):
        return (self.class_level("ranger") >= 2 and self.combat_style == "two-weapon"
                and self._light_or_no_armor())

    # ------------------------------------------------------------ skills
    def class_skills(self) -> set:
        out = set()
        for c in self.classes():
            out.update(CLASSES[c]["class_skills"])
        for d in self.domains:
            out.update(DOMAINS.get(d, {}).get("skills", []))
        return out

    def is_class_skill(self, skill: str) -> bool:
        return skill in self.class_skills()

    def max_ranks(self, skill: str, at_level: Optional[int] = None) -> float:
        lvl = at_level or self.level
        return lvl + 3 if self.is_class_skill(skill) else (lvl + 3) / 2

    def can_use_skill(self, skill: str) -> bool:
        return not SKILLS[skill].get("trained") or self.skill_ranks.get(skill, 0) > 0

    def skill_components(self, skill: str) -> List[Tuple[str, int, str]]:
        info = SKILLS[skill]
        ranks = int(self.skill_ranks.get(skill, 0))
        comps = [("ranks", ranks, "ranks"),
                 ("ability", self.mod(info["ability"]), info["ability"].upper())]
        typed = []
        rb = self.race_data.get("skill_bonus", {}).get(skill)
        if rb:
            typed.append(("racial", rb, "racial"))
        if self.class_level("druid") and skill in ("Knowledge (nature)", "Survival"):
            typed.append(("untyped", 2, "nature sense"))
        if skill == "Hide":
            sz = rules.SIZE_HIDE[self.size]
            if sz:
                comps.append(("size", sz, "size"))
        for f in self.feat_list():
            if f in SKILL_FEATS and skill in SKILL_FEATS[f]:
                typed.append(("untyped", SKILL_FEATS[f][skill], f))
            if f == f"Skill Focus ({skill})":
                typed.append(("untyped", 3, "Skill Focus"))
        for src, dst in SYNERGIES:
            if dst == skill and self.skill_ranks.get(src, 0) >= 5:
                typed.append(("untyped", 2, f"synergy ({src})"))
        acp = info.get("acp")
        if acp:
            pen = self.armor_check_penalty()
            if pen:
                comps.append(("untyped", pen * acp, "armor check penalty"))
        if skill in ("Disable Device", "Open Lock"):
            if not self.has_item("thieves' tools"):
                comps.append(("untyped", -2, "no thieves' tools"))
        for e in self.inventory:
            sb = item_data(e).get("skill_bonus", {})
            if skill in sb:
                typed.append(("circumstance_item", sb[skill], item_name(e)))
        typed += self.bonuses("skills") + self.bonuses(f"skill:{skill}")
        if self.has_tag("shaken"):
            comps.append(("untyped", -2, "shaken"))
        comps.extend(rules.stacked_breakdown(typed))
        return comps

    def skill_total(self, skill):
        return sum(v for _, v, _ in self.skill_components(skill))

    def skill_points_for_level(self, cls: str, first: bool) -> int:
        base = CLASSES[cls]["skill_points"] + rules.ability_mod(self.base_ability_score("int"))
        base = max(1, base)
        if self.race_data.get("bonus_skill_points"):
            base += 1
        return base * 4 if first else base

    # ------------------------------------------------------------ magic
    def caster_classes(self) -> List[str]:
        out = []
        for c in self.classes():
            if CLASSES[c].get("caster") and self.spells_per_day(c):
                out.append(c)
        return out

    def caster_class_level(self, cls: str) -> int:
        """Class level for spells, including prestige classes that advance it."""
        lvl = self.class_level(cls)
        kind = CLASSES[cls].get("caster")
        for pc, n in self.classes().items():
            prog = CLASSES[pc].get("progression")
            if not prog or kind not in prog:
                continue
            if self.prestige_target.get(f"{pc}:{kind}") == cls:
                lvl += sum(1 for i in range(1, n + 1) if i in prog[kind])
        return lvl

    def caster_level(self, cls: str) -> int:
        lvl = self.caster_class_level(cls)
        if CLASSES[cls].get("caster_level_half"):
            return lvl // 2 if lvl >= 4 else 0
        return lvl

    def cast_ability(self, cls: str) -> str:
        return CLASSES[cls]["cast_ability"]

    def spells_per_day(self, cls: str) -> Dict[int, int]:
        info = CLASSES[cls]
        if cls == "paladin" and self.fallen:
            return {}
        table = info.get("spells_per_day", {})
        lvl = min(self.caster_class_level(cls), rules.MAX_LEVEL)
        row = table.get(lvl)
        if not row:
            return {}
        score = self.ability(info["cast_ability"]) or 0
        amod = rules.ability_mod(score)
        out = {}
        for sl, base in enumerate(row):
            if base is None:
                continue
            if score < 10 + sl:
                continue
            n = base + rules.bonus_spells(amod, sl)
            if cls == "wizard" and self.specialty:
                n += 1   # specialist's extra slot (for a spell of the specialty school)
            if n > 0:
                out[sl] = n
        return out

    def domain_slots(self) -> Dict[int, int]:
        if self.class_level("cleric") < 1 or not self.domains:
            return {}
        per = self.spells_per_day("cleric")
        return {sl: 1 for sl in per if sl >= 1}

    def spell_dc(self, cls: str, spell: str, level: Optional[int] = None) -> int:
        sl = level if level is not None else SPELLS[spell]["levels"].get(
            cls, SPELLS[spell]["levels"].get("cleric_domain", 1))
        dc = 10 + sl + self.mod(self.cast_ability(cls))
        if self.has_feat(f"Spell Focus ({SPELLS[spell]['school']})"):
            dc += 1
        return dc

    def domain_spells(self, level: int) -> List[str]:
        return [DOMAINS[d]["spells"][level] for d in self.domains
                if level in DOMAINS[d]["spells"]]

    def reset_spells(self) -> None:
        """Called after rest: everything prepared becomes available again."""
        for cls, by_level in self.prepared.items():
            for slots in by_level.values():
                for s in slots:
                    s["used"] = False
        self.spont_used = {}

    FOCUS = {"wizard": "spell component pouch", "sorcerer": "spell component pouch",
             "bard": "spell component pouch", "cleric": "holy symbol",
             "paladin": "holy symbol"}

    def minds(self) -> List[dict]:
        """Intelligent items in hand: [(entry, its data)]."""
        out = []
        for slot in ("main", "off"):
            e = self.equipped(slot)
            if e and item_data(e).get("intelligent"):
                out.append((e, item_data(e)))
        return out

    def ensure_focus(self) -> None:
        """New casters get their pouch or holy symbol once (also for old saves)."""
        given = self.__dict__.setdefault("focus_given", [])
        for cls in set(self.class_levels):
            item = self.FOCUS.get(cls)
            if item and item not in given:
                given.append(item)
                if not self.has_item(item):
                    self.add_item(item)

    def missing_focus(self) -> Optional[str]:
        """What this caster lacks to cast at all (material components / divine focus)."""
        for cls in self.caster_classes():
            item = self.FOCUS.get(cls)
            if item and not self.has_item(item):
                return (f"{self.name} has no {item} and can't cast "
                        f"{cls} spells without one. (Shops sell them.)")
        return None

    def xp_penalty(self) -> float:
        """Multiclass penalty: -20% XP for each base class more than one level away from
        your highest. Your race's favored class (your highest, for humans and
        half-elves) and prestige classes don't count."""
        from .data.classes import CLASSES
        counts = {c_: n for c_, n in Counter(self.class_levels).items()
                  if not CLASSES[c_].get("prestige")}
        fav = self.race_data.get("favored_class", "any")
        if fav == "any" and counts:
            fav = max(counts, key=counts.get)
        counts.pop(fav, None)
        if len(counts) < 2:
            return 0.0
        top = max(counts.values())
        return min(0.8, 0.2 * sum(1 for n in counts.values() if top - n >= 2))

    def can_cast_now(self) -> bool:
        if self.wild_form() and not self.has_feat("Natural Spell"):
            return False
        return not self.has_tag("raging")

    def available_casts(self) -> List[dict]:
        """Every spell this character could cast right now."""
        out = []
        if self.wild_form() and not self.has_feat("Natural Spell"):
            return out
        for cls in self.caster_classes():
            if CLASSES[cls].get("prepared"):
                for sl, slots in sorted(self.prepared.get(cls, {}).items()):
                    seen = set()
                    for s in slots:
                        if s["used"]:
                            continue
                        key = (s["spell"], s.get("domain", False))
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append({"class": cls, "spell": s["spell"], "level": int(sl),
                                    "slot": s, "domain": s.get("domain", False)})
                if cls == "cleric":
                    conv = INFLICT_BY_LEVEL if self.energy == "negative" else CURE_BY_LEVEL
                    for sl, slots in sorted(self.prepared.get(cls, {}).items()):
                        cure = conv.get(int(sl))
                        if not cure:
                            continue
                        donors = [s for s in slots if not s["used"] and not s.get("domain")
                                  and s["spell"] != cure]
                        if donors:
                            out.append({"class": cls, "spell": cure, "level": int(sl),
                                        "slot": donors[0], "spontaneous": True})
                if cls == "druid":
                    for sl, slots in sorted(self.prepared.get(cls, {}).items()):
                        sna = SNA_BY_LEVEL.get(int(sl))
                        donors = [s for s in slots if not s["used"] and s["spell"] != sna]
                        if sna and donors:
                            out.append({"class": cls, "spell": sna, "level": int(sl),
                                        "slot": donors[0], "spontaneous": True})
            else:
                per = self.spells_per_day(cls)
                for sl, n in sorted(per.items()):
                    if self.spont_used.get(sl, 0) >= n:
                        continue
                    for sp in self.spells_known.get(sl, []):
                        out.append({"class": cls, "spell": sp, "level": sl, "slot": None})
        return out

    def expend(self, cast: dict) -> None:
        if cast.get("slot") is not None:
            cast["slot"]["used"] = True
        elif cast.get("class"):
            sl = cast["level"]
            self.spont_used[sl] = self.spont_used.get(sl, 0) + 1

    def arcane_spell_failure(self, cls: Optional[str] = None) -> int:
        arcane = [c for c in self.classes() if CLASSES[c].get("caster") == "arcane"]
        if cls is not None:
            arcane = [cls] if cls in arcane else []
        if not arcane:
            return 0
        total = 0
        a = self.armor_data()
        if a and not (a["category"] == "light"
                      and all(CLASSES[c].get("light_armor_casting") for c in arcane)):
            total += a.get("asf", 0)
        sh = self.shield_data()
        if sh:
            total += sh.get("asf", 0)
        return total

    # ------------------------------------------------------------ daily abilities
    def rage_per_day(self) -> int:
        b = self.class_level("barbarian")
        if not b:
            return 0
        return 1 + b // 4

    def turn_level(self) -> int:
        lvl = self.class_level("cleric")
        if self.class_level("paladin") >= 4 and not self.fallen:
            lvl += self.class_level("paladin") - 3
        return lvl

    def turn_per_day(self) -> int:
        if self.turn_level() < 1:
            return 0
        n = 3 + self.mod("cha")
        n += 4 * self.feat_list().count("Extra Turning")
        return max(0, n)

    def smite_per_day(self) -> int:
        p = self.class_level("paladin")
        if not p or self.fallen:
            return 0
        return 1 + p // 5 + 2 * self.feat_list().count("Extra Smiting")

    def lay_on_hands_pool(self) -> int:
        p = self.class_level("paladin") if not self.fallen else 0
        return p * self.mod("cha") if p >= 2 and self.mod("cha") > 0 else 0

    def music_per_day(self) -> int:
        b = self.class_level("bard")
        return b + 4 * self.feat_list().count("Extra Music") if b else 0

    def wild_shape_per_day(self) -> int:
        d = self.class_level("druid")
        if d < 5:
            return 0
        return 1 if d < 6 else 2 if d < 7 else 3 if d < 10 else 4 if d < 14 else \
            5 if d < 18 else 6

    def elemental_shape_per_day(self) -> int:
        d = self.class_level("druid")
        return 0 if d < 16 else 1 if d < 18 else 2 if d < 20 else 3

    def stunning_fist_per_day(self) -> int:
        if not self.has_feat("Stunning Fist"):
            return 0
        m = self.class_level("monk")
        return m + (self.level - m) // 4

    def wholeness_pool(self) -> int:
        m = self.class_level("monk")
        return 2 * m if m >= 7 else 0

    def uses_total(self, key: str) -> int:
        return {"rage": self.rage_per_day(), "turn": self.turn_per_day(),
                "feat_of_strength": 1 if "Strength" in self.domains else 0,
                "smite": self.smite_per_day(), "lay_on_hands": self.lay_on_hands_pool(),
                "music": self.music_per_day(), "wild_shape": self.wild_shape_per_day(),
                "stunning_fist": self.stunning_fist_per_day(),
                "wholeness": self.wholeness_pool(),
                "elemental_shape": self.elemental_shape_per_day(),
                "quivering_palm": 1 if self.class_level("monk") >= 15 else 0,
                "defensive_roll": 1 if "defensive roll" in self.rogue_specials else 0,
                "stance": (self.class_level("dwarven defender") + 1) // 2,
                "hail_of_arrows": 1 if self.class_level("arcane archer") >= 8 else 0,
                "arrow_of_death": 1 if self.class_level("arcane archer") >= 10 else 0,
                **{DOMAINS[d]["use"]: 1 for d in self.domains if DOMAINS.get(d, {}).get("use")},
                "inspire_competence": 0}.get(key, 0)

    def uses_left(self, key: str) -> int:
        return max(0, self.uses_total(key) - self.daily.get(key, 0))

    def spend(self, key: str, n: int = 1) -> None:
        self.daily[key] = self.daily.get(key, 0) + n

    DAILY_LABELS = [("rage", "Rage"), ("turn", "Turn undead"),
                    ("feat_of_strength", "Feat of strength"), ("smite", "Smite evil"),
                    ("lay_on_hands", "Lay on hands (hp)"), ("music", "Bardic music"),
                    ("wild_shape", "Wild shape"), ("stunning_fist", "Stunning fist"),
                    ("wholeness", "Wholeness of body (hp)"), ("death_touch", "Death touch"),
                    ("dsmite", "Destruction smite"), ("good_fortune", "Good fortune"),
                    ("protective_ward", "Protective ward"),
                    ("greater_turning", "Greater turning"),
                    ("elemental_shape", "Elemental shape"),
                    ("quivering_palm", "Quivering palm"), ("defensive_roll", "Defensive roll"),
                    ("stance", "Defensive stance"), ("hail_of_arrows", "Hail of arrows"),
                    ("arrow_of_death", "Arrow of death")]

    def daily_list(self) -> List[str]:
        return [f"{label} {self.uses_left(k)}/{self.uses_total(k)}"
                for k, label in self.DAILY_LABELS if self.uses_total(k)]

    def special_abilities(self) -> List[str]:
        out = list(self.race_data["traits"])
        for cls, n in self.classes().items():
            for lvl in range(1, n + 1):
                for f in CLASSES[cls]["features"].get(lvl, []):
                    out.append(f"{CLASSES[cls]['name']} {lvl}: {f}")
        for d in self.domains:
            out.append(f"{d} domain: {DOMAINS[d]['power']}")
        if self.class_level("cleric"):
            out.append("Channels negative energy: rebukes/commands undead, spontaneous "
                       "inflict spells" if self.energy == "negative" else
                       "Channels positive energy: turns undead, spontaneous cure spells")
        if self.specialty:
            out.append(f"Specialist wizard: {self.specialty} (+1 spell per level of that "
                       f"school); prohibited: {', '.join(self.prohibited)}")
        if self.fallen:
            out.append("FALLEN PALADIN: no paladin powers until atonement")
        for fe in self.favored_enemies:
            out.append(f"Favored enemy ({fe['type']}) +{fe['bonus']}")
        from .data.classes import ROGUE_SPECIALS
        for sp in self.rogue_specials:
            out.append(ROGUE_SPECIALS[sp])
        if self.combat_style:
            out.append(f"Combat style: {self.combat_style}")
        for line in (_comp.companion_line(self), _comp.mount_line(self),
                     _comp.familiar_line(self)):
            if line:
                out.append(line)
        return out

    # ------------------------------------------------------------ xp
    def xp_next(self) -> int:
        return rules.xp_for_level(self.level + 1)

    def can_level_up(self) -> bool:
        return self.level < rules.MAX_LEVEL and self.xp >= self.xp_next()

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        _comp.sync_companion(self)
        return {
            "name": self.name, "player": self.player, "race": self.race,
            "class_levels": self.class_levels, "base_abilities": self.base_abilities,
            "ability_increases": self.ability_increases, "hp_rolls": self.hp_rolls,
            "skill_ranks": self.skill_ranks, "feats": self.feats,
            "alignment": self.alignment, "deity": self.deity, "domains": self.domains,
            "gender": self.gender, "age": self.age, "height": self.height,
            "weight": self.weight, "languages": self.languages,
            "focus_given": self.__dict__.get("focus_given", []),
            "hungry_days": self.__dict__.get("hungry_days", 0),
            "cohort_of": self.__dict__.get("cohort_of", ""),
            "favored_enemies": self.favored_enemies, "combat_style": self.combat_style,
            "spellbook": self.spellbook,
            "spells_known": {str(k): v for k, v in self.spells_known.items()},
            "prepared": {c: {str(k): v for k, v in d.items()} for c, d in self.prepared.items()},
            "spont_used": {str(k): v for k, v in self.spont_used.items()},
            "inventory": self.inventory, "cp": self.cp, "xp": self.xp, "notes": self.notes,
            "damage": self.damage, "temp_hp": self.temp_hp,
            "ability_damage": self.ability_damage, "stable": self.stable, "dead": self.dead,
            "effects": [e.to_dict() for e in self.effects], "afflictions": self.afflictions,
            "daily": self.daily, "power_attack": self.power_attack,
            "bonus_hp": self.bonus_hp, "companion": self.companion,
            "nonlethal": self.nonlethal, "energy": self.energy, "specialty": self.specialty,
            "prohibited": self.prohibited, "mount": self.mount, "fallen": self.fallen,
            "rogue_specials": self.rogue_specials, "prestige_target": self.prestige_target,
            "familiar": self.familiar,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Character":
        c = cls(d["name"], d["race"], d.get("player", ""))
        for k in ("class_levels", "base_abilities", "ability_increases", "hp_rolls",
                  "skill_ranks", "feats", "alignment", "deity", "domains", "gender", "age",
                  "height", "weight", "languages", "favored_enemies", "combat_style",
                  "focus_given", "hungry_days", "cohort_of", "spellbook", "inventory", "cp", "xp", "notes", "damage", "temp_hp",
                  "ability_damage", "stable", "dead", "afflictions", "daily",
                  "power_attack", "bonus_hp", "companion", "familiar", "nonlethal", "energy", "specialty",
                  "prohibited", "mount", "fallen", "rogue_specials",
                  "prestige_target"):
            if k in d:
                setattr(c, k, d[k])
        c.spells_known = {int(k): v for k, v in d.get("spells_known", {}).items()}
        c.prepared = {cl: {int(k): v for k, v in dd.items()}
                      for cl, dd in d.get("prepared", {}).items()}
        c.spont_used = {int(k): v for k, v in d.get("spont_used", {}).items()}
        c.effects = [Effect.from_dict(e) for e in d.get("effects", [])]
        # heroes saved before companions/familiars existed get the default ones
        if "familiar" not in d and (c.class_level("wizard") or c.class_level("sorcerer")):
            _comp.choose_familiar(c, None, auto=True)
        if "companion" not in d and _comp.effective_level(c) >= 1:
            _comp.choose_companion(c, None, auto=True)
        return c
