# D&D 3.5 Text Adventure: *The Ember King's Barrow*

A D&D 3.5 game for one to four players, played in a shared browser page (online)
or at one keyboard in the terminal. The
computer is the Game Master: it narrates, runs the monsters, rolls behind the
screen, and applies the D&D 3.5 rules (SRD), showing the math for every roll.

```
python3 play.py
```

It needs only Python 3.8 or newer. There are no third-party packages to install.

## Play online (friends in different places)

The game includes a small web server. One person hosts it, and everyone opens the
same link in a browser. You all see the same GM output live. You can click menu
choices or type answers, and there's a chat sidebar. Nobody needs to install
anything.

### Host it on Fly.io (recommended)

You need a Fly.io account and the `fly` command-line tool
(<https://fly.io/docs/flyctl/install/>). Run these from this folder:

```bash
fly auth login
fly launch --no-deploy --copy-config      # say yes to copying fly.toml; pick a unique app name
fly volumes create dnd_saves --size 1     # keeps saves/autosaves between sessions
fly secrets set TABLE_PASSWORD=pick-something   # optional, but keeps strangers out
fly deploy
fly scale count 1                          # IMPORTANT: the live game runs on exactly one machine
```

Then both of you open `https://<your-app-name>.fly.dev`. Enter your name, keep the
table name the same (for example `main`), and enter the password. To run a second
campaign at the same time, give it a different table name.

- When nobody's connected, the machine sleeps, which costs next to nothing. It
  wakes up when you open the page. The game in memory is lost while it sleeps,
  so pick **Load a saved game → autosave**. The game autosaves every time you
  enter a new area. Use **Save game** before you stop for the night.
- To update after a code change, run `git pull`, then `fly deploy`.

### Or host it from your own computer

```bash
python3 -m dnd35.web --port 8080
```

Then share `http://<your-ip>:8080` with your friend. This needs port forwarding,
or a tunnel such as Tailscale, `cloudflared tunnel`, or `ngrok http 8080`.

## Quick start for two players

1. Run `python3 play.py`.
2. Pick **Quick start** to start right away with two ready-made heroes (a dwarf
   fighter and an elf wizard), or **New game** to build your own characters.
3. With two players, pick **one hero each in heroic mode**. Heroic mode gives
   maximum hit points every level plus bonus HP equal to half your Constitution.
   You can also play the classic way, with **two heroes each** (a four-person party).
4. Out of combat, the party decides together. In combat, the game announces whose
   turn it is (with the player's name). Online, that player answers. In the
   terminal, pass the keyboard.

Every menu is numbered. Type the number, or the first few letters of an option.
Type `/quit` at any prompt to leave.

Command-line options:

| Option | Effect |
|---|---|
| `--seed N` | Reproducible dice |
| `--no-color` | Plain text (also respects `NO_COLOR`) |
| `--sheet pip --level 3` | Print a ready-made hero's sheet and exit |

## What's in it

**Characters (Player's Handbook / SRD 3.5)**
- 7 races: human, dwarf, elf, gnome, half-elf, half-orc, halfling, with all
  their combat-relevant traits (stonecunning, sleep immunity, +1 vs goblinoids,
  size modifiers, and so on).
- 7 classes, levels 1 to 5: barbarian, cleric, fighter, ranger, rogue, sorcerer,
  wizard. **Multiclassing** is supported.
- Ability scores by 4d6-drop-lowest (with the PHB reroll rule), the elite array,
  or 25-point buy.
- All 44 skills, with class/cross-class ranks, synergies, armor check penalties,
  and trained-only skills.
- About 50 feats with real mechanics (Power Attack, Cleave, Weapon Finesse,
  Point Blank/Precise/Rapid Shot, Two-Weapon Fighting, Dodge/Mobility, Combat
  Casting, Spell Focus, Extra Turning...), each with its prerequisites.
- Class features: rage, uncanny dodge, trap sense, sneak attack, trapfinding,
  evasion, favored enemy, combat styles, wild empathy, turn undead, domains,
  spontaneous cure casting, a spellbook, and spells known.
- 50 spells (cantrips through 3rd level) with real effects: *magic missile*,
  *sleep*, *color spray*, *bless*, *hold person*, *spiritual weapon*, *fireball*,
  *haste*, and more. Casters can be prepared or spontaneous, bonus spells come
  from high ability scores, and arcane spell failure applies.
- Weapons, armor, shields, masterwork and +1 gear, potions, scrolls (with Use
  Magic Device), alchemist's fire, holy water, encumbrance, and ammunition (you
  recover half of it after a fight).
- **Detailed character sheets** that break down every number: AC by source,
  each save, every attack line with iterative attacks, every skill, spells per
  day with save DCs, active effects, gear and load.

**Combat**
- Initiative, surprise rounds, and flat-footed characters.
- Standard, move, and full-round actions: attack, full attack, charge, withdraw,
  total defense, fighting defensively, drawing weapons, standing up.
- Attacks of opportunity, flanking, firing into melee, and casting defensively
  (Concentration).
- Critical threats and confirmation rolls, damage reduction, energy immunity and
  vulnerability, concealment, and two-weapon fighting.
- The 3.5 bonus-type stacking rules (morale, luck, deflection, dodge...).
- Disabled, dying, and stabilizing at 0 to -9 HP, and death at -10.
- Monster tactics: they gang up, throw javelins, flee when broken, and ghouls
  paralyze. The boss has a recharge attack.

**The computer GM**
- An original adventure of 17 areas: a village hub, wilderness, an upper and
  lower barrow, and a boss tomb.
- Skill challenges, traps (search, disable, or jump over), a secret alcove, a
  riddle door, locks you can pick or force, and encounters you can talk or sneak
  your way through.
- The village has an inn, a shop, and a shrine with healing services. You can
  gather rumors and recruit replacement heroes.
- Resting heals naturally, restores spells, and gives you a chance to prepare new
  ones. Resting in the dungeon can bring wandering monsters. Diseases are tracked.
- Experience follows the DMG table and is split among the party. Level-ups are
  interactive, or you can use a recommended build.
- Save/load (JSON in `saves/`) and an autosave every time you enter an area.

## Tips for surviving

- Low-level D&D is deadly. Rest at the inn (a real bed doubles natural healing)
  and buy potions at the shrine.
- Skeletons shrug off blades (DR 5/bludgeoning) and zombies shrug off maces
  (DR 5/slashing). Gather rumors in town, and loot the crypt.
- *Sleep* and *color spray* win early fights. Clerics should use turn undead.
- Flank with your melee heroes. Use *Search* in suspicious rooms.
- Some fights can be avoided or softened with Intimidate, Diplomacy, Handle
  Animal, or a bit of sneaking.

## Project layout

```
play.py                    start the game
dnd35/
  dice.py rules.py         dice expressions, 3.5 tables (BAB, saves, XP, sizes, stacking)
  effects.py               typed temporary effects & conditions
  creature.py              shared stat math (AC, saves, attacks, damage, DR)
  character.py monster.py  PCs and monsters
  levelup.py creation.py   character creation, leveling, pregens, recommended builds
  sheet.py                 character sheet rendering
  magic.py combat.py       spells and the combat engine
  shop.py                  shopping & inventory
  adventure/engine.py      the GM: rooms, checks, traps, encounters, rest, town
  adventure/ember_barrow.py   the adventure itself (pure data + a few scripts)
  data/                    races, classes, skills, feats, items, spells, monsters
  game.py ui.py            menus, hot-seat flow, terminal I/O
  web.py                   online shared table (web page + long-poll API, stdlib only)
Dockerfile fly.toml        Fly.io deployment
tests/                     unit tests, plus randomized "fuzz" play-throughs
```

Run the tests with:

```
python3 -m unittest discover -s tests
```

## Extending it

- **New monster**: add a stat block to `data/monsters.py`. Attack bonuses, AC,
  and saves are derived from HD, BAB, abilities, gear, and feats, the same way
  as for PCs. `tests/test_rules.py` checks them against Monster Manual numbers.
- **New spell**: add it to `data/spells.py` and give it a branch in
  `magic.cast_spell`.
- **New adventure**: copy `adventure/ember_barrow.py`. Rooms have `exits`,
  `features` (actions with optional skill checks and success/failure effects),
  `traps`, `secrets`, and `encounters_enter`. Effects are small dicts such as
  `{"do": "xp", "amount": 100}` or `{"do": "fight", "enc": "guards"}`.

## Simplifications (deliberate)

- There is no battle grid. Positioning is abstracted as being "in melee with" a
  foe, which still drives attacks of opportunity, flanking, charging, full
  attacks, and firing into melee.
- Levels are capped at 5. Spells go up to 3rd level.
- Familiars and the ranger's animal companion are flavor only. Grapple, trip
  (other than wolves), bull rush, and metamagic aren't implemented.
- Monsters die at 0 HP. PCs use the full dying rules.
