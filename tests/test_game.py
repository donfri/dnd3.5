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


class TestNoRepeatRewards(unittest.TestCase):
    def test_a_successful_check_feature_is_done(self):
        gs = engine.GameState(ember_barrow, [build_pregen("pip")], {})
        gs.room = "cistern"
        gs.flags.add("enc:rats")
        gm = engine.GM(AutoUI(), gs)
        gm.roll_check = lambda *a, **k: 99
        dive = next(f for f in gm.features() if f["id"] == "dive")
        gm.do_feature(dive)
        self.assertEqual(sum(e["qty"] for e in gs.party[0].inventory
                             if e["id"] == "silver holy symbol"), 1)
        self.assertNotIn("dive", [f["id"] for f in gm.features()])   # can't farm it

    def test_every_rewarding_check_is_one_time(self):
        from dnd35.adventure import ORDER
        for adv in ORDER:
            for rid, room in adv.ROOMS.items():
                for f in room.get("features", []):
                    pays = any(e.get("do") in ("item", "gold", "xp", "items_each")
                               for e in f.get("success", []) + f.get("effects", []))
                    if pays:
                        self.assertTrue(f.get("once", bool(f.get("check"))),
                                        (adv.ID, rid, f["id"]))


class TestTrapCrossing(unittest.TestCase):
    def test_walking_into_an_unseen_trap_still_gets_you_across(self):
        ui = AutoUI()
        party = [build_pregen("thorgar"), build_pregen("pip")]
        gs = engine.GameState(ember_barrow, party, {})
        gs.room = "entry"
        gm = engine.GM(ui, gs)
        went = []
        gm.enter = went.append
        gm.try_exit("north", ember_barrow.ROOMS["entry"]["exits"]["north"])
        self.assertEqual(went, ["guard_room"])
        self.assertTrue(any("far side" in t for t in ui.transcript))

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


class TestCharacterForm(unittest.TestCase):
    def spec(self, **kw):
        d = {"name": "Mira", "race": "dwarf", "cls": "cleric", "alignment": "Neutral Good",
             "method": "array", "build": "auto", "kit": True,
             "scores": {"str": 13, "dex": 10, "con": 14, "int": 8, "wis": 15, "cha": 12}}
        d.update(kw)
        return d

    def test_validation(self):
        from dnd35.creation import check_form
        rolled = [16, 14, 13, 12, 11, 9]
        self.assertIsNone(check_form(self.spec(), rolled))
        self.assertIn("name", check_form(self.spec(name="  "), rolled))
        self.assertIsNotNone(check_form(self.spec(cls="paladin", alignment="Chaotic Evil"),
                                        rolled))
        cheat = dict(self.spec()["scores"], str=18)
        self.assertIn("exactly once", check_form(self.spec(scores=cheat), rolled))
        self.assertIsNotNone(check_form(self.spec(method="roll"), rolled))
        rich = {a: 18 for a in ("str", "dex", "con", "int", "wis", "cha")}
        self.assertIn("25 points", check_form(self.spec(method="buy", scores=rich), rolled))
        self.assertIsNotNone(check_form(self.spec(race="dragon"), rolled))

    def test_form_builds_a_hero(self):
        from dnd35.creation import create_character

        class FormUI(AutoUI):
            def character_form(ui, schema):
                self.assertEqual(len(schema["rolled"]), 6)
                return self.spec()
        ch = create_character(FormUI(), "Chris", start_level=2)
        self.assertEqual((ch.name, ch.race, ch.level, ch.player), ("Mira", "dwarf", 2, "Chris"))
        self.assertEqual(ch.ability("con"), 16)              # 14 + 2 racial
        self.assertTrue(ch.has_item("holy symbol"))


class TestIntelligentItems(unittest.TestCase):
    def test_sword_accepts_or_rejects_its_wielder(self):
        from dnd35.data.items import item_clash, item_data, item_name, make_item
        good = build_pregen("elowen", level=6)               # lawful good paladin
        e = good.add_item(make_item("dawnreed"))
        self.assertEqual((item_name(e), e["enhancement"]), ("Dawnreed", 2))
        self.assertIn("A calm voice", good.equip(e))
        self.assertFalse(item_clash(good.alignment, item_data(e)))
        rogue = build_pregen("pip", level=6)
        rogue.alignment = "Chaotic Evil"
        before = sum(v for _, v, _ in rogue.save_components("will"))
        e2 = rogue.add_item(make_item("dawnreed"))
        self.assertIn("resents", rogue.equip(e2))
        self.assertEqual(sum(v for _, v, _ in rogue.save_components("will")), before - 1)

    def test_once_a_day_gift(self):
        from dnd35.data.items import make_item
        p = build_pregen("elowen", level=6)
        p.equip(p.add_item(make_item("dawnreed")))
        p.damage = 20
        cb = Combat(AutoUI(), [p], [Monster("orc")])
        cb.act_item_power(cb.s(p), p.equipped("main"))
        self.assertLess(p.damage, 20)
        self.assertTrue(p.daily.get("mind:dawnreed"))


class TestCursedItems(unittest.TestCase):
    def test_disguised_until_worn_then_stuck(self):
        from dnd35.data.items import item_name, make_item, stuck
        ch = build_pregen("thorgar")
        ac = ch.ac()
        e = ch.add_item(make_item("bracers of defenselessness"))
        self.assertEqual(item_name(e), "Bracers of armor +2")       # it looks useful
        msg = ch.equip(e)
        self.assertIn("CURSED", msg)
        self.assertEqual(ch.ac(), ac - 5)
        self.assertTrue(stuck(e))
        self.assertFalse(ch.unequip(e))                              # it won't come off
        self.assertIn("cursed", item_name(e).lower())
        good = ch.add_item(make_item("bracers of armor +2"))
        self.assertIn("no room", ch.equip(good))

    def test_found_magic_is_unidentified(self):
        from dnd35.data.items import item_name
        gs = engine.GameState(ember_barrow, [build_pregen("thorgar")], {})
        gm = engine.GM(AutoUI(), gs)
        gm.run([{"do": "item", "id": "gauntlets of fumbling"}])
        e = gs.party[0].find_item("gauntlets of fumbling")
        self.assertTrue(e.get("unidentified"))
        self.assertEqual(item_name(e), "Unidentified gloves")
        self.assertIn("Nobody knows", gs.party[0].equip(e))
        gs.party[0].cp = 100 * 100
        gm.identify_items()
        self.assertTrue(e.get("curse_known"))                        # the sage sees it


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
