import json
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
            with urllib.request.urlopen(f"{base}/api/poll?table=test&since={since}&name={name}"
                                        ) as r:
                return json.load(r)

        def post(path, body):
            req = urllib.request.Request(base + path, json.dumps(body).encode(),
                                         {"Content-Type": "application/json"})
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


if __name__ == "__main__":
    unittest.main()


class TestOwnership(unittest.TestCase):
    def test_only_owner_answers_when_present(self):
        t = web.Table.__new__(web.Table)  # no game thread needed
        t.presence = {"Alice": time.time(), "Bob": time.time()}
        t.owner = "Bob"
        t.waiting = True
        t.inputs = []
        t.cond = threading.Condition()
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
