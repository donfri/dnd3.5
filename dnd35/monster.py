"""Monsters built from stat blocks in data/monsters.py."""
from __future__ import annotations

import copy
from typing import List, Optional

from . import dice, rules
from .creature import Creature, weapon_info_from_entry
from .data.items import item_data, make_item
from .data.monsters import MONSTERS


class Monster(Creature):
    is_pc = False

    def __init__(self, key: str, name: Optional[str] = None, roll_hp: bool = True,
                 overrides: Optional[dict] = None):
        super().__init__()
        block = copy.deepcopy(MONSTERS[key])
        if overrides:
            block.update(overrides)
        self.key = key
        self.block = block
        self.name = name or block["name"]
        self.ctype = block["type"]
        self.subtypes = list(block.get("subtypes", []))
        self.base_size = block["size"]
        self.evil = block.get("evil", False)
        self.cr = block["cr"]
        self.abilities = dict(block["abilities"])
        self.feats = list(block.get("feats", []))
        self.weapons = [make_item(w) for w in block.get("weapons", [])]
        self.armor = make_item(block["armor"]) if block.get("armor") else None
        self.shield = make_item(block["shield"]) if block.get("shield") else None
        hd, die = block["hd"], block["hit_die"]
        conm = rules.ability_mod(self.abilities.get("con")) if self.abilities.get("con") else 0
        if roll_hp:
            base = sum(dice.die(die) for _ in range(hd))
        else:
            base = int(hd * (die + 1) / 2)
        hp = base + conm * hd + (3 if "Toughness" in self.feats else 0) + block.get("bonus_hp", 0)
        self._max_hp = max(1, hp)
        self.special_cooldowns = {}
        self.fled = False
        self.unhealable = 0   # fire/acid damage a regenerating monster can't heal

    # hooks
    def base_ability_score(self, ab):
        return self.abilities.get(ab)

    def bab_base(self):
        return self.block["bab"]

    def base_save(self, kind):
        f, r, w = self.block["base_saves"]
        return {"fort": f, "ref": r, "will": w}[kind]

    def hit_dice(self):
        return self.block["hd"]

    def max_hp(self):
        base = self.abilities.get("con")
        if base is None:
            return self._max_hp
        # Con changes (poison, bear's endurance) shift hit points per HD
        delta = rules.ability_mod(self.ability("con")) - rules.ability_mod(base)
        return max(1, self._max_hp + delta * self.block["hd"])

    def feat_list(self):
        return self.feats

    # regeneration (trolls): only fire/acid damage can kill
    def take_damage(self, amount, dtype="", magic=False):
        regen = self.block.get("regeneration")
        dealt, note = super().take_damage(amount, dtype, magic)
        if regen and dealt and dtype in regen["bypass"]:
            self.unhealable += dealt
        if regen:
            self.check_death()
        return dealt, note

    def check_death(self):
        regen = self.block.get("regeneration")
        if not regen:
            return super().check_death()
        if self.unhealable >= self.max_hp():
            self.dead = True
        elif self.hp <= 0 and not self.dead:
            if not self.get_effect("Regenerating"):
                from .effects import Effect
                self.add_effect(Effect("Regenerating", None, tags=["unconscious"]))

    def regenerate(self) -> int:
        regen = self.block.get("regeneration")
        if not regen or self.dead:
            return 0
        amt = min(regen["amount"], max(0, self.damage - self.unhealable))
        self.damage -= amt
        if self.hp > 0:
            self.remove_effect("Regenerating")
        return amt

    def static_bonuses(self, stat):
        out = []
        if stat == "ac" and "Dodge" in self.feats:
            out.append(("dodge", 1, "Dodge"))
        if stat == "ac" and self.block.get("deflection"):
            out.append(("deflection", self.block["deflection"], "deflection"))
        return out

    def armor_data(self):
        return item_data(self.armor) if self.armor else None

    def shield_data(self):
        return item_data(self.shield) if self.shield else None

    def natural_armor(self):
        return self.block.get("natural", 0)

    def spell_resistance(self):
        return self.block.get("sr", 0)

    def dr(self):
        return list(self.block.get("dr", []))

    def immunities(self):
        imm = list(self.block.get("immune", []))
        if self.ctype == "undead":
            imm += ["sleep", "mind-affecting", "paralysis", "poison", "disease", "stun"]
        return imm

    def vulnerabilities(self):
        return list(self.block.get("vulnerable", []))

    def skill_total(self, skill):
        sk = self.block.get("skills", {})
        if skill in sk:
            return sk[skill] + (-2 if self.has_tag("shaken") else 0)
        from .data.skills import SKILLS
        ab = SKILLS.get(skill, {}).get("ability", "wis")
        return self.mod(ab)

    def weapon_infos(self) -> List[dict]:
        out = []
        for e in self.weapons:
            out.append(weapon_info_from_entry(e, self.base_size))
        for nat in self.block.get("natural_attacks", []):
            w = {"name": nat["name"], "wid": nat["name"], "damage": nat["damage"],
                 "base_damage": nat["damage"], "crit_range": nat.get("crit_range", 20),
                 "crit_mult": nat.get("crit_mult", 2), "dtype": nat.get("dtype", "B"),
                 "ranged": False, "thrown": False, "light": False, "two_handed": False,
                 "natural": True, "primary": nat.get("primary", True), "special": nat}
            if "str_mult" in nat:
                w["str_mult"] = nat["str_mult"]
            out.append(w)
        return out

    def melee_attacks(self) -> List[dict]:
        return [w for w in self.weapon_infos() if not w["ranged"]]

    def ranged_attacks(self) -> List[dict]:
        return [w for w in self.weapon_infos() if w["ranged"]]

    def statline(self) -> str:
        parts = [f"{self.name}: HP {self.hp}/{self.max_hp()}  AC {self.ac()}"]
        for w in self.weapon_infos():
            ab = sum(v for _, v, _ in self.attack_components(w))
            d, comps = self.damage_profile(w)
            bonus = sum(v for _, v, _ in comps)
            dmg = d + (f"{bonus:+d}" if bonus else "")
            parts.append(f"{w['name']} {ab:+d} ({dmg})")
        return "  ".join(parts)

    def to_dict(self):
        return {"key": self.key, "name": self.name, "damage": self.damage,
                "max_hp": self._max_hp}
