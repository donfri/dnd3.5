"""Shared combat state: one CState per creature in a fight."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .creature import Creature


class CState:
    def __init__(self, cr: Creature, side: str):
        self.c = cr
        self.side = side
        self.init = 0
        self.flat = True
        self.engaged: set = set()
        self.aoo_used = 0
        self.std = True
        self.move = True
        self.full_used = False
        self.moved = False
        self.cleave_used = False
        self.fled = False
        self.spent_ammo: Dict[str, int] = {}
        self.burst_cd = 0
        self.breath_cd = 0
        self.sla_used: Dict[str, int] = {}
        self.surprise = False
        self.deflect_used = False
        self.stepped = False
        self.delayed = False
        self.readied: Optional[dict] = None
        self.quickened = False
        self.pos: Tuple[int, int] = (0, 0)

    @property
    def single(self) -> bool:
        """Surprise round or slowed: one move OR one standard action."""
        return self.surprise or self.c.has_tag("slowed")


def wound_word(cr: Creature) -> str:
    if cr.dead:
        return "dead"
    frac = cr.hp / max(1, cr.max_hp())
    if frac >= 1:
        return "unhurt"
    if frac > 0.75:
        return "scratched"
    if frac > 0.5:
        return "wounded"
    if frac > 0.25:
        return "badly wounded"
    return "near death"
