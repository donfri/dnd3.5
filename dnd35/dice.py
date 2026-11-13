"""Dice rolling.

Supports expressions such as "1d20", "2d6+3", "1d8-1", "3", "1d6+1d6+2".
Every roll can be described for the table so the players can see the math.
"""
from __future__ import annotations

import random
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

_rng = random.Random()

# Who is rolling right now (set around attacks, saves, checks...). A front end can
# install hooks to let a player press "Roll" for their own hero (before) and to
# show the dice (after). The numbers always come from this module's RNG.
_local = threading.local()          # each game thread has its own roller stack
before_roll: Optional[Callable] = None   # (who, what, expr) -> None, may block
after_roll: Optional[Callable] = None    # (who, what, expr, [(sides, [values])], total)


@contextmanager
def rolling(who, what: str):
    stack = _stack()
    stack.append((who, what))
    try:
        yield
    finally:
        stack.pop()


def _stack() -> List[tuple]:
    if not hasattr(_local, "rollers"):
        _local.rollers = []
    return _local.rollers


def _roller():
    stack = _stack()
    return stack[-1] if stack else (None, "")


def _before(expr: str) -> None:
    who, what = _roller()
    if who is not None and before_roll is not None:
        before_roll(who, what, expr)


def _after(expr: str, rolls, total: int) -> None:
    who, what = _roller()
    if who is not None and after_roll is not None:
        after_roll(who, what, expr, rolls, total)

TERM_RE = re.compile(r"([+-]?)\s*(\d*d\d+|\d+)")


def seed(value) -> None:
    """Seed the global dice RNG (used by tests and for reproducible sessions)."""
    _rng.seed(value)


def die(sides: int) -> int:
    return _rng.randint(1, sides)


def d20() -> int:
    _before("1d20")
    v = die(20)
    _after("1d20", [(20, [v])], v)
    return v


def percent() -> int:
    return die(100)


def choice(seq):
    return _rng.choice(seq)


def shuffle(seq):
    _rng.shuffle(seq)


@dataclass
class DiceTerm:
    count: int
    sides: int  # 0 for flat modifiers
    sign: int = 1

    @property
    def is_flat(self) -> bool:
        return self.sides == 0


@dataclass
class RollResult:
    expr: str
    total: int
    rolls: List[Tuple[int, List[int]]] = field(default_factory=list)  # (sides, results)
    flat: int = 0

    def detail(self) -> str:
        parts = []
        for sides, res in self.rolls:
            parts.append(f"d{sides}:{'+'.join(str(r) for r in res)}")
        if self.flat:
            parts.append(f"{self.flat:+d}")
        return f"{self.expr} [{' '.join(parts)}] = {self.total}"

    def __int__(self):
        return self.total


def parse(expr: str) -> List[DiceTerm]:
    expr = str(expr).replace(" ", "").lower()
    if not expr:
        return [DiceTerm(0, 0)]
    terms: List[DiceTerm] = []
    pos = 0
    for m in TERM_RE.finditer(expr):
        if m.start() != pos:
            raise ValueError(f"Bad dice expression: {expr!r}")
        pos = m.end()
        sign = -1 if m.group(1) == "-" else 1
        tok = m.group(2)
        if "d" in tok:
            c, s = tok.split("d")
            terms.append(DiceTerm(int(c) if c else 1, int(s), sign))
        else:
            terms.append(DiceTerm(int(tok), 0, sign))
    if pos != len(expr):
        raise ValueError(f"Bad dice expression: {expr!r}")
    return terms


def roll(expr: str, multiplier: int = 1) -> RollResult:
    """Roll an expression. ``multiplier`` rolls the whole expression N times
    and sums it (this is how 3.5 critical hits work: roll damage x times)."""
    terms = parse(expr)
    has_dice = any(not t.is_flat for t in terms)
    label = expr if multiplier <= 1 else f"({expr})x{multiplier}"
    if has_dice:
        _before(label)
    total = 0
    rolls = []
    flat = 0
    for _ in range(max(1, multiplier)):
        for t in terms:
            if t.is_flat:
                flat += t.sign * t.count
                total += t.sign * t.count
            else:
                res = [die(t.sides) for _ in range(t.count)]
                rolls.append((t.sides, res if t.sign > 0 else [-r for r in res]))
                total += t.sign * sum(res)
    if has_dice:
        _after(label, rolls, total)
    return RollResult(label, total, rolls, flat)


def average(expr: str) -> float:
    total = 0.0
    for t in parse(expr):
        if t.is_flat:
            total += t.sign * t.count
        else:
            total += t.sign * t.count * (t.sides + 1) / 2
    return total


def maximum(expr: str) -> int:
    total = 0
    for t in parse(expr):
        total += t.sign * t.count * (t.sides if not t.is_flat else 1)
    return total


def roll_4d6_drop_lowest() -> Tuple[int, List[int]]:
    dice = sorted((die(6) for _ in range(4)), reverse=True)
    return sum(dice[:3]), dice
