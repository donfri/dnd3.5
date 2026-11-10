import unittest

from dnd35 import dice, rules
from dnd35.creation import build_pregen
from dnd35.monster import Monster


class TestDice(unittest.TestCase):
    def test_parse_and_bounds(self):
        dice.seed(1)
        for _ in range(200):
            r = dice.roll("2d6+3")
            self.assertTrue(5 <= r.total <= 15)
        self.assertEqual(dice.roll("4").total, 4)
        self.assertEqual(dice.average("1d8+2"), 6.5)
        self.assertEqual(dice.maximum("2d4+1"), 9)

    def test_crit_multiplier(self):
        dice.seed(2)
        for _ in range(100):
            r = dice.roll("1d4+1", multiplier=3)
            self.assertTrue(6 <= r.total <= 15)

    def test_bad_expression(self):
        with self.assertRaises(ValueError):
            dice.parse("2x6")


class TestRules(unittest.TestCase):
    def test_ability_mod(self):
        self.assertEqual(rules.ability_mod(10), 0)
        self.assertEqual(rules.ability_mod(11), 0)
        self.assertEqual(rules.ability_mod(9), -1)
        self.assertEqual(rules.ability_mod(18), 4)

    def test_progressions(self):
        self.assertEqual(rules.bab_for("good", 5), 5)
        self.assertEqual(rules.bab_for("average", 4), 3)
        self.assertEqual(rules.bab_for("poor", 5), 2)
        self.assertEqual(rules.base_save_for(True, 1), 2)
        self.assertEqual(rules.base_save_for(False, 3), 1)
        self.assertEqual(rules.iterative_attacks(11), [11, 6, 1])

    def test_xp(self):
        self.assertEqual(rules.xp_for_level(2), 1000)
        self.assertEqual(rules.xp_for_level(3), 3000)
        self.assertEqual(rules.xp_award(1, 1), 300)
        self.assertEqual(rules.xp_award(1, 4), 1350)
        self.assertEqual(rules.xp_award(5, 5), 1500)
        self.assertEqual(rules.xp_award(1, 1 / 3), 100)

    def test_stacking(self):
        self.assertEqual(rules.stack_bonuses([("morale", 1), ("morale", 2)]), 2)
        self.assertEqual(rules.stack_bonuses([("dodge", 1), ("dodge", 1)]), 2)
        self.assertEqual(rules.stack_bonuses([("luck", 1), ("morale", 1), ("luck", -1)]), 1)

    def test_bonus_spells(self):
        self.assertEqual(rules.bonus_spells(3, 1), 1)
        self.assertEqual(rules.bonus_spells(5, 1), 2)
        self.assertEqual(rules.bonus_spells(1, 2), 0)


class TestMonsters(unittest.TestCase):
    """Derived numbers should match the Monster Manual."""

    def check(self, key, ac, attack, saves):
        m = Monster(key, roll_hp=False)
        self.assertEqual(m.ac(), ac, key)
        w = m.weapon_infos()[0]
        self.assertEqual(sum(v for _, v, _ in m.attack_components(w)), attack, key)
        self.assertEqual((m.save("fort"), m.save("ref"), m.save("will")), saves, key)

    def test_stat_blocks(self):
        self.check("goblin", 15, 2, (3, 1, -1))
        self.check("hobgoblin", 15, 2, (4, 1, -1))
        self.check("bugbear", 17, 5, (2, 4, 1))
        self.check("orc", 13, 4, (3, 0, -2))
        self.check("human skeleton", 15, 1, (0, 1, 2))
        self.check("human zombie", 11, 2, (0, -1, 3))
        self.check("wolf", 14, 3, (5, 5, 1))
        self.check("dire rat", 15, 4, (3, 5, 3))
        self.check("ghoul", 14, 2, (0, 2, 5))

    def test_dr(self):
        m = Monster("human skeleton", roll_hp=False)
        dealt, note = m.take_damage(4, "S")
        self.assertEqual(dealt, 0)
        dealt, _ = m.take_damage(4, "B")
        self.assertEqual(dealt, 4)


class TestCharacters(unittest.TestCase):
    def test_fighter(self):
        dice.seed(3)
        f = build_pregen("thorgar")
        self.assertEqual(f.bab(), 1)
        self.assertEqual(f.ac(), 17)
        self.assertEqual(f.max_hp(), 13)
        self.assertEqual(f.save("fort"), 5)
        w = f.weapon_infos()[0]
        self.assertEqual(w["wid"], "longsword")
        self.assertEqual(sum(v for _, v, _ in f.attack_components(w)), 4)

    def test_small_rogue(self):
        p = build_pregen("pip")
        self.assertEqual(p.size, "small")
        self.assertEqual(p.sneak_attack_dice(), 1)
        rapier = p.weapon_infos()[0]
        self.assertEqual(rapier["damage"], "1d4")
        self.assertEqual(p.skill_total("Hide"), 2 + 3 + 4)

    def test_cleric_spells(self):
        c = build_pregen("aldric")
        casts = c.available_casts()
        names = {x["spell"] for x in casts}
        self.assertIn("Bless", names)
        self.assertIn("Cure Light Wounds", names)  # domain or spontaneous
        self.assertEqual(c.turn_per_day(), 4)

    def test_levels(self):
        for key in ("thorgar", "lyra", "pip", "aldric", "kesh", "faelin", "sable"):
            ch = build_pregen(key, level=5)
            self.assertEqual(ch.level, 5)
            self.assertGreater(ch.max_hp(), 10)

    def test_roundtrip(self):
        from dnd35.character import Character
        ch = build_pregen("lyra", level=3)
        d = ch.to_dict()
        ch2 = Character.from_dict(d)
        self.assertEqual(ch2.to_dict(), d)
        self.assertEqual(ch2.ac(), ch.ac())
        self.assertEqual(ch2.spells_per_day("wizard"), ch.spells_per_day("wizard"))


if __name__ == "__main__":
    unittest.main()
