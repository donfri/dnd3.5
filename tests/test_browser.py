"""Real-browser checks (run in CI; skipped where Playwright isn't installed)."""
import os
import threading
import unittest
from http.server import ThreadingHTTPServer

from dnd35 import web

try:
    from playwright.sync_api import sync_playwright
except ImportError:      # pragma: no cover
    sync_playwright = None

EVIL = '<img src=x onerror="window.__pwned=1">'


@unittest.skipUnless(sync_playwright and os.environ.get("DND35_BROWSER_TESTS"),
                     "set DND35_BROWSER_TESTS=1 with Playwright installed")
class TestBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.srv.shutdown()

    def page(self, table, name, phone=False):
        ctx = self.browser.new_context(viewport={"width": 390 if phone else 1200,
                                                 "height": 780})
        pg = ctx.new_page()
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.goto(f"{self.base}/?table={table}")
        pg.fill("#jname", name)
        pg.click("#join button")
        pg.wait_for_timeout(900)
        return pg

    def begin(self, pg):
        pg.click('#opts button:has-text("Quick start")')
        pg.wait_for_timeout(700)
        pg.locator("#opts button").first.click()
        pg.wait_for_timeout(1200)

    def open_sheet(self, pg):
        pg.evaluate("showTab('party')")
        pg.wait_for_timeout(1200)
        pg.click('#party button:has-text("Character sheet")')
        pg.wait_for_timeout(400)

    def start_fight(self, pg):
        want = ["Quick start", "Ember King", "Follow the Old Mill", "Continue east"]
        for _ in range(40):
            if "what do you do" in pg.locator("#prompt").inner_text() and \
                    pg.locator(".bmap").count():
                return
            texts = pg.locator("#opts button").all_inner_texts()
            if not texts:
                pg.wait_for_timeout(400)
                continue
            idx = next((i for w in want for i, t in enumerate(texts) if w in t), 0)
            pg.locator("#opts button").nth(idx).click()
            pg.wait_for_timeout(450)
        self.fail("never reached a fight")

    def test_hostile_text_is_never_run(self):
        pg = self.page("bx1", EVIL)
        pg.evaluate("t=>{document.getElementById('chatin').value=t;sendChat()}", EVIL)
        self.begin(pg)
        for tab in ("party", "map", "journal", "dice", "chat", "full", "story"):
            pg.evaluate("t=>showTab(t)", tab)
            pg.wait_for_timeout(250)
        self.open_sheet(pg)
        self.assertIsNone(pg.evaluate("window.__pwned||null"))
        self.assertEqual(pg.locator("img[src=x]").count(), 0)
        self.assertEqual(pg.errors, [])

    def test_fight_on_a_phone(self):
        pg = self.page("bx2", "Chris", phone=True)
        self.start_fight(pg)
        self.assertTrue(pg.locator("#curtab").is_visible())
        self.assertGreater(pg.locator(".bmap svg circle").count(), 1)
        box = pg.locator("#bottom").bounding_box()
        self.assertLess(box["height"], 780 * 0.5)
        self.assertEqual(pg.errors, [])

    def test_sheet_opens_and_closes(self):
        pg = self.page("bx3", "Chris", phone=True)
        self.begin(pg)
        self.open_sheet(pg)
        self.assertTrue(pg.locator("#modal .top button:has-text('Close')").is_visible())
        pg.go_back()
        pg.wait_for_timeout(300)
        self.assertEqual(pg.locator("#modal").evaluate("e=>e.style.display"), "none")


if __name__ == "__main__":
    unittest.main()
