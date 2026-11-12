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

from .ui import UI, Color, QuitGame, c

MAX_EVENTS = 4000
POLL_SECONDS = 25
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
    pos, total, parts, dice_count = 0, 0, [], 0
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
    return {"expr": expr.strip(), "detail": "  ".join(parts), "total": total}


class WebUI(UI):
    """A UI whose screen is an event log shared by every connected browser."""

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
        self.table.emit({"t": "prompt", "text": ANSI_RE.sub("", prompt), "options": opts,
                         "kind": kind, "groups": groups, "owner": owner})
        text, who = self.table.wait_input(owner)
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
        self.table.emit({"t": "line", "kind": "echo",
                         "text": c(f"> {who + ': ' if who else ''}{shown}", "bold")})
        if text.strip().lower() in ("/quit", "/exit"):
            return ""  # nobody can kill the shared table from a browser
        return text

    def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
        if options:
            opts = [ANSI_RE.sub("", o) for o in options]
            grp = list(groups) if groups else None
            if allow_cancel:
                opts = opts + ["(back)"]
                if grp:
                    grp.append("Game")
            prev = (self._pending_groups, self._explore)
            self._pending_groups = grp
            self._explore = prompt == "What do you do?" and bool(groups)
            try:
                return self._with_options(opts, "choose", super().choose, prompt, options,
                                          allow_cancel, default)
            finally:
                self._pending_groups, self._explore = prev
        return super().choose(prompt, options, allow_cancel, default)

    def confirm(self, prompt, default=True):
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

    def wait_input(self, owner: str = ""):
        with self.cond:
            self.waiting = True
            self.owner = owner
            while not self.inputs:
                self.cond.wait()
            self.waiting = False
            self.owner = ""
            return self.inputs.pop(0)

    def present(self) -> List[str]:
        now = time.time()
        return [n for n, t in self.presence.items() if now - t < POLL_SECONDS + 15]

    @staticmethod
    def _norm(name: str) -> str:
        return " ".join(str(name).split()).lower()

    def may_answer(self, who: str) -> bool:
        """The hero's player answers for that hero. If they're not connected
        (or the hero isn't claimed by anyone here), anyone may answer."""
        owner = self.owner
        if not owner:
            return True
        here = {self._norm(n) for n in self.present()}
        if self._norm(owner) not in here:
            return True
        return self._norm(who) == self._norm(owner)

    def submit(self, text: str, who: str):
        with self.cond:
            if not self.waiting:
                return False, "The GM is not waiting for input right now."
            if not self.may_answer(who):
                return False, f"It's {self.owner}'s decision. Wait for them (or chat)."
            self.inputs.append((text[:200], who[:30]))
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
            nxt = p.xp_next() if p.level < 5 else None
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
            self.presence[" ".join(who.split())[:30]] = time.time()
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
                    "reset": since < self.first_seq}

    def _run(self) -> None:
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
                self.ui.out(traceback.format_exc(), ("dim",))
            time.sleep(0.5)


TABLES: Dict[str, Table] = {}
TABLES_LOCK = threading.Lock()


def get_table(name: str) -> Table:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)[:32] or "main"
    with TABLES_LOCK:
        if name not in TABLES:
            TABLES[name] = Table(name)
        return TABLES[name]


class Handler(BaseHTTPRequestHandler):
    server_version = "dnd35/1"

    def log_message(self, fmt, *args):  # quieter logs
        if os.environ.get("DND35_VERBOSE"):
            super().log_message(fmt, *args)

    def _auth(self, qs) -> bool:
        pw = os.environ.get("TABLE_PASSWORD")
        if not pw:
            return True
        given = self.headers.get("X-Password") or qs.get("pw", [""])[0]
        return given.strip() == pw.strip()

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
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if u.path == "/api/state":
            if not self._auth(qs):
                self._json({"error": "bad password"}, 403)
                return
            t = get_table(qs.get("table", ["main"])[0])
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
            if not self._auth(qs):
                self._json({"error": "bad password"}, 403)
                return
            t = get_table(qs.get("table", ["main"])[0])
            since = int(qs.get("since", ["0"])[0] or 0)
            self._json(t.poll(since, qs.get("name", [""])[0]))
            return
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not self._auth(qs):
            self._json({"error": "bad password"}, 403)
            return
        length = min(int(self.headers.get("Content-Length", 0) or 0), 10000)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            body = {}
        t = get_table(body.get("table", "main"))
        who = str(body.get("name", ""))[:30]
        if u.path == "/api/input":
            ok, why = t.submit(str(body.get("text", "")), who)
            self._json({"ok": ok, "why": why})
        elif u.path == "/api/tts":
            from . import tts
            if not tts.status()["available"]:
                self._json({"error": "server voice not installed"}, 503)
                return
            try:
                data = tts.synthesize(str(body.get("text", "")), str(body.get("role", "gm")),
                                      float(body.get("speed", 1.0) or 1.0))
            except Exception as e:  # noqa: BLE001
                self._json({"error": str(e)}, 500)
                return
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


PAGE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_page.html"),
            encoding="utf-8").read()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Host a shared D&D 3.5 table on the web")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = ap.parse_args(argv)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    print(f"D&D 3.5 table running on http://{args.host}:{args.port}/  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
