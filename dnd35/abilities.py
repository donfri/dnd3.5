"""Class abilities usable in and out of combat: lay on hands, wholeness of body,
wild shape, bardic music."""
from __future__ import annotations

from typing import List

from . import dice
from .data.monsters import ELEMENTAL_SHAPES, MONSTERS, WILD_SHAPES
from .effects import ROUNDS_PER_HOUR, ROUNDS_PER_MINUTE, Effect
from .magic import heal, saving_throw


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
    out = [k for k, need in WILD_SHAPES.items() if lvl >= need] if p.uses_left("wild_shape") \
        else []
    if p.uses_left("elemental_shape"):
        out += [k for k, need in ELEMENTAL_SHAPES.items() if lvl >= need]
    return out


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
    p.spend("elemental_shape" if key in ELEMENTAL_SHAPES else "wild_shape")
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


def courage_bonus(bard) -> int:
    lvl = bard.class_level("bard")
    return 1 + (lvl >= 8) + (lvl >= 14) + (lvl >= 20)


def inspire_courage(ui, bard, party) -> None:
    bard.spend("music")
    b = courage_bonus(bard)
    ui.out(f"{bard.name} strikes up a stirring song of courage!", ("bmagenta",))
    for a in party:
        if not a.dead:
            a.add_effect(Effect("Inspire Courage", 8, [("attack", "morale", b),
                                                       ("damage", "morale", b),
                                                       ("saves_vs_fear", "morale", b)]))


def protective_ward(ui, cleric, tgt) -> None:
    cleric.spend("protective_ward")
    lvl = cleric.class_level("cleric")
    tgt.add_effect(Effect("Protective ward", ROUNDS_PER_HOUR, [("saves", "resistance", lvl)],
                          tags=["consume_any"]))
    ui.good(f"{cleric.name} touches {tgt.name}: +{lvl} on their next saving throw.")


def music_options(bard, in_combat: bool):
    lvl = bard.class_level("bard")
    perf = bard.skill_ranks.get("Perform", 0)
    out = []
    if perf >= 3:
        if in_combat:
            out.append(("courage", f"Inspire courage (+{courage_bonus(bard)} attack and "
                                   f"damage for the party)"))
            out.append(("fascinate", f"Fascinate (up to {1 + (lvl - 1) // 3} foes stand "
                                     f"spellbound until hurt)"))
            out.append(("countersong", "Countersong (+4 on the party's saves against sonic "
                                       "attacks and fear)"))
        if lvl >= 3 and perf >= 6:
            out.append(("competence", "Inspire competence (+2 on an ally's skill checks)"))
        if in_combat and lvl >= 6 and perf >= 9:
            out.append(("suggestion", "Suggestion (a fascinated foe is persuaded to leave "
                                      "the fight)"))
        if in_combat and lvl >= 9 and perf >= 12:
            out.append(("greatness", "Inspire greatness (one ally: +2d10 temp hp, +2 attack, "
                                     "+1 Fort)"))
        if in_combat and lvl >= 15 and perf >= 18:
            out.append(("heroics", "Inspire heroics (one ally: +4 morale on saves, +4 dodge "
                                   "AC)"))
    return out


def bardic_music(ui, bard, allies, enemies, kind: str) -> None:
    lvl = bard.class_level("bard")
    dc = 10 + lvl // 2 + bard.mod("cha")
    bard.spend("music")
    if kind == "courage":
        inspire_courage(ui, bard, allies)
        bard.daily["music"] -= 1   # inspire_courage already spent a use
    elif kind == "fascinate":
        ui.out(f"{bard.name} plays a haunting, hypnotic melody...", ("bmagenta",))
        for f in [e for e in enemies if not e.dead][:1 + (lvl - 1) // 3]:
            if getattr(f, "block", {}).get("mindless") or "mind-affecting" in f.immunities():
                ui.out(f"  {f.name} doesn't notice the music.")
            elif not saving_throw(ui, f, "will", dc, ["mind-affecting", "sonic"], "fascinate"):
                f.add_effect(Effect("Fascinated", lvl, tags=["fascinated", "dazed"],
                                    source=bard.name))
                ui.good(f"  {f.name} stands spellbound, listening.")
    elif kind == "countersong":
        ui.out(f"{bard.name} sings a countering melody.", ("bmagenta",))
        for a in allies:
            a.add_effect(Effect("Countersong", 10, [("saves_vs_sonic", "morale", 4),
                                                    ("saves_vs_fear", "morale", 4)]))
    elif kind == "competence":
        tgt = allies[0] if len(allies) == 1 else allies[ui.choose(
            "Inspire whom?", [a.name for a in allies])]
        tgt.add_effect(Effect("Inspire competence", 2 * ROUNDS_PER_MINUTE,
                              [("skills", "competence", 2)]))
        ui.good(f"{bard.name}'s song steadies {tgt.name}: +2 on skill checks for a while.")
    elif kind == "suggestion":
        fasc = [e for e in enemies if e.get_effect("Fascinated")]
        if not fasc:
            ui.out("No one is fascinated.")
            bard.daily["music"] -= 1
            return
        f = fasc[0]
        if not saving_throw(ui, f, "will", dc, ["mind-affecting", "language"], "suggestion"):
            f.add_effect(Effect("Suggestion", lvl * ROUNDS_PER_MINUTE,
                                tags=["frightened"], source=bard.name))
            ui.good(f"  {bard.name} sings softly that this fight isn't worth it... and "
                    f"{f.name} agrees, and walks away.")
    elif kind == "heroics":
        tgt = allies[0] if len(allies) == 1 else allies[ui.choose(
            "Inspire whom?", [a.name for a in allies])]
        tgt.add_effect(Effect("Inspire heroics", 10, [("saves", "morale", 4),
                                                      ("ac", "dodge", 4)]))
        ui.good(f"{tgt.name} stands like a legend: +4 on saves, +4 AC.")
    elif kind == "greatness":
        tgt = allies[0] if len(allies) == 1 else allies[ui.choose(
            "Inspire whom?", [a.name for a in allies])]
        hp = dice.roll("2d10").total
        tgt.temp_hp += hp
        tgt.add_effect(Effect("Inspire greatness", 10, [("attack", "competence", 2),
                                                        ("save_fort", "competence", 1)],
                              data={"on_end": "temp_hp", "amount": hp}))
        ui.good(f"{tgt.name} is filled with greatness: +{hp} temporary hp, +2 attack, "
                f"+1 Fortitude.")


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
        if (p.uses_left("wild_shape") or p.uses_left("elemental_shape")) and not p.wild_form():
            acts.append((f"{p.name}: wild shape ({p.uses_left('wild_shape')} left today"
                         + (f", {p.uses_left('elemental_shape')} elemental"
                            if p.uses_left("elemental_shape") else "") + ")", p, "shape"))
        if p.wild_form():
            acts.append((f"{p.name}: return to normal form", p, "revert"))
        if p.uses_left("protective_ward"):
            acts.append((f"{p.name}: protective ward (+{p.class_level('cleric')} on an ally's "
                         f"next save)", p, "ward"))
        if p.uses_left("music") and any(k == "competence" for k, _ in music_options(p, False)):
            acts.append((f"{p.name}: inspire competence (+2 on an ally's skill checks)", p,
                         "competence"))
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
        elif kind == "ward":
            living = [a for a in party if not a.dead]
            tgt = living[0] if len(living) == 1 else living[ui.choose(
                "Ward whom?", [a.name for a in living])]
            protective_ward(ui, p, tgt)
        elif kind == "competence":
            bardic_music(ui, p, [a for a in party if not a.dead], [], "competence")
        else:
            revert_shape(ui, p)


def has_usable(party) -> bool:
    for p in party:
        if not p.conscious:
            continue
        if (p.uses_left("lay_on_hands") and any(a.damage > 0 and not a.dead for a in party)) \
                or (p.uses_left("wholeness") and p.damage > 0) \
                or (p.uses_left("wild_shape") and not p.wild_form()) or p.wild_form() \
                or p.uses_left("protective_ward") or (
                    p.uses_left("music") and p.class_level("bard") >= 3
                    and p.skill_ranks.get("Perform", 0) >= 6):
            return True
    return False
