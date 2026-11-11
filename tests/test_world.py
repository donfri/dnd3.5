"""Round F: light and darkness, hazards, Diplomacy attitudes, haggling, crafting."""
import tempfile
import unittest

from dnd35 import dice
from dnd35.adventure import engine, ember_barrow, greyfang_pass
from dnd35.combat import Combat
from dnd35.crafting import craft, craftable, enchant_menu
from dnd35.creation import build_pregen
from dnd35.effects import Effect
from dnd35.monster import Monster
from dnd35.ui import AutoUI


class Yes(AutoUI):
    def confirm(self, prompt, default=True):
        self._tick()
        return True

    def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
        self._tick()
        return default or 0


def gm_for(adv, party):
    engine.SAVE_DIR = tempfile.mkdtemp()
    gs = engine.GameState(adv, party, {})
    return gs, engine.GM(Yes(), gs)


class TestLight(unittest.TestCase):
    def test_torches_and_darkness(self):
        h = build_pregen("aldric", level=1)   # human: no darkvision
        h.inventory = [e for e in h.inventory if e["id"] != "torch"]
        gs, gm = gm_for(ember_barrow, [h])
        gs.room = "cistern"
        h.prepared = {}
        gm.ensure_light()
        self.assertTrue(gm.in_darkness())
        h.add_item("torch", 2)
        gm.ensure_light()
        self.assertFalse(gm.in_darkness())
        self.assertEqual(h.find_item("torch")["qty"], 1)
        gs.pass_time(61)
        self.assertTrue(gm.in_darkness())

    def test_fighting_blind(self):
        h = build_pregen("aldric", level=3)
        d = build_pregen("thorgar", level=3)   # dwarf: darkvision
        cb = Combat(AutoUI(), [h, d], [Monster("goblin")], dark=True)
        self.assertTrue(h.has_tag("blinded"))
        self.assertFalse(d.has_tag("blinded"))
        cb.finish("victory")
        self.assertFalse(h.has_tag("blinded"))


class TestHazardsAndTalk(unittest.TestCase):
    def test_hazards(self):
        h = build_pregen("thorgar", level=3)
        gs, gm = gm_for(greyfang_pass, [h])
        for seed in range(10):
            dice.seed(seed)
            gm.hazard({"do": "swim", "dc": 30})
        self.assertGreater(h.nonlethal, 0)
        h.nonlethal = 0
        h.add_effect(Effect("Endure Elements", 1000))
        gm.hazard({"do": "exposure", "type": "cold", "dc": 99})
        self.assertEqual(h.nonlethal, 0)
        hp = h.hp
        gm.hazard({"do": "fall", "feet": 60})
        self.assertLess(h.hp, hp)

    def test_diplomacy_shifts_attitude(self):
        b = build_pregen("wren", level=10)
        b.skill_ranks["Diplomacy"] = 13
        gs, gm = gm_for(greyfang_pass, [b])
        done = []
        for day in range(20):
            gs.minutes += 1440
            dice.seed(day)
            gm.diplomacy({"npc": "Gutch", "start": "unfriendly", "goal": "friendly",
                          "success": [{"do": "flag", "name": "won"}], "failure": []}, b)
            if "won" in gs.flags:
                done.append(day)
                break
        self.assertTrue(done)
        self.assertIn(gs.attitudes["Gutch"], ("friendly", "helpful"))


class TestCrafting(unittest.TestCase):
    def test_scribe_and_enchant(self):
        w = build_pregen("lyra", level=9)
        w.cp = 100000 * 100
        w.xp += 5000
        w.feats += ["Craft Magic Arms and Armor", "Craft Wand"]
        items = craftable(w)
        kinds = {why for _, why in items}
        self.assertIn("Scribe Scroll", kinds)
        self.assertIn("Craft Wand", kinds)
        scroll = next(i for i, why in items if why == "Scribe Scroll" and "fireball" in i)
        xp, cp = w.xp, w.cp
        self.assertTrue(craft(Yes(), w, scroll))
        self.assertTrue(w.has_item(scroll))
        self.assertLess(w.xp, xp)
        self.assertLess(w.cp, cp)
        enchant_menu(Yes(), w, 3)
        staff = w.equipped("main")
        self.assertEqual(staff.get("enhancement"), 1)

    def test_cannot_lose_a_level(self):
        w = build_pregen("lyra", level=9)
        w.cp = 10 ** 9
        w.xp = 36000   # exactly the 9th-level minimum
        self.assertFalse(craft(Yes(), w, "scroll of fireball"))


if __name__ == "__main__":
    unittest.main()
