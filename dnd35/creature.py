"""Shared stat math for PCs and monsters (D&D 3.5)."""
from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Sequence, Tuple

from . import rules
from .data.items import item_data
from .effects import Effect, HELPLESS_TAGS, NO_ACTION_TAGS
from .rules import ability_mod, stack_bonuses, stacked_breakdown

_uid = itertools.count(1)

ENERGY = {"fire", "cold", "acid", "electricity", "sonic", "force", "holy", "positive",
          "negative", "untyped_magic"}

SAVE_ABILITY = {"fort": "con", "ref": "dex", "will": "wis"}
SAVE_NAMES = {"fort": "Fortitude", "ref": "Reflex", "will": "Will"}


class Creature:
    is_pc = False

    def __init__(self):
        self.uid = next(_uid)
        self.effects: List[Effect] = []
        self.damage = 0          # lethal damage taken
        self.temp_hp = 0
        self.ability_damage: Dict[str, int] = {}
        self.stable = False
        self.dead = False
        self.afflictions: List[dict] = []   # diseases
        self.nonlethal = 0
        self.daily: Dict[str, int] = {}     # uses spent today (rage, turning...)

    # ------------------------------------------------------------ hooks
    name = "creature"
    ctype = "humanoid"
    subtypes: Sequence[str] = ()
    base_size = "medium"
    evil = False

    def base_ability_score(self, ab: str) -> Optional[int]:
        raise NotImplementedError

    def static_bonuses(self, stat: str) -> List[Tuple[str, int, str]]:
        return []

    def bab_base(self) -> int:
        raise NotImplementedError

    def base_save(self, kind: str) -> int:
        raise NotImplementedError

    def hit_dice(self) -> int:
        raise NotImplementedError

    def max_hp(self) -> int:
        raise NotImplementedError

    def has_feat(self, feat: str) -> bool:
        return feat in self.feat_list()

    def feat_list(self) -> List[str]:
        return []

    def armor_data(self) -> Optional[dict]:
        return None

    def shield_data(self) -> Optional[dict]:
        return None

    def natural_armor(self) -> int:
        return 0

    def weapon_infos(self) -> List[dict]:
        return []

    def is_proficient(self, wdata: dict) -> bool:
        return True

    def armor_proficient(self, adata: dict) -> bool:
        return True

    def dr(self) -> List[Tuple[int, str]]:
        return []

    def immunities(self) -> List[str]:
        return []

    def spell_resistance(self) -> int:
        return 0

    def vulnerabilities(self) -> List[str]:
        return []

    def skill_total(self, skill: str) -> int:
        return 0

    # ------------------------------------------------------------ effects
    def add_effect(self, eff: Effect, replace: bool = True) -> Effect:
        if replace:
            self.effects = [e for e in self.effects if e.name != eff.name]
        self.effects.append(eff)
        return eff

    def remove_effect(self, name: str) -> Optional[Effect]:
        for e in list(self.effects):
            if e.name == name:
                self.effects.remove(e)
                return e
        return None

    def get_effect(self, name: str) -> Optional[Effect]:
        for e in self.effects:
            if e.name == name:
                return e
        return None

    def has_tag(self, tag: str) -> bool:
        if tag == "unconscious" and self.is_pc and self.hp < 0 and not self.dead:
            return True
        if tag == "unconscious" and self.nonlethal and not self.dead \
                and self.nonlethal > max(0, self.hp):
            return True
        return any(tag in e.tags for e in self.effects)

    def _effect_tags(self) -> set:
        out = set()
        for e in self.effects:
            out |= e.tags
        return out

    def tags(self) -> set:
        out = set()
        for e in self.effects:
            out |= e.tags
        if self.is_pc and self.hp < 0 and not self.dead:
            out.add("unconscious")
        if self.nonlethal and not self.dead and self.nonlethal > max(0, self.hp):
            out.add("unconscious")
        return out

    @property
    def incorporeal(self) -> bool:
        return bool(getattr(self, "block", {}).get("incorporeal"))

    def take_nonlethal(self, amount: int) -> int:
        if not self.is_living() or "nonlethal" in self.immunities():
            return 0
        self.nonlethal += amount
        return amount

    def bonuses(self, stat: str) -> List[Tuple[str, int, str]]:
        out = list(self.static_bonuses(stat))
        for e in self.effects:
            for btype, val in e.mods_for(stat):
                out.append((btype, val, e.name))
        return out

    def bonus(self, stat: str) -> int:
        return stack_bonuses((t, v) for t, v, _ in self.bonuses(stat))

    # ------------------------------------------------------------ abilities
    def ability(self, ab: str) -> Optional[int]:
        base = self.base_ability_score(ab)
        if base is None:
            return None
        score = base + self.bonus(ab) - self.ability_damage.get(ab, 0)
        tags = self._effect_tags()
        if ab in ("str", "dex"):
            if "exhausted" in tags:
                score -= 6
            elif "fatigued" in tags:
                score -= 2
        if ab == "dex" and ("paralyzed" in tags or "asleep" in tags or "unconscious" in tags
                            or (self.is_pc and not self.dead and self.hp < 0)):
            return 0
        return max(0, score)

    def mod(self, ab: str) -> int:
        return ability_mod(self.ability(ab))

    # ------------------------------------------------------------ size
    @property
    def size(self) -> str:
        s = self.base_size
        if self.has_tag("enlarged"):
            idx = rules.SIZES.index(s)
            s = rules.SIZES[min(idx + 1, len(rules.SIZES) - 1)]
        return s

    # ------------------------------------------------------------ hp
    @property
    def hp(self) -> int:
        return self.max_hp() - self.damage

    @property
    def alive(self) -> bool:
        return not self.dead

    @property
    def conscious(self) -> bool:
        if self.dead:
            return False
        if self.hp < 0:
            return False
        return not (self.tags() & {"asleep", "unconscious", "paralyzed"})

    def can_act(self) -> bool:
        if self.dead or self.hp < 0:
            return False
        return not (self.tags() & NO_ACTION_TAGS)

    def helpless(self) -> bool:
        return self.dead or self.hp < 0 or bool(self.tags() & HELPLESS_TAGS)

    def status_word(self) -> str:
        if self.dead:
            return "DEAD"
        hp = self.hp
        if hp < 0:
            return "stable" if self.stable else "DYING"
        if hp == 0:
            return "disabled"
        t = self.tags()
        if self.nonlethal and self.nonlethal > max(0, hp):
            return "knocked out"
        for word in ("paralyzed", "asleep", "stunned", "dazed", "turned", "prone", "shaken",
                     "fatigued"):
            if word in t:
                return word
        return "ok"

    def check_death(self) -> None:
        if self.is_pc:
            if self.hp <= -10:
                self.dead = True
        else:
            if self.hp <= 0:
                self.dead = True

    def take_damage(self, amount: int, dtype: str = "", magic: bool = False) -> Tuple[int, str]:
        """Apply damage. dtype is a weapon damage type string such as "S", "BP" or an
        energy type like "fire". Returns (damage dealt, note)."""
        if amount <= 0:
            return 0, ""
        note = ""
        if dtype in ENERGY:
            if dtype in self.immunities():
                return 0, f"immune to {dtype}"
            pe = self.get_effect("Protection from Energy")
            if pe and pe.data.get("dtype") == dtype:
                soak = min(pe.data.get("left", 0), amount)
                pe.data["left"] = pe.data.get("left", 0) - soak
                amount -= soak
                note = f"protection from energy absorbs {soak}"
                if pe.data["left"] <= 0:
                    self.effects.remove(pe)
                if amount <= 0:
                    return 0, note
            if dtype in self.vulnerabilities():
                amount = int(amount * 1.5)
                note = f"vulnerable to {dtype}!"
            resist = self.bonus(f"resist_{dtype}")
            if resist:
                reduced = min(resist, amount)
                amount -= reduced
                note = f"resists {reduced} {dtype}"
        elif dtype and not magic:
            for dr_amt, bypass in self.dr():
                if not _dr_bypassed(bypass, dtype):
                    reduced = min(dr_amt, amount)
                    amount -= reduced
                    note = f"DR {dr_amt}/{_dr_name(bypass)} absorbs {reduced}"
                    self.on_dr_absorbed(bypass, reduced)
                    break
        if amount <= 0:
            return 0, note
        absorbed = 0
        if self.temp_hp:
            absorbed = min(self.temp_hp, amount)
            self.temp_hp -= absorbed
            amount -= absorbed
            if absorbed:
                note = (note + "; " if note else "") + f"{absorbed} absorbed by temp hp"
        self.damage += amount
        if amount > 0:
            self.stable = False
            # damage wakes sleepers
            for e in list(self.effects):
                if "asleep" in e.tags or "fascinated" in e.tags:
                    self.effects.remove(e)
        self.check_death()
        return amount + absorbed, note

    def on_dr_absorbed(self, bypass: str, amount: int) -> None:
        pass

    def heal(self, amount: int) -> int:
        if self.dead or amount <= 0:
            return 0
        self.nonlethal = max(0, self.nonlethal - amount)
        healed = min(amount, self.damage)
        self.damage -= healed
        if self.hp >= 0:
            self.stable = False
        return healed

    # ------------------------------------------------------------ combat stats
    def bab(self) -> int:
        return self.bab_base()

    def initiative(self) -> int:
        return self.mod("dex") + self.bonus("init") + (4 if self.has_feat("Improved Initiative")
                                                      else 0)

    def grapple(self) -> int:
        return self.bab() + self.mod("str") + rules.SIZE_GRAPPLE[self.size]

    def max_dex_bonus(self) -> Optional[int]:
        caps = []
        a = self.armor_data()
        if a and a.get("max_dex") is not None:
            caps.append(a["max_dex"])
        s = self.shield_data()
        if s and s.get("max_dex") is not None:
            caps.append(s["max_dex"])
        return min(caps) if caps else None

    def armor_check_penalty(self) -> int:
        total = 0
        for d in (self.armor_data(), self.shield_data()):
            if d:
                total += d.get("acp", 0)
        return total

    def ac_components(self, kind: str = "normal", attacker: "Creature" = None,
                      ranged: bool = False, uncanny: bool = None) -> List[Tuple[str, int, str]]:
        comps: List[Tuple[str, int, str]] = [("base", 10, "base")]
        tags = self.tags()
        dex = self.mod("dex")
        cap = self.max_dex_bonus()
        if cap is not None:
            dex = min(dex, cap)
        lose_dex = kind == "flat" or bool(tags & {"stunned", "blinded"})
        if uncanny is None:
            uncanny = self.has_uncanny_dodge()
        if kind == "flat" and uncanny and not (tags & {"stunned", "blinded"}):
            lose_dex = False
        if lose_dex and dex > 0:
            dex = 0
        if dex:
            comps.append(("dex", dex, "Dexterity"))
        size = rules.SIZE_ATTACK_AC[self.size]
        if size:
            comps.append(("size", size, f"size ({self.size})"))
        touch = kind == "touch"
        typed: List[Tuple[str, int, str]] = []
        if not touch:
            a = self.armor_data()
            if a:
                typed.append(("armor", a["ac"] + a.get("enhancement", 0), a["name"]))
            s = self.shield_data()
            if s:
                typed.append(("shield", s["ac"] + s.get("enhancement", 0), s["name"]))
            nat = self.natural_armor()
            if nat:
                typed.append(("natural", nat, "natural armor"))
        for btype, val, src in self.bonuses("ac"):
            if touch and btype in ("armor", "shield", "natural", "natural_enh", "armor_enh",
                                   "shield_enh"):
                continue
            if btype == "natural_enh" and not self.natural_armor():
                btype = "natural"
            if btype == "dodge" and (lose_dex and kind == "flat"):
                continue
            typed.append((btype, val, src))
        if attacker is not None:
            if attacker.evil:
                typed.extend(self.bonuses("ac_vs_evil"))
            for subtype, val in self.dodge_vs().items():
                if subtype == attacker.ctype or subtype in attacker.subtypes:
                    typed.append(("dodge", val, f"racial vs {subtype}"))
        comps.extend(stacked_breakdown(typed))
        if "stunned" in tags or "blinded" in tags:
            comps.append(("untyped", -2, "stunned" if "stunned" in tags else "blinded"))
        if "prone" in tags:
            comps.append(("untyped", 4 if ranged else -4, "prone"))
        if "charging" in tags:
            comps.append(("untyped", -2, "charging"))
        if "raging" in tags:
            comps.append(("untyped", -2, "rage"))
        return comps

    def ac(self, kind: str = "normal", attacker: "Creature" = None, ranged: bool = False) -> int:
        return sum(v for _, v, _ in self.ac_components(kind, attacker, ranged))

    def dodge_vs(self) -> Dict[str, int]:
        return {}

    def has_uncanny_dodge(self) -> bool:
        return False

    def save_vs_tags(self, tags: Sequence[str]) -> List[Tuple[str, int, str]]:
        return []

    def save_components(self, kind: str, tags: Sequence[str] = ()) -> List[Tuple[str, int, str]]:
        comps = [("base", self.base_save(kind), "base save")]
        ab = SAVE_ABILITY[kind]
        if ab == "con" and self.ability("con") is None:
            ab = None
        if ab:
            comps.append(("ability", self.mod(ab), rules.ABILITY_NAMES[ab]))
        typed = self.bonuses(f"save_{kind}") + self.bonuses("saves")
        typed += self.save_vs_tags(tags)
        if "evil_source" in tags:
            typed += self.bonuses("saves_vs_evil")
        if "fear" in tags:
            typed += self.bonuses("saves_vs_fear")
        if "spell" in tags:
            typed += self.bonuses("saves_vs_spell")
        if "sonic" in tags:
            typed += self.bonuses("saves_vs_sonic")
        if "enchantment" in tags:
            typed += self.bonuses("saves_vs_enchantment")
        comps.extend(stacked_breakdown(typed))
        return comps

    def save(self, kind: str, tags: Sequence[str] = ()) -> int:
        return sum(v for _, v, _ in self.save_components(kind, tags))

    # ------------------------------------------------------------ attacks
    def attack_components(self, w: dict, bab: int = None, target: "Creature" = None,
                          offhand: bool = False, twf: bool = False, power: int = 0,
                          situational: Sequence[Tuple[str, int, str]] = ()) -> List[Tuple[str, int, str]]:
        if bab is None:
            bab = self.bab()
        comps: List[Tuple[str, int, str]] = [("base", bab, "base attack")]
        ranged = w.get("ranged", False)
        if ranged:
            comps.append(("ability", self.mod("dex"), "Dex"))
        elif self.ability("str") is None:
            comps.append(("ability", self.mod("dex"), "Dex"))
        else:
            strm = self.mod("str")
            if self.has_feat("Weapon Finesse") and (w.get("light") or w.get("finesse")
                                                    or w.get("natural")):
                dexm = self.mod("dex")
                if dexm > strm:
                    comps.append(("ability", dexm, "Dex (finesse)"))
                else:
                    comps.append(("ability", strm, "Str"))
            else:
                comps.append(("ability", strm, "Str"))
        size = rules.SIZE_ATTACK_AC[self.size]
        if size:
            comps.append(("size", size, "size"))
        enh = self.weapon_enhancement(w)
        if enh:
            comps.append(("enhancement", enh, "enhancement"))
        elif w.get("masterwork"):
            comps.append(("enhancement", 1, "masterwork"))
        if self.has_feat(f"Weapon Focus ({w.get('wid')})"):
            comps.append(("untyped", 1, "Weapon Focus"))
        if self.has_feat(f"Greater Weapon Focus ({w.get('wid')})"):
            comps.append(("untyped", 1, "Greater Weapon Focus"))
        if not w.get("natural") and not self.is_proficient(w):
            comps.append(("untyped", -4, "nonproficient"))
        for d in (self.armor_data(), self.shield_data()):
            if d and not self.armor_proficient(d) and d.get("acp"):
                comps.append(("untyped", d["acp"], f"nonproficient: {d['name']}"))
        if w.get("natural") and not w.get("primary", True):
            comps.append(("untyped", -2 if self.has_feat("Multiattack") else -5, "secondary"))
        typed = self.bonuses("attack") + self.bonuses("ranged_attack" if ranged
                                                      else "melee_attack")
        comps.extend(stacked_breakdown(typed))
        comps.extend(self.racial_attack_bonus(w, target))
        if ranged and self.has_feat("Point Blank Shot"):
            comps.append(("untyped", 1, "Point Blank Shot"))
        if twf:
            light_off = w.get("_offhand_light", False)
            feat = self.has_feat("Two-Weapon Fighting") or self.has_twf_style()
            if offhand:
                pen = -10 + (2 if light_off else 0) + (6 if feat else 0)
            else:
                pen = -6 + (2 if light_off else 0) + (2 if feat else 0)
            comps.append(("untyped", pen, "two-weapon fighting"))
        if power and not ranged:
            comps.append(("untyped", -power, "Power Attack"))
        tags = self.tags()
        if "prone" in tags and not ranged:
            comps.append(("untyped", -4, "prone"))
        if "shaken" in tags:
            comps.append(("untyped", -2, "shaken"))
        comps.extend(situational)
        return comps

    def weapon_enhancement(self, w: dict) -> int:
        enh = w.get("enhancement", 0)
        if w.get("natural") or w.get("wid") == "unarmed strike":
            return max(enh, self.bonus("natural_weapon_enh"))
        enh = max(enh, self.bonus("weapon_enh"))
        if self.has_tag("shillelagh") and w.get("wid") in ("club", "quarterstaff"):
            enh = max(enh, 1)
        return enh

    def racial_attack_bonus(self, w: dict, target: Optional["Creature"]):
        return []

    def has_twf_style(self) -> bool:
        return False

    def str_damage(self, w: dict, offhand: bool = False) -> int:
        strm = self.mod("str")
        if w.get("ranged") and not w.get("thrown"):
            if w.get("sling"):
                return strm
            if w.get("bow"):
                return min(0, strm)
            return 0
        if offhand:
            return strm // 2 if strm > 0 else strm
        mult = w.get("str_mult")
        if mult is None:
            if w.get("natural"):
                mult = 1.0 if w.get("primary", True) else 0.5
            elif w.get("two_handed"):
                mult = 1.5
            else:
                mult = 1.0
        if strm > 0:
            return int(strm * mult)
        return strm

    def damage_profile(self, w: dict, target: "Creature" = None, offhand: bool = False,
                       power: int = 0) -> Tuple[str, List[Tuple[str, int, str]]]:
        dice = w["damage"]
        if self.has_tag("enlarged") and self.base_size == "medium" and not w.get("natural"):
            dice = rules.scale_damage(w.get("base_damage", dice), "large")
        if self.has_tag("shillelagh") and w.get("wid") in ("club", "quarterstaff"):
            dice = rules.scale_damage(rules.scale_damage(dice, "large"), "large")
        comps: List[Tuple[str, int, str]] = []
        s = self.str_damage(w, offhand)
        if s:
            comps.append(("ability", s, "Str"))
        enh = self.weapon_enhancement(w)
        if enh:
            comps.append(("enhancement", enh, "enhancement"))
        if self.has_feat(f"Weapon Specialization ({w.get('wid')})"):
            comps.append(("untyped", 2, "Weapon Specialization"))
        if power and not w.get("ranged") and not (w.get("light") and not w.get("natural")):
            mult = 2 if w.get("two_handed") else 1
            comps.append(("untyped", power * mult, "Power Attack"))
        typed = self.bonuses("damage") + self.bonuses("ranged_damage" if w.get("ranged")
                                                      else "melee_damage")
        comps.extend(stacked_breakdown(typed))
        if w.get("ranged") and self.has_feat("Point Blank Shot"):
            comps.append(("untyped", 1, "Point Blank Shot"))
        comps.extend(self.damage_vs(target))
        return dice, comps

    def damage_vs(self, target: Optional["Creature"]):
        return []

    def sneak_attack_dice(self) -> int:
        return 0

    def crit_immune(self) -> bool:
        return self.ctype == "undead"

    def sneak_immune(self) -> bool:
        return self.ctype == "undead"

    def is_living(self) -> bool:
        return self.ctype not in ("undead", "construct")

    # ------------------------------------------------------------ time
    def tick(self, rounds: int = 1, ui=None) -> List[str]:
        """Advance effect durations. Returns names of expired effects."""
        expired = []
        for e in list(self.effects):
            if e.duration is None:
                continue
            e.duration -= rounds
            if e.duration <= 0:
                self.effects.remove(e)
                expired.append(e)
        msgs = []
        for e in expired:
            msgs.append(f"{self.name}: {e.name} ends.")
            on_end = e.data.get("on_end")
            if on_end == "rage":
                if not e.data.get("tireless"):
                    self.add_effect(Effect("Fatigued (after rage)", 10 * 60, tags=["fatigued"],
                                           source="rage"))
                    msgs.append(f"{self.name} is fatigued after raging.")
            if on_end == "temp_hp":
                self.temp_hp = max(0, self.temp_hp - e.data.get("amount", 0))
        return msgs


def _dr_bypassed(bypass: str, dtype: str) -> bool:
    """DR entries name what gets through: weapon damage letters ("B", "S"), nothing
    ("" or "-": DR x/-), or a material/quality word ("adamantine", "magic") that
    ordinary attacks here never have."""
    if bypass in ("", "-"):
        return False
    if bypass == "magic":
        return "*" in dtype
    if bypass.isupper():
        return any(ch in dtype for ch in bypass)
    return False


def _dr_name(bypass: str) -> str:
    if bypass in ("", "-"):
        return "-"
    if not bypass.isupper():
        return bypass
    names = {"B": "bludgeoning", "S": "slashing", "P": "piercing"}
    return " or ".join(names.get(b, b) for b in bypass)


def weapon_info_from_entry(entry: dict, size: str) -> dict:
    d = item_data(entry)
    base = d["damage"]
    dmg = rules.scale_damage(base, size)
    return {
        "name": _entry_name(entry, d), "wid": entry["id"], "damage": dmg, "base_damage": base,
        "crit_range": d["crit_range"], "crit_mult": d["crit_mult"], "dtype": d["dtype"],
        "ranged": d["ranged"], "thrown": d.get("thrown", False) and d["ranged"],
        "throwable": d.get("thrown", False), "light": d["hands"] == "light",
        "two_handed": d["hands"] == "two" or (d["hands"] == "ranged" and d.get("bow")),
        "finesse": d.get("finesse", False), "natural": False,
        "enhancement": d.get("enhancement", 0), "masterwork": d.get("masterwork", False),
        "range": d.get("range", 0), "ammo": d.get("ammo"), "bow": d.get("bow", False),
        "sling": d.get("sling", False), "category": d["category"], "entry": entry,
        "nonlethal": d.get("nonlethal", False), "reach": d.get("reach", False),
        "trip_bonus": d.get("trip_bonus", 0), "disarm_bonus": d.get("disarm_bonus", 0),
    }


def _entry_name(entry, d):
    from .data.items import item_name
    return item_name(entry)


def thrown_variant(w: dict) -> dict:
    """Make a ranged (thrown) version of a melee weapon that can be thrown."""
    t = dict(w)
    t["ranged"] = True
    t["thrown"] = True
    t["two_handed"] = False
    t["name"] = f"{w['name']} (thrown)"
    return t
