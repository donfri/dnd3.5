"""Walk the Thornwood Fen from start to finish (fights auto-won) to check the
adventure's flags, exits and scripts fit together."""
import tempfile
import unittest
from unittest import mock

from dnd35 import dice
from dnd35.adventure import engine, thornwood_fen as fen
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.monster import Monster
from dnd35.ui import AutoUI


def auto_win(self):
    for m in self.monsters:
        m.dead = True
        self.xp_monsters.append(m)
    return "victory"


class Walker(AutoUI):
    def confirm(self, prompt, default=True):
        self._tick()
        return default

    def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
        self._tick()
        return default if default is not None else 0


class TestThornwoodFen(unittest.TestCase):
    def setUp(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        dice.seed(3)
        self.party = [build_pregen("thorgar", "a", level=7), build_pregen("lyra", "b", level=7)]
        self.ui = Walker()
        self.gs = engine.GameState(fen, self.party, {"heroic": True})
        self.gm = engine.GM(self.ui, self.gs)
        self.gm.enter(fen.START)

    def feature(self, fid):
        f = next(f for f in self.gm.features() if f["id"] == fid)
        self.gm.do_feature(f)

    def go(self, ex_id):
        ex = dict(self.gm.exits())[ex_id]
        self.gm.try_exit(ex_id, ex)

    @mock.patch.object(Combat, "run", auto_win)
    def test_full_walkthrough(self):
        gs = self.gs
        self.feature("warden")
        self.assertIn("quest", gs.flags)
        for p in self.party:
            p.cp += 1000 * 100
        self.go("east")
        self.assertEqual(gs.room, "fen_road")
        self.go("east")
        self.assertEqual(gs.room, "causeway")
        self.feature("toll")
        self.assertTrue(self.gm.enc_done("bridge"))
        self.go("east")
        self.assertEqual(gs.room, "lizard_village")
        self.gm.run([{"do": "custom", "fn": "free_lizards"}])
        self.assertIn("lizards_free", gs.flags)
        self.go("south")
        self.assertEqual(gs.room, "barrow_isle")
        self.feature("tomb")
        self.assertTrue(any(p.has_item("ring of protection +2") for p in self.party))
        self.go("north")
        self.go("boat")
        self.assertEqual(gs.room, "undercroft")
        self.gm.run([{"do": "custom", "fn": "free_children"}])
        self.assertIn("children_free", gs.flags)
        self.go("nave")
        self.assertEqual(gs.room, "nave")
        self.feature("fight")
        self.feature("hoard")
        self.assertIn("thorn_dead", gs.flags)
        self.go("down")
        self.go("water")
        self.go("west")
        self.go("west")
        self.go("west")
        self.assertEqual(gs.room, "marrowmere")
        with self.assertRaises(engine.GameOver):
            self.feature("victory")

    def test_freeing_lizardfolk_thins_the_boss_fight(self):
        self.gm.run([{"do": "custom", "fn": "free_lizards"}])
        mons = self.gm.build_monsters("thorn")
        self.assertEqual([m.key for m in mons], ["green hag"])


class TestFenMonsters(unittest.TestCase):
    def test_troll_regenerates_unless_burned(self):
        t = Monster("troll", roll_hp=False)
        t.take_damage(70, "S")
        self.assertFalse(t.dead)
        self.assertTrue(t.helpless())
        t.regenerate()
        t.regenerate()
        self.assertTrue(t.hp > 0 or t.get_effect("Regenerating"))
        t.take_damage(200, "fire", magic=True)
        self.assertTrue(t.dead)

    def test_gargoyle_needs_magic(self):
        g = Monster("gargoyle", roll_hp=False)
        self.assertEqual(g.take_damage(8, "S")[0], 0)
        self.assertEqual(g.take_damage(12, "S*")[0], 12)

    def test_wight_drains(self):
        dice.seed(1)
        ui = AutoUI()
        p = build_pregen("thorgar", level=6)
        hp = p.max_hp()
        from dnd35.magic import drain_level
        drain_level(ui, p, 14)
        self.assertEqual(p.max_hp(), hp - 5)
        self.assertEqual(p.negative_levels(), 1)


if __name__ == "__main__":
    unittest.main()
