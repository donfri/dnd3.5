"""Player characters."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import rules
from .creature import Creature, weapon_info_from_entry, thrown_variant
from .data.classes import CLASSES, DEITIES, DOMAINS
from .data.feats import FEATS
from .data.items import WEAPONS, item_data, item_name, make_item
from .data.races import RACES
from .data.skills import SKILLS, SYNERGIES
from .data.spells import SPELLS
from .effects import Effect

EQUIP_SLOTS = ["main", "off", "armor", "shield", "ring", "ring2", "cloak", "amulet"]

CURE_BY_LEVEL = {0: "Cure Minor Wounds", 1: "Cure Light Wounds", 2: "Cure Moderate Wounds",
                 3: "Cure Serious Wounds"}

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
        return self.race_data["size"]

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
        return max(1, total)

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
        if "War" in self.domains and self.deity in DEITIES:
            w = DEITIES[self.deity]["weapon"]
            out.append(f"Weapon Focus ({w})")
        return out

    def _light_or_no_armor(self) -> bool:
        e = self.equipped("armor")
        return e is None or item_data(e)["category"] == "light"

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
        if not e:
            return None
        d = item_data(e)
        eff = self.bonus("armor_enh")
        if eff:
            d["enhancement"] = max(d.get("enhancement", 0), eff)
        return d

    def shield_data(self):
        e = self.equipped("shield")
        return item_data(e) if e else None

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
        d = item_data(entry)
        kind = d["kind"]
        if slot is None:
            if kind == "armor":
                slot = "armor"
            elif kind == "shield":
                slot = "shield"
            elif kind == "weapon":
                slot = "main"
            elif kind == "ring":
                slot = "ring" if not self.equipped("ring") else "ring2"
            elif kind in ("cloak", "amulet"):
                slot = kind
            else:
                return f"You can't equip {item_name(entry)}."
        # split stacks so only one is equipped
        if entry.get("qty", 1) > 1 and kind == "weapon":
            entry["qty"] -= 1
            entry = dict(entry, qty=1)
            entry.pop("slot", None)
            self.inventory.append(entry)
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
        return f"{self.name} equips {item_name(entry)} ({slot})."

    def unequip(self, entry: dict) -> None:
        entry.pop("slot", None)
        self._merge_stacks()

    def _merge_stacks(self):
        merged: List[dict] = []
        for e in self.inventory:
            if not e.get("slot"):
                for m in merged:
                    if (not m.get("slot") and m["id"] == e["id"]
                            and m.get("masterwork") == e.get("masterwork")
                            and m.get("enhancement") == e.get("enhancement")
                            and m.get("custom_name") == e.get("custom_name")):
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
        base = self.race_data["speed"]
        a = self.armor_data()
        if a and a.get("speed_reduce") and not self.race_data.get("speed_unaffected_by_armor"):
            base = 20 if base == 30 else 15
        if self.class_level("barbarian") >= 1 and not (a and a["category"] == "heavy"):
            base += 10
        base += self.bonus("speed")
        return base

    def weapon_infos(self) -> List[dict]:
        out = []
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
        for f in self.feat_list():
            if f.startswith("Martial Weapon Proficiency ("):
                profs.add(f[len("Martial Weapon Proficiency ("):-1])
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
        for slot in ("ring", "ring2", "cloak", "amulet"):
            e = self.equipped(slot)
            if e:
                for s, btype, val in item_data(e).get("bonuses", []):
                    if s == stat:
                        out.append((btype, val, item_name(e)))
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
        return out

    def trap_sense(self) -> int:
        b = self.class_level("barbarian")
        r = self.class_level("rogue")
        return (1 if b >= 3 else 0) + (1 if r >= 3 else 0)

    def dodge_vs(self):
        return dict(self.race_data.get("dodge_vs", {}))

    def has_uncanny_dodge(self):
        return self.class_level("barbarian") >= 2 or self.class_level("rogue") >= 4

    def has_evasion(self) -> bool:
        return self.class_level("rogue") >= 2

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
        return (r + 1) // 2 if r else 0

    def has_twf_style(self):
        return (self.class_level("ranger") >= 2 and self.combat_style == "two-weapon"
                and self._light_or_no_armor())

    # ------------------------------------------------------------ skills
    def class_skills(self) -> set:
        out = set()
        for c in self.classes():
            out.update(CLASSES[c]["class_skills"])
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

    def caster_level(self, cls: str) -> int:
        lvl = self.class_level(cls)
        if CLASSES[cls].get("caster_level_half"):
            return lvl // 2 if lvl >= 4 else 0
        return lvl

    def cast_ability(self, cls: str) -> str:
        return CLASSES[cls]["cast_ability"]

    def spells_per_day(self, cls: str) -> Dict[int, int]:
        info = CLASSES[cls]
        table = info.get("spells_per_day", {})
        lvl = min(self.class_level(cls), rules.MAX_LEVEL)
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
            if n > 0:
                out[sl] = n
        return out

    def domain_slots(self) -> Dict[int, int]:
        if self.class_level("cleric") < 1 or not self.domains:
            return {}
        per = self.spells_per_day("cleric")
        return {sl: 1 for sl in per if sl >= 1}

    def spell_dc(self, cls: str, spell: str) -> int:
        sl = SPELLS[spell]["levels"].get(cls, SPELLS[spell]["levels"].get("cleric_domain", 1))
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

    def available_casts(self) -> List[dict]:
        """Every spell this character could cast right now."""
        out = []
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
                if cls == "cleric" and not self.evil:
                    for sl, slots in sorted(self.prepared.get(cls, {}).items()):
                        cure = CURE_BY_LEVEL.get(int(sl))
                        if not cure:
                            continue
                        donors = [s for s in slots if not s["used"] and not s.get("domain")
                                  and s["spell"] != cure]
                        if donors:
                            out.append({"class": cls, "spell": cure, "level": int(sl),
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

    def arcane_spell_failure(self) -> int:
        if not any(CLASSES[c].get("caster") == "arcane" for c in self.classes()):
            return 0
        total = 0
        for d in (self.armor_data(), self.shield_data()):
            if d:
                total += d.get("asf", 0)
        return total

    # ------------------------------------------------------------ daily abilities
    def rage_per_day(self) -> int:
        b = self.class_level("barbarian")
        if not b:
            return 0
        return 1 + b // 4

    def turn_per_day(self) -> int:
        if self.class_level("cleric") < 1:
            return 0
        n = 3 + self.mod("cha")
        n += 4 * self.feat_list().count("Extra Turning")
        return max(0, n)

    def uses_left(self, key: str) -> int:
        total = {"rage": self.rage_per_day(), "turn": self.turn_per_day(),
                 "feat_of_strength": 1 if "Strength" in self.domains else 0}.get(key, 0)
        return max(0, total - self.daily.get(key, 0))

    def spend(self, key: str) -> None:
        self.daily[key] = self.daily.get(key, 0) + 1

    def special_abilities(self) -> List[str]:
        out = list(self.race_data["traits"])
        for cls, n in self.classes().items():
            for lvl in range(1, n + 1):
                for f in CLASSES[cls]["features"].get(lvl, []):
                    out.append(f"{CLASSES[cls]['name']} {lvl}: {f}")
        for d in self.domains:
            out.append(f"{d} domain: {DOMAINS[d]['power']}")
        for fe in self.favored_enemies:
            out.append(f"Favored enemy ({fe['type']}) +{fe['bonus']}")
        if self.combat_style:
            out.append(f"Combat style: {self.combat_style}")
        return out

    # ------------------------------------------------------------ xp
    def xp_next(self) -> int:
        return rules.xp_for_level(self.level + 1)

    def can_level_up(self) -> bool:
        return self.level < rules.MAX_LEVEL and self.xp >= self.xp_next()

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        return {
            "name": self.name, "player": self.player, "race": self.race,
            "class_levels": self.class_levels, "base_abilities": self.base_abilities,
            "ability_increases": self.ability_increases, "hp_rolls": self.hp_rolls,
            "skill_ranks": self.skill_ranks, "feats": self.feats,
            "alignment": self.alignment, "deity": self.deity, "domains": self.domains,
            "gender": self.gender, "age": self.age, "height": self.height,
            "weight": self.weight, "languages": self.languages,
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
            "bonus_hp": self.bonus_hp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Character":
        c = cls(d["name"], d["race"], d.get("player", ""))
        for k in ("class_levels", "base_abilities", "ability_increases", "hp_rolls",
                  "skill_ranks", "feats", "alignment", "deity", "domains", "gender", "age",
                  "height", "weight", "languages", "favored_enemies", "combat_style",
                  "spellbook", "inventory", "cp", "xp", "notes", "damage", "temp_hp",
                  "ability_damage", "stable", "dead", "afflictions", "daily",
                  "power_attack", "bonus_hp"):
            if k in d:
                setattr(c, k, d[k])
        c.spells_known = {int(k): v for k, v in d.get("spells_known", {}).items()}
        c.prepared = {cl: {int(k): v for k, v in dd.items()}
                      for cl, dd in d.get("prepared", {}).items()}
        c.spont_used = {int(k): v for k, v in d.get("spont_used", {}).items()}
        c.effects = [Effect.from_dict(e) for e in d.get("effects", [])]
        return c
