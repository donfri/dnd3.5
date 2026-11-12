"""Round D: the battle grid (distance, movement, range, areas, flanking, maps)."""
import unittest

from dnd35 import dice, grid
from dnd35.combat import Combat
from dnd35.creation import build_pregen
from dnd35.monster import Monster
from dnd35.ui import AutoUI


def fight(*monsters, heroes=("thorgar",), level=5):
    dice.seed(1)
    party = [build_pregen(h, "a", level=level) for h in heroes]
    ms = [Monster(k) for k in monsters]
    cb = Combat(AutoUI(), party, ms)
    cb.order = list(cb.st.values())
    cb.acted = set()
    for x in cb.st.values():
        x.flat = False
    return cb, party, ms


class TestGeometry(unittest.TestCase):
    def test_diagonals_alternate_5_10(self):
        self.assertEqual(grid.dist((0, 0), (1, 1)), 5)
        self.assertEqual(grid.dist((0, 0), (2, 2)), 15)
        self.assertEqual(grid.dist((0, 0), (3, 3)), 20)
        self.assertEqual(grid.dist((0, 0), (6, 0)), 30)

    def test_burst_cone_line(self):
        burst = grid.area_squares("burst", 10, (0, 0), (6, 4))
        self.assertIn((6, 4), burst)
        self.assertIn((8, 4), burst)
        self.assertNotIn((9, 4), burst)
        cone = grid.area_squares("cone", 15, (2, 4), (6, 4))
        self.assertIn((3, 4), cone)
        self.assertIn((5, 5), cone)
        self.assertNotIn((1, 4), cone)
        self.assertNotIn((6, 4), cone)      # 20 ft away: past a 15-ft cone
        line = grid.area_squares("line", 120, (0, 4), (5, 4))
        self.assertIn((13, 4), line)
        self.assertNotIn((5, 6), line)

    def test_ascii_render(self):
        lines = grid.render({(0, 0): "T "}, [])
        self.assertEqual(len(lines), grid.H + 1)
        self.assertTrue(lines[1].startswith(" 0 T "))


class TestGridCombat(unittest.TestCase):
    def test_starting_positions_are_apart(self):
        cb, (p,), (orc,) = fight("orc")
        self.assertGreaterEqual(cb.distance(p, orc), 30)
        self.assertLess(cb.s(p).pos[0], cb.s(orc).pos[0])

    def test_slow_hero_takes_two_moves(self):
        cb, (p,), (orc,) = fight("orc")
        cb.s(orc).pos = (cb.s(p).pos[0] + 8, cb.s(p).pos[1])   # 40 ft away
        self.assertEqual(cb.speed_of(p), 20)                    # dwarf in armor
        self.assertFalse(cb.close_in(p, orc))
        self.assertTrue(cb.fell_short)
        self.assertFalse(cb.is_engaged(p, orc))
        self.assertEqual(cb.distance(p, orc), 20)
        self.assertTrue(cb.close_in(p, orc))
        self.assertTrue(cb.is_engaged(p, orc))
        self.assertTrue(grid.adjacent(cb.s(p).pos, cb.s(orc).pos))

    def test_charge_covers_double_speed(self):
        cb, (p,), (orc,) = fight("orc")
        cb.s(orc).pos = (cb.s(p).pos[0] + 8, cb.s(p).pos[1])
        x = cb.s(p)
        cb.act_charge(x, orc)
        self.assertTrue(cb.is_engaged(p, orc))
        self.assertFalse(x.std or x.move)

    def test_too_far_to_charge(self):
        cb, (p,), (orc,) = fight("orc")
        cb.s(orc).pos = (cb.s(p).pos[0] + 11, cb.s(p).pos[1])   # 55 ft
        x = cb.s(p)
        cb.act_charge(x, orc)
        self.assertFalse(cb.is_engaged(p, orc))
        self.assertTrue(x.std and x.move)                       # nothing spent

    def test_monster_runs_then_fights(self):
        cb, (p,), (orc,) = fight("orc")
        orc.weapons = [w for w in orc.weapons if "javelin" not in str(w)]
        cb.s(p).pos, cb.s(orc).pos = (0, 0), (13, 8)          # 85 ft: too far to charge
        cb.monster_turn(cb.s(orc), False)
        self.assertFalse(cb.is_engaged(p, orc))
        self.assertLessEqual(cb.distance(p, orc), 30)
        cb.start_of_turn(cb.s(orc))
        cb.monster_turn(cb.s(orc), False)
        self.assertTrue(cb.is_engaged(p, orc))

    def test_range_increments(self):
        cb, (p,), (orc,) = fight("orc", heroes=("lyra",))
        bow = next(w for w in p.weapon_infos() if w["ranged"])
        cb.s(orc).pos = (cb.s(p).pos[0] + 2, cb.s(p).pos[1])
        self.assertEqual(cb.range_penalty(p, orc, bow), (0, False))
        far = dict(bow, range=10)
        cb.s(orc).pos = (cb.s(p).pos[0] + 7, cb.s(p).pos[1])   # 35 ft, 10-ft increment
        self.assertEqual(cb.range_penalty(p, orc, far)[0], -6)

    def test_flanking_needs_opposite_sides(self):
        cb, (a, b), (orc,) = fight("orc", heroes=("thorgar", "aldric"))
        cb.s(orc).pos = (6, 4)
        cb.s(a).pos = (5, 4)
        cb.s(b).pos = (5, 5)
        cb.engage(a, orc)
        cb.engage(b, orc)
        self.assertFalse(cb.flanked(a, orc))
        cb.s(b).pos = (7, 4)
        self.assertTrue(cb.flanked(a, orc))

    def test_second_attacker_steps_round_to_flank(self):
        cb, (a, b), (orc,) = fight("orc", heroes=("thorgar", "aldric"))
        cb.s(orc).pos = (6, 4)
        cb.s(a).pos = (5, 4)
        cb.s(b).pos = (4, 5)
        cb.engage(a, orc)
        cb.close_in(b, orc)
        self.assertTrue(cb.flanked(b, orc))

    def test_fireball_catches_friends_in_the_burst(self):
        cb, (w, f), (o1, o2) = fight("orc", "orc", heroes=("lyra", "thorgar"))
        cb.s(o1).pos, cb.s(o2).pos = (8, 4), (9, 4)
        cb.s(f).pos = (7, 4)
        cb.s(w).pos = (1, 4)
        inside = cb.area_targets(w, "Fireball", o1)
        self.assertIn(f, inside)
        self.assertNotIn(w, inside)
        foes, friends = cb._area_catch(w, "Fireball", o1, 8)
        self.assertEqual(set(foes), {o1, o2})
        self.assertEqual(friends, [f])
        # aiming at the far orc keeps the fighter out of a 20-ft burst? no: 10 ft away
        cb.s(f).pos = (3, 4)
        self.assertEqual(cb._area_catch(w, "Fireball", o2, 8)[1], [])

    def test_selective_area_spares_friends(self):
        cb, (w, f), (o1,) = fight("orc", heroes=("lyra", "thorgar"))
        cb.s(o1).pos, cb.s(f).pos = (8, 4), (7, 4)
        self.assertEqual(cb._area_catch(w, "Slow", o1, 6)[1], [])

    def test_retreat_moves_away(self):
        cb, (p,), (orc,) = fight("orc")
        cb.close_in(p, orc, budget=200)
        before = cb.distance(p, orc)
        cb.act_move_away(cb.s(p))
        self.assertGreater(cb.distance(p, orc), before)
        self.assertFalse(cb.is_engaged(p, orc))

    def test_battle_state_for_web(self):
        cb, party, ms = fight("orc", "goblin", heroes=("thorgar", "lyra"))
        st = cb.battle_state()
        self.assertEqual((st["w"], st["h"]), (grid.W, grid.H))
        labels = {t["name"]: t["label"] for t in st["tokens"]}
        self.assertEqual(labels[party[0].name], "T")
        self.assertEqual({t["side"] for t in st["tokens"]}, {"pc", "foe"})

    def test_full_fights_still_finish(self):
        for seed in range(6):
            dice.seed(seed)
            party = [build_pregen(k, "a", level=3) for k in ("thorgar", "lyra", "pip")]
            res = Combat(AutoUI(seed=seed), party,
                         [Monster("orc"), Monster("goblin"), Monster("wolf")]).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


class TestTerrain(unittest.TestCase):
    def test_difficult_ground_costs_double(self):
        t = grid.Terrain("open", {(1, 0): "rubble"})
        self.assertEqual(t.costs((0, 0))[0][(1, 0)], 10)
        self.assertEqual(t.costs((0, 0))[0][(2, 0)], 15)

    def test_walls_block_and_corners_cant_be_cut(self):
        t = grid.Terrain("dungeon", {(1, 0): "wall", (0, 1): "wall"})
        self.assertNotIn((1, 1), t.costs((0, 0))[0])     # boxed in: no diagonal squeeze
        t = grid.Terrain("dungeon", {(1, y): "wall" for y in range(grid.H - 1)})
        self.assertEqual(t.costs((0, 0))[0][(2, 0)], 90)  # around the end of the wall

    def test_line_of_effect_and_cover(self):
        t = grid.Terrain("dungeon", {(3, 4): "wall", (6, 2): "tree"})
        self.assertFalse(t.line_of_effect((1, 4), (5, 4)))
        self.assertTrue(t.line_of_effect((1, 2), (8, 2)))
        self.assertTrue(t.cover((1, 2), (8, 2)))          # trees give cover, not a wall

    def test_walls_stop_a_fireball(self):
        t = grid.Terrain("dungeon", {(6, y): "wall" for y in range(grid.H)})
        sq = grid.area_squares("burst", 20, (0, 0), (4, 4), t)
        self.assertIn((5, 4), sq)
        self.assertNotIn((7, 4), sq)

    def test_every_theme_is_connected(self):
        for theme in grid.THEME_TEXT:
            for seed in range(15):
                dice.seed(seed)
                t = grid.generate(theme)
                self.assertTrue(t.connected(), (theme, seed))

    def test_room_themes(self):
        self.assertEqual(grid.theme_for({"name": "The Old Stone Bridge"}), "bridge")
        self.assertEqual(grid.theme_for({"name": "The Crypt"}), "dungeon")
        self.assertEqual(grid.theme_for({"name": "X", "desc": "dense, thorny woods"}), "forest")
        self.assertEqual(grid.theme_for({"name": "X", "terrain": "marsh"}), "marsh")

    def test_tokens_start_on_open_ground(self):
        for theme in ("bridge", "cave", "forest", "marsh", "ledge"):
            dice.seed(4)
            party = [build_pregen(k, "a", level=5) for k in ("thorgar", "lyra", "moss")]
            cb = Combat(AutoUI(), party, [Monster("orc") for _ in range(5)], terrain=theme)
            spots = [x.pos for x in cb.st.values()]
            self.assertEqual(len(spots), len(set(spots)))
            self.assertTrue(all(cb.terrain.walkable(q) for q in spots), theme)

    def test_blocked_bridge_means_no_way_through(self):
        cb, (a, b), (o1, o2) = fight("orc", "orc", heroes=("thorgar", "aldric"))
        cb.terrain = grid.Terrain("bridge", {(x, y): "deep" for x in range(grid.W)
                                             for y in range(grid.H) if y != 4})
        cb.s(a).pos, cb.s(b).pos, cb.s(o2).pos, cb.s(o1).pos = (2, 4), (5, 4), (9, 4), (12, 4)
        self.assertEqual(cb.feet_to_melee(o2, a), grid.INF)   # Aldric holds the bridge
        self.assertEqual(cb.feet_to_melee(o1, b), 30)         # allies can pass each other
        cb.close_in(o2, a, budget=60)
        self.assertEqual(cb.s(o2).pos, (6, 4))                # as close as it can get

    def test_rough_ground_stops_a_charge(self):
        cb, (p,), (orc,) = fight("orc")
        cb.terrain = grid.Terrain("forest", {(x, y): "brush" for x in (4, 5, 6)
                                             for y in range(grid.H)})
        cb.s(p).pos, cb.s(orc).pos = (2, 4), (8, 4)
        self.assertFalse(cb.clear_charge(p, orc))
        x = cb.s(p)
        cb.act_charge(x, orc)
        self.assertTrue(x.std and x.move)

    def test_no_clear_shot_through_a_wall(self):
        cb, (p,), (orc,) = fight("orc", heroes=("lyra",))
        cb.terrain = grid.Terrain("dungeon", {(5, y): "wall" for y in range(grid.H)})
        cb.s(p).pos, cb.s(orc).pos = (2, 4), (8, 4)
        self.assertFalse(cb.clear_shot(p, orc))

    def test_terrain_fights_finish(self):
        for i, theme in enumerate(grid.THEME_TEXT):
            dice.seed(i)
            party = [build_pregen(k, "a", level=4) for k in ("thorgar", "lyra", "moss")]
            res = Combat(AutoUI(seed=i), party, [Monster("orc"), Monster("goblin"),
                                                  Monster("wolf")], terrain=theme).run()
            self.assertIn(res, ("victory", "defeat", "fled"))


if __name__ == "__main__":
    unittest.main()
