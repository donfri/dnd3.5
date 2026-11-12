"""Every hero's combat menu, in every situation, lists each choice once."""
import collections
import unittest

from dnd35 import dice
from dnd35.abilities import wild_shape
from dnd35.combat import Combat
from dnd35.creation import PREGENS, build_pregen
from dnd35.effects import Effect
from dnd35.monster import Monster
from dnd35.ui import AutoUI


class MenuUI(AutoUI):
    def __init__(self):
        super().__init__()
        self.menus = []

    def choose(self, prompt, options, allow_cancel=False, default=None, groups=None):
        if prompt.endswith("what do you do?"):
            self.menus.append(list(options))
            return len(options) - 1          # End turn
        return super().choose(prompt, options, allow_cancel, default, groups)


class TestCombatMenus(unittest.TestCase):
    def test_no_duplicate_choices(self):
        problems = []
        for key in PREGENS:
            for lvl in (1, 12):
                for sit in ("far", "melee", "grapple", "prone", "wild", "ally"):
                    dice.seed(lvl)
                    p = build_pregen(key, "a", level=lvl)
                    party = [p] + ([build_pregen("thorgar", "b", level=lvl)]
                                   if sit == "ally" else [])
                    ui = MenuUI()
                    cb = Combat(ui, party, [Monster("orc"), Monster("goblin")])
                    cb.order, cb.acted = list(cb.st.values()), set()
                    orc = cb.monsters[0]
                    if sit != "far":
                        cb.close_in(p, orc, budget=999)
                    if sit == "ally":
                        cb.close_in(party[1], orc, budget=999)
                    if sit == "grapple":
                        p.add_effect(Effect("Grappling", None, tags=["grappled"],
                                            data={"with": orc.uid}))
                        orc.add_effect(Effect("Grappling", None, tags=["grappled"],
                                              data={"with": p.uid}))
                    if sit == "prone":
                        p.add_effect(Effect("Prone", None, tags=["prone"]))
                    if sit == "wild" and not (p.uses_left("wild_shape") and wild_shape(ui, p)):
                        continue
                    x = cb.s(p)
                    x.flat = False
                    cb._pc_turn(x, False)
                    for menu in ui.menus:
                        names = collections.Counter(o.split(" (")[0] for o in menu)
                        dup = [n for n, k in names.items() if k > 1]
                        if dup:
                            problems.append(f"{key} L{lvl} {sit}: {dup}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
