"""Round E: levels 11-20, 6th-9th level spells, prestige classes, elemental shapes."""
import unittest

from dnd35 import dice
from dnd35.abilities import wild_shape
from dnd35.character import Character
from dnd35.combat import Combat
from dnd35.creation import PREGENS, build_pregen
from dnd35.data.classes import PRESTIGE
from dnd35.levelup import gain_level, prestige_eligible
from dnd35.monster import Monster
from dnd35.sheet import render, sheet_data
from dnd35.ui import AutoUI, ScriptedUI


class TestHighLevels(unittest.TestCase):
    def test_pregens_to_twenty(self):
        for key in PREGENS:
            ch = build_pregen(key, level=20)
            self.assertEqual(ch.level, 20)
            render(ch)
            sheet_data(ch)
        self.assertEqual(max(build_pregen("lyra", level=20).spells_per_day("wizard")), 9)
        self.assertEqual(max(build_pregen("wren", level=20).spells_per_day("bard")), 6)
        from dnd35.data.classes import CLASSES
        self.assertEqual(len(CLASSES["paladin"]["spells_per_day"][20]) - 1, 4)

    def test_class_features_scale(self):
        k = build_pregen("kesh", level=20)
        self.assertEqual(k.rage_per_day(), 6)
        self.assertEqual(k.dr(), [(5, "-")])
        m = build_pregen("jin", level=20)
        self.assertEqual(m.weapon_infos()[0]["damage"], "2d10")
        self.assertIn((10, "magic"), m.dr())
        self.assertGreater(m.spell_resistance(), 20)
        self.assertIn("poison", m.immunities())
        p = build_pregen("pip", level=19)
        self.assertEqual(p.sneak_attack_dice(), 10)
        self.assertEqual(len(p.rogue_specials), 4)
        self.assertTrue(p.has_improved_evasion())

    def test_elemental_wild_shape(self):
        d = build_pregen("moss", level=16)
        d.daily["wild_shape"] = 99
        self.assertTrue(wild_shape(ScriptedUI(["1"]), d))
        self.assertEqual(d.wild_form()["type"], "elemental")
        self.assertIn("poison", d.immunities())

    def test_epic_fights(self):
        keys = list(PREGENS)
        foes = [["juvenile white dragon", "ogre mage"], ["troll", "troll", "wraith"],
                ["large earth elemental", "large fire elemental"], ["mummy", "mummy"]]
        for seed in range(16):
            dice.seed(seed)
            party = [build_pregen(keys[seed % len(keys)], "a", level=15 + seed % 6),
                     build_pregen(keys[(seed + 5) % len(keys)], "b", level=15 + seed % 6)]
            res = Combat(AutoUI(seed=seed), party, [Monster(k) for k in foes[seed % 4]]).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


def build(race, plan, ab=None, **kw):
    ch = Character("Hero", race)
    ch.alignment = kw.get("alignment", "Neutral Good")
    ch.base_abilities = ab or {"str": 14, "dex": 16, "con": 14, "int": 16, "wis": 12, "cha": 10}
    for cls, n in plan:
        for _ in range(n):
            gain_level(ch, cls, None, auto=True)
    return ch


class TestPrestige(unittest.TestCase):
    def test_eldritch_knight_advances_wizard(self):
        ch = build("human", [("fighter", 1), ("wizard", 5)])
        self.assertTrue(prestige_eligible(ch, "eldritch knight"))
        cl = ch.caster_level("wizard")
        for _ in range(3):
            gain_level(ch, "eldritch knight", None, auto=True)
        self.assertEqual(ch.caster_level("wizard"), cl + 2)
        self.assertEqual(ch.prestige_target["eldritch knight:arcane"], "wizard")

    def test_mystic_theurge(self):
        ch = build("human", [("wizard", 3), ("cleric", 3)])
        ch.skill_ranks["Knowledge (arcana)"] = 6
        ch.skill_ranks["Knowledge (religion)"] = 6
        self.assertTrue(prestige_eligible(ch, "mystic theurge"))
        w, c = ch.caster_level("wizard"), ch.caster_level("cleric")
        gain_level(ch, "mystic theurge", None, auto=True)
        self.assertEqual((ch.caster_level("wizard"), ch.caster_level("cleric")), (w + 1, c + 1))

    def test_other_prestige_classes(self):
        dd = build("dwarf", [("fighter", 8)], alignment="Lawful Good")
        dd.feats += ["Dodge", "Endurance", "Toughness"]
        self.assertTrue(prestige_eligible(dd, "dwarven defender"))
        ac = dd.ac()
        for _ in range(6):
            gain_level(dd, "dwarven defender", None, auto=True)
        self.assertGreater(dd.ac(), ac)
        self.assertEqual(dd.uses_total("stance"), 3)
        self.assertIn((3, "-"), dd.dr())
        aa = build("elf", [("fighter", 4), ("wizard", 2)])
        aa.feats += ["Point Blank Shot", "Precise Shot", "Weapon Focus (longbow)"]
        aa.class_levels = ["fighter"] * 6 + ["wizard"] * 2
        for _ in range(9):
            gain_level(aa, "arcane archer", None, auto=True)
        bow = {"bow": True, "enhancement": 0}
        self.assertEqual(aa.weapon_enhancement(bow), 5)
        sin = build("human", [("rogue", 5)], alignment="Neutral Evil")
        sin.skill_ranks.update({"Disguise": 4, "Hide": 8, "Move Silently": 8})
        self.assertTrue(prestige_eligible(sin, "assassin"))
        gain_level(sin, "assassin", None, auto=True)
        self.assertEqual(sin.sneak_attack_dice(), 4)
        for cls in PRESTIGE:
            self.assertIn("requires", PRESTIGE[cls])

    def test_prestige_classes_fight(self):
        for seed, (race, plan, extra) in enumerate([
                ("dwarf", [("fighter", 8), ("dwarven defender", 4)], ["Dodge", "Endurance",
                                                                       "Toughness"]),
                ("human", [("fighter", 1), ("wizard", 5), ("eldritch knight", 5)], []),
                ("elf", [("fighter", 6), ("wizard", 1), ("arcane archer", 5)], []),
                ("human", [("rogue", 6), ("assassin", 5)], [])]):
            dice.seed(seed)
            ch = build(race, plan, alignment="Lawful Good" if race == "dwarf" else
                       "Neutral Evil" if plan[-1][0] == "assassin" else "Neutral Good")
            ch.feats += extra
            from dnd35.creation import apply_kit
            apply_kit(ch, plan[0][0])
            buddy = build_pregen("aldric", "b", level=ch.level)
            for s in range(6):
                res = Combat(AutoUI(seed=s), [ch, buddy], [Monster("troll"),
                                                          Monster("ogre")]).run()
                self.assertIn(res, ("victory", "defeat", "fled"))
                ch.damage = buddy.damage = 0
                ch.dead = buddy.dead = False
                ch.effects, buddy.effects = [], []
                ch.daily = {}


if __name__ == "__main__":
    unittest.main()
