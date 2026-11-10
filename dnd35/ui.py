"""Terminal input/output.

All game code talks to a UI object instead of print()/input() directly so the
game can be driven by scripts in tests (see ScriptedUI / AutoUI).
"""
from __future__ import annotations

import os
import random
import sys
import textwrap
from typing import List, Optional, Sequence

WIDTH = 78


class Color:
    enabled = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    CODES = {
        "bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "bred": "91", "bgreen": "92", "byellow": "93", "bblue": "94",
        "bmagenta": "95", "bcyan": "96",
    }

    @classmethod
    def wrap(cls, text: str, *styles: str) -> str:
        if not cls.enabled or not styles:
            return text
        codes = ";".join(cls.CODES[s] for s in styles if s in cls.CODES)
        return f"\033[{codes}m{text}\033[0m"


def c(text, *styles) -> str:
    return Color.wrap(str(text), *styles)


if os.name == "nt":  # enable ANSI escapes on Windows 10+ terminals
    os.system("")


class QuitGame(Exception):
    pass


class UI:
    """Interactive terminal UI."""

    def __init__(self):
        self.transcript: List[str] = []

    # ---------------------------------------------------------------- output
    def out(self, text: str = "", style: Sequence[str] = ()) -> None:
        line = c(text, *style) if style else text
        self.transcript.append(text)
        print(line)

    def para(self, text: str, style: Sequence[str] = (), indent: str = "") -> None:
        """Print word-wrapped prose (GM narration)."""
        for block in str(text).strip("\n").split("\n\n"):
            block = " ".join(block.split())
            wrapped = textwrap.fill(block, WIDTH, initial_indent=indent, subsequent_indent=indent)
            self.out(wrapped, style)
            self.out()

    def gm(self, text: str) -> None:
        self.para(text, ("bcyan",))

    def header(self, text: str) -> None:
        bar = "=" * WIDTH
        self.out(bar, ("yellow",))
        self.out(text.center(WIDTH), ("bold", "byellow"))
        self.out(bar, ("yellow",))

    def sub(self, text: str) -> None:
        self.out(f"-- {text} " + "-" * max(0, WIDTH - len(text) - 4), ("yellow",))

    def roll(self, text: str) -> None:
        self.out("  " + text, ("dim",))

    def good(self, text: str) -> None:
        self.out(text, ("bgreen",))

    def bad(self, text: str) -> None:
        self.out(text, ("bred",))

    def warn(self, text: str) -> None:
        self.out(text, ("byellow",))

    # ---------------------------------------------------------------- input
    def _raw_input(self, prompt: str) -> str:
        try:
            return input(prompt)
        except EOFError:
            raise QuitGame()

    def ask(self, prompt: str, default: Optional[str] = None) -> str:
        suffix = f" [{default}]" if default not in (None, "") else ""
        ans = self._raw_input(c(f"{prompt}{suffix}: ", "bold")).strip()
        self.transcript.append(f"> {ans}")
        if ans.lower() in ("/quit", "/exit"):
            raise QuitGame()
        if not ans and default is not None:
            return default
        return ans

    def ask_int(self, prompt: str, lo: int, hi: int, default: Optional[int] = None) -> int:
        while True:
            raw = self.ask(f"{prompt} ({lo}-{hi})", None if default is None else str(default))
            try:
                v = int(raw)
                if lo <= v <= hi:
                    return v
            except ValueError:
                pass
            self.bad(f"Please enter a number from {lo} to {hi}.")

    def confirm(self, prompt: str, default: bool = True) -> bool:
        d = "Y/n" if default else "y/N"
        while True:
            ans = self.ask(f"{prompt} ({d})", "").lower()
            if not ans:
                return default
            if ans in ("y", "yes"):
                return True
            if ans in ("n", "no"):
                return False

    def choose(self, prompt: str, options: Sequence[str], allow_cancel: bool = False,
               default: Optional[int] = None) -> Optional[int]:
        """Show a numbered menu and return the chosen index (or None on cancel)."""
        if not options:
            return None
        for i, opt in enumerate(options, 1):
            self.out(f"  {c(str(i).rjust(2), 'bold', 'byellow')}. {opt}")
        if allow_cancel:
            self.out(f"  {c(' 0', 'bold', 'byellow')}. (back)")
        while True:
            raw = self.ask(prompt, None if default is None else str(default + 1))
            if allow_cancel and raw in ("0", "", "b", "back"):
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return int(raw) - 1
            # allow typing a unique prefix of the option text
            low = raw.lower()
            if low:
                hits = [i for i, o in enumerate(options) if _strip_ansi(o).lower().startswith(low)]
                if len(hits) == 1:
                    return hits[0]
            self.bad("Pick one of the numbers above.")

    def choose_many(self, prompt: str, options: Sequence[str], max_n: int) -> List[int]:
        for i, opt in enumerate(options, 1):
            self.out(f"  {c(str(i).rjust(2), 'bold', 'byellow')}. {opt}")
        while True:
            raw = self.ask(f"{prompt} (numbers separated by spaces, up to {max_n})")
            try:
                picks = [int(x) - 1 for x in raw.replace(",", " ").split()]
            except ValueError:
                picks = []
            picks = list(dict.fromkeys(picks))
            if picks and len(picks) <= max_n and all(0 <= p < len(options) for p in picks):
                return picks
            self.bad("Invalid selection.")

    def pause(self) -> None:
        self.ask(c("(press Enter)", "dim"), "")


def _strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)


class ScriptedUI(UI):
    """Feeds pre-written answers; raises QuitGame when it runs out."""

    def __init__(self, answers: Sequence[str], echo: bool = False):
        super().__init__()
        self.answers = list(answers)
        self.echo = echo

    def out(self, text: str = "", style: Sequence[str] = ()) -> None:
        self.transcript.append(text)
        if self.echo:
            print(text)

    def _raw_input(self, prompt: str) -> str:
        if not self.answers:
            raise QuitGame()
        return self.answers.pop(0)


class AutoUI(UI):
    """Plays the game by picking random menu entries. Used for fuzz testing."""

    def __init__(self, seed: int = 0, max_inputs: int = 3000, echo: bool = False):
        super().__init__()
        self.r = random.Random(seed)
        self.max_inputs = max_inputs
        self.count = 0
        self.echo = echo

    def out(self, text: str = "", style: Sequence[str] = ()) -> None:
        self.transcript.append(text)
        if len(self.transcript) > 4000:
            del self.transcript[:2000]
        if self.echo:
            print(text)

    def _tick(self):
        self.count += 1
        if self.count > self.max_inputs:
            raise QuitGame()

    def ask(self, prompt: str, default: Optional[str] = None) -> str:
        self._tick()
        if default is not None and self.r.random() < 0.7:
            return default
        return self.r.choice(["fire", "Bob", "", "1", "2", "3", "x"])

    def ask_int(self, prompt, lo, hi, default=None):
        self._tick()
        return self.r.randint(lo, hi)

    def confirm(self, prompt, default=True):
        self._tick()
        return self.r.random() < 0.6

    def choose(self, prompt, options, allow_cancel=False, default=None):
        self._tick()
        if not options:
            return None
        if allow_cancel and self.r.random() < 0.1:
            return None
        safe = [i for i, o in enumerate(options) if "Quit" not in o]
        if safe and self.r.random() < 0.97:
            return self.r.choice(safe)
        return self.r.randrange(len(options))

    def choose_many(self, prompt, options, max_n):
        self._tick()
        n = self.r.randint(1, min(max_n, len(options)))
        return self.r.sample(range(len(options)), n)

    def pause(self):
        self._tick()
