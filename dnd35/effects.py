"""Temporary effects (spells, conditions, rage...) attached to creatures.

An Effect carries typed modifiers ("stat", "bonus type", value) that the rules
engine stacks with 3.5 rules, plus tags that represent conditions such as
"paralyzed" or "shaken".
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

ROUNDS_PER_MINUTE = 10
ROUNDS_PER_HOUR = 600

CONDITION_TEXT = {
    "shaken": "Shaken (-2 attacks, saves, skill checks)",
    "fatigued": "Fatigued (-2 Str, -2 Dex, can't charge or run)",
    "exhausted": "Exhausted (-6 Str, -6 Dex)",
    "paralyzed": "Paralyzed (helpless, can't act)",
    "asleep": "Asleep (helpless)",
    "stunned": "Stunned (can't act, -2 AC, loses Dex to AC)",
    "dazed": "Dazed (can't act)",
    "blinded": "Blinded (-2 AC, loses Dex to AC, 50% miss chance)",
    "prone": "Prone (-4 melee attacks; -4 AC vs melee, +4 AC vs ranged)",
    "turned": "Turned (cowering/fleeing from holy power)",
    "raging": "Raging",
    "unconscious": "Unconscious",
    "stable": "Stable",
    "enlarged": "Enlarged (Large size)",
    "charging": "Charging (-2 AC)",
    "total_defense": "Total defense (+4 dodge AC)",
    "entangled": "Entangled (-2 attacks, -4 Dex, can't move)",
    "slowed": "Slowed (one action per turn, -1 attack, AC and Reflex)",
    "frightened": "Frightened (flees in panic)",
    "invisible": "Invisible",
    "wild_shape": "Wild shape",
    "fighting_defensively": "Fighting defensively (-4 attack, +2 dodge AC)",
}

HELPLESS_TAGS = {"paralyzed", "asleep", "unconscious"}
NO_ACTION_TAGS = {"paralyzed", "asleep", "unconscious", "stunned", "dazed", "turned"}


class Effect:
    def __init__(self, name: str, duration: Optional[int] = None,
                 mods: Optional[Sequence] = None, tags: Optional[Sequence[str]] = None,
                 source: str = "", data: Optional[Dict[str, Any]] = None,
                 hidden: bool = False):
        self.name = name
        self.duration = duration  # rounds remaining; None = until removed
        self.mods: List[List] = [list(m) for m in (mods or [])]
        self.tags = set(tags or [])
        self.source = source
        self.data = dict(data or {})
        self.hidden = hidden

    def mods_for(self, stat: str):
        for s, btype, val in self.mods:
            if s == stat:
                yield btype, val

    def describe(self) -> str:
        parts = []
        for s, btype, val in self.mods:
            parts.append(f"{val:+d} {btype.replace('_', ' ')} {s.replace('_', ' ')}")
        dur = ""
        if self.duration is not None:
            if self.duration >= ROUNDS_PER_HOUR:
                dur = f" ({self.duration // ROUNDS_PER_HOUR} hr)"
            elif self.duration >= ROUNDS_PER_MINUTE:
                dur = f" ({self.duration // ROUNDS_PER_MINUTE} min)"
            else:
                dur = f" ({self.duration} rd)"
        extra = ", ".join(parts)
        tags = ", ".join(sorted(t for t in self.tags if not t.startswith("_")))
        body = "; ".join(x for x in (extra, tags) if x)
        return f"{self.name}{dur}" + (f": {body}" if body else "")

    def to_dict(self) -> dict:
        return {"name": self.name, "duration": self.duration, "mods": self.mods,
                "tags": sorted(self.tags), "source": self.source, "data": self.data,
                "hidden": self.hidden}

    @classmethod
    def from_dict(cls, d: dict) -> "Effect":
        return cls(d["name"], d.get("duration"), d.get("mods"), d.get("tags"),
                   d.get("source", ""), d.get("data"), d.get("hidden", False))
