"""Round A: wands, staffs, rods, metamagic, spell resistance, dispel magic, summoning."""
import unittest

from dnd35 import dice
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.data.items import charges_left, item_name
from dnd35.magic import (_sroll, cast_spell, device_cast, dispel, metamagic_choices,
                         pay_metamagic, resists)
from dnd35 import magic
from dnd35.monster import Monster
from dnd35.ui import AutoUI


class TestDevices(unittest.TestCase):
    def test_wand_charges(self):
        c = build_pregen("aldric", level=3)
        e = c.add_item("wand of cure light wounds")
        self.assertEqual(charges_left(e), 50)
        c.damage = 10
        device_cast(AutoUI(), c, e, "Cure Light Wounds", [c])
        self.assertEqual(charges_left(e), 49)
        self.assertIn("49 charges", item_name(e))
        e["charges"] = 1
        device_cast(AutoUI(), c, e, "Cure Light Wounds", [c])
        self.assertNotIn(e, c.inventory)

    def test_wands_dont_merge(self):
        c = build_pregen("aldric", level=3)
        a = c.add_item("wand of magic missile")
        c.add_item("wand of magic missile")
        a["charges"] = 10
        c._merge_stacks()
        self.assertEqual(len([e for e in c.inventory if e["id"] == "wand of magic missile"]), 2)

    def test_staff_uses_higher_caster_level(self):
        w = build_pregen("lyra", level=10)
        e = w.add_item("staff of fire")
        dice.seed(1)
        ui = AutoUI()
        orc = Monster("orc")
        device_cast(ui, w, e, "Fireball", [orc])
        self.assertTrue(any("10d6" in t for t in ui.transcript))


class TestMetamagic(unittest.TestCase):
    def test_maximize_and_empower(self):
        magic._META = {"Maximize Spell"}
        self.assertEqual(_sroll("5d6").total, 30)
        magic._META = {"Empower Spell"}
        dice.seed(3)
        r = _sroll("4d6")
        dice.seed(3)
        self.assertEqual(r.total, dice.roll("4d6").total * 3 // 2)
        magic._META = set()

    def test_metamagic_uses_higher_slot(self):
        w = build_pregen("lyra", level=7)
        w.feats.append("Extend Spell")
        cast = next(c for c in w.available_casts() if c["level"] == 1)
        opts = metamagic_choices(w, cast)
        self.assertTrue(any(o[1] == "Extend Spell" for o in opts))
        free2 = sum(1 for s in w.prepared["wizard"][2] if not s["used"])
        pay_metamagic(w, cast, {"feats": {"Extend Spell"}, "adj": 1, "rod": None})
        self.assertEqual(sum(1 for s in w.prepared["wizard"][2] if not s["used"]), free2 - 1)

    def test_extend_doubles_duration(self):
        w = build_pregen("lyra", level=5)
        cast_spell(AutoUI(), w, "Mage Armor", [w], 5, 11, meta={"Extend Spell"})
        self.assertEqual(w.get_effect("Mage Armor").duration, 2 * 600 * 5)

    def test_rod(self):
        s = build_pregen("sable", level=5)
        s.add_item("lesser rod of empower spell")
        cast = next(c for c in s.available_casts() if c["level"] == 1)
        rods = [o for o in metamagic_choices(s, cast) if o[3] is not None]
        self.assertTrue(rods)
        for _ in range(3):
            pay_metamagic(s, cast, {"feats": {"Empower Spell"}, "adj": 0, "rod": rods[0][3]})
        self.assertFalse([o for o in metamagic_choices(s, cast) if o[3] is not None])


class TestSRDispelSummon(unittest.TestCase):
    def test_hag_resists_sometimes(self):
        w = build_pregen("lyra", level=5)
        hag = Monster("green hag")
        res = []
        for seed in range(40):
            dice.seed(seed)
            res.append(resists(AutoUI(), w, hag, 5))
        self.assertTrue(any(res) and not all(res))

    def test_dispel_removes_enemy_buff(self):
        w = build_pregen("lyra", level=9)
        orc = Monster("orc")
        cast_spell(AutoUI(), w, "Bull's Strength", [orc], 1, 12)   # pretend it's theirs
        for seed in range(20):
            dice.seed(seed)
            dispel(AutoUI(), w, orc, 10, [w])
            if not orc.get_effect("Bull's Strength"):
                return
        self.fail("never dispelled")

    def test_summon_joins_fight(self):
        d = build_pregen("moss", level=5)
        orc = Monster("orc")
        cb = Combat(AutoUI(), [d], [orc])
        cast_spell(AutoUI(), d, "Summon Nature's Ally II", [d], 5, 12, cb)
        summons = [c for c in cb.companions if getattr(c, "summoned", False)]
        self.assertEqual(len(summons), 1)
        self.assertIn(summons[0], cb.allies(d))

    def test_druid_spontaneous_summon(self):
        d = build_pregen("moss", level=3)
        self.assertTrue(any(c["spell"].startswith("Summon Nature's Ally")
                            for c in d.available_casts()))

    def test_fights_with_new_magic(self):
        for seed in range(20):
            dice.seed(seed)
            w = build_pregen(["lyra", "moss", "sable", "aldric"][seed % 4], "a", level=9)
            w.feats += ["Quicken Spell", "Empower Spell", "Extend Spell", "Maximize Spell"]
            w.add_item("wand of fireball")
            w.add_item("staff of healing")
            f = build_pregen("thorgar", "b", level=9)
            res = Combat(AutoUI(seed=seed), [w, f],
                         [Monster("green hag"), Monster("troll")]).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


if __name__ == "__main__":
    unittest.main()
