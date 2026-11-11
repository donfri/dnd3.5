"""Round B: flying, incorporeal, breath, fear auras, spell-like abilities, counterspells,
nonlethal damage, sunder/feint/overrun/aid/coup de grace, exotic weapons."""
import unittest

from dnd35 import dice
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.effects import Effect
from dnd35.monster import Monster
from dnd35.ui import AutoUI


def setup(*monsters, hero="thorgar", level=8):
    ui = AutoUI()
    p = build_pregen(hero, "a", level=level)
    ms = [Monster(k) for k in monsters]
    cb = Combat(ui, [p], ms)
    for x in cb.st.values():   # start at close quarters (10 ft apart)
        if x.side == "mon":
            x.pos = (4, x.pos[1])
    cb.order = list(cb.st.values())
    cb.acted = set()
    for x in cb.st.values():
        x.flat = False
    return ui, cb, p, ms


class TestMonsterPowers(unittest.TestCase):
    def test_incorporeal_needs_magic(self):
        ui, cb, p, (sh,) = setup("shadow")
        w = cb.best_melee(p)
        for seed in range(10):
            dice.seed(seed)
            cb.make_attack(p, sh, w, 20)
        self.assertEqual(sh.damage, 0)
        self.assertTrue(any("passes straight through" in t for t in ui.transcript))
        p.equipped("main")["enhancement"] = 1
        for seed in range(20):
            dice.seed(seed)
            cb.make_attack(p, sh, cb.best_melee(p), 20)
        self.assertGreater(sh.damage, 0)

    def test_shadow_drains_strength(self):
        ui, cb, p, (sh,) = setup("shadow")
        w = sh.melee_attacks()[0]
        for seed in range(20):
            dice.seed(seed)
            cb.make_attack(sh, p, w, 20)
        self.assertGreater(p.ability_damage.get("str", 0), 0)
        self.assertEqual(p.damage, 0)

    def test_flying_foe_out_of_reach(self):
        ui, cb, p, (wy,) = setup("wyvern")
        self.assertTrue(cb.airborne(wy))
        self.assertFalse(cb.reachable(p, wy))
        p.add_effect(Effect("Fly", 10, tags=["flying"]))
        self.assertTrue(cb.reachable(p, wy))

    def test_breath_weapon(self):
        ui, cb, p, (hh,) = setup("hell hound")
        dice.seed(2)
        cb.breathe(hh, hh.block["breath"], [p])
        self.assertTrue(any("cone of fire" in t for t in ui.transcript))

    def test_fear_aura_and_courage(self):
        ui, cb, p, (mu,) = setup("mummy", hero="thorgar")
        cb.start_auras()
        self.assertTrue(any("dread" in t for t in ui.transcript))
        ui2, cb2, pal, (mu2,) = setup("mummy", hero="elowen")
        cb2.start_auras()
        self.assertTrue(any("unafraid" in t for t in ui2.transcript))

    def test_sla_and_counterspell(self):
        ui = AutoUI()
        w = build_pregen("lyra", "a", level=9)
        om = Monster("ogre mage")
        cb = Combat(ui, [w], [om])
        cb.round = 2
        w.skill_ranks["Spellcraft"] = 12
        x = cb.s(w)
        x.readied = {"counter": True, "w": None}
        sla = {"spell": "Sleep", "cl": 9, "dc": 14, "uses": 1}
        countered = False
        for seed in range(30):
            dice.seed(seed)
            x.readied = {"counter": True, "w": None}
            w.reset_spells()
            if cb.try_counterspell(om, sla):
                countered = True
                break
        self.assertTrue(countered)

    def test_nonlethal_knockout(self):
        ui, cb, p, (orc,) = setup("orc")
        p.add_effect(Effect("Subduing", None, hidden=True))
        cb.apply_hit(p, orc, cb.best_melee(p), False, False, 0, False)
        self.assertEqual(orc.damage, 0)
        self.assertGreater(orc.nonlethal, 0)
        orc.nonlethal = 100
        self.assertTrue(orc.helpless())
        self.assertFalse(orc.dead)

    def test_feint_denies_dex(self):
        ui, cb, p, (orc,) = setup("orc", hero="pip")
        cb.engage(p, orc)
        orc.add_effect(Effect("Feinted", 2, data={"by": p.uid}, hidden=True))
        cb.make_attack(p, orc, cb.best_melee(p), p.bab())
        self.assertIsNone(orc.get_effect("Feinted"))

    def test_exotic_proficiency(self):
        d = build_pregen("thorgar", level=1)  # dwarf: waraxe is martial for him
        self.assertTrue(d.is_proficient({"wid": "dwarven waraxe", "category": "exotic"}))
        w = build_pregen("lyra", level=1)
        self.assertFalse(w.is_proficient({"wid": "spiked chain", "category": "exotic"}))
        m = build_pregen("jin", level=1)
        self.assertTrue(m.is_proficient({"wid": "kama", "category": "exotic"}))

    def test_fights_with_new_monsters(self):
        keys = ["thorgar", "lyra", "aldric", "moss", "elowen", "wren", "jin", "pip"]
        foes = [["shadow", "shadow"], ["wraith"], ["mummy"], ["wyvern"], ["ogre mage"],
                ["juvenile white dragon"], ["hell hound", "hell hound"]]
        for seed in range(28):
            dice.seed(seed)
            party = [build_pregen(keys[seed % 8], "a", level=8),
                     build_pregen(keys[(seed + 3) % 8], "b", level=8)]
            party[0].equipped("main") and party[0].equipped("main").update(enhancement=1)
            res = Combat(AutoUI(seed=seed), party,
                         [Monster(k) for k in foes[seed % len(foes)]]).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


if __name__ == "__main__":
    unittest.main()
