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
