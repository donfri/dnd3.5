"""Class abilities usable in and out of combat: lay on hands, wholeness of body,
wild shape, bardic music."""
from __future__ import annotations

from typing import List

from .data.monsters import MONSTERS, WILD_SHAPES
from .effects import ROUNDS_PER_HOUR, Effect
from .magic import heal


def lay_on_hands(ui, p, tgt) -> None:
    left = p.uses_left("lay_on_hands")
    amt = min(left, tgt.damage)
    if amt <= 0:
        ui.out(f"{tgt.name} isn't hurt.")
        return
    if amt > 1 and ui.choose(f"Heal how much? ({left} hp of healing left today)",
                             [f"All that's needed ({amt})", "Choose an amount"],
                             default=0) == 1:
        amt = ui.ask_int("Hit points to heal", 1, amt, amt)
    p.spend("lay_on_hands", amt)
    ui.out(f"{p.name} lays hands on {tgt.name}; warm golden light flows.", ("byellow",))
    heal(ui, tgt, amt)


def wholeness_of_body(ui, p) -> None:
    amt = min(p.uses_left("wholeness"), p.damage)
    p.spend("wholeness", amt)
    ui.out(f"{p.name} breathes deeply and turns their ki inward.", ("bcyan",))
    heal(ui, p, amt)


def shape_options(p) -> List[str]:
    lvl = p.class_level("druid")
    return [k for k, need in WILD_SHAPES.items() if lvl >= need]


def wild_shape(ui, p) -> bool:
    opts = shape_options(p)
    labels = []
    for k in opts:
        m = MONSTERS[k]
        atk = ", ".join(f"{a['name']} {a['damage']}" for a in m["natural_attacks"])
        ab = m["abilities"]
        labels.append(f"{m['name']} ({m['size']}; Str {ab['str']} Dex {ab['dex']} "
                      f"Con {ab['con']}; natural armor +{m['natural']}; {atk}; "
                      f"speed {m['speed']} ft.)")
    i = ui.choose("Take which form?", labels, allow_cancel=True)
    if i is None:
        return False
    key = opts[i]
    p.spend("wild_shape")
    p.add_effect(Effect("Wild Shape", ROUNDS_PER_HOUR * p.class_level("druid"),
                        tags=["wild_shape"], data={"form": key},
                        source=MONSTERS[key]["name"]))
    ui.out(f"{p.name}'s body twists and grows fur... {p.name} is now a "
           f"{MONSTERS[key]['name'].lower()}!", ("bgreen",))
    if not p.has_feat("Natural Spell"):
        ui.out("  (No spellcasting in animal form without the Natural Spell feat. Armor and "
               "gear meld into the new body.)", ("dim",))
    _shape_heal(ui, p)
    return True


def revert_shape(ui, p) -> None:
    p.remove_effect("Wild Shape")
    ui.out(f"{p.name} returns to their own form.", ("bgreen",))
    _shape_heal(ui, p)


def _shape_heal(ui, p) -> None:
    if p.damage > 0:
        ui.out("  Changing shape knits wounds as if from a night's rest:")
        heal(ui, p, p.level)
    if p.hp > p.max_hp():
        p.damage = 0


def inspire_courage(ui, bard, party) -> None:
    bard.spend("music")
    b = 2 if bard.class_level("bard") >= 8 else 1
    ui.out(f"{bard.name} strikes up a stirring song of courage!", ("bmagenta",))
    for a in party:
        if not a.dead:
            a.add_effect(Effect("Inspire Courage", 8, [("attack", "morale", b),
                                                       ("damage", "morale", b),
                                                       ("saves_vs_fear", "morale", b)]))


def ability_menu(ui, party) -> None:
    """Out-of-combat use of class abilities (the 'Use a class ability' menu)."""
    acts = []
    for p in party:
        if not p.conscious:
            continue
        hurt = [a for a in party if a.damage > 0 and not a.dead]
        if p.uses_left("lay_on_hands") and hurt:
            acts.append((f"{p.name}: lay on hands ({p.uses_left('lay_on_hands')} hp left)",
                         p, "loh"))
        if p.uses_left("wholeness") and p.damage > 0:
            acts.append((f"{p.name}: wholeness of body ({p.uses_left('wholeness')} hp left)",
                         p, "whole"))
        if p.uses_left("wild_shape") and not p.wild_form():
            acts.append((f"{p.name}: wild shape ({p.uses_left('wild_shape')} left today)",
                         p, "shape"))
        if p.wild_form():
            acts.append((f"{p.name}: return to normal form", p, "revert"))
    if not acts:
        ui.out("No class abilities are useful right now.")
        return
    i = ui.choose("Use which ability?", [a[0] for a in acts], allow_cancel=True)
    if i is None:
        return
    _, p, kind = acts[i]
    with ui.acting(p.player):
        if kind == "loh":
            hurt = [a for a in party if a.damage > 0 and not a.dead]
            tgt = hurt[0] if len(hurt) == 1 else hurt[ui.choose(
                "Lay hands on whom?", [f"{a.name} ({a.hp}/{a.max_hp()})" for a in hurt])]
            lay_on_hands(ui, p, tgt)
        elif kind == "whole":
            wholeness_of_body(ui, p)
        elif kind == "shape":
            wild_shape(ui, p)
        else:
            revert_shape(ui, p)


def has_usable(party) -> bool:
    for p in party:
        if not p.conscious:
            continue
        if (p.uses_left("lay_on_hands") and any(a.damage > 0 and not a.dead for a in party)) \
                or (p.uses_left("wholeness") and p.damage > 0) \
                or (p.uses_left("wild_shape") and not p.wild_form()) or p.wild_form():
            return True
    return False
