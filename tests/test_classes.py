"""Round 2: bard, druid, monk, paladin, levels to 10, 4th-5th level spells."""
import unittest

from dnd35 import dice, rules
from dnd35.abilities import wild_shape
from dnd35.character import Character
from dnd35.combat import Combat
from dnd35.creation import PREGENS, build_pregen
from dnd35.data.classes import CLASSES, alignment_allowed
from dnd35.data.spells import SPELLS, spells_for
from dnd35.effects import Effect
from dnd35.levelup import gain_level
from dnd35.magic import cast_spell
from dnd35.monster import Monster
from dnd35.sheet import render, sheet_data
from dnd35.ui import AutoUI, ScriptedUI


class TestClassTables(unittest.TestCase):
    def test_every_class_to_twenty(self):
        from dnd35.data.classes import CLASS_ORDER
        for cls in CLASS_ORDER:
            ch = Character("T", "human")
            ch.base_abilities = {"str": 14, "dex": 14, "con": 14, "int": 14, "wis": 14,
                                 "cha": 14}
            for _ in range(20):
                gain_level(ch, cls, None, auto=True)
            self.assertEqual(ch.level, 20)
            render(ch)
            sheet_data(ch)
            if CLASSES[cls].get("caster"):
                self.assertTrue(ch.spells_per_day(cls), cls)

    def test_known_spells_exist_for_spontaneous_casters(self):
        for cls in ("bard", "sorcerer"):
            for lvl, row in CLASSES[cls]["spells_known"].items():
                for sl, n in enumerate(row):
                    self.assertGreaterEqual(len(spells_for(cls, sl)), n, (cls, lvl, sl))

    def test_alignment_rules(self):
        self.assertTrue(alignment_allowed("paladin", "Lawful Good"))
        self.assertFalse(alignment_allowed("paladin", "Neutral Good"))
        self.assertFalse(alignment_allowed("monk", "Chaotic Good"))
        self.assertTrue(alignment_allowed("druid", "Neutral Good"))
        self.assertFalse(alignment_allowed("druid", "Chaotic Good"))
        self.assertFalse(alignment_allowed("bard", "Lawful Neutral"))

    def test_pregens_respect_alignment(self):
        for key, p in PREGENS.items():
            self.assertTrue(alignment_allowed(p["cls"], p["alignment"]), key)


class TestNewClassFeatures(unittest.TestCase):
    def test_monk(self):
        m = build_pregen("jin", level=8)
        unarmed = m.weapon_infos()[0]
        self.assertEqual(unarmed["damage"], "1d10")
        self.assertTrue(m.has_evasion())
        self.assertIn("disease", m.immunities())
        self.assertGreater(m.speed(), 30)
        ac_bonus = [c for c in m.ac_components("touch") if c[2] == "monk AC bonus"]
        self.assertTrue(ac_bonus)
        m.add_item("chain shirt")
        m.equip(m.find_item("chain shirt"))
        self.assertFalse([c for c in m.ac_components() if c[2] == "monk AC bonus"])

    def test_paladin(self):
        p = build_pregen("elowen", level=5)
        self.assertIn(("divine_grace", 2, "divine grace"), p.save_components("will"))
        self.assertIn("fear", p.immunities())
        self.assertEqual(p.smite_per_day(), 2)
        self.assertEqual(p.lay_on_hands_pool(), 10)
        self.assertEqual(p.turn_level(), 2)

    def test_bard_light_armor_casting(self):
        b = build_pregen("wren", level=3)
        self.assertEqual(b.arcane_spell_failure("bard"), 0)
        b.add_item("chain shirt")
        b.equip(b.find_item("chain shirt"))
        self.assertEqual(b.arcane_spell_failure("bard"), 0)
        b.add_item("buckler")
        b.equip(b.find_item("buckler"))
        self.assertEqual(b.arcane_spell_failure("bard"), 5)

    def test_druid_wild_shape_and_metal(self):
        d = build_pregen("moss", level=8)
        msg = d.equip(d.add_item("chainmail"))
        self.assertIn("refuses", msg)
        ui = ScriptedUI(["4"])  # brown bear
        self.assertTrue(wild_shape(ui, d))
        self.assertEqual(d.size, "large")
        self.assertEqual(d.ability("str"), 27)
        self.assertTrue(all(w["natural"] for w in d.weapon_infos()))
        self.assertIsNone(d.armor_data())

    def test_barbarian_dr_and_trap_sense(self):
        k = build_pregen("kesh", level=10)
        self.assertEqual(k.dr(), [(2, "-")])
        self.assertEqual(k.trap_sense(), 3)
        dealt, note = k.take_damage(10, "S")
        self.assertEqual(dealt, 8)

    def test_stoneskin_runs_out(self):
        w = build_pregen("lyra", level=9)
        w.add_effect(Effect("Stoneskin", 100, data={"left": 15}))
        dealt, _ = w.take_damage(12, "S")
        self.assertEqual(dealt, 2)
        dealt, _ = w.take_damage(12, "S")
        self.assertEqual(dealt, 7)
        self.assertIsNone(w.get_effect("Stoneskin"))


class TestNewSpells(unittest.TestCase):
    def test_every_spell_resolves(self):
        for n, sp in SPELLS.items():
            dice.seed(5)
            ui = AutoUI()
            c = build_pregen("aldric", level=9)
            f = build_pregen("thorgar", level=9)
            ms = [Monster(k) for k in ("orc", "wolf", "human zombie", "ogre")]
            cb = Combat(ui, [c, f], ms)
            cb.engage(c, ms[0])
            if n == "Raise Dead":
                f.dead = True
            tg = {"enemy": ms[:1], "enemies": ms[:sp["max_targets"]], "ally": [f],
                  "allies": [c, f], "self": [c], "none": [c], "creature": ms[:1],
                  "summon": [c]}[sp["target"]]
            cast_spell(ui, c, n, tg, 9, 17, cb, allies=[c, f], enemies=ms)
            self.assertNotIn("no mechanical effect", "\n".join(ui.transcript), n)

    def test_raise_dead_costs_xp(self):
        f = build_pregen("thorgar", level=5)
        xp = f.xp
        f.dead = True
        ui = AutoUI()
        cast_spell(ui, f, "Raise Dead", [f], 9, 17)
        self.assertFalse(f.dead)
        self.assertLess(f.xp, xp)
        self.assertEqual(f.level, 5)


class TestFights(unittest.TestCase):
    def test_new_classes_fight(self):
        keys = ["wren", "moss", "jin", "elowen"]
        for seed in range(40):
            dice.seed(seed)
            ui = AutoUI(seed=seed)
            lvl = [1, 3, 5, 8, 10][seed % 5]
            party = [build_pregen(keys[seed % 4], "a", level=lvl),
                     build_pregen(keys[(seed + 1) % 4], "b", level=lvl)]
            ms = [Monster(k) for k in ("ogre", "gnoll", "ghoul")[: 1 + seed % 3]]
            self.assertIn(Combat(ui, party, ms).run(), ("victory", "defeat", "fled"))

    def test_max_level(self):
        self.assertEqual(rules.MAX_LEVEL, 20)
        ch = build_pregen("thorgar", level=20)
        ch.xp = 10 ** 7
        self.assertFalse(ch.can_level_up())


if __name__ == "__main__":
    unittest.main()
