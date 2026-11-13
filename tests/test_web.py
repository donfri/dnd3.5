import json
import os
import urllib.error
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from dnd35 import web


class TestWeb(unittest.TestCase):
    def test_two_players_share_a_table(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def poll(name, since=0):
            req = urllib.request.Request(
                f"{base}/api/poll?table=test&since={since}&name={name}",
                headers={"X-Player-Token": "tok-" + name})
            with urllib.request.urlopen(req) as r:
                return json.load(r)

        def post(path, body):
            req = urllib.request.Request(base + path, json.dumps(body).encode(),
                                         {"Content-Type": "application/json",
                                          "X-Player-Token": "tok-" + body.get("name", "")})
            with urllib.request.urlopen(req) as r:
                return json.load(r)

        for _ in range(50):
            j = poll("Alice")
            if j["waiting"]:
                break
            time.sleep(0.1)
        self.assertTrue(j["waiting"])
        post("/api/chat", {"table": "test", "name": "Bob", "text": "hi"})
        self.assertTrue(post("/api/input", {"table": "test", "name": "Bob", "text": "2"})["ok"])
        time.sleep(0.3)
        self.assertTrue(post("/api/input", {"table": "test", "name": "Bob", "text": "1"})["ok"])
        time.sleep(0.5)
        j = poll("Bob", since=0)
        texts = " ".join(e.get("text", "") for e in j["events"])
        self.assertIn("Millbrook", texts)
        self.assertEqual(sorted(j["here"]), ["Alice", "Bob"])
        self.assertTrue(any(e["t"] == "chat" for e in j["events"]))
        with urllib.request.urlopen(base + "/") as r:
            self.assertIn(b"Join the table", r.read())
        srv.shutdown()


class TestOwnership(unittest.TestCase):
    def test_only_owner_answers_when_present(self):
        t = web.Table.__new__(web.Table)  # no game thread needed
        t.presence = {"Alice": time.time(), "Bob": time.time()}
        t.owner = "Bob"
        t.waiting = True
        t.inputs = []
        t.cond = threading.Condition()
        t.item_lock = threading.Lock()
        t.afk = {}
        ok, why = t.submit("1", "Alice")
        self.assertFalse(ok)
        self.assertIn("Bob", why)
        ok, _ = t.submit("1", "bob")
        self.assertTrue(ok)
        t.inputs.clear()
        t.presence = {"Alice": time.time()}  # Bob left: anyone may answer
        ok, _ = t.submit("1", "Alice")
        self.assertTrue(ok)


class TestAway(unittest.TestCase):
    def bare_table(self):
        t = web.Table.__new__(web.Table)  # no game thread needed
        t.presence = {"Alice": time.time(), "Bob": time.time()}
        t.afk = {}
        t.afk_mode = "computer"
        t.item_lock = threading.Lock()
        t.owner = ""
        t.waiting = False
        t.inputs = []
        t.events, t.seq, t.first_seq = [], 0, 0
        t.cond = threading.Condition()
        t.ui = web.WebUI.__new__(web.WebUI)
        t.ui.game_state = None
        return t

    def test_away_player_can_be_answered_for(self):
        t = self.bare_table()
        t.owner, t.waiting = "Bob", True
        self.assertFalse(t.may_answer("Alice"))
        t.set_afk("Bob", True)
        self.assertTrue(t.is_afk("bob"))
        self.assertTrue(t.may_answer("Alice"))
        self.assertTrue(any("away" in e.get("text", "") for e in t.events))
        t.set_afk("Bob", False)
        self.assertFalse(t.may_answer("Alice"))

    def test_back_summary_counts_cover(self):
        t = self.bare_table()
        t.set_afk("Bob", True)
        t.note_cover("Bob", "party")
        t.note_cover("bob", "party")
        t.note_cover("Bob", "computer")
        t.set_afk("Bob", False)
        last = t.events[-1]["text"]
        self.assertIn("the party made 2 choices", last)
        self.assertIn("the computer made 1", last)

    def test_page_gone_five_minutes_counts_as_away(self):
        t = self.bare_table()
        t.presence["Bob"] = time.time() - web.IDLE_SECONDS - 5
        self.assertTrue(t.is_afk("Bob"))
        self.assertFalse(t.is_afk("Alice"))

    def test_autopilot_answers_for_away_player(self):
        t = self.bare_table()
        t.set_afk("Bob", True, auto=True)
        old = web.AUTOPILOT_DELAY
        web.AUTOPILOT_DELAY = 0.05
        try:
            ans, who = t.wait_input("Bob", lambda: "2")
        finally:
            web.AUTOPILOT_DELAY = old
        self.assertEqual(ans, "2")
        self.assertIn("autopilot", who)
        # not away: a real answer is used instead
        t.set_afk("Bob", False)
        t.inputs.append(("1", "Bob"))
        self.assertEqual(t.wait_input("Bob", lambda: "2"), ("1", "Bob"))

    def test_autopick_choices(self):
        ui = web.WebUI.__new__(web.WebUI)
        ui.battle_now = {"round": 1}
        ui._auto_counts = {}
        menu = ["Attack (standard action)", "Full attack (all your attacks)",
                "Trip a foe (knock them prone)", "End turn"]
        self.assertEqual(ui.autopick("Thorgar, what do you do?: ", menu, "choose", None), "2")
        far = ["Attack (standard action)", "Charge", "Move toward a foe (move action)",
               "End turn"]
        self.assertEqual(ui.autopick("Lyra, what do you do?", far, "choose", None), "1")
        self.assertEqual(ui.autopick("Lyra, what do you do?", far, "choose", None), "3")
        for _ in range(3):
            ui.autopick("Lyra, what do you do?", far, "choose", None)
        self.assertEqual(ui.autopick("Lyra, what do you do?", far, "choose", None), "4")
        moved = ["Attack (standard action)", "Move toward a foe again (uses your standard "
                 "action)", "End turn"]
        ui.battle_now = {"round": 2}
        ui.autopick("Lyra, what do you do?", moved, "choose", None)
        self.assertEqual(ui.autopick("Lyra, what do you do?", moved, "choose", None), "2")
        foes = ["Goblin A (unhurt; 45 ft)", "Goblin B (wounded; 20 ft)", "(back)"]
        self.assertEqual(ui.autopick("Target", foes, "choose", None), "2")
        self.assertEqual(ui.autopick("Charge it instead?", ["Yes", "No"], "confirm", True), "y")


class TestManualDice(unittest.TestCase):
    def test_waits_for_the_player_only_when_they_are_here(self):
        t = TestAway().bare_table()
        t.manual = set()

        class Hero:
            is_pc, player, name = True, "Bob", "Thorgar"
        hero = Hero()
        t.before_roll(hero, "attack", "1d20")            # Bob hasn't asked: no prompt
        self.assertFalse(any(e["t"] == "prompt" for e in t.events))
        t.set_manual("Bob", True)
        threading.Timer(0.2, lambda: t.submit("1", "Bob")).start()
        start = time.time()
        t.before_roll(hero, "attack", "1d20")
        self.assertGreater(time.time() - start, 0.15)     # it waited for Bob's click
        self.assertTrue(any(e.get("kind") == "roll" for e in t.events))
        t.set_afk("Bob", True)                            # away: rolled for him at once
        start = time.time()
        t.before_roll(hero, "attack", "1d20")
        self.assertLess(time.time() - start, 0.1)

    def test_dice_events_for_heroes_only(self):
        t = TestAway().bare_table()

        class Hero:
            is_pc, player, name = True, "Bob", "Thorgar"

        class Orc:
            is_pc, name = False, "Orc"
        t.after_roll(Orc(), "attack", "1d20", [(20, [7])], 7)
        t.after_roll(Hero(), "attack", "1d20", [(20, [20])], 20)
        ev = [e for e in t.events if e["t"] == "dice"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["rolls"], [[20, [20]]])

    def test_free_rolls_report_faces(self):
        r = web.free_roll("2d6+1")
        self.assertEqual(r["rolls"][0][0], 6)
        self.assertEqual(len(r["rolls"][0][1]), 2)


class TestTTS(unittest.TestCase):
    def test_status_and_fallback(self):
        from dnd35 import tts
        st = tts.status()
        self.assertIn("available", st)
        self.assertEqual(set(st["voices"]), {"gm", "npc"})


class TestFreeRoll(unittest.TestCase):
    def test_expressions(self):
        for _ in range(200):
            self.assertTrue(1 <= web.free_roll("d20")["total"] <= 20)
            self.assertTrue(3 <= web.free_roll("2d6+1")["total"] <= 13)
            self.assertTrue(3 <= web.free_roll("4d6kh3")["total"] <= 18)
        for bad in ("banana", "", "1000d6", "d1", "2d6+"):
            with self.assertRaises(ValueError):
                web.free_roll(bad)


class TestSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, path, body=None, headers=None):
        h = {"Content-Type": "application/json", **(headers or {})}
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data, h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def test_security_headers(self):
        code, h, _ = self.req("/")
        self.assertEqual(code, 200)
        self.assertIn("frame-ancestors 'none'", h["Content-Security-Policy"])
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")

    def test_name_bound_to_one_browser(self):
        body = {"table": "sec", "name": "Chris", "text": "hi"}
        self.assertEqual(self.req("/api/chat", body, {"X-Player-Token": "a"})[0], 200)
        code, _, out = self.req("/api/chat", body, {"X-Player-Token": "b"})
        self.assertEqual(code, 409)
        self.assertIn(b"already using", out)
        self.assertEqual(self.req("/api/chat", body)[0], 400)          # no token
        self.assertEqual(self.req("/api/chat", dict(body, name="Dana"),
                                  {"X-Player-Token": "b"})[0], 200)

    def test_bad_bodies_rejected(self):
        r = urllib.request.Request(self.base + "/api/chat", b"[1,2]",
                                   {"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(r)
        self.assertEqual(cm.exception.code, 400)

    def test_password_and_lockout(self):
        old = os.environ.get("TABLE_PASSWORD")
        os.environ["TABLE_PASSWORD"] = "sesame"
        web.FAILS.clear()
        try:
            ok = self.req("/api/chat", {"table": "sec", "name": "Eve", "text": "x"},
                          {"X-Password": "sesame", "X-Player-Token": "e"})
            self.assertEqual(ok[0], 200)
            for _ in range(web.FAIL_LIMIT):
                self.assertEqual(self.req("/api/chat", {"table": "sec"},
                                          {"X-Password": "nope"})[0], 403)
            # locked out now, even with the right password
            self.assertEqual(self.req("/api/chat", {"table": "sec", "name": "Eve"},
                                      {"X-Password": "sesame", "X-Player-Token": "e"})[0], 429)
        finally:
            web.FAILS.clear()
            if old is None:
                os.environ.pop("TABLE_PASSWORD", None)
            else:
                os.environ["TABLE_PASSWORD"] = old

    def test_table_limit(self):
        old = web.MAX_TABLES
        web.MAX_TABLES = len(web.TABLES)
        try:
            code, _, _ = self.req("/api/chat", {"table": "brand-new-table", "name": "Z"},
                                  {"X-Player-Token": "z"})
            self.assertEqual(code, 503)
        finally:
            web.MAX_TABLES = old

    def test_party_mode_turns_off_autopilot(self):
        t = TestAway().bare_table()
        t.afk_mode = "party"
        t.set_afk("Bob", True)
        t.inputs.append(("3", "Alice"))
        self.assertEqual(t.wait_input("Bob", lambda: "1"), ("3", "Alice"))


if __name__ == "__main__":
    unittest.main()
