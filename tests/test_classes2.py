"""Round C: domains, deities, evil clerics, bardic music, paladin mount/code, familiar
powers, specialist wizards."""
import tempfile
import unittest

from dnd35 import dice
from dnd35.abilities import bardic_music, music_options
from dnd35.adventure import engine, greyfang_pass
from dnd35.character import Character
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.data.classes import DEITIES, domain_allowed
from dnd35.levelup import gain_level
from dnd35.magic import saving_throw
from dnd35.monster import Monster
from dnd35.ui import AutoUI


def cleric(alignment, deity, domains, level=6, energy=None):
    ch = Character("Vex", "human")
    ch.alignment = alignment
    ch.deity = deity
    ch.base_abilities = {"str": 12, "dex": 10, "con": 14, "int": 10, "wis": 16, "cha": 14}
    for _ in range(level):
        gain_level(ch, "cleric", None, auto=True)
    ch.domains = domains
    if energy:
        ch.energy = energy
    from dnd35.levelup import prepare_spells
    prepare_spells(ch, None, auto=True)
    return ch


class TestDomains(unittest.TestCase):
    def test_every_deity_has_two_legal_domains(self):
        for name, d in DEITIES.items():
            self.assertGreaterEqual(
                len([x for x in d["domains"] if domain_allowed(x, d["alignment"])]), 2, name)
        self.assertFalse(domain_allowed("Good", "Neutral Evil"))
        self.assertFalse(domain_allowed("Chaos", "Lawful Good"))

    def test_evil_cleric_inflicts_and_commands(self):
        ch = cleric("Neutral Evil", "Nerull", ["Death", "Trickery"], level=6)
        self.assertEqual(ch.energy, "negative")
        self.assertTrue(any(c["spell"].startswith("Inflict") and c.get("spontaneous")
                            for c in ch.available_casts()))
        sk = Monster("human skeleton")
        cb = Combat(AutoUI(), [ch], [sk, Monster("orc")])
        cb.command_undead(ch, sk)
        self.assertIn(sk, cb.companions)
        self.assertIn(sk, cb.allies(ch))
        self.assertNotIn(sk, cb.monsters)

    def test_domain_powers(self):
        ch = cleric("Neutral Good", "Fharlanghn", ["Luck", "Protection"])
        self.assertEqual(ch.uses_left("good_fortune"), 1)
        self.assertEqual(ch.uses_left("protective_ward"), 1)
        for seed in range(40):
            dice.seed(seed)
            saving_throw(AutoUI(), ch, "fort", 40)
        self.assertEqual(ch.uses_left("good_fortune"), 0)
        k = cleric("True Neutral", "Boccob", ["Knowledge", "Trickery"])
        self.assertTrue(k.is_class_skill("Knowledge (arcana)"))
        self.assertTrue(k.is_class_skill("Hide"))

    def test_magic_domain_uses_arcane_wands(self):
        from dnd35.magic import scroll_usable
        ch = cleric("True Neutral", "Boccob", ["Magic", "Trickery"])
        self.assertEqual(scroll_usable(ch, {"spell": "Fireball", "list": "arcane"}),
                         (True, False))


class TestBardPaladinWizard(unittest.TestCase):
    def test_bardic_music(self):
        b = build_pregen("wren", level=9)
        b.skill_ranks["Perform"] = 12
        kinds = [k for k, _ in music_options(b, True)]
        for k in ("courage", "fascinate", "countersong", "suggestion", "greatness"):
            self.assertIn(k, kinds)
        orc = Monster("orc")
        for seed in range(10):
            dice.seed(seed)
            bardic_music(AutoUI(), b, [b], [orc], "fascinate")
            if orc.get_effect("Fascinated"):
                break
        self.assertFalse(orc.can_act())
        orc.take_damage(1, "S")
        self.assertIsNone(orc.get_effect("Fascinated"))

    def test_paladin_mount_and_fall(self):
        p = build_pregen("elowen", level=6)
        self.assertIsNotNone(p.mount)
        mounts = p.companions_all()
        self.assertTrue(any(m.kind == "heavy warhorse" for m in mounts))
        cb = Combat(AutoUI(), [p], [Monster("orc")])
        self.assertTrue(any(c.kind == "heavy warhorse" for c in cb.companions))
        p.fallen = True
        self.assertEqual(p.smite_per_day(), 0)
        self.assertEqual(p.companions_all(), [])
        self.assertNotIn("fear", p.immunities())
        engine.SAVE_DIR = tempfile.mkdtemp()
        gs = engine.GameState(greyfang_pass, [p], {})
        gm = engine.GM(AutoUI(), gs)
        p.cp = 1000 * 100

        class UI(AutoUI):
            def choose(self, prompt, options, **kw):
                self._tick()
                for i, o in enumerate(options):
                    if "Atonement" in o:
                        return i
                return len(options) - 1
        gm.ui = UI()
        gm.temple_services()
        self.assertFalse(p.fallen)

    def test_specialist_wizard(self):
        w = Character("Ix", "elf")
        w.base_abilities = {"str": 8, "dex": 14, "con": 12, "int": 16, "wis": 10, "cha": 10}
        w.specialty = "evocation"
        w.prohibited = ["enchantment", "illusion"]
        gain_level(w, "wizard", None, auto=True)
        self.assertFalse([s for s in w.spellbook if s in ("Daze",)])
        self.assertEqual(w.spells_per_day("wizard")[1], 1 + 1 + 1)   # base, Int, specialist

    def test_familiar_scouts(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        w = build_pregen("lyra", level=3)
        gs = engine.GameState(greyfang_pass, [w], {})
        gm = engine.GM(AutoUI(), gs)
        gs.room = "gorge"
        gm.familiar_scout()


if __name__ == "__main__":
    unittest.main()
