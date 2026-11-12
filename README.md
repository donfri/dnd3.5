# D&D 3.5 Text Adventures

A D&D 3.5 game for one to four players, played in a shared browser page (online)
or at one keyboard in the terminal. The
computer is the Game Master: it narrates, runs the monsters, rolls behind the
screen, and applies the D&D 3.5 rules (SRD), showing the math for every roll.

```
python3 play.py
```

It needs only Python 3.8 or newer. There are no third-party packages to install.

## Adventures

| Adventure | Levels | What's in it |
|---|---|---|
| **The Ember King's Barrow** | 1-3 | Goblins have kidnapped the miller's apprentice; an old barrow, undead, a riddle door, a fire-crowned king. |
| **The Drowned Lantern** | 1-3 | A dark lighthouse, kobold wreckers, smugglers, giant spiders, a sunken wreck, and a traitor in the village. |
| **Greyfang Pass** | 3-5 | A sequel: gnoll raiders, worgs, a broken bridge, a captured keep, dwarf prisoners and Skarn the ogre warlord. |
| **The Thornwood Fen** | 6-8 | Missing children, a troll under the causeway (bring fire), charmed lizardfolk, a wight-haunted barrow, gargoyles, and a green hag in a drowned abbey. |

Pick one under **New game**. Each adventure is designed so two heroes can win it,
and gets harder automatically when there are more heroes.

**Keep your heroes:** when you finish an adventure, the game offers to take the
same heroes straight into the next one. You can also do it later: choose **New
game → bring our heroes from a saved game**. They keep their levels, gear and
gold, and arrive rested. New heroes for a higher-level adventure are built at
the right level with the right starting wealth.

To write your own adventure, see *Extending it* below.

## Play online (friends in different places)

The game includes a small web server. One person hosts it, and everyone opens the
same link in a browser. You all see the same GM output live. Nobody needs to
install anything. The page is split into tabs:

- **Story**: narration and results, with your choices grouped underneath (*Do
  something here*, *Go somewhere*, *Attack & magic*, *Move*...). The rarely used
  options sit behind **More options**.
- **Party**: a card for each hero with HP bar, AC, conditions, XP and gold. The
  **Full character sheet** button opens the complete sheet.
- **Journal**: where you are, the quest log and rumors, and places visited.
- **Dice**: every roll with its math, so the story stays readable.
- **Chat**: talk to each other. A badge shows unread messages.
- **Full log**: everything, unfiltered.

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

- **Whose turn:** each hero belongs to a player, shown on the Party tab. Quick start
  hands out heroes in the order players joined. Only a hero's player can answer
  for that hero: combat turns, level-ups, spell prep, inventory, and character
  creation. Everyone else sees "Waiting for …" and greyed-out buttons. Exploration
  choices are party decisions anyone can make. If a hero's player isn't connected,
  anyone can answer for them, or use **Play this hero** on the Party tab to take
  it over. Names aren't passwords; this is to keep turns tidy among friends.
- **🗺 Map:** draws itself as you explore. It shows rooms you've visited,
  doorways you've seen but not walked through, where you are, locked doors, and
  traps you've found.
- **Gear:** in the Party tab, open **Character sheet & gear**: the Equipment table
  has buttons to Equip, Unequip, Off hand, Use (potions and scrolls, on yourself
  or a friend), Give and Drop. These work while exploring, between actions, and
  only for your own hero.
- **Turn alerts:** if you've switched to another tab, the page plays a chime,
  flashes its title, and can show a desktop notification when it's your
  decision. Set these up under 🔊⚙.
- **Never lose progress:** each table autosaves after every action, into its own
  file. When anyone opens the table, after a server restart or Fly putting the
  machine to sleep, it picks up exactly where you left off.
- **Phones:** the page adapts to small screens, with stacked buttons, text that
  wraps to the screen, and a full-screen character sheet.
- **Narrator:** the 🔊⚙ menu reads the story aloud. Choose *Story & dialogue* or
  *Story + combat*. By default the **server voice** is used: the server renders
  speech with [Piper](https://github.com/rhasspy/piper), a free offline neural
  voice, and the page plays it as one continuous audio stream. It sounds the same
  for everyone and avoids the clicks that some computers' built-in voices make
  (macOS in particular). There are two voices: a narrator, and a different voice
  for characters' dialogue. You can switch to *This computer's voices* if you
  prefer. Volume and speed are per player, and *Skip* stops the current reading.
  Piper and its two voices (~120 MB) are installed by the Dockerfile. If they're
  missing, the page quietly falls back to browser voices. To use them locally:
  `pip install piper-tts && python -m dnd35.tts --download`.
- When nobody's connected, the machine sleeps, which costs next to nothing. It
  wakes up when you open the page. The game in memory is lost while it sleeps,
  so pick **Load a saved game → autosave**. The game autosaves every time you
  enter a new area. Use **Save game** before you stop for the night.
- To update after a code change, run `git pull`, then `fly deploy`.

### Auto-deploy from GitHub

This repo includes `.github/workflows/fly-deploy.yml`. Every push to `main` runs
the tests and then runs `fly deploy`. To turn it on:

1. Do the one-time Fly setup above (`fly launch`, volume, secret, `fly deploy`,
   `fly scale count 1`). Then commit the `fly.toml` with your app name in it.
2. Run `fly tokens create deploy -x 999999h` and copy the token.
3. On GitHub, open the repo's **Settings → Secrets and variables → Actions →
   New repository secret**. Name it `FLY_API_TOKEN` and paste the token.
4. From then on, `git push` deploys. You can watch it in the repo's **Actions** tab.

### Or host it from your own computer

```bash
python3 -m dnd35.web --port 8080
```

Then share `http://<your-ip>:8080` with your friend. This needs port forwarding,
or a tunnel such as Tailscale, `cloudflared tunnel`, or `ngrok http 8080`.

### Hearing a line again

Every line in the story has a small speaker button (on a computer it appears
when you point at the line; on a phone it's always there, faintly). Click or tap
it to hear that paragraph again, even with the narrator switched off. Characters'
speech uses the character voice.

### Stepping away (AFK)

Press **☕ AFK** at the top of the page when you step away. Everyone sees you're
away, the computer plays your heroes' turns in fights (closing in, attacking,
stabilizing a dying friend), and anyone at the table can answer your other
questions so the game keeps moving. Press **I'm back** (or just answer a
question) to take over again. If your page sees no mouse, keyboard or touch for
5 minutes you're marked away automatically, and moving the mouse or tapping
brings you back. A player whose page has been closed for 5 minutes is treated
as away too.

### On a phone

The choices panel takes at most 40% of the screen, shows choices two to a row
without their explanations (press and hold one to see it), and folds down to a
single line on every tab except Story. Tap **choose ▴** to open it there, or
**hide ▾** to fold it on the Story tab.

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
- All 11 core classes, levels 1 to 20: barbarian, bard, cleric, druid, fighter,
  monk, paladin, ranger, rogue, sorcerer, wizard. **Multiclassing** is supported,
  and class alignment rules apply (paladins are lawful good, monks lawful, and so
  on).
- **Prestige classes** (each with its Dungeon Master's Guide requirements):
  Eldritch Knight, Mystic Theurge, Arcane Trickster, Dwarven Defender, Duelist,
  Arcane Archer, and Assassin (without assassin spells).
- High-level class features: greater and mighty rage, rogue special abilities
  (crippling strike, defensive roll, slippery mind...), monk greater flurry,
  diamond soul, quivering palm and perfect self, elemental wild shape, inspire
  heroics, and combat style mastery.
- Ability scores by 4d6-drop-lowest (with the PHB reroll rule), the elite array,
  or 25-point buy.
- All 44 skills, with class/cross-class ranks, synergies, armor check penalties,
  and trained-only skills.
- About 70 feats with real mechanics (Power Attack, Cleave/Great Cleave, Weapon
  Finesse, Point Blank/Precise/Rapid Shot, Manyshot, Two-Weapon Fighting and
  Improved TWF, Dodge/Mobility/Spring Attack, Improved Critical, Combat Reflexes,
  Stunning Fist, Deflect Arrows, Natural Spell, Extra Smiting...), each with its
  prerequisites.
- Class features: rage, damage reduction, uncanny dodge (and improved), trap
  sense, sneak attack, trapfinding, evasion and improved evasion, favored enemy,
  combat styles, wild empathy, turn undead, domains, spontaneous cure casting,
  a spellbook, and spells known. Plus:
  - **Bard:** inspire courage, bardic knowledge, casting in light armor.
  - **Druid:** nature sense, wild shape at 5th level (wolf, black bear, leopard;
    brown bear and dire wolf at 8th), no metal armor, venom immunity.
  - **Monk:** Wisdom to AC, flurry of blows, monk unarmed damage, fast movement,
    stunning fist, still mind, purity of body, wholeness of body.
  - **Paladin:** smite evil, divine grace, lay on hands, aura of courage (+4 vs
    fear for the party), divine health, turn undead, paladin spells, and a
    celestial warhorse at 5th level that fights beside you. Break the code (for
    example, murdering a helpless creature that isn't evil) and you fall until a
    temple performs atonement.
  - **Cleric:** 19 deities from the Player's Handbook and 18 domains with their
    powers (death touch, destruction smite, good fortune, protective ward,
    greater turning...). Evil clerics, and neutral ones who choose to, channel
    negative energy: they rebuke undead, command weak undead to fight for them,
    and convert spells into inflict spells. Domain spells use this game's
    closest spell where the official one isn't implemented.
  - **Bard music:** inspire courage, fascinate, countersong, inspire
    competence, suggestion, and inspire greatness.
  - **Wizard:** optional school specialization, with an extra spell per level
    and prohibited schools.
  - **Familiars:** deliver touch spells from 3rd level and scout the next area
    for you.
- About 180 spells, cantrips through 9th level, with real effects: *magic
  missile*, *sleep*, *bless*, *hold person*, *fireball*, *haste*, *entangle*,
  *barkskin*, *call lightning*, *slow*, *stoneskin*, *flame strike*, *cone of
  cold*, *raise dead*, *heal*, *chain lightning*, *disintegrate*, *finger of death*,
  *fire storm*, *power word kill*, *meteor swarm*, *wail of the banshee*, *true
  resurrection*, and more. Casters can be prepared or spontaneous, bonus
  spells come from high ability scores, and arcane spell failure applies.
- **Wands** (50 charges, spell trigger or Use Magic Device), **staffs** (several
  spells, using your caster level if it's higher), and **metamagic rods**.
- **Metamagic**: Empower, Extend, Maximize, Quicken (a free-action spell each
  round), Still and Silent. You choose it when you cast, and it uses a higher slot.
- **Spell resistance** (caster level checks, Spell Penetration), **dispel magic**,
  and **summoning** (Summon Monster I-V, Summon Nature's Ally I-V). Summoned
  creatures fight for whoever cast the spell, and druids can swap any prepared
  spell for a summon.
- Weapons, armor, shields, masterwork, +1 and +2 gear, rings, cloaks, amulets,
  bracers, belts, gauntlets and headbands, potions, scrolls (with Use Magic
  Device), alchemist's fire, holy water, encumbrance, and ammunition (you
  recover half of it after a fight).
- **Detailed character sheets** that break down every number: AC by source,
  each save, every attack line with iterative attacks, every skill, spells per
  day with save DCs, active effects, gear and load.

**Combat**
- A **battle grid** of 5-foot squares (70 by 45 feet). Foes start 30 to 45 feet
  away (closer in the dark). Speed limits how far you move each turn: slow heroes
  may need two moves or a charge to reach a foe, and monsters run, charge, or
  throw javelins as they come. Distance uses the 3.5 diagonal rule (5, 10, 5...).
  Ranged attacks take -2 per range increment. Flanking needs an ally on the far
  side of the foe (heroes step round to flank when they can). Spells like
  Fireball, Burning Hands, Lightning Bolt and Cone of Cold are real bursts,
  cones and lines: you pick where to aim, and you're warned if a friend (or you)
  would be caught. Breath weapons hit everyone in their cone.
- **Terrain** fits the place you're fighting: trees and undergrowth on the forest
  road, pillars and rubble in crypts, rock walls in caves, deep pools and reeds
  in the fen, carts and mud in villages, and a narrow bridge or ledge where
  there's no way round. Walls and trees block movement, rubble, reeds, shallow
  water and mud cost double, you can't charge across rough ground, walls block
  arrows and spells (and stop a fireball's blast), and shooting past trees,
  crates or pillars gives the target cover (+4 AC). Heroes and monsters find
  their own way around obstacles; you can slip past friends but not foes, so
  one hero can hold a bridge. A room can name its battlefield with a `terrain`
  key, and an encounter can override it.
- The terminal prints an ASCII battle map each round; the web page draws it in
  the story, and the **Map** tab shows it live during a fight.
- Initiative, surprise rounds, and flat-footed characters.
- Standard, move, and full-round actions: attack, full attack, charge, withdraw,
  total defense, fighting defensively, drawing weapons, standing up.
- Attacks of opportunity (and Combat Reflexes), flanking, firing into melee, and
  casting defensively (Concentration).
- Combat maneuvers: **trip, disarm, grapple** (hurt, pin, break free), and **bull
  rush**, with their Improved feats. You also get the **5-foot step**, **ready**
  (strike the first foe who comes at you), and **delay**.
- **Reach**: Large monsters and reach weapons (longspear, glaive, guisarme,
  ranseur) get a free swing at anyone closing in, and reach wielders can strike
  past the front line.
- **Animal companions** for druids (and rangers from 4th level) fight beside you,
  and your player commands them. They grow stronger as you level, and a new one
  comes if yours falls. Wizards and sorcerers get a **familiar** with its master
  bonus (a toad's +3 hp, a cat's +3 Move Silently...) plus Alertness.
- Critical threats and confirmation rolls, damage reduction, energy immunity and
  vulnerability, concealment, and two-weapon fighting.
- The 3.5 bonus-type stacking rules (morale, luck, deflection, dodge...).
- More combat options: **sunder**, **feint** (Bluff vs Sense Motive), **overrun**,
  **aid another**, **coup de grace**, fighting to **subdue** (nonlethal damage, with
  knocked-out foes tied up), and **readying a counterspell**.
- Exotic weapons (bastard sword, dwarven waraxe, spiked chain, whip, kama,
  nunchaku, siangham), Exotic Weapon Proficiency, and dwarven weapon familiarity.
- Disabled, dying, and stabilizing at 0 to -9 HP, and death at -10.
- Monster tactics: they gang up, throw javelins, and flee when broken. Ghouls
  paralyze and the boss has a recharge attack.
- Monster powers: **flying** (out of reach unless you fly, shoot, or ready an
  attack), **incorporeal** undead (only magic weapons hurt them, with a 50% miss
  chance), **breath weapons**, **fear auras** (resisted by a paladin's aura of
  courage), **spell-like abilities** (which you can counterspell), regeneration,
  energy drain, ability drain, improved grab, and rend. New monsters include
  hell hounds, shadows, wraiths, mummies, wyverns, an ogre mage and a juvenile
  white dragon.

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
- **Light and darkness**: underground areas are dark. The party lights torches
  (1 hour), a lantern (6 hours per flask of oil) or a *light* spell
  automatically. Without light, heroes who lack darkvision fight blind (50% miss
  chance, -2 AC) and can't search.
- **Hazards**: swimming (Swim checks, nearly drowning), cold and heat exposure
  (*endure elements* protects you), and falls (1d6 per 10 ft.).
- **Diplomacy** follows the SRD attitude table: hostile, unfriendly, indifferent,
  friendly, helpful. Talk a troll into letting you pass or a gnoll band into
  leaving. You can also **haggle** in shops (10% off on a good day).
- **Crafting** in town: Brew Potion, Scribe Scroll, Craft Wand, Craft Wondrous
  Item, and Craft Magic Arms and Armor. Each item costs half its price in gold,
  1/25 of its price in XP (never enough to lose a level), and a day per 1,000 gp.
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
  grid.py                  battle grid: distances, movement, areas, ASCII map
  abilities.py             lay on hands, wild shape, wholeness of body, bardic music
  companions.py            animal companions and familiars
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
- **New adventure**: copy one of the files in `dnd35/adventure/`, give it a new
  `ID`, `TITLE`, `LEVELS` and `SUMMARY`, and add it to `ORDER` in
  `dnd35/adventure/__init__.py`. `python -m unittest` checks that every exit,
  encounter, item and script it uses actually exists. Rooms have `exits`,
  `features` (actions with optional skill checks and success/failure effects),
  `traps`, `secrets`, and `encounters_enter`. Effects are small dicts such as
  `{"do": "xp", "amount": 100}` or `{"do": "fight", "enc": "guards"}`.

## Simplifications (deliberate)

- You choose who to move toward, and the game picks the route and the exact
  square (stepping round to flank when it can). Moving past a foe you aren't
  fighting doesn't provoke. Battlefields are generated fresh for each fight.
- Levels go to 20 (no epic levels), and the adventures cover levels 1 to 8.
  Higher-level heroes can still start any adventure, but it won't be a challenge.
- *Raise dead* costs the hero half a level of experience instead of a whole
  level (or 2 Constitution at 1st level). The temple can cast it for 5,450 gp.
- Familiars don't fight.
  Metamagic is chosen at casting time (spending the higher slot then) rather
  than at preparation.
- Monsters die at 0 HP. PCs use the full dying rules.
