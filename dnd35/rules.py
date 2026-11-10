"""Core D&D 3.5 rules tables and helpers (SRD-based)."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

MAX_LEVEL = 5

ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]
ABILITY_NAMES = {
    "str": "Strength", "dex": "Dexterity", "con": "Constitution",
    "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma",
}


def ability_mod(score: Optional[int]) -> int:
    if score is None:
        return 0
    return (score - 10) // 2


def fmt_mod(n: int) -> str:
    return f"{n:+d}"


# ---------------------------------------------------------------- progression
def bab_for(progression: str, level: int) -> int:
    if progression == "good":
        return level
    if progression == "average":
        return (level * 3) // 4
    return level // 2


def base_save_for(good: bool, level: int) -> int:
    if level <= 0:
        return 0
    return 2 + level // 2 if good else level // 3


def iterative_attacks(bab: int) -> List[int]:
    """Return the list of attack bonuses for a full attack (BAB only)."""
    out = [bab]
    b = bab - 5
    while b >= 1 and len(out) < 4:
        out.append(b)
        b -= 5
    return out


def xp_for_level(level: int) -> int:
    return 1000 * level * (level - 1) // 2


def level_for_xp(xp: int) -> int:
    lvl = 1
    while lvl < 20 and xp >= xp_for_level(lvl + 1):
        lvl += 1
    return lvl


_XP_MULT = {-7: 1 / 12, -6: 1 / 8, -5: 1 / 6, -4: 1 / 4, -3: 1 / 3, -2: 1 / 2, -1: 2 / 3,
            0: 1, 1: 1.5, 2: 2, 3: 3, 4: 4, 5: 6, 6: 8, 7: 12}


def xp_award(party_level: int, cr: float) -> int:
    """XP for defeating ONE monster of challenge rating ``cr`` for a single
    character of ``party_level`` (DMG table 2-6, before dividing among the
    party)."""
    party_level = max(1, int(round(party_level)))
    if cr < 1:
        return int(xp_award(party_level, 1) * cr)
    cr = int(cr)
    if party_level <= 3:
        if cr <= 3:
            return 300 * cr
        base, diff = 900, cr - 3
    else:
        base, diff = 300 * party_level, cr - party_level
    if diff < -7 or diff > 7:
        return 0 if diff < 0 else int(base * 12)
    return int(base * _XP_MULT[diff])


# ---------------------------------------------------------------- bonus stacking
STACKING_TYPES = {"dodge", "untyped", "circumstance", "racial_stack"}


def stack_bonuses(bonuses: Iterable[Tuple[str, int]]) -> int:
    """Apply 3.5 stacking rules: bonuses of the same type do not stack (take
    the highest) except dodge, circumstance and untyped bonuses. Penalties
    always stack."""
    best: Dict[str, int] = {}
    total = 0
    for btype, value in bonuses:
        if value < 0:
            total += value
        elif btype in STACKING_TYPES:
            total += value
        else:
            best[btype] = max(best.get(btype, 0), value)
    return total + sum(best.values())


def stacked_breakdown(bonuses: Iterable[Tuple[str, int, str]]) -> List[Tuple[str, int, str]]:
    """Like stack_bonuses but returns the contributing (type, value, source)."""
    out = []
    best: Dict[str, Tuple[str, int, str]] = {}
    for btype, value, src in bonuses:
        if value < 0 or btype in STACKING_TYPES:
            out.append((btype, value, src))
        elif btype not in best or best[btype][1] < value:
            best[btype] = (btype, value, src)
    out.extend(best.values())
    return out


# ---------------------------------------------------------------- size
SIZES = ["fine", "diminutive", "tiny", "small", "medium", "large", "huge"]
SIZE_ATTACK_AC = {"fine": 8, "diminutive": 4, "tiny": 2, "small": 1, "medium": 0,
                  "large": -1, "huge": -2}
SIZE_GRAPPLE = {"fine": -16, "diminutive": -12, "tiny": -8, "small": -4, "medium": 0,
                "large": 4, "huge": 8}
SIZE_HIDE = {"fine": 16, "diminutive": 12, "tiny": 8, "small": 4, "medium": 0,
             "large": -4, "huge": -8}

# weapon damage by size (medium -> small / large)
DAMAGE_SMALL = {"1d2": "1", "1d3": "1d2", "1d4": "1d3", "1d6": "1d4", "1d8": "1d6",
                "1d10": "1d8", "1d12": "1d10", "2d4": "1d6", "2d6": "1d10",
                "2d8": "2d6", "3d6": "2d6"}
DAMAGE_LARGE = {"1d2": "1d3", "1d3": "1d4", "1d4": "1d6", "1d6": "1d8", "1d8": "2d6",
                "1d10": "2d8", "1d12": "3d6", "2d4": "2d6", "2d6": "3d6", "2d8": "3d8"}


def scale_damage(dice: str, size: str) -> str:
    if size == "small":
        return DAMAGE_SMALL.get(dice, dice)
    if size == "large":
        return DAMAGE_LARGE.get(dice, dice)
    return dice


# ---------------------------------------------------------------- carrying capacity
_LOAD = {1: 10, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60, 7: 70, 8: 80, 9: 90, 10: 100,
         11: 115, 12: 130, 13: 150, 14: 175, 15: 200, 16: 230, 17: 260, 18: 300,
         19: 350, 20: 400, 21: 460, 22: 520, 23: 600, 24: 700, 25: 800, 26: 920,
         27: 1040, 28: 1200, 29: 1400}


def heavy_load(strength: int, size: str = "medium") -> float:
    strength = max(1, strength)
    if strength in _LOAD:
        cap = _LOAD[strength]
    else:
        cap = _LOAD[20 + (strength % 10)] * 4 ** ((strength - 20) // 10)
    if size == "small":
        cap *= 0.75
    elif size == "large":
        cap *= 2
    return cap


def load_category(weight: float, strength: int, size: str = "medium") -> str:
    heavy = heavy_load(strength, size)
    if weight <= heavy / 3:
        return "light"
    if weight <= heavy * 2 / 3:
        return "medium"
    if weight <= heavy:
        return "heavy"
    return "overloaded"


# ---------------------------------------------------------------- turn undead
def turning_max_hd(check: int, cleric_level: int) -> int:
    if check <= 0:
        delta = -4
    elif check <= 3:
        delta = -3
    elif check <= 6:
        delta = -2
    elif check <= 9:
        delta = -1
    elif check <= 12:
        delta = 0
    elif check <= 15:
        delta = 1
    elif check <= 18:
        delta = 2
    elif check <= 21:
        delta = 3
    else:
        delta = 4
    return cleric_level + delta


# ---------------------------------------------------------------- spells
def bonus_spells(ability_modifier: int, spell_level: int) -> int:
    if spell_level == 0 or ability_modifier < spell_level:
        return 0
    return (ability_modifier - spell_level) // 4 + 1


def spell_service_cost(spell_level: int, caster_level: int) -> int:
    if spell_level == 0:
        return 5 * caster_level
    return 10 * spell_level * caster_level


def money_str(cp: int) -> str:
    gp, rem = divmod(cp, 100)
    sp, cp_ = divmod(rem, 10)
    parts = []
    if gp:
        parts.append(f"{gp} gp")
    if sp:
        parts.append(f"{sp} sp")
    if cp_ or not parts:
        parts.append(f"{cp_} cp")
    return " ".join(parts)


def tally(items) -> Dict:
    d = defaultdict(int)
    for i in items:
        d[i] += 1
    return dict(d)
