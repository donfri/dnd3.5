"""Main menu and game flow."""
from __future__ import annotations

import argparse
import sys

from . import __version__, dice
from .adventure import ORDER
from .adventure.engine import (GM, GameOver, GameState, list_saves, load_game, save_game,
                               save_info)
from .creation import build_pregen, choose_pregen, create_character
from .sheet import render
from .ui import UI, Color, QuitGame, c


BANNER = r"""
  ____        ____     _____ ____
 |  _ \ _ __ |  _ \   |___ /| ___|
 | | | | '_ \| | | |    |_ \|___ \
 | |_| | | | | |_| |   ___) |___) |
 |____/|_| |_|____/   |____(_)____/

  T E X T   A D V E N T U R E S
  D&D 3.5 rules, computer Game Master"""

HELP_TEXT = """
HOW TO PLAY. Everything is menu-driven: type the number of an option and press
Enter. You can also type the first few letters of an option. Type /quit at any
prompt to leave immediately.

HOT SEAT. The heroes share one keyboard. Out of combat the party decides
together; in combat each hero's turn is announced with the player's name, so pass
the keyboard.

THE RULES are D&D 3.5 (SRD): d20 + modifiers vs a DC or Armor Class; natural 20
always hits and threatens a critical (confirm with a second roll); natural 1
always misses. Every roll is shown with its math.

COMBAT. Each turn you get a standard action (attack, cast, use an item) plus a
move action (close into melee, draw a weapon, stand up), or one full-round
action (full attack, charge, withdraw). Positioning is abstracted as 'melee':
once you move next to a foe you are in melee with it. Leaving melee, casting,
shooting or drinking a potion while in melee provokes attacks of opportunity
(cast defensively to avoid them). Two allies in melee with the same foe flank it
(+2 to hit, and rogues add sneak attack damage). Firing into a melee is -4
unless you have Precise Shot.

DYING. At 0 hp you are disabled; below 0 you are unconscious and dying (lose 1 hp
per round, 10% chance to stabilize). At -10 you die. A Heal check (DC 15) or any
healing stabilizes a dying friend.

EXPLORING. Search the area to find traps and secret doors (takes 2 minutes;
only rogues can find the hardest traps). Turn on sneaking to try to surprise
monsters. Rest for 8 hours to heal (1 hp/level, doubled in a real bed), regain
spells and daily abilities. Resting in the dungeon can attract wandering
monsters. The village has an inn, a shop and a temple.

CHARACTER SHEETS show the full math for every number. Level up when you have
enough XP (the game will tell you).
"""


def make_heroic(ch) -> None:
    """Heroic mode: maximum hit points every level, plus bonus vigor equal to half the
    hero's base Constitution score (a common house rule for small parties)."""
    from .data.classes import CLASSES
    ch.hp_rolls = [CLASSES[cls]["hd"] for cls in ch.class_levels]
    ch.bonus_hp = ch.base_ability_score("con") // 2


def choose_adventure(ui: UI, prompt: str = "Which adventure?"):
    opts = [f"{a.TITLE} (levels {a.LEVELS}): {a.SUMMARY}" for a in ORDER]
    return ORDER[ui.choose(prompt, opts, default=0)]


def ready_party(party) -> list:
    """Bring heroes into a new adventure: alive, rested, conditions cleared."""
    out = []
    for p in party:
        if p.dead:
            continue
        p.damage = 0
        p.temp_hp = 0
        p.stable = False
        p.effects = []
        p.daily = {}
        p.ability_damage = {}
        p.afflictions = []
        p.reset_spells()
        if getattr(p, "companion", None):
            p.companion.update(damage=0, dead=False)
            p._companion_inst = None
        out.append(p)
    return out


def start_adventure(ui: UI, adv, party, settings) -> GameState:
    gs = GameState(adv, party, settings)
    ui.header(adv.TITLE.upper())
    ui.gm(adv.INTRO)
    return gs


def bring_heroes(ui: UI):
    """Pick a save and return (party, settings) from it, or None."""
    saves = list_saves()
    if not saves:
        ui.warn("There are no saved games to bring heroes from.")
        return None
    i = ui.choose("Bring the heroes from which save?", [save_info(n) for n in saves],
                  allow_cancel=True)
    if i is None:
        return None
    old = load_game(saves[i])
    party = ready_party(old.party)
    if not party:
        ui.warn("Everyone in that save is dead.")
        return None
    ui.good("The heroes arrive, rested and ready: " +
            ", ".join(f"{p.name} (level {p.level})" for p in party))
    return party, dict(old.settings)


def new_game(ui: UI, quick: bool = False) -> GameState:
    ui.header("NEW GAME")
    adv = choose_adventure(ui)
    ui.para(f"{adv.TITLE}: designed for 1-4 heroes of level {adv.LEVELS}. With two players, "
            f"each of you can run one hero (heroic mode recommended) or two heroes each "
            f"(the classic four-person party).")
    start_level = getattr(adv, "START_LEVEL", 1)
    if not quick:
        how = ui.choose("Who is going on this adventure?", [
            "New heroes" + (f" (built at level {start_level})" if start_level > 1 else ""),
            "Bring our heroes from a saved game (keeps levels, gear and gold)"], default=0)
        if how == 1:
            got = bring_heroes(ui)
            if got:
                party, settings = got
                low = [p.name for p in party if p.level < start_level]
                if low:
                    ui.warn(f"Heads up: {', '.join(low)} is below level {start_level}; this "
                            f"one will be tough.")
                return start_adventure(ui, adv, party, settings)
    n = 2 if quick else ui.ask_int("How many heroes in the party?", 1, 4, 2)
    heroic = True if quick else ui.confirm(
        "Heroic mode? (max hit points every level + bonus hit points equal to half your "
        "Constitution; recommended for parties of 1-2 heroes)",
        n <= 2)
    party = []
    taken = []
    seats = list(getattr(ui, "seat_players", lambda: [])())
    for i in range(n):
        ui.header(f"HERO {i + 1} OF {n}")
        player = "" if quick else ui.ask("Player name", f"Player {i + 1}")
        with ui.acting(player):
            ch = _make_hero(ui, quick, i, player or (seats[i] if i < len(seats) else ""),
                            taken, start_level)
        if heroic:
            make_heroic(ch)
        party.append(ch)
    return start_adventure(ui, adv, party, {"heroic": heroic})


def _make_hero(ui, quick, i, player, taken, level=1):
    if quick:
        key = ["thorgar", "lyra", "pip", "aldric"][i]
        ch = build_pregen(key, player or f"Player {i + 1}", level=level)
        taken.append(key)
    else:
        choice = ui.choose(f"{player}, how do you want to make your hero?", [
            "Create a new character (full D&D 3.5 creation)",
            "Pick a ready-made hero"], default=0)
        if choice == 0:
            ch = create_character(ui, player, start_level=level)
        else:
            ch = choose_pregen(ui, player, taken, level=level)
    return ch


def play(ui: UI, gs: GameState) -> None:
    gm = GM(ui, gs)
    while True:
        try:
            gm.loop()
        except GameOver as go:
            if go.result == "victory":
                ui.header("VICTORY")
                ui.gm(gs.adv.ENDING)
                for p in gs.party:
                    ui.out(render(p, full=False))
                name = f"victory-{gs.adv.ID}"
                save_game(gs, name)
                ui.good(f"Your heroes are saved as '{name}'.")
                if ui.confirm("Take these heroes on another adventure now?", True):
                    nxt = choose_adventure(ui, "Where to next?")
                    gs = start_adventure(ui, nxt, ready_party(gs.party), dict(gs.settings))
                    gm = GM(ui, gs)
                    continue
                ui.good("Thanks for playing! (Later: New game -> bring heroes from a save.)")
                return
            ui.header("THE PARTY HAS FALLEN")
            ui.gm("Darkness closes in, and the tale ends here... unless fate allows a second "
                  "chance.")
            saves = list_saves()
            auto = getattr(ui, "autosave_name", "autosave")
            if auto in saves and ui.confirm("Go back to the last autosave (just before "
                                            "this fight)?", True):
                gs = load_game(auto)
                gm = GM(ui, gs)
                gm.describe_brief()
                continue
            return


def main_menu(ui: UI) -> None:
    ui.out(c(BANNER, "byellow"))
    ui.out(c(f"  version {__version__}", "dim"))
    while True:
        saves = list_saves()
        auto = getattr(ui, "autosave_name", "autosave")
        opts = []
        if auto in saves:
            opts.append("Continue: " + save_info(auto).split(": ", 1)[-1])
        opts += ["New game", "Quick start (two ready-made heroes, heroic mode)"]
        if saves:
            opts.append("Load a saved game")
        opts += ["How to play", "Quit"]
        i = ui.choose("Main menu", opts)
        label = opts[i]
        try:
            if label.startswith("Continue: "):
                gm_play_loaded(ui, load_game(auto))
            elif label == "New game":
                play(ui, new_game(ui))
            elif label.startswith("Quick start"):
                play(ui, new_game(ui, quick=True))
            elif label.startswith("Load"):
                j = ui.choose("Load which save?", [save_info(n) for n in saves],
                              allow_cancel=True)
                if j is not None:
                    gs = load_game(saves[j])
                    ui.good(f"Loaded '{saves[j]}' ({gs.time_str()}).")
                    gm_play_loaded(ui, gs)
            elif label == "How to play":
                ui.para(HELP_TEXT)
            else:
                return
        except QuitGame:
            return


def gm_play_loaded(ui: UI, gs: GameState) -> None:
    gs.rs()["visited"] = True
    play(ui, gs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="D&D 3.5 text adventure with a computer GM")
    ap.add_argument("--seed", type=int, help="seed the dice (reproducible games)")
    ap.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    ap.add_argument("--sheet", metavar="PREGEN", help="print a pregenerated hero's sheet and "
                                                      "exit (thorgar, lyra, pip, aldric, kesh, "
                                                      "faelin, sable)")
    ap.add_argument("--level", type=int, default=1, help="level for --sheet")
    args = ap.parse_args(argv)
    if args.no_color:
        Color.enabled = False
    if args.seed is not None:
        dice.seed(args.seed)
    if args.sheet:
        print(render(build_pregen(args.sheet, level=args.level)))
        return 0
    ui = UI()
    try:
        main_menu(ui)
    except (QuitGame, KeyboardInterrupt):
        print()
    print("Farewell, adventurers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
