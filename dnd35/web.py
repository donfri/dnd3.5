"""Online play: a tiny web server so remote players share one live game table.

    python -m dnd35.web --port 8080

Everyone who opens the page sees the same GM output in real time and can click
menu choices or type answers. The page has tabs for the story, the party's
character sheets, the journal, dice rolls and chat. Standard library only (no installs), so it runs anywhere, including Fly.io.

Environment variables:
    PORT              port to listen on (default 8080)
    TABLE_PASSWORD    if set, players must enter this password to join
    DND35_SAVE_DIR    where save files go (use a persistent volume on Fly.io)
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import random
import re
import threading
import time
import traceback
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse

from . import dice
from .rules import MAX_LEVEL
from .ui import UI, Color, QuitGame, c

MAX_EVENTS = 4000
POLL_SECONDS = 25
MAX_TABLES = 8          # each table runs its own game thread
MAX_PRESENCE = 40       # names remembered per table
NAME_HOLD = 90          # seconds a name stays bound to the browser that used it
FAIL_LIMIT, FAIL_WINDOW = 8, 600   # wrong passwords per IP before a 10-minute lockout
SESSION_DAYS = 30
RATE = {"default": (20, 5.0), "tts": (8, 1.0)}   # bucket size, refills per second
TTS_SLOTS = threading.BoundedSemaphore(2)   # voice synthesis is CPU-heavy
IDLE_SECONDS = 300      # page gone this long: treat the player as away
AUTOPILOT_DELAY = 1.5   # seconds before the computer answers for an away player
ANSI_RE = re.compile(r"\033\[[0-9;]*m")
SPEECH_RE = re.compile(r"^([A-Z][\w' .-]{0,30}): \u201c(.*)\u201d$")


_FREE_RNG = random.SystemRandom()
ROLL_TERM = re.compile(r"([+-]?)(\d*)d(\d+)(?:(kh|kl)(\d+))?|([+-]?)(\d+)")


def free_roll(expr: str) -> dict:
    """Roll dice for players' side games, e.g. '2d6+1', 'd20', '4d6kh3' (keep highest 3).
    Rolled on the server so nobody can fake a result."""
    e = expr.replace(" ", "").lower()
    if not e or len(e) > 40:
        raise ValueError("Type dice like 2d6+1, d20 or 4d6kh3.")
    if e[0] not in "+-":
        e = "+" + e
    pos, total, parts, dice_count, faces = 0, 0, [], 0, []
    for m in ROLL_TERM.finditer(e):
        if m.start() != pos:
            raise ValueError(f"I don't understand '{expr}'. Try 2d6+1, d20 or 4d6kh3.")
        pos = m.end()
        if m.group(3):
            sign = -1 if m.group(1) == "-" else 1
            n, sides = int(m.group(2) or 1), int(m.group(3))
            dice_count += n
            if n < 1 or sides < 2 or dice_count > 100 or sides > 1000:
                raise ValueError("Up to 100 dice, with 2 to 1000 sides each.")
            rolls = [_FREE_RNG.randint(1, sides) for _ in range(n)]
            faces.append([sides, rolls[:20]])
            kept = rolls
            note = ""
            if m.group(4):
                k = max(1, min(n, int(m.group(5))))
                kept = sorted(rolls, reverse=(m.group(4) == "kh"))[:k]
                note = f" keep {'highest' if m.group(4) == 'kh' else 'lowest'} {k}"
            total += sign * sum(kept)
            parts.append(f"{'-' if sign < 0 else ''}{n}d{sides}{note}: {rolls}")
        else:
            sign = -1 if m.group(6) == "-" else 1
            total += sign * int(m.group(7))
            parts.append(f"{sign * int(m.group(7)):+d}")
    if pos != len(e) or not dice_count:
        raise ValueError(f"I don't understand '{expr}'. Try 2d6+1, d20 or 4d6kh3.")
    return {"expr": expr.strip(), "detail": "  ".join(parts), "total": total,
            "rolls": faces[:6]}


class WebUI(UI):
    """A UI whose screen is an event log shared by every connected browser."""

    has_party_tab = True   # gear is managed from the Party tab, so no Inventory menu item

    def __init__(self, table: "Table"):
        super().__init__()
        self.table = table
        self._pending_options: Optional[List[str]] = None
        self._pending_kind = "text"
        self._pending_groups: Optional[List[str]] = None
        self.game_state = None  # set by the GM so the page can show party/journal tabs
        self._owners: List[str] = []
        self.last_who = ""
        self._explore = False
        self.battle_now: Optional[dict] = None
        self._pending_default = None
        self._auto_counts: Dict[tuple, int] = {}

    # ownership: only the hero's player may answer prompts inside acting()
    @contextmanager
    def acting(self, player: str):
        self._owners.append(player or "")
        try:
            yield
        finally:
            self._owners.pop()

    def seat_players(self) -> List[str]:
        """People at the table, in the order they joined (for quick start)."""
        return self.table.present()

    def current_owner(self) -> str:
        return next((o for o in reversed(self._owners) if o), "")

    # output -> events
    def out(self, text: str = "", style: Sequence[str] = ()) -> None:
        line = c(text, *style) if style else str(text)
        plain = ANSI_RE.sub("", line)
        if plain.startswith("=" * 20) and plain.count("\n") >= 8:
            # a character sheet: show it in a pop-up instead of flooding the story
            title = next((ln.strip() for ln in plain.splitlines()[1:] if ln.strip()), "Sheet")
            title = title.split("  ")[0].title()
            self.table.emit({"t": "block", "title": title, "text": line})
            return
        self.table.emit({"t": "line", "text": line})

    def battle(self, state: Optional[dict], inline: bool = False) -> None:
        """Battle grid for the page's map (inline = also drop a snapshot in the story)."""
        self.battle_now = state
        self.table.emit({"t": "battle", "b": state, "inline": bool(inline and state)})

    # narration (read aloud by browsers that turn the narrator on)
    def para(self, text: str, style: Sequence[str] = (), indent: str = "") -> None:
        plain = " ".join(str(text).split())
        if plain and ("bcyan" in style or "bmagenta" in style or "byellow" in style):
            m = SPEECH_RE.match(plain)
            if m:
                self.table.emit({"t": "narrate", "kind": "npc", "who": m.group(1),
                                 "text": m.group(2)})
            else:
                self.table.emit({"t": "narrate", "kind": "gm", "text": plain})
        # let the browser wrap paragraphs to the screen width (phones!)
        for block in str(text).strip("\n").split("\n\n"):
            block = " ".join(block.split())
            if block:
                self.out(indent + block, style)
                self.out()

    def header(self, text: str) -> None:
        title = text.strip()
        if title and not title.startswith(("TABLE", "NEW GAME", "HERO ")):
            words = " ".join(w.capitalize() for w in title.lower().split())
            self.table.emit({"t": "narrate", "kind": "title", "text": words + "."})
        # short heading instead of 80-column banner bars (fits phones)
        self.out()
        self.out(f"\u25c6 {title} \u25c6", ("bold", "byellow"))

    def sub(self, text: str) -> None:
        self.out(f"\u2014 {text} \u2014", ("yellow",))

    # input <- browser
    def _raw_input(self, prompt: str) -> str:
        opts = self._pending_options
        kind = self._pending_kind
        groups = self._pending_groups if kind == "choose" else None
        owner = self.current_owner()
        self.table.explore_idle = self._explore
        keys = getattr(self, "_pending_keys", None) if kind == "choose" else None
        self._pending_keys = None
        self.table.emit({"t": "prompt", "text": ANSI_RE.sub("", prompt), "options": opts,
                         "kind": kind, "groups": groups, "owner": owner, "keys": keys})
        plain = ANSI_RE.sub("", prompt)
        default = self._pending_default
        auto = None
        if owner and self.battle_now is not None:
            # in a fight, an away player's hero is played by the computer
            auto = (lambda: self.autopick(plain, opts, kind, default, keys))
        text, who = self.table.wait_input(owner, auto)
        self.table.explore_idle = False
        self.last_who = who
        shown = text if text else "(enter)"
        if opts and kind == "choose" and text.strip().isdigit():
            n = int(text.strip())
            if 1 <= n <= len(opts):
                shown = opts[n - 1]
            elif n == 0 and opts[-1] == "(back)":
                shown = "back"
        elif kind == "confirm":
            shown = {"y": "Yes", "n": "No"}.get(text.strip().lower()[:1], shown)
        by = who
        if owner and who and not who.startswith("autopilot") and \
                self.table._norm(who) != self.table._norm(owner):
            by = f"{who} (for {owner})"      # someone played an absent friend's hero
            self.table.note_cover(owner, "party")
        elif who.startswith("autopilot"):
            self.table.note_cover(owner, "computer")
        self.table.emit({"t": "line", "kind": "echo",
                         "text": c(f"> {by + ': ' if by else ''}{shown}", "bold")})
        if text.strip().lower() in ("/quit", "/exit"):
            return ""  # nobody can kill the shared table from a browser
        return text

    def autopick(self, prompt: str, opts: Optional[List[str]], kind: str, default,
                 keys: Optional[List[str]] = None) -> str:
        """What the computer answers for a hero whose player is away (combat only):
        fight the nearest foe, say yes to sensible offers, never back out."""
        if kind == "confirm":
            return "y" if default is not False else "n"
        if not opts or kind != "choose":
            return ""
        real = [o for o in opts if o != "(back)"]

        # action ids from the game when it sends them, button text otherwise
        IDS = {"Stabilize a dying ally": "stabilize", "Full attack": "attack_full",
               "Attack": "attack", "Move toward a foe (": "approach",
               "Move toward a foe again": "approach", "End turn": "end"}

        def pick(*starts):
            for st in starts:
                if keys and IDS.get(st) in keys:
                    return str(keys.index(IDS[st]) + 1)
                for i, o in enumerate(real):
                    if o.startswith(st):
                        return str(i + 1)
            return None
        prompt = prompt.strip().rstrip(":").strip()
        low = prompt.lower()
        if low.endswith("what do you do?"):
            rnd = (self.battle_now or {}).get("round", 0)
            key = (rnd, prompt)
            n = self._auto_counts.get(key, 0) + 1
            self._auto_counts = {key: n}
            in_melee = bool(keys and {"trip", "feint", "bull_rush"} & set(keys)) or any(
                o.startswith(("Trip a foe", "Feint", "Bull rush")) for o in real)
            if n <= 4:
                ans = pick("Stabilize a dying ally") if n == 1 else None
                if not ans and in_melee:
                    ans = pick("Full attack", "Attack")
                elif not ans:
                    # out of reach: attack (it offers a charge or a move) the first time,
                    # then just keep closing the distance
                    ans = (pick("Attack") if n == 1 else None) or \
                        pick("Move toward a foe (", "Move toward a foe again", "Attack")
                if ans:
                    return ans
            return pick("End turn") or str(len(real))
        if any("in melee with you" in o for o in real):
            return str(next(i for i, o in enumerate(real) if "in melee with you" in o) + 1)
        feet = []
        for i, o in enumerate(real):
            m = re.search(r"(\d+) ft\)", o) or re.search(r"(\d+) ft;", o)
            if m:
                feet.append((int(m.group(1)), i))
        if feet:
            return str(min(feet)[1] + 1)
        if default is not None and isinstance(default, int) and 0 <= default < len(real):
            return str(default + 1)
        return "1"

    def character_form(self, schema: dict) -> Optional[dict]:
        """Show the one-page character form. Returns the filled-in form, or None if
        the player would rather answer the questions one at a time."""
        owner = self.current_owner()
        self.table.emit({"t": "prompt", "text": "Create your hero", "options": None,
                         "kind": "form", "form": schema, "owner": owner, "groups": None})
        text, who = self.table.wait_input(owner)
        self.last_who = who
        try:
            spec = json.loads(text)
        except ValueError:
            spec = None
        if not isinstance(spec, dict) or not spec.get("name"):
            self.table.emit({"t": "line", "kind": "echo", "text": c(
                f"> {who}: (step-by-step questions)", "bold")})
            return None
        self.table.emit({"t": "line", "kind": "echo", "text": c(
            f"> {who}: creates {str(spec.get('name'))[:40]}", "bold")})
        return spec

    def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
        if options:
            opts = [ANSI_RE.sub("", o) for o in options]
            grp = list(groups) if groups else None
            if allow_cancel:
                opts = opts + ["(back)"]
                if grp:
                    grp.append("Game")
            self._pending_keys = getattr(self, "option_keys", None)
            self.option_keys = None
            if self._pending_keys and len(self._pending_keys) != len(options):
                self._pending_keys = None
            prev = (self._pending_groups, self._explore)
            self._pending_default = default
            self._pending_groups = grp
            self._explore = prompt == "What do you do?" and bool(groups)
            try:
                return self._with_options(opts, "choose", super().choose, prompt, options,
                                          allow_cancel, default)
            finally:
                self._pending_groups, self._explore = prev
        return super().choose(prompt, options, allow_cancel, default)

    def confirm(self, prompt, default=True):
        self._pending_default = default
        return self._with_options(["Yes", "No"], "confirm", super().confirm, prompt, default)

    def pause(self):
        return None  # sheets open in a pop-up on the web page; no need to wait

    def ask(self, prompt, default=None):
        if self._pending_kind == "text":
            self._pending_options = None
        if str(prompt).startswith(("Player name", "Who will play the new hero")):
            return self._pick_player(prompt, default)
        return super().ask(prompt, default)

    def _pick_player(self, prompt, default=None) -> str:
        """Online, a hero's player must be someone at the table (so 'whose turn'
        matching works), so offer the joined names as buttons."""
        here = self.table.present()
        if not here:
            ans = super().ask(prompt, "")
            return ans or self.last_who or (default or "")
        opts = here + ["Someone not here yet (type their name)"]
        i = self.choose("Who plays this hero?", opts)
        if i is not None and i < len(here):
            return here[i]
        ans = super().ask("Their name (it must match the name they join with)", "")
        return ans or self.last_who or (default or "")

    def _with_options(self, opts, kind, fn, *args):
        prev = (self._pending_options, self._pending_kind)
        self._pending_options, self._pending_kind = opts, kind
        try:
            return fn(*args)
        finally:
            self._pending_options, self._pending_kind = prev


class Table:
    """One shared game. Runs the normal game loop in a background thread."""

    def __init__(self, name: str):
        self.name = name
        self.events: List[dict] = []
        self.first_seq = 0
        self.seq = 0
        self.cond = threading.Condition()
        self.inputs: List[tuple] = []
        self.waiting = False
        self.owner = ""
        self.explore_idle = False
        self.item_lock = threading.Lock()
        self.presence: Dict[str, float] = {}
        self.afk: Dict[str, str] = {}      # normalized name -> "manual" / "idle"
        self.afk_mode = "computer"         # or "party": friends answer for away players
        self.tokens: Dict[str, list] = {}  # normalized name -> [browser token, last seen]
        self.covered: Dict[str, list] = {}  # away player -> [party answers, computer answers]
        self.manual: set = set()           # players who press "Roll" for their own heroes
        self.ui = WebUI(self)
        self.ui.autosave_name = f"autosave-{name}"
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def emit(self, ev: dict) -> None:
        with self.cond:
            ev["seq"] = self.seq
            self.seq += 1
            self.events.append(ev)
            if len(self.events) > MAX_EVENTS:
                drop = len(self.events) - MAX_EVENTS
                del self.events[:drop]
                self.first_seq = self.events[0]["seq"]
            self.cond.notify_all()

    def wait_input(self, owner: str = "", auto=None):
        """Wait for an answer. If the hero's player is away and auto is given, the
        computer answers for them after a short pause (so others can follow along)."""
        with self.cond:
            self.waiting = True
            self.owner = owner
            since = None
            while not self.inputs:
                if auto is not None and owner and self.afk_mode == "computer" \
                        and self.is_afk(owner):
                    since = since or time.time()
                    left = AUTOPILOT_DELAY - (time.time() - since)
                    if left <= 0:
                        ans = auto()
                        self.waiting = False
                        self.owner = ""
                        return ans, f"autopilot for {owner}"
                    self.cond.wait(timeout=left)
                    continue
                since = None
                self.cond.wait(timeout=5 if auto is not None else None)
            self.waiting = False
            self.owner = ""
            return self.inputs.pop(0)

    # ---- dice: optional manual rolls, and dice events for the animations
    def _hero_player(self, who) -> str:
        return (getattr(who, "player", "") or "") if getattr(who, "is_pc", False) else ""

    def before_roll(self, who, what: str, expr: str) -> None:
        """A player who rolls their own dice presses Roll before their hero's roll.
        Away or offline players are never waited for."""
        player = self._hero_player(who)
        if not player:
            return
        here = {self._norm(n) for n in self.present()}
        if self._norm(player) not in here or self.is_afk(player):
            # the hero's own player isn't here: whoever is playing it now rolls for it
            last = getattr(self.ui, "last_who", "") or ""
            if not last or last.startswith("autopilot") or self._norm(last) not in here \
                    or self.is_afk(last):
                return
            player = last
        if self._norm(player) not in self.manual:
            return
        self.emit({"t": "prompt", "text": f"{who.name}: {what} \u2014 roll {expr}",
                   "options": [f"\U0001f3b2 Roll {expr}"], "kind": "roll", "groups": None,
                   "owner": player})
        with self.cond:
            self.waiting = True
            self.owner = player
            self.inputs.clear()
            while not self.inputs:
                here = {self._norm(n) for n in self.present()}
                if self._norm(player) not in here or self.is_afk(player):
                    break
                self.cond.wait(timeout=5)
            if self.inputs:
                self.inputs.pop(0)
            self.waiting = False
            self.owner = ""

    def after_roll(self, who, what: str, expr: str, rolls, total: int) -> None:
        player = self._hero_player(who)
        if not player:
            return
        self.emit({"t": "dice", "hero": who.name, "player": player, "what": what,
                   "expr": expr, "rolls": [[sd, list(v)[:20]] for sd, v in rolls][:6],
                   "total": total})

    def set_manual(self, who: str, on: bool) -> None:
        key = self._norm(who)
        if not key:
            return
        with self.cond:
            if on:
                self.manual.add(key)
            else:
                self.manual.discard(key)
            self.cond.notify_all()

    def note_cover(self, owner: str, by: str) -> None:
        if not hasattr(self, "covered"):
            self.covered = {}
        n = self.covered.setdefault(self._norm(owner), [0, 0])
        n[0 if by == "party" else 1] += 1

    def is_afk(self, name: str) -> bool:
        """Marked away, or their page has been gone for over 5 minutes."""
        key = self._norm(name)
        if key in getattr(self, "afk", {}):
            return True
        seen = [t for n, t in list(self.presence.items()) if self._norm(n) == key]
        return bool(seen) and time.time() - max(seen) > IDLE_SECONDS

    def set_afk(self, who: str, away: bool, auto: bool = False) -> None:
        key = self._norm(who)
        if not key:
            return
        heroes = []
        gs = self.ui.game_state
        if gs is not None:
            heroes = [p.name for p in gs.party if self._norm(p.player or "") == key and not p.dead]
        with self.cond:
            was = key in self.afk
            if away and not was:
                self.afk[key] = "idle" if auto else "manual"
                getattr(self, "covered", {}).pop(key, None)   # count from now
            elif not away and was:
                del self.afk[key]
            else:
                if away:
                    self.afk[key] = "idle" if auto else "manual"
                return
            self.cond.notify_all()
        name = " ".join(who.split())
        if away:
            mine = ", ".join(heroes)
            why = " (no activity for 5 minutes)" if auto else ""
            how = (f" The computer will play {mine} in fights; anyone can answer for them "
                   f"otherwise." if self.afk_mode == "computer" else
                   f" Anyone at the table can answer for {mine}.") if mine else ""
            self.emit({"t": "line", "text": c(f"\u23f8 {name} is away{why}.{how}", "yellow")})
        else:
            party, comp = (getattr(self, "covered", {}).pop(key, None) or [0, 0])
            done = []
            if party:
                done.append(f"the party made {party} choice{'s' if party != 1 else ''}")
            if comp:
                done.append(f"the computer made {comp}")
            extra = (" While you were away, " + " and ".join(done) + " for your heroes."
                     ) if done else ""
            self.emit({"t": "line", "text": c(f"\u25b6 {name} is back.{extra}", "yellow")})

    def set_afk_mode(self, mode: str, who: str) -> None:
        if mode not in ("computer", "party") or mode == self.afk_mode:
            return
        with self.cond:
            self.afk_mode = mode
            self.cond.notify_all()
        name = " ".join(who.split()) or "Someone"
        text = ("the computer plays away players' heroes in fights" if mode == "computer"
                else "the party controls away players' heroes")
        self.emit({"t": "line", "text": c(f"{name} changed a table setting: {text}.", "yellow")})

    def bind_name(self, who: str, token: str) -> bool:
        """One browser per name: stops someone else at the table answering as you.
        A name is free again once its browser has been quiet for NAME_HOLD seconds."""
        key = self._norm(who)
        if not key:
            return True
        now = time.time()
        with self.cond:
            cur = self.tokens.get(key)
            if cur and cur[0] != token and now - cur[1] < NAME_HOLD:
                return False
            self.tokens[key] = [token, now]
            if len(self.tokens) > MAX_PRESENCE:
                for k in sorted(self.tokens, key=lambda k: self.tokens[k][1])[:10]:
                    self.tokens.pop(k, None)
            return True

    def present(self) -> List[str]:
        now = time.time()
        return [n for n, t in list(self.presence.items()) if now - t < POLL_SECONDS + 15]

    @staticmethod
    def _norm(name: str) -> str:
        return " ".join(str(name).split()).lower()

    def may_answer(self, who: str) -> bool:
        """The hero's player answers for that hero. If they're not connected
        (or the hero isn't claimed by anyone here), anyone may answer."""
        owner = self.owner
        if not owner:
            return True
        if self.is_afk(owner) and self._norm(who) != self._norm(owner):
            return True
        here = {self._norm(n) for n in self.present()}
        if self._norm(owner) not in here:
            return True
        return self._norm(who) == self._norm(owner)

    def submit(self, text: str, who: str):
        with self.item_lock, self.cond:   # never resume the game mid gear-change
            if not self.waiting:
                return False, "The GM is not waiting for input right now."
            if not self.may_answer(who):
                return False, f"It's {self.owner}'s decision. Wait for them (or chat)."
            self.inputs.append((text[:2000], who[:30]))
            self.cond.notify_all()
            return True, ""

    def item_action(self, hero: int, item: int, action: str, target: int, who: str):
        """Inventory changes from the character sheet, only between exploration actions."""
        from .data.items import EQUIPPABLE_KINDS, item_data, item_name
        from .magic import cast_spell, use_scroll_check
        from .effects import Effect, ROUNDS_PER_HOUR
        gs = self.ui.game_state
        if gs is None:
            return False, "No game running."
        with self.item_lock:
            if not (self.waiting and self.explore_idle):
                return False, ("You can manage gear while exploring, between actions "
                               "(not during combat, shopping or other questions).")
            if not (0 <= hero < len(gs.party)):
                return False, "No such hero."
            ch = gs.party[hero]
            owner = ch.player or ""
            here = {self._norm(n) for n in self.present()}
            if owner and self._norm(owner) in here and self._norm(owner) != self._norm(who):
                return False, f"That's {owner}'s hero. Ask them (or use chat)."
            if ch.dead or not (0 <= item < len(ch.inventory)):
                return False, "That item isn't there any more."
            e = ch.inventory[item]
            d = item_data(e)
            name = item_name(e)
            others = [p for p in gs.party if not p.dead]
            tgt = gs.party[target] if 0 <= target < len(gs.party) else ch

            def say(msg):
                self.emit({"t": "line", "kind": "inv", "text": c(f"\U0001f392 {msg}", "bcyan")})

            if e.get("unidentified") and action in ("use", "equip", "equip_off"):
                return False, ("Nobody knows what that does yet. Have it identified in "
                               "town, or let a spellcaster study it.")
            from .data.items import stuck
            if stuck(e) and action in ("unequip", "drop", "give", "equip", "equip_off"):
                return False, f"{name} is cursed. It won't come off without Remove Curse."
            if action in ("equip", "equip_off"):
                if d["kind"] not in EQUIPPABLE_KINDS:
                    return False, "That can't be equipped."
                say(ch.equip(e, "off" if action == "equip_off" else None))
            elif action == "unequip":
                ch.unequip(e)
                say(f"{ch.name} puts away {name}.")
            elif action == "drop":
                e.pop("slot", None)
                ch.inventory.remove(e)
                say(f"{ch.name} drops {name}.")
            elif action == "give":
                if tgt is ch or tgt not in others:
                    return False, "Give it to whom?"
                given = dict(e, qty=1)
                given.pop("slot", None)
                if e.get("qty", 1) > 1:
                    e["qty"] -= 1
                else:
                    ch.inventory.remove(e)
                tgt.add_item(given)
                say(f"{ch.name} gives {name} to {tgt.name}.")
            elif action == "use" and d["kind"] == "wand":
                from .data.spells import SPELLS
                from .magic import device_cast, use_device_check
                sp = SPELLS[d["spell"]]
                if sp["target"] in ("enemy", "enemies"):
                    return False, "Save that for a fight."
                if use_device_check(self.ui, ch, d, d["spell"]):
                    say(f"{ch.name} uses {name}.")
                    device_cast(self.ui, ch, e, d["spell"],
                                [tgt if sp["target"] == "ally" else ch], allies=others)
            elif action == "use":
                use = d.get("use")
                if use == "antitoxin":
                    ch.add_effect(Effect("Antitoxin", ROUNDS_PER_HOUR,
                                         [("save_fort_poison", "alchemical", 5)]))
                    ch.remove_item(e, 1)
                    say(f"{ch.name} drinks the antitoxin.")
                elif use in ("spell", "scroll"):
                    from .data.spells import SPELLS
                    sp = SPELLS[d["spell"]]
                    if sp["target"] in ("enemy", "enemies"):
                        return False, "Save that for a fight."
                    if use == "scroll" and not use_scroll_check(self.ui, ch, d):
                        return True, ""
                    lvl = min(sp["levels"].values())
                    who_gets = tgt if sp["target"] == "ally" else ch
                    if use == "spell" and who_gets is not ch:
                        say(f"{ch.name} gives {who_gets.name} {name}.")
                    else:
                        say(f"{ch.name} uses {name}.")
                    cast_spell(self.ui, ch if use == "scroll" else who_gets, d["spell"],
                               [who_gets], d.get("cl", 1), 10 + lvl + lvl // 2,
                               allies=others)
                    ch.remove_item(e, 1)
                else:
                    return False, "That can't be used outside combat."
            else:
                return False, "Unknown action."
            return True, ""

    def claim(self, index: int, who: str):
        gs = self.ui.game_state
        if gs is None or not (0 <= index < len(gs.party)) or not who:
            return False, "Nothing to claim."
        hero = gs.party[index]
        cur = hero.player or ""
        here = {n.lower() for n in self.present()}
        if cur and cur.lower() in here and cur.lower() != who.lower():
            return False, f"{hero.name} is played by {cur}, who is at the table."
        hero.player = who
        self.emit({"t": "line", "text": c(f"{who} now plays {hero.name}.", "bgreen")})
        return True, ""

    def chat(self, text: str, who: str) -> None:
        self.emit({"t": "chat", "who": who[:30], "text": text[:500]})

    def state(self) -> dict:
        """Snapshot of the party and journal for the Party / Journal tabs."""
        gs = self.ui.game_state
        if gs is None:
            return {"active": False}
        from .rules import money_str
        from .sheet import render, sheet_data
        party = []
        for p in list(gs.party):
            nxt = p.xp_next() if p.level < MAX_LEVEL else None
            party.append({
                "name": p.name, "player": p.player, "race": p.race_data["name"],
                "classes": p.class_summary(), "level": p.level, "hp": p.hp,
                "max_hp": p.max_hp(), "temp_hp": p.temp_hp, "ac": p.ac(),
                "touch": p.ac("touch"), "flat": p.ac("flat"), "status": p.status_word(),
                "effects": [e.describe() for e in p.effects if not e.hidden],
                "xp": p.xp, "xp_next": nxt, "can_level": p.can_level_up(),
                "money": money_str(p.cp), "sheet": render(p), "sheet_data": sheet_data(p),
                "spells": sum(1 for _ in p.available_casts()),
            })
        rooms = gs.adv.ROOMS
        visited = [rooms[r]["name"] for r, st in gs.rooms.items()
                   if st.get("visited") and r in rooms]
        from .adventure.mapping import map_data
        return {"active": True, "location": rooms.get(gs.room, {}).get("name", gs.room),
                "can_manage": bool(self.waiting and self.explore_idle),
                "map": map_data(gs),
                "battle": getattr(self.ui, "battle_now", None),
                "time": gs.time_str(), "party": party, "journal": list(gs.journal),
                "visited": visited, "adventure": gs.adv.TITLE,
                "heroic": gs.settings.get("heroic", False)}

    def poll(self, since: int, who: str, timeout: float = POLL_SECONDS) -> dict:
        if who and who.strip():
            with self.cond:
                self.presence[" ".join(who.split())[:30]] = time.time()
                if len(self.presence) > MAX_PRESENCE:
                    for n in sorted(self.presence, key=self.presence.get)[:10]:
                        self.presence.pop(n, None)
        deadline = time.time() + timeout
        with self.cond:
            while self.seq <= since and time.time() < deadline:
                self.cond.wait(timeout=max(0.1, deadline - time.time()))
            start = max(since, self.first_seq)
            evs = [e for e in self.events if e["seq"] >= start]
            here = sorted(self.present())
            return {"events": evs, "next": self.seq, "here": here, "waiting": self.waiting,
                    "owner": self.owner if self.waiting else "",
                    "may_answer": self.may_answer(who) if self.waiting else False,
                    "away": [n for n in here if self._norm(n) in self.afk],
                    "me_away": self.afk.get(self._norm(who), ""),
                    "afk_mode": self.afk_mode,
                    "manual": self._norm(who) in getattr(self, "manual", set()),
                    "reset": since < self.first_seq}

    def _run(self) -> None:
        GAME_THREADS[threading.get_ident()] = self
        from .adventure.engine import list_saves, load_game, save_info
        from .game import gm_play_loaded, main_menu
        Color.enabled = True
        resume = True
        while True:
            try:
                self.ui.header(f"TABLE '{self.name}' IS OPEN")
                self.ui.para("Everyone at this table sees the same game. Click a choice or "
                             "type an answer. In combat, the game names whose turn it is; "
                             "that player should answer. Use the chat box to talk.")
                auto = self.ui.autosave_name
                if resume and auto in list_saves():
                    resume = False
                    self.ui.good("Resuming where you left off: " +
                                 save_info(auto).split(": ", 1)[-1])
                    self.ui.out("(To start something else, choose More options -> Quit "
                                "to go to the main menu.)", ("dim",))
                    gm_play_loaded(self.ui, load_game(auto))
                    continue
                resume = False
                main_menu(self.ui)
            except QuitGame:
                pass
            except Exception:  # keep the table alive no matter what
                self.ui.out("The GM fumbled the dice (internal error). Restarting the "
                            "main menu; load the autosave to continue.", ("bred",))
                traceback.print_exc()   # details go to the server log, not to players
            time.sleep(0.5)


GAME_THREADS: Dict[int, "Table"] = {}


def _dispatch(method):
    def hook(*args):
        t = GAME_THREADS.get(threading.get_ident())
        if t is not None:
            getattr(t, method)(*args)
    return hook


dice.before_roll = _dispatch("before_roll")   # only game threads of web tables are affected
dice.after_roll = _dispatch("after_roll")

TABLES: Dict[str, Table] = {}
TABLES_LOCK = threading.Lock()


class TooManyTables(Exception):
    pass


def get_table(name: str) -> Table:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", str(name))[:32] or "main"
    with TABLES_LOCK:
        if name not in TABLES:
            if len(TABLES) >= MAX_TABLES:
                raise TooManyTables()
            TABLES[name] = Table(name)
        return TABLES[name]


BUCKETS: Dict[tuple, list] = {}
BUCKETS_LOCK = threading.Lock()


def allow(who: str, kind: str = "default") -> bool:
    """Token-bucket rate limit per browser (or address) and kind of request."""
    size, per_sec = RATE[kind]
    now = time.time()
    with BUCKETS_LOCK:
        if len(BUCKETS) > 5000:
            BUCKETS.clear()
        b = BUCKETS.setdefault((who, kind), [float(size), now])
        b[0] = min(size, b[0] + (now - b[1]) * per_sec)
        b[1] = now
        if b[0] < 1:
            return False
        b[0] -= 1
        return True


def session_token(pw: str, exp: Optional[int] = None) -> str:
    """A signed pass the browser keeps instead of the password itself. It survives
    server restarts and stops working when the password changes or after 30 days."""
    exp = exp or int(time.time()) + SESSION_DAYS * 86400
    sig = hmac.new(hashlib.sha256(pw.strip().encode()).digest(),
                   f"dnd35-session:{exp}".encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def session_ok(token: str, pw: str) -> bool:
    try:
        exp = int(token.split(".", 1)[0])
    except ValueError:
        return False
    return exp > time.time() and hmac.compare_digest(token, session_token(pw, exp))


FAILS: Dict[str, list] = {}
FAILS_LOCK = threading.Lock()


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                                "media-src 'self' blob:; connect-src 'self'; "
                                "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),
}


class Handler(BaseHTTPRequestHandler):
    server_version = "dnd35"
    sys_version = ""
    timeout = 90   # drop stalled connections (long polls last 25 s)

    def end_headers(self):
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        super().end_headers()

    def _ip(self) -> str:
        return (self.headers.get("Fly-Client-IP") or self.client_address[0] or "?")[:64]

    def _locked_out(self) -> bool:
        with FAILS_LOCK:
            now = time.time()
            times = [t for t in FAILS.get(self._ip(), []) if now - t < FAIL_WINDOW]
            FAILS[self._ip()] = times
            if len(FAILS) > 5000:
                FAILS.clear()
            return len(times) >= FAIL_LIMIT

    def _deny(self) -> bool:
        """True (and an error sent) if the password is wrong or this IP is locked out."""
        if self._locked_out():
            self._json({"error": "too many wrong passwords; try again in 10 minutes"}, 429)
            return True
        if self._auth():
            return False
        with FAILS_LOCK:
            FAILS.setdefault(self._ip(), []).append(time.time())
        self._json({"error": "bad password"}, 403)
        return True

    def _player_ok(self, t: "Table", who: str) -> bool:
        token = self.headers.get("X-Player-Token", "")[:64]
        if not who.strip():
            return True
        if not token:
            self._json({"error": "reload", "why": "Please reload the page."}, 400)
            return False
        if not t.bind_name(who, token):
            self._json({"error": "name taken",
                        "why": f"Someone else is already using the name '{who}' at this "
                               f"table. Pick another name (if it's you on another device, "
                               f"close it there and wait a minute)."}, 409)
            return False
        return True

    def _table(self, name) -> Optional["Table"]:
        try:
            return get_table(name)
        except TooManyTables:
            self._json({"error": "too many tables", "why": "This server is full; use an "
                        "existing table name."}, 503)
            return None

    def log_message(self, fmt, *args):  # quieter logs
        if os.environ.get("DND35_VERBOSE"):
            super().log_message(fmt, *args)

    def _auth(self) -> bool:
        pw = os.environ.get("TABLE_PASSWORD")
        if not pw:
            return True
        sess = self.headers.get("X-Session") or ""
        if sess and session_ok(sess[:120], pw):
            return True
        given = (self.headers.get("X-Password") or "").strip()
        return bool(given) and hmac.compare_digest(given.encode(), pw.strip().encode())

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            data = PAGE.replace("__NEEDPW__", "true" if os.environ.get("TABLE_PASSWORD")
                                else "false").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")   # always pick up new versions
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if u.path in STATIC:
            data, ctype = STATIC[u.path]
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "public, max-age=31536000, immutable"
                             if qs.get("v") == [_VER] else "no-cache")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if u.path == "/api/state":
            if self._deny():
                return
            t = self._table(qs.get("table", ["main"])[0])
            if t is None:
                return
            try:
                self._json(t.state())
            except Exception:  # game thread mid-update; the page will retry
                self._json({"active": False, "busy": True})
            return
        if u.path == "/api/tts/status":
            from . import tts
            self._json(tts.status())
            return
        if u.path == "/healthz":
            self._json({"ok": True})
            return
        if u.path == "/api/poll":
            if self._deny():
                return
            t = self._table(qs.get("table", ["main"])[0])
            if t is None:
                return
            who = qs.get("name", [""])[0][:30]
            if not self._player_ok(t, who):
                return
            try:
                since = max(0, int(qs.get("since", ["0"])[0] or 0))
            except ValueError:
                since = 0
            self._json(t.poll(since, who))
            return
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        if self._deny():
            return
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = -1
        if not 0 <= length <= 10000:
            self._json({"error": "bad request"}, 400)
            return
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except ValueError:
            self._json({"error": "bad request"}, 400)
            return
        if u.path == "/api/login":
            self._json({"ok": True, "session": session_token(
                os.environ.get("TABLE_PASSWORD") or "")})
            return
        limiter = self.headers.get("X-Player-Token", "")[:64] or self._ip()
        if not allow(limiter, "tts" if u.path == "/api/tts" else "default"):
            self._json({"ok": False, "error": "slow down",
                        "why": "Too many requests; wait a moment."}, 429)
            return
        t = self._table(body.get("table", "main"))
        if t is None:
            return
        who = str(body.get("name", ""))[:30]
        if u.path != "/api/tts" and not self._player_ok(t, who):
            return
        if u.path == "/api/input":
            ok, why = t.submit(str(body.get("text", "")), who)
            self._json({"ok": ok, "why": why})
        elif u.path == "/api/tts":
            from . import tts
            if not tts.status()["available"]:
                self._json({"error": "server voice not installed"}, 503)
                return
            if not TTS_SLOTS.acquire(timeout=20):
                self._json({"error": "voice busy"}, 503)
                return
            try:
                data = tts.synthesize(str(body.get("text", ""))[:1500],
                                      str(body.get("role", "gm")),
                                      float(body.get("speed", 1.0) or 1.0))
            except Exception:  # noqa: BLE001
                traceback.print_exc()
                self._json({"error": "voice failed"}, 500)
                return
            finally:
                TTS_SLOTS.release()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif u.path == "/api/item":
            try:
                ok, why = t.item_action(int(body.get("hero", -1)), int(body.get("item", -1)),
                                        str(body.get("action", "")),
                                        int(body.get("target", -1)), who)
            except (TypeError, ValueError):
                ok, why = False, "bad request"
            self._json({"ok": ok, "why": why})
        elif u.path == "/api/claim":
            try:
                ok, why = t.claim(int(body.get("hero", -1)), who)
            except (TypeError, ValueError):
                ok, why = False, "bad request"
            self._json({"ok": ok, "why": why})
        elif u.path == "/api/afk":
            t.set_afk(who, bool(body.get("away")), bool(body.get("auto")))
            self._json({"ok": True})
        elif u.path == "/api/prefs":
            t.set_manual(who, bool(body.get("manual_dice")))
            self._json({"ok": True})
        elif u.path == "/api/afkmode":
            t.set_afk_mode(str(body.get("mode", "")), who)
            self._json({"ok": True})
        elif u.path == "/api/chat":
            t.chat(str(body.get("text", "")), who)
            self._json({"ok": True})
        elif u.path == "/api/roll":
            try:
                res = free_roll(str(body.get("expr", "")))
            except ValueError as e:
                self._json({"ok": False, "why": str(e)})
                return
            t.emit({"t": "roll", "who": who or "someone", "label": str(body.get("label", ""))[:60],
                    **res})
            self._json({"ok": True, **res})
        else:
            self.send_error(404)


_HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = {}
for _name, _ctype in (("app.js", "text/javascript; charset=utf-8"),
                      ("app.css", "text/css; charset=utf-8")):
    with open(os.path.join(_HERE, "static", _name), "rb") as _f:
        STATIC["/static/" + _name] = (_f.read(), _ctype)
_VER = hashlib.sha256(b"".join(v[0] for v in STATIC.values())).hexdigest()[:12]
PAGE = open(os.path.join(_HERE, "web_page.html"), encoding="utf-8").read().replace(
    "__VER__", _VER)


def drop_privileges() -> None:
    """If started as root (as in the container), hand the save folder to an
    unprivileged user and switch to it. Any failure just leaves things as they were."""
    user = os.environ.get("DND35_RUN_AS")
    if not user or not hasattr(os, "getuid") or os.getuid() != 0:
        return
    try:
        import pwd
        from .adventure.engine import SAVE_DIR
        pw = pwd.getpwnam(user)
        os.makedirs(SAVE_DIR, exist_ok=True)
        for root, dirs, files in os.walk(SAVE_DIR):
            for n in [root] + [os.path.join(root, f) for f in files]:
                os.chown(n, pw.pw_uid, pw.pw_gid)
        os.setgroups([])
        os.setgid(pw.pw_gid)
        os.setuid(pw.pw_uid)
        os.environ["HOME"] = pw.pw_dir
        print(f"running as {user}")
    except Exception as e:  # noqa: BLE001
        print(f"could not switch to user {user}: {e}; continuing as root")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Host a shared D&D 3.5 table on the web")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = ap.parse_args(argv)
    local = args.host in ("127.0.0.1", "localhost", "::1")
    if not local and not os.environ.get("TABLE_PASSWORD") and \
            not os.environ.get("DND35_ALLOW_OPEN"):
        print("Refusing to start: this server would be open to anyone on the network.\n"
              "Set TABLE_PASSWORD (on Fly: fly secrets set TABLE_PASSWORD=...), or set\n"
              "DND35_ALLOW_OPEN=1 if you really want no password.")
        return 2
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    drop_privileges()
    print(f"D&D 3.5 table running on http://{args.host}:{args.port}/  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
