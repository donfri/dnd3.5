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


class TestAutosaveAfterFights(unittest.TestCase):
    def test_a_won_fight_is_saved_at_once(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        party = [build_pregen("thorgar"), build_pregen("lyra")]
        gs = engine.GameState(ember_barrow, party, {})
        gs.room = "old_bridge"
        ui = AutoUI()
        ui.autosave_name = "afterfight"
        gm = engine.GM(ui, gs)
        old = engine.Combat.run
        engine.Combat.run = lambda self: "victory"
        try:
            gm.start_encounter("ambush")
        finally:
            engine.Combat.run = old
        saved = engine.load_game("afterfight", ember_barrow)
        self.assertIn("enc:ambush", saved.flags)   # a restart now won't bring them back


class TestTrapCrossing(unittest.TestCase):
    def test_everyone_jumps_once_and_the_party_moves_on(self):
        class UI(AutoUI):
            def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
                for i, o in enumerate(options):
                    if o.startswith("Jump across"):
                        return i
                return super().choose(prompt, options, allow_cancel, default, groups)
        ui = UI()
        party = [build_pregen(k) for k in ("thorgar", "lyra", "pip")]
        for p in party:
            make_heroic(p)
        gs = engine.GameState(ember_barrow, party, {"heroic": True})
        gs.room = "entry"
        gs.rs()["found_traps"].append("pit")
        gm = engine.GM(ui, gs)
        went = []
        gm.enter = went.append
        old = dice.d20
        dice.d20 = lambda: 1            # everyone who has to roll fails
        try:
            gm.try_exit("north", ember_barrow.ROOMS["entry"]["exits"]["north"])
        finally:
            dice.d20 = old
        jumps = [t for t in ui.transcript if " Jump:" in t]
        self.assertEqual(len(jumps), 3)                     # one attempt each, no retries
        self.assertEqual(went, ["guard_room"])              # the party moved on together
        rolled = [p for p in party if any(p.name in t and "d20=1" in t for t in jumps)]
        self.assertTrue(rolled)
        self.assertTrue(all(p.damage > 0 for p in rolled))  # failures sprang the pit
        self.assertTrue(any("Everyone is across" in t for t in ui.transcript))


class TestSafeSaves(unittest.TestCase):
    def test_backup_used_when_save_is_damaged(self):
        engine.SAVE_DIR = tempfile.mkdtemp()
        gs = engine.GameState(ember_barrow, [build_pregen("pip")], {})
        engine.save_game(gs, "s")
        gs.flags.add("later")
        engine.save_game(gs, "s")
        path = os.path.join(engine.SAVE_DIR, "s.json")
        self.assertTrue(os.path.exists(path + ".bak"))
        self.assertFalse(os.path.exists(path + ".tmp"))
        with open(path, "w") as f:
            f.write("{ broken")
        self.assertNotIn("later", engine.load_game("s", ember_barrow).flags)  # the backup
        self.assertEqual(engine.list_saves(), ["s"])


class TestAdventureData(unittest.TestCase):
    def test_all_adventures_valid(self):
        from dnd35.adventure import ORDER
        from dnd35.adventure.engine import GM
        from dnd35.data.items import make_item
        from dnd35.data.skills import SKILLS
        from dnd35.data.monsters import MONSTERS
        known_effects = {"text", "say", "xp", "gold", "item", "items_each", "remove_item",
                         "flag", "unflag", "journal", "damage", "ability_damage", "buff",
                         "heal_all", "fight", "stealth_fight", "resolve_enc", "remove_monster",
                         "add_monster", "reveal_exit", "unlock_exit", "goto", "shop", "rest",
                         "temple", "rumors", "recruit", "riddle", "end_adventure", "custom",
                         "swim", "exposure", "fall", "diplomacy", "paladin_falls"}
        for adv in ORDER:
            for attr in ("ID", "TITLE", "LEVELS", "SUMMARY", "START", "INTRO", "ENDING",
                         "ROOMS", "ENCOUNTERS", "RUMORS", "WANDERING"):
                self.assertTrue(hasattr(adv, attr), (adv.ID, attr))
            self.assertIn(adv.START, adv.ROOMS)

            def check_effects(effs, where):
                for e in effs:
                    self.assertIn(e["do"], known_effects, where)
                    if e["do"] in ("item", "items_each", "remove_item"):
                        make_item(e["id"])
                    if e["do"] in ("fight", "stealth_fight", "resolve_enc", "remove_monster",
                                   "add_monster"):
                        self.assertIn(e["enc"], adv.ENCOUNTERS, where)
                    if e["do"] == "custom":
                        self.assertTrue(callable(getattr(adv, e["fn"], None)), where)
                    if e["do"] in ("riddle", "diplomacy"):
                        check_effects(e["success"] + e["failure"], where)

            for rid, room in adv.ROOMS.items():
                where = f"{adv.ID}:{rid}"
                for ex in room.get("exits", {}).values():
                    self.assertIn(ex["to"], adv.ROOMS, where)
                    if ex.get("trap"):
                        self.assertIn(ex["trap"], room.get("traps", {}), where)
                    if ex.get("blocked_by"):
                        self.assertIn(ex["blocked_by"], adv.ENCOUNTERS, where)
                    if ex.get("lock", {}).get("key"):
                        make_item(ex["lock"]["key"])
                    check_effects(ex.get("effects", []), where)
                for enc in room.get("encounters_enter", []):
                    self.assertIn(enc, adv.ENCOUNTERS, where)
                for f in room.get("features", []) + room.get("secrets", []):
                    chk = f.get("check")
                    if chk and not chk["skill"].startswith("ability:") and \
                            chk["skill"] != "Wild Empathy":
                        sk = chk["skill"]
                        for one in (sk[5:].split("|") if sk.startswith("best:") else [sk]):
                            self.assertIn(one, SKILLS, where)
                    for key in ("effects", "success", "failure", "fail_by_5"):
                        check_effects(f.get(key, []), f"{where}:{f.get('id')}")
                for t in room.get("traps", {}).values():
                    check_effects(t["effects"], where)
                check_effects(room.get("on_enter", []) + room.get("on_first_enter", []), where)
            for enc in adv.ENCOUNTERS.values():
                for m in enc["monsters"] + enc.get("per_extra_hero", []):
                    self.assertIn(m, MONSTERS)
            for w in adv.WANDERING:
                for m in w["monsters"]:
                    self.assertIn(m, MONSTERS)
        self.assertTrue(GM)


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
