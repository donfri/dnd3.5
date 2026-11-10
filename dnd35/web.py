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
        super().para(text, style, indent)

    def header(self, text: str) -> None:
        title = text.strip()
        if title and not title.startswith(("TABLE", "NEW GAME", "HERO ")):
            words = " ".join(w.capitalize() for w in title.lower().split())
            self.table.emit({"t": "narrate", "kind": "title", "text": words + "."})
        super().header(text)

    # input <- browser
    def _raw_input(self, prompt: str) -> str:
        opts = self._pending_options
        kind = self._pending_kind
        groups = self._pending_groups if kind == "choose" else None
        owner = self.current_owner()
        self.table.emit({"t": "prompt", "text": ANSI_RE.sub("", prompt), "options": opts,
                         "kind": kind, "groups": groups, "owner": owner})
        text, who = self.table.wait_input(owner)
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
            prev = self._pending_groups
            self._pending_groups = grp
            try:
                return self._with_options(opts, "choose", super().choose, prompt, options,
                                          allow_cancel, default)
            finally:
                self._pending_groups = prev
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
        self.presence: Dict[str, float] = {}
        self.ui = WebUI(self)
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
        from .sheet import render
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
                "money": money_str(p.cp), "sheet": render(p),
                "spells": sum(1 for _ in p.available_casts()),
            })
        rooms = gs.adv.ROOMS
        visited = [rooms[r]["name"] for r, st in gs.rooms.items()
                   if st.get("visited") and r in rooms]
        return {"active": True, "location": rooms.get(gs.room, {}).get("name", gs.room),
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
        from .game import main_menu
        Color.enabled = True
        while True:
            try:
                self.ui.header(f"TABLE '{self.name}' IS OPEN")
                self.ui.para("Everyone at this table sees the same game. Click a choice or "
                             "type an answer. In combat, the game names whose turn it is; "
                             "that player should answer. Use the chat box to talk.")
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
        return given == pw

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
        elif u.path == "/api/claim":
            try:
                ok, why = t.claim(int(body.get("hero", -1)), who)
            except (TypeError, ValueError):
                ok, why = False, "bad request"
            self._json({"ok": ok, "why": why})
        elif u.path == "/api/chat":
            t.chat(str(body.get("text", "")), who)
            self._json({"ok": True})
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
