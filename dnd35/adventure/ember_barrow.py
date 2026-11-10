"""THE EMBER KING'S BARROW
An original introductory adventure for 1-4 heroes of 1st level (ends around 3rd).

Goblins have been raiding the farms around Millbrook, and last night they
dragged off Tomas, the miller's apprentice. Their trail leads to an old barrow
on Ashen Hill, where something older than goblins is waking up.
"""

ID = "ember_barrow"
TITLE = "The Ember King's Barrow"
START = "millbrook"
REST_ENCOUNTER_CHANCE = 0.25

INTRO = """
The village of Millbrook sits where the Old Mill Road crosses the Silverrun, a
cluster of thatched roofs, a stone mill, and one good inn. It is the kind of
place where nothing happens, which is exactly why everyone is so frightened now.

For a month, goblins have been stealing chickens, then sheep, then anything not
nailed down. Last night they came for people. Tomas, the miller's apprentice,
was dragged screaming into the dark while he checked the sluice gate.

You arrived in Millbrook this morning, and the innkeeper of the Crooked Kettle
has been watching you since you walked in: travelers with weapons, the first
she's seen in weeks.
"""

ENDING = """
The crown of the Ember King cools in your hands as the barrow behind you goes
quiet, its fire finally out. In Millbrook the bells ring, the mill wheel turns
again, and Marta pours drinks on the house until well past midnight.

The tale of the heroes who walked into Ashen Hill will be told in the Crooked
Kettle for years. Whatever comes next, you have earned your names.

THE END (for now).
"""

RUMORS = [
    (5, "The goblins only started raiding after old Hegg the shepherd saw 'a red glow' "
        "on Ashen Hill at midsummer."),
    (10, "The goblin band is led by a huge, hairy brute the goblins call Grukk. He's no "
         "goblin. Bigger. Quieter. A bugbear, maybe."),
    (10, "A barrow-wight? No, worse: they say an old king was buried in that hill with a "
         "crown of living fire, and a curse to keep it."),
    (15, "Skeletons don't care much for blades. A hammer or mace shatters them; swords just "
         "clatter off the bones."),
    (15, "The barrow's builders loved riddles. Grandmother said the king's door answers only "
         "to 'the thing that is fed but never full.'"),
    (20, "There's a ghoul's grave in the deep part, the old priests said. Elves are immune "
         "to a ghoul's paralyzing touch, but the rest of us had better pray."),
    (20, "Fire will barely scratch the thing in the deepest tomb. Cold, though... cold is "
         "what it fears."),
]

WANDERING = [
    {"text": "Squeaking and scrabbling: hungry dire rats find you!",
     "monsters": ["dire rat", "dire rat"]},
    {"text": "A goblin patrol stumbles across your camp!",
     "monsters": ["goblin", "goblin"], "requires": {"not_flag": "enc:warren"}},
    {"text": "A lone skeleton clatters out of the dark, its jaw hanging open.",
     "monsters": ["human skeleton"]},
]

ENCOUNTERS = {
    "ambush": {
        "room": "old_bridge", "monsters": ["goblin", "goblin"],
        "per_extra_hero": ["goblin"], "ambush": True,
        "ambush_text": "The reeds by the bridge rustle against the wind...",
        "text": "Goblins burst from the reeds, shrieking and waving morningstars!",
        "title": "GOBLIN AMBUSH",
    },
    "sentry": {
        "room": "barrow_hill", "monsters": ["goblin"], "title": "THE SENTRY",
        "text": "The goblin sentry leaps up, fumbling for its weapon.",
    },
    "guards": {
        "room": "guard_room", "monsters": ["goblin", "goblin", "goblin archer"],
        "per_extra_hero": ["goblin"], "title": "THE GUARD ROOM",
        "text": "Goblins around a dice game scatter for their weapons, yelling in their "
                "squeaky tongue!",
    },
    "rats": {
        "room": "cistern", "monsters": ["dire rat", "dire rat"],
        "per_extra_hero": ["dire rat"], "title": "THE CISTERN",
        "text": "Wet, red-eyed shapes scramble up out of the black water!",
    },
    "skeletons": {
        "room": "crypt", "monsters": ["human skeleton", "human skeleton"],
        "per_extra_hero": ["human skeleton"], "title": "THE RESTLESS DEAD",
        "text": "Bones scrape on stone. In the niches along the walls, the dead sit up.",
    },
    "barracks": {
        "room": "barracks", "monsters": ["hobgoblin", "goblin"],
        "per_extra_hero": ["goblin"], "names": {"hobgoblin": "Sergeant Vrask"},
        "title": "THE BARRACKS",
        "text": "A hobgoblin in studded leather barks orders, and a goblin scrambles off a "
                "bunk to obey.",
    },
    "wolf": {
        "room": "kennel", "monsters": ["wolf"], "per_extra_hero": [],
        "title": "THE KENNEL", "text": "The wolf lunges to the end of its chain... and the "
                                        "rusted chain snaps!",
    },
    "zombies": {
        "room": "lower_hall", "monsters": ["human zombie", "human zombie"],
        "per_extra_hero": ["human zombie"], "title": "THE HALL OF SERVANTS",
        "text": "Two of the robed figures along the walls lurch forward, grey hands raised.",
    },
    "warren": {
        "room": "warren", "monsters": ["bugbear", "goblin"],
        "per_extra_hero": ["goblin"], "names": {"bugbear": "Grukk"},
        "title": "GRUKK'S WARREN", "can_flee": True,
        "text": "Grukk rises from his throne of stolen sacks, hefting a spiked morningstar. "
                "'More little meat,' he rumbles. 'Good.'",
    },
    "antechamber": {
        "room": "antechamber", "monsters": ["ghoul", "human zombie"],
        "per_extra_hero": ["ghoul"], "title": "THE HUNGRY DEAD",
        "text": "Something crouched over old bones looks up at you with a long grey tongue.",
    },
    "ember_king": {
        "room": "tomb", "monsters": ["ember husk"],
        "per_extra_hero": ["human skeleton"], "title": "THE EMBER KING",
        "can_flee": True,
        "text": "The crowned corpse rises from its throne. Heat rolls off it like an opened "
                "oven, and its voice is the crackle of a dying fire: 'WHO FEEDS MY FLAME?'",
    },
}


def T(text):
    return {"do": "text", "text": text}


def SAY(who, text):
    return {"do": "say", "who": who, "text": text}


ROOMS = {
    # ================================================================ village
    "millbrook": {
        "name": "Millbrook Village", "town": True, "wandering": False,
        "desc": "The muddy square of Millbrook: the Crooked Kettle inn, Hollin's General "
                "Goods, a small whitewashed shrine to Pelor, and the stone mill on the river. "
                "East, the Old Mill Road disappears into the Thornwood.",
        "features": [
            {"id": "marta", "label": "Talk to Marta, the innkeeper of the Crooked Kettle",
             "requires": {"not_flag": "quest"}, "once": True, "effects": [
                SAY("Marta", "You've got the look of people who can handle themselves. I'll "
                             "be plain: the goblins took Tomas last night. He's a good lad, "
                             "barely nineteen, and his master is beside himself."),
                SAY("Marta", "Their tracks go east along the Mill Road, toward Ashen Hill, "
                             "where the old barrow is. The village can pay a hundred gold "
                             "each if you bring him home. Here, take these. My late husband "
                             "always said a healing draught is cheaper than a funeral."),
                {"do": "items_each", "id": "potion of cure light wounds", "qty": 1},
                {"do": "flag", "name": "quest"},
                {"do": "journal", "text": "Quest: rescue Tomas the miller's apprentice from "
                                          "the goblins at Ashen Hill (100 gp each)."},
            ]},
            {"id": "marta2", "label": "Talk to Marta again",
             "requires": {"flag": "quest", "not_flag": "tomas_home"}, "effects": [
                SAY("Marta", "Go on, then. East along the Mill Road. And if you hear anything "
                             "about that red glow on the hill, I don't want to know about "
                             "it until Tomas is home."),
            ]},
            {"id": "return_tomas", "label": "Bring Tomas home to the mill",
             "requires": {"flags": ["tomas_rescued"], "not_flag": "tomas_home"},
             "once": True, "effects": [
                T("Old Berric the miller drops his sack of flour and runs across the square. He "
                  "crushes Tomas in a hug, then turns to you with wet eyes and a purse."),
                SAY("Berric", "I've no words. Take this, all of it. And... the lad says "
                              "there's something worse down there than goblins. If that "
                              "thing wakes fully, Millbrook won't last the winter."),
                {"do": "gold", "gp": 200},
                {"do": "xp", "amount": 300, "why": "Tomas rescued"},
                {"do": "flag", "name": "tomas_home"},
                {"do": "journal", "text": "Tomas is home. Something called the Ember King "
                                          "stirs in the deepest tomb under Ashen Hill."},
            ]},
            {"id": "return_crown", "label": "Present the Ember King's crown to the village",
             "requires": {"flag": "ember_king_dead"}, "once": True, "effects": [
                T("The whole village gathers as you hold up the blackened crown. Sister Elowen "
                  "blesses it and seals it in the shrine's reliquary forever."),
                {"do": "gold", "gp": 300},
                {"do": "xp", "amount": 600, "why": "The Ember King laid to rest"},
                {"do": "end_adventure"},
            ]},
            {"id": "rumors", "label": "Ask around the common room for rumors (Gather Information)",
             "effects": [{"do": "rumors"}]},
            {"id": "shop", "label": "Shop at Hollin's General Goods (gear, weapons, armor)",
             "effects": [{"do": "shop", "name": "Hollin's General Goods",
                          "sections": ["general", "weapons", "armor", "magic"]}]},
            {"id": "temple", "label": "Visit the Shrine of Pelor (healing, potions, cures)",
             "effects": [{"do": "temple"}]},
            {"id": "inn", "label": "Rent rooms at the Crooked Kettle and rest (5 sp each)",
             "effects": [{"do": "rest", "cost_sp": 5, "safe": True}]},
            {"id": "recruit", "label": "Recruit a new hero (replace the fallen or grow the party)",
             "effects": [{"do": "recruit"}]},
        ],
        "exits": {
            "east": {"to": "forest_road", "label": "Follow the Old Mill Road into the Thornwood",
                     "requires": {"flag": "quest"}},
        },
    },
    # ================================================================ wilderness
    "forest_road": {
        "name": "The Old Mill Road", "travel_minutes": 60, "wandering": False,
        "first": "The road narrows as the Thornwood closes in. Brambles snag your cloaks. The "
                 "birdsong stops a little too often.",
        "desc": "A rutted road through dense, thorny woods. Muddy prints and drag marks lead "
                "east. Millbrook lies back to the west.",
        "features": [
            {"id": "tracks", "label": "Study the tracks (Survival DC 12; Track feat needed)",
             "check": {"skill": "Survival", "dc": 12, "retry": False},
             "success": [
                T("Four or five small booted feet, goblin-sized, and one much larger set, "
                  "bare and clawed. Something heavy was dragged between them. They left the "
                  "road ahead to cut around the old stone bridge, then doubled back... "
                  "they're watching the bridge."),
                {"do": "flag", "name": "warned_ambush"},
                {"do": "xp", "amount": 25, "why": "good tracking"},
             ],
             "failure": [T("The ground is a muddle of prints. Goblins went east; that much is "
                           "obvious.")]},
            {"id": "listen", "label": "Stop and listen to the woods (Listen DC 15)",
             "check": {"skill": "Listen", "dc": 15, "who": "each", "need": "any",
                       "retry": False},
             "success": [T("Far ahead, near the river: a cackle, quickly hushed. Someone is "
                           "waiting by the bridge."), {"do": "flag", "name": "warned_ambush"}],
             "failure": [T("Wind in the thorns. Nothing else.")]},
        ],
        "exits": {
            "west": {"to": "millbrook", "label": "Back to Millbrook"},
            "east": {"to": "old_bridge", "label": "Continue east toward the river"},
        },
    },
    "old_bridge": {
        "name": "The Old Stone Bridge", "flee_to": "forest_road",
        "desc": "A mossy humpbacked bridge crosses the Silverrun. Tall reeds crowd the banks. "
                "Beyond the river, a bare hill rises: Ashen Hill, crowned with a ring of "
                "standing stones.",
        "encounters_enter": ["ambush"],
        "features": [
            {"id": "warned", "label": "(You were expecting this!)",
             "requires": {"flag": "warned_ambush", "not_flag": "enc:ambush"},
             "effects": []},
            {"id": "loot", "label": "Search the goblins' bodies",
             "requires": {"enc_cleared": "ambush"}, "once": True, "effects": [
                T("Crude pouches hold a few coins, and one goblin carries a scrap of hide "
                  "with a charcoal map: a hill, a door, and a crown drawn in red."),
                {"do": "gold", "gp": 9},
                {"do": "journal", "text": "A goblin map shows a door in Ashen Hill and a "
                                          "crown drawn in red."},
             ]},
        ],
        "exits": {
            "west": {"to": "forest_road", "label": "Back along the road"},
            "north": {"to": "barrow_hill", "label": "Cross the bridge and climb Ashen Hill",
                      "blocked_by": "ambush"},
        },
    },
    "barrow_hill": {
        "name": "Ashen Hill", "flee_to": "old_bridge",
        "first": "The grass on Ashen Hill is grey and brittle, as if a fire passed through "
                 "long ago and nothing ever grew right afterward. The standing stones are "
                 "carved with flames.",
        "desc": "Among the stones a dark doorway leads down into the hill. A goblin sentry "
                "sits beside it, chewing on something and not paying much attention.",
        "features": [
            {"id": "attack_sentry", "label": "Charge the sentry!",
             "requires": {"enc_active": "sentry"},
             "effects": [{"do": "fight", "enc": "sentry"}]},
            {"id": "sneak_sentry", "label": "Creep up on the sentry (Move Silently vs its Listen)",
             "requires": {"enc_active": "sentry"},
             "effects": [{"do": "stealth_fight", "enc": "sentry"}]},
            {"id": "scare_sentry", "label": "Scare the sentry off (Intimidate DC 12)",
             "requires": {"enc_active": "sentry"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Intimidate", "dc": 12},
             "success": [
                T("The goblin takes one look at you, squeals, and bolts... not into the hill, "
                  "but down the slope toward the river. It won't be back."),
                {"do": "resolve_enc", "enc": "sentry"},
             ],
             "failure": [
                T("The goblin cackles, then dives through the doorway yelling a warning!"),
                {"do": "resolve_enc", "enc": "sentry", "xp": False},
                {"do": "flag", "name": "alarm"},
                {"do": "add_monster", "enc": "guards", "key": "goblin", "room": "guard_room"},
             ]},
            {"id": "stones", "label": "Study the carvings on the standing stones "
                                      "(Knowledge (history) DC 12)",
             "check": {"skill": "Knowledge (history)", "dc": 12, "retry": False},
             "success": [T("These are the grave-markers of King Aurek, called the Ember King, "
                           "a fire-worshipping warlord who ruled here before Millbrook "
                           "existed. Legend says he wanted to burn forever, and his priests "
                           "obliged."),
                         {"do": "journal", "text": "The barrow belongs to Aurek, the Ember "
                                                   "King, a fire-worshipping warlord."}],
             "failure": [T("Old flames, old kings. The details escape you.")]},
        ],
        "exits": {
            "south": {"to": "old_bridge", "label": "Back down to the bridge"},
            "down": {"to": "entry", "label": "Descend into the barrow",
                     "blocked_by": "sentry",
                     "blocked_text": "Deal with the sentry first."},
        },
    },
    # ================================================================ upper barrow
    "entry": {
        "name": "The Collapsed Antechamber", "flee_to": "barrow_hill",
        "first": "Stale, warm air rolls up the steps. The walls are blackened with ancient "
                 "soot, though no fire has burned here in centuries.",
        "desc": "A long hall of fitted stone, half collapsed. Goblin rubbish is everywhere. A "
                "passage continues north; a dripping archway opens to the east. In the middle "
                "of the north passage the flagstones look oddly clean.",
        "traps": {
            "pit": {"name": "Pit trap", "search_dc": 20, "disable_dc": 20, "stone": True,
                    "xp": 50, "found_text": "A 10-foot pit hidden under a pivoting flagstone.",
                    "trigger_text": "A flagstone tips under your boots!",
                    "bypass": {"skill": "Jump", "dc": 10},
                    "bypass_label": "Jump across the 5-foot gap (Jump DC 10 each)",
                    "effects": [{"do": "damage", "dice": "1d6", "who": "actor",
                                 "save": ["ref", 20, "negates"], "tags": ["trap"]}]},
        },
        "features": [],
        "exits": {
            "up": {"to": "barrow_hill", "label": "Climb back out to Ashen Hill"},
            "north": {"to": "guard_room", "label": "North along the clean-floored passage",
                      "trap": "pit"},
            "east": {"to": "cistern", "label": "Through the dripping archway"},
        },
    },
    "cistern": {
        "name": "The Old Cistern", "flee_to": "entry",
        "desc": "A round chamber around a deep pool of black water. The smell of rat is "
                "overpowering. Something glints at the bottom of the pool.",
        "encounters_enter": ["rats"],
        "features": [
            {"id": "dive", "label": "Dive for the glint at the bottom of the pool (Swim DC 10)",
             "requires": {"enc_cleared": "rats"},
             "check": {"skill": "Swim", "dc": 10, "take10_ok": True},
             "success": [T("Cold, black, deep, and then your fingers close on a slim "
                           "bottle and a silver chain."),
                         {"do": "item", "id": "potion of cure light wounds", "to_actor": True},
                         {"do": "item", "id": "silver holy symbol", "to_actor": True}],
             "failure": [T("The water closes over your head and your armor drags you down. "
                           "You come up coughing, empty-handed."),
                         {"do": "damage", "dice": "1d3", "who": "actor"}]},
        ],
        "exits": {"west": {"to": "entry", "label": "Back to the antechamber"}},
    },
    "guard_room": {
        "name": "The Guard Room", "flee_to": "entry",
        "desc": "A square room with a goblin cookfire, gnawed bones, and an iron-bound chest "
                "against the wall. Doors lead west and north.",
        "encounters_enter": ["guards"],
        "features": [
            {"id": "chest_lock", "label": "Open the iron-bound chest (Open Lock DC 15)",
             "requires": {"enc_cleared": "guards", "not_flag": "chest_open"},
             "check": {"skill": "Open Lock", "dc": 15, "take10_ok": True},
             "success": [T("The lock clicks open."), {"do": "flag", "name": "chest_open"},
                         {"do": "gold", "gp": 35},
                         {"do": "item", "id": "potion of cure light wounds"},
                         {"do": "item", "id": "alchemist's fire", "qty": 2}],
             "failure": [T("The lock is stiff with rust. You can try again.")]},
            {"id": "chest_smash", "label": "Smash the chest open (Strength DC 17)",
             "requires": {"enc_cleared": "guards", "not_flag": "chest_open"},
             "check": {"skill": "ability:str", "dc": 17},
             "success": [T("The hinges burst. Inside, one flask has shattered, but the rest "
                           "is fine."), {"do": "flag", "name": "chest_open"},
                         {"do": "gold", "gp": 35},
                         {"do": "item", "id": "potion of cure light wounds"},
                         {"do": "item", "id": "alchemist's fire", "qty": 1}],
             "failure": [T("You bruise your shoulder. The chest is unimpressed.")]},
        ],
        "exits": {
            "south": {"to": "entry", "label": "Back to the antechamber"},
            "west": {"to": "crypt", "label": "A cold draft from the west door"},
            "north": {"to": "barracks", "label": "Goblin voices beyond the north door"},
        },
    },
    "crypt": {
        "name": "The Crypt of the Honor Guard", "flee_to": "guard_room",
        "first": "Rows of burial niches line the walls. Each holds a skeleton in the rags of "
                 "a red tabard, a rusted blade across its chest.",
        "desc": "A long, cold crypt. Faded murals show a crowned man standing in fire while "
                "warriors kneel. A narrow stair at the north end climbs to a shrine.",
        "encounters_enter": ["skeletons"],
        "features": [
            {"id": "mural", "label": "Read the murals' inscriptions (Decipher Script or "
                                     "Knowledge (religion) DC 13)",
             "check": {"skill": "Knowledge (religion)", "dc": 13, "retry": False},
             "success": [T("'Here kneel those who fed the King's flame. The King hungers, and "
                           "is fed, and is never full.' A prayer, or a warning."),
                         {"do": "journal", "text": "Inscription: 'The King hungers, and is "
                                                   "fed, and is never full.'"}],
             "failure": [T("Archaic script. You make out the word 'flame' a lot.")]},
            {"id": "niches", "label": "Search the burial niches for grave goods",
             "requires": {"enc_cleared": "skeletons"}, "once": True, "effects": [
                T("Most of the grave goods are rust, but one niche holds a well-oiled "
                  "warhammer of fine dwarven make and a pouch of old coins."),
                {"do": "item", "id": "masterwork warhammer"},
                {"do": "gold", "gp": 22},
             ]},
        ],
        "exits": {
            "east": {"to": "guard_room", "label": "Back to the guard room"},
            "north": {"to": "shrine", "label": "Up the narrow stair to the shrine"},
        },
    },
    "shrine": {
        "name": "The Shrine of the Flame", "flee_to": "crypt",
        "desc": "A small domed shrine. A basalt altar holds a bowl of cold ash. The east wall "
                "is a single slab of stone carved with a great flame and a line of verse.",
        "features": [
            {"id": "altar", "label": "Examine the altar (Knowledge (religion) DC 12)",
             "check": {"skill": "Knowledge (religion)", "dc": 12, "retry": False},
             "success": [T("The ash bowl was for offerings to a fire god of conquest. Whoever "
                           "consecrated this place meant the fire to protect the King's "
                           "servants. A brief prayer to any good god might turn that warmth "
                           "to your side."),
                         {"do": "flag", "name": "altar_known"}],
             "failure": [T("An old altar. It feels warm to the touch, which is odd.")]},
            {"id": "pray", "label": "Pray at the altar for protection",
             "requires": {"flag": "altar_known"}, "once": True, "effects": [
                T("The ash in the bowl glows briefly and goes out. A gentle warmth settles "
                  "over you."),
                {"do": "buff", "name": "Warmth of the Old Altar", "duration": 6000,
                 "mods": [["resist_fire", "resistance", 5], ["saves", "sacred", 1]]},
            ]},
            {"id": "riddle", "label": "Read the verse on the carved east wall",
             "requires": {"not_flag": "riddle_solved"}, "effects": [
                {"do": "riddle",
                 "riddle": "Carved beneath the flame: 'Feed me and I live, give me drink and I "
                           "die. I am ever hungry and never full. Name me, and pass.'",
                 "answers": ["fire", "flame", "flames", "ember", "embers", "a fire"],
                 "success": [T("The carved flame flares with real light and the slab grinds "
                               "aside, revealing a hidden treasury."),
                             {"do": "flag", "name": "riddle_solved"},
                             {"do": "reveal_exit", "exit": "east"},
                             {"do": "xp", "amount": 100, "why": "riddle solved"}],
                 "failure": [T("The carved flame spits a gout of real fire!"),
                             {"do": "damage", "dice": "1d6", "dtype": "fire", "who": "actor",
                              "save": ["ref", 12, "half"]}]},
             ]},
        ],
        "exits": {
            "south": {"to": "crypt", "label": "Down to the crypt"},
            "east": {"to": "treasury", "label": "Into the hidden treasury",
                     "hidden": {"found_text": "a hidden door"}},
        },
    },
    "treasury": {
        "name": "The Hidden Treasury", "flee_to": "shrine",
        "desc": "A tiny vault, untouched for centuries. A small bronze-bound coffer sits on a "
                "plinth.",
        "traps": {
            "needle": {"name": "Poison needle trap", "search_dc": 22, "disable_dc": 20,
                       "xp": 50, "found_text": "A tiny needle hidden in the coffer's latch.",
                       "trigger_text": "A needle jabs your finger!", "one_shot": True,
                       "effects": [{"do": "ability_damage", "ability": "con", "dice": "1d2",
                                    "save": ["fort", 13], "tags": ["poison"]}]},
        },
        "features": [
            {"id": "coffer", "label": "Open the coffer", "once": True,
             "effects": [{"do": "custom", "fn": "open_coffer"}]},
        ],
        "exits": {"west": {"to": "shrine", "label": "Back to the shrine"}},
    },
    "barracks": {
        "name": "The Goblin Barracks", "flee_to": "guard_room",
        "desc": "Filthy bunks of straw and stolen blankets. A heavy iron door stands in the "
                "east wall; a stench of animal comes from an opening to the north.",
        "encounters_enter": ["barracks"],
        "features": [
            {"id": "bunks", "label": "Search the bunks", "requires": {"enc_cleared": "barracks"},
             "once": True, "effects": [
                T("Under the sergeant's bunk: a pouch of coins, a scroll in a bone case, and "
                  "a heavy iron key stamped with a flame."),
                {"do": "gold", "gp": 18},
                {"do": "item", "id": "scroll of cure light wounds"},
                {"do": "item", "id": "iron key"},
             ]},
        ],
        "exits": {
            "south": {"to": "guard_room", "label": "Back to the guard room"},
            "north": {"to": "kennel", "label": "Toward the animal stench"},
            "east": {"to": "lower_stairs", "label": "The heavy iron door",
                     "lock": {"key": "iron key", "open_dc": 20, "break_dc": 23,
                              "text": "The iron door is locked."}},
        },
    },
    "kennel": {
        "name": "The Kennel", "flee_to": "barracks",
        "desc": "Gnawed bones and a heavy chain bolted to the wall. A big grey wolf, ribs "
                "showing, growls low in its throat.",
        "features": [
            {"id": "fight_wolf", "label": "Fight the wolf", "requires": {"enc_active": "wolf"},
             "effects": [{"do": "fight", "enc": "wolf"}]},
            {"id": "feed_wolf", "label": "Toss it some food and calm it (Handle Animal DC 12; "
                                         "untrained heroes use Charisma)",
             "requires": {"enc_active": "wolf"}, "once_on_fail": True,
             "check": {"skill": "Handle Animal", "dc": 12, "retry": False},
             "success": [T("The wolf wolfs down the food (of course), then flops onto its "
                           "side and watches you without malice. Someone's been starving it."),
                         {"do": "resolve_enc", "enc": "wolf"}],
             "failure": [T("The wolf snaps at your hand and lunges!"),
                         {"do": "fight", "enc": "wolf"}]},
            {"id": "empathy_wolf", "label": "Calm it with wild empathy (ranger: d20 + level + Cha "
                                            "vs 15)",
             "requires": {"enc_active": "wolf", "class": "ranger"}, "once_on_fail": True,
             "check": {"skill": "Wild Empathy", "dc": 15, "retry": False},
             "success": [T("You crouch, speak softly, and hold out a hand. The wolf sniffs it, "
                           "then lowers its head. You slip the chain from its collar and it "
                           "pads off into the dark, free."),
                         {"do": "resolve_enc", "enc": "wolf"}],
             "failure": [T("It's too wild with hunger to trust you."),
                         {"do": "fight", "enc": "wolf"}]},
        ],
        "exits": {"south": {"to": "barracks", "label": "Back to the barracks"}},
    },
    # ================================================================ lower barrow
    "lower_stairs": {
        "name": "The Burning Stair", "flee_to": "barracks",
        "first": "Beyond the iron door, a stair spirals down into a warmth that grows with "
                 "every step. The stone walls are faintly warm to the touch, like a hearth "
                 "an hour after the fire's gone out.",
        "desc": "A spiral stair between the goblin level above and the deep halls below.",
        "features": [],
        "exits": {
            "up": {"to": "barracks", "label": "Up to the barracks"},
            "down": {"to": "lower_hall", "label": "Down into the deep halls"},
        },
    },
    "lower_hall": {
        "name": "The Hall of Servants", "flee_to": "lower_stairs",
        "desc": "A pillared hall where dozens of robed corpses stand in alcoves, as if waiting "
                "to serve. To the north, firelight and goblin laughter. To the east, a pair of "
                "bronze doors marked with a crowned flame.",
        "encounters_enter": ["zombies"],
        "features": [],
        "exits": {
            "up": {"to": "lower_stairs", "label": "Back up the stair"},
            "north": {"to": "warren", "label": "Toward the firelight and voices"},
            "east": {"to": "antechamber", "label": "The bronze doors of the crowned flame",
                     "lock": {"key": "ember sigil",
                              "text": "The bronze doors have no handle, only a round, "
                                      "disc-shaped recess bearing a flame. No lock to pick; "
                                      "no hinge to force."}},
        },
    },
    "warren": {
        "name": "Grukk's Warren", "flee_to": "lower_hall",
        "desc": "A cave crammed with stolen sacks, barrels and chicken bones. A crude throne "
                "of grain sacks stands at the back. A young man in a miller's apron is tied "
                "to a post, gagged and wide-eyed.",
        "features": [
            {"id": "fight_grukk", "label": "Attack!", "requires": {"enc_active": "warren"},
             "effects": [{"do": "fight", "enc": "warren"}]},
            {"id": "intimidate_grukk", "label": "Demand Tomas's release (Intimidate DC 18)",
             "requires": {"enc_active": "warren"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Intimidate", "dc": 18},
             "success": [
                T("Your voice cracks across the cave like a whip. The goblin at Grukk's side "
                  "loses its nerve and flees screaming. Grukk snarls, alone now."),
                {"do": "remove_monster", "enc": "warren", "count": 1, "room": "warren"},
                {"do": "fight", "enc": "warren"},
             ],
             "failure": [T("Grukk laughs, a deep, ugly sound. 'Brave meat.'"),
                         {"do": "fight", "enc": "warren"}]},
            {"id": "parley", "label": "Try to bargain with Grukk (Diplomacy DC 20)",
             "requires": {"enc_active": "warren"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Diplomacy", "dc": 20},
             "success": [
                SAY("Grukk", "Hrm. Grukk only takes the boy because the Burning One wants "
                             "warm blood. Grukk does not like the Burning One. You go kill it, "
                             "Grukk takes the treasure. Boy is yours."),
                T("Grukk cuts Tomas loose and shoves him at you, then tosses you a warm "
                  "bronze disc. 'Opens the king's door.' He and his goblins slip away into "
                  "the dark."),
                {"do": "resolve_enc", "enc": "warren", "factor": 1.0},
                {"do": "flag", "name": "grukk_parley"},
                {"do": "item", "id": "ember sigil"},
                {"do": "custom", "fn": "free_tomas"},
             ],
             "failure": [T("'Grukk does not bargain with food.'"),
                         {"do": "fight", "enc": "warren"}]},
            {"id": "loot_grukk", "label": "Search Grukk's throne",
             "requires": {"enc_cleared": "warren", "not_flag": "grukk_parley"}, "once": True,
             "effects": [
                T("Among the stolen junk: a heavy purse, a potion, and a warm bronze disc "
                  "stamped with a crowned flame, hanging on a thong."),
                {"do": "gold", "gp": 64},
                {"do": "item", "id": "potion of cure light wounds"},
                {"do": "item", "id": "ember sigil"},
             ]},
            {"id": "free", "label": "Untie Tomas",
             "requires": {"enc_cleared": "warren", "not_flag": "tomas_rescued"},
             "effects": [{"do": "custom", "fn": "free_tomas"}]},
        ],
        "exits": {"south": {"to": "lower_hall", "label": "Back to the Hall of Servants"}},
    },
    "antechamber": {
        "name": "The King's Antechamber", "flee_to": "lower_hall",
        "desc": "Heat shimmers above the floor. Bones are scattered everywhere, cracked open "
                "for the marrow. A great archway glows dull red to the east.",
        "encounters_enter": ["antechamber"],
        "secrets": [
            {"id": "alcove", "search_dc": 18, "effects": [
                T("Behind a loose stone: a hidden alcove holding a grey cloak that never "
                  "seems to get dusty, and a handful of rubies."),
                {"do": "item", "id": "cloak of resistance +1"},
                {"do": "gold", "gp": 75},
            ]},
        ],
        "features": [],
        "exits": {
            "west": {"to": "lower_hall", "label": "Back through the bronze doors"},
            "east": {"to": "tomb", "label": "Through the glowing archway: the King's tomb",
                     "blocked_by": "antechamber"},
        },
    },
    "tomb": {
        "name": "The Tomb of the Ember King", "flee_to": "antechamber", "no_rest": True,
        "no_rest_text": "Not here. Not with that heat on your face.",
        "desc": "A round chamber lit by a pit of coals that never die. On a throne of black "
                "iron sits a crowned corpse, its ribs glowing like a forge.",
        "encounters_enter": ["ember_king"],
        "features": [
            {"id": "crown", "label": "Take the Ember King's crown",
             "requires": {"enc_cleared": "ember_king"}, "once": True, "effects": [
                T("The crown is blackened iron set with dull red stones. As you lift it, the "
                  "coals in the pit sigh and go grey for the first time in a thousand years."),
                {"do": "flag", "name": "ember_king_dead"},
                {"do": "gold", "gp": 150},
                {"do": "item", "id": "+1 longsword"},
                {"do": "item", "id": "ring of protection +1"},
                {"do": "journal", "text": "The Ember King is destroyed. Take the crown back "
                                          "to Millbrook."},
             ]},
        ],
        "exits": {"west": {"to": "antechamber", "label": "Back to the antechamber"}},
    },
}


# ---------------------------------------------------------------- custom scripted bits
def open_coffer(gm, actor, eff):
    st = gm.gs.rs()
    if "needle" not in st["disabled_traps"]:
        if "needle" in st["found_traps"]:
            i = gm.ui.choose("You know there's a poison needle in the latch.",
                             ["Try to disable it first (Disable Device DC 20)",
                              "Open it anyway (risk the needle)", "Leave it for now"])
            if i == 0:
                gm.disable_trap("needle")
            if i == 2 or (i == 0 and "needle" not in st["disabled_traps"]):
                st["used"].remove("coffer")
                return
        if "needle" not in st["disabled_traps"]:
            victim = gm.pick_hero("Who opens the coffer?") or gm.gs.able()[0]
            gm.trigger_trap("needle", victim)
    gm.run([T("Inside, on faded velvet: a pouch of gems, a scroll, and a vial of thick red "
              "liquid."),
            {"do": "gold", "gp": 120},
            {"do": "item", "id": "scroll of sleep"},
            {"do": "item", "id": "potion of bull's strength"}])


def free_tomas(gm, actor, eff):
    if "tomas_rescued" in gm.gs.flags:
        return
    gm.gs.flags.add("tomas_rescued")
    gm.run([
        T("You cut Tomas free. He's bruised and shaking but unhurt."),
        SAY("Tomas", "They were going to give me to it. The thing behind the bronze doors. "
                     "The goblins call it the Burning One. It talks in your head... it wants "
                     "to be fed. Please, just get me home."),
        {"do": "journal", "text": "Tomas rescued! Bring him back to Millbrook. Beyond the "
                                  "bronze doors waits the 'Burning One'."},
        {"do": "xp", "amount": 50, "why": "Tomas freed"},
    ])
