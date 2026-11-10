"""End-to-end tests: combat engine, save/load, and randomized play-throughs."""
import os
import tempfile
import unittest

from dnd35 import dice
from dnd35.adventure import ember_barrow, engine
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.game import main_menu, make_heroic, new_game
from dnd35.monster import Monster
from dnd35.ui import AutoUI, QuitGame, ScriptedUI


class TestCombat(unittest.TestCase):
    def test_many_random_fights_finish(self):
        results = {}
        for seed in range(25):
            dice.seed(seed)
            party = [build_pregen("thorgar"), build_pregen("aldric")]
            mons = [Monster("goblin"), Monster("human skeleton")]
            ui = AutoUI(seed, max_inputs=5000)
            try:
                r = Combat(ui, party, mons).run()
            except QuitGame:
                r = "timeout"
            results[r] = results.get(r, 0) + 1
        self.assertNotIn("timeout", results)

    def test_sleep_spell(self):
        dice.seed(4)
        from dnd35.magic import cast_spell
        ui = ScriptedUI([])
        lyra = build_pregen("lyra")
        gobs = [Monster("goblin"), Monster("goblin")]
        cast_spell(ui, lyra, "Sleep", gobs, 1, 100)  # only a natural 20 saves
        self.assertTrue(all(g.has_tag("asleep") for g in gobs))
        skel = Monster("human skeleton")
        cast_spell(ui, lyra, "Sleep", [skel], 1, 30)
        self.assertFalse(skel.has_tag("asleep"))


class TestSaveLoad(unittest.TestCase):
    def test_roundtrip(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        party = [build_pregen("pip"), build_pregen("kesh")]
        for p in party:
            make_heroic(p)
        gs = engine.GameState(ember_barrow, party, {"heroic": True})
        gs.flags.add("quest")
        gs.room = "entry"
        gs.rs()["found_traps"].append("pit")
        engine.save_game(gs, "t")
        gs2 = engine.load_game("t", ember_barrow)
        self.assertEqual(gs2.room, "entry")
        self.assertIn("quest", gs2.flags)
        self.assertEqual(gs2.party[0].to_dict(), party[0].to_dict())
        self.assertIn("t", engine.list_saves())


class TestAdventureData(unittest.TestCase):
    def test_exits_and_encounters_valid(self):
        from dnd35.data.monsters import MONSTERS
        for rid, room in ember_barrow.ROOMS.items():
            for ex in room.get("exits", {}).values():
                self.assertIn(ex["to"], ember_barrow.ROOMS, rid)
            for enc in room.get("encounters_enter", []):
                self.assertIn(enc, ember_barrow.ENCOUNTERS)
        for enc in ember_barrow.ENCOUNTERS.values():
            for m in enc["monsters"] + enc.get("per_extra_hero", []):
                self.assertIn(m, MONSTERS)


class TestFuzz(unittest.TestCase):
    """Random menu choices must never crash the game."""

    def test_random_play(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        for seed in range(int(os.environ.get("FUZZ_GAMES", "6"))):
            dice.seed(seed)
            ui = AutoUI(seed, max_inputs=1500)
            try:
                gs = new_game(ui, quick=seed % 2 == 0)
                engine.GM(ui, gs).loop()
            except (QuitGame, engine.GameOver):
                pass

    def test_main_menu(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        dice.seed(9)
        try:
            main_menu(AutoUI(9, max_inputs=800))
        except QuitGame:
            pass


if __name__ == "__main__":
    unittest.main()
