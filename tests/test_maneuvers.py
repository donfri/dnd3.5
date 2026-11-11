"""Round 3: combat maneuvers, reach, ready/delay, companions and familiars."""
import unittest

from dnd35 import dice
from dnd35.character import Character
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.effects import Effect
from dnd35.monster import Monster
from dnd35.ui import AutoUI


def setup(*monsters, hero="thorgar", level=5):
    ui = AutoUI()
    p = build_pregen(hero, "a", level=level)
    ms = [Monster(k) for k in monsters]
    cb = Combat(ui, [p], ms)
    cb.order = list(cb.st.values())
    cb.acted = set()
    for x in cb.st.values():
        x.flat = False
    return ui, cb, p, ms


class TestManeuvers(unittest.TestCase):
    def test_reach_gives_attack_of_opportunity(self):
        ui, cb, p, (ogre,) = setup("ogre")
        self.assertTrue(cb.has_reach(ogre))
        cb.close_in(p, ogre)
        self.assertEqual(cb.s(ogre).aoo_used, 1)
        self.assertTrue(cb.is_engaged(p, ogre))

    def test_reach_weapon_for_heroes(self):
        ui, cb, p, (orc,) = setup("orc")
        e = p.add_item("glaive")
        p.equip(e)
        self.assertTrue(cb.has_reach(p))
        cb.close_in(orc, p)
        self.assertEqual(cb.s(p).aoo_used, 1)

    def test_readied_attack_triggers(self):
        ui, cb, p, (orc,) = setup("orc")
        w = cb.best_melee(p)
        cb.s(p).readied = {"w": w}
        cb.close_in(orc, p)
        self.assertIsNone(cb.s(p).readied)
        self.assertTrue(any("readied attack triggers" in t for t in ui.transcript))

    def test_bull_rush_breaks_engagement(self):
        for seed in range(30):
            dice.seed(seed)
            ui, cb, p, (gob,) = setup("goblin")
            cb.engage(p, gob)
            cb.act_bull_rush(cb.s(p))
            if not cb.is_engaged(p, gob):
                return
        self.fail("a strong dwarf never bull-rushed a goblin")

    def test_trip_and_counter(self):
        prone = 0
        for seed in range(30):
            dice.seed(seed)
            ui, cb, p, (orc,) = setup("orc")
            cb.engage(p, orc)
            cb.act_trip(cb.s(p))
            prone += orc.has_tag("prone")
        self.assertGreater(prone, 0)

    def test_grapple_lifecycle(self):
        ui, cb, p, (orc,) = setup("orc")
        cb.engage(p, orc)
        p.add_effect(Effect("Grappling", None, tags=["grappled"], data={"with": orc.uid}))
        orc.add_effect(Effect("Grappling", None, tags=["grappled"], data={"with": p.uid}))
        self.assertIs(cb.grapple_partner(p), orc)
        orc.damage = 1000
        orc.check_death()
        cb.after_damage(orc)
        self.assertFalse(p.has_tag("grappled"))

    def test_disarm_monster(self):
        for seed in range(40):
            dice.seed(seed)
            ui, cb, p, (orc,) = setup("orc", level=8)
            p.feats.append("Improved Disarm")
            cb.engage(p, orc)
            cb.act_disarm(cb.s(p))
            if orc.get_effect("Disarmed"):
                self.assertFalse(any(not w["ranged"] for w in orc.weapon_infos()))
                return
        self.fail("never disarmed")

    def test_five_foot_step_and_delay(self):
        ui, cb, p, (orc,) = setup("orc")
        cb.engage(p, orc)
        x = cb.s(p)
        cb.act_step(x)
        self.assertFalse(cb.is_engaged(p, orc))
        self.assertEqual(cb.s(orc).aoo_used, 0)
        self.assertTrue(x.std)
        x2 = cb.s(orc)
        cb.order = [x, x2]
        cb.acted = {id(x)}
        ui2 = AutoUI()
        cb.ui = ui2
        x.std = x.move = True
        cb.act_delay(x, [x2])
        self.assertEqual(cb.order, [x2, x])
        self.assertTrue(x.delayed)


class TestCompanions(unittest.TestCase):
    def test_druid_companion_fights_and_persists(self):
        d = build_pregen("moss", level=6)
        self.assertIsNotNone(d.companion)
        comp = d.companion_creature()
        self.assertGreater(comp.hit_dice(), 2)
        self.assertTrue(comp.has_evasion())
        cb = Combat(AutoUI(), [d], [Monster("orc")])
        self.assertIn(comp.uid, cb.st)
        self.assertIn(comp, cb.allies(d))
        comp.damage = 3
        d2 = Character.from_dict(d.to_dict())
        self.assertEqual(d2.companion_creature().damage, 3)

    def test_ranger_companion_at_four(self):
        self.assertIsNone(build_pregen("faelin", level=3).companion)
        self.assertIsNotNone(build_pregen("faelin", level=4).companion)

    def test_familiar_bonuses(self):
        s = build_pregen("sable", level=1)
        self.assertEqual(s.familiar["kind"], "toad")
        self.assertIn("Alertness", s.feat_list())
        hp = s.max_hp()
        s.familiar = None
        self.assertEqual(s.max_hp(), hp - 3)

    def test_companion_fights(self):
        for seed in range(15):
            dice.seed(seed)
            d = build_pregen("moss", "a", level=1 + seed % 8)
            f = build_pregen("jin", "b", level=1 + seed % 8)
            res = Combat(AutoUI(seed=seed), [d, f], [Monster("gnoll"), Monster("wolf")]).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


if __name__ == "__main__":
    unittest.main()
