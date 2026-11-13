"""THE DROWNED LANTERN
An original adventure for 1-4 heroes of 1st-3rd level.

The lighthouse above the fishing village of Saltmere has gone dark, and ships
keep breaking on the Teeth. Kobold wreckers are luring them in, but someone
with a ledger and a ship of her own is paying them.
"""

ID = "drowned_lantern"
TITLE = "The Drowned Lantern"
LEVELS = "1-3"
START_LEVEL = 1
SUMMARY = ("A dark lighthouse, wrecked ships, kobold wreckers and the smugglers who pay "
           "them. Sea caves, a sunken wreck, and a captain with a secret.")
START = "saltmere"
REST_ENCOUNTER_CHANCE = 0.25
TEMPLE_NAME = "Chapel of the Tides"
TEMPLE_GREETING = ("Mother Wenna, keeper of the Chapel of the Tides, wrings out her sleeves. "
                   "'The sea gives and the sea takes. What do you need, dears?'")

INTRO = """
Saltmere clings to the bottom of a cliff like a barnacle: thirty stone cottages, a
tarred wooden pier, and a smell of fish that never quite leaves your clothes.

Above it, on the headland, stands the Lantern, the lighthouse that has guided
boats past the reef called the Teeth for a hundred years. Nine nights ago it went
dark. Since then, three ships have broken on the rocks. Their cargo never washes
ashore. Their crews do, eventually.

You came to Saltmere for a bed and a hot meal. The harbormaster found you first.
"""

ENDING = """
The Lantern burns again over the Teeth, and the first ship to round the headland
blows its horn three times in thanks. In the Gull & Anchor, the fishermen of
Saltmere stand you drinks until the barrels run dry, and Bram's empty office is
handed to someone who can count honestly.

Captain Merrow's ledger goes north to the magistrates. Some of the names in it
are very important people. That, as they say, is another story.

THE END (for now).
"""

RUMORS = [
    (5, "The lighthouse keeper, old Corwin, hasn't come down to the village since the "
        "light went out. Nobody's been brave enough to climb up and check."),
    (10, "Kobolds! Little scaly dog-things. Pip the net-mender saw a dozen on the cliff "
         "path with lanterns on poles, the night the Silver Gannet sank."),
    (10, "There's a ship anchored behind Gull Rock that never comes into harbor. Black "
         "sails. Comes and goes at night."),
    (15, "The old smugglers' stair goes down the cliff from the lighthouse yard to a cove. "
         "Grandfather said there were caves under the whole headland."),
    (15, "Bram the harbormaster bought his wife a silver necklace last week. On a "
         "harbormaster's pay? Hmph."),
    (20, "The sea caves have spiders in them, big as dogs. Their bite saps your strength. "
         "Antitoxin from the chapel helps."),
]

WANDERING = [
    {"text": "Scrabbling claws and wet whiskers: dire rats from the cliff burrows!",
     "monsters": ["dire rat", "dire rat"]},
    {"text": "A kobold patrol with a hooded lantern stumbles onto you!",
     "monsters": ["kobold", "kobold", "kobold"], "requires": {"not_flag": "enc:yard"}},
    {"text": "The floor ahead ripples: a squealing tide of rats pours out of the cracks!",
     "monsters": ["rat swarm"]},
    {"text": "Something big skitters down the wall toward you...",
     "monsters": ["monstrous spider"]},
]

ENCOUNTERS = {
    "yard": {"room": "lighthouse_yard", "monsters": ["kobold", "kobold", "kobold"],
             "per_extra_hero": ["kobold"], "ambush": True,
             "ambush_text": "Little lanterns wink out among the rocks as you step into the yard.",
             "text": "Kobolds pour out of hiding, yipping, spears and slings ready!",
             "title": "KOBOLD WRECKERS"},
    "cellar": {"room": "cellar", "monsters": ["dire rat", "dire rat"],
               "per_extra_hero": ["dire rat"], "title": "THE CELLAR",
               "text": "The sacks of flour aren't the only thing down here that's been eaten."},
    "lamp": {"room": "lamp_room", "monsters": ["smuggler", "kobold"],
             "per_extra_hero": ["kobold"], "title": "THE LAMP ROOM",
             "text": "A man in a tarred coat and a kobold with a crossbow guard the great "
                     "lens, which is wrapped in black sailcloth."},
    "cove": {"room": "cove", "monsters": ["smuggler", "smuggler"],
             "per_extra_hero": ["kobold"], "title": "SMUGGLERS' COVE",
             "text": "Two smugglers loading a longboat drop their crates and reach for weapons."},
    "spiders": {"room": "sea_caves", "monsters": ["monstrous spider"],
                "per_extra_hero": ["dire rat"], "title": "THE WEBBED CAVE",
                "ambush": True, "ambush_text": "Strands of web brush your face in the dark...",
                "text": "A giant spider drops from the ceiling!"},
    "drowned": {"room": "wreck_grotto", "monsters": ["human zombie", "human skeleton"],
                "per_extra_hero": ["human skeleton"], "title": "THE DROWNED CREW",
                "text": "The sailors of the Silver Gannet rise from the water, still wearing "
                        "their sea boots."},
    "captain": {"room": "captains_den", "monsters": ["captain merrow", "smuggler"],
                "per_extra_hero": ["smuggler"], "title": "CAPTAIN ILSA MERROW",
                "can_flee": True,
                "text": "'You've cost me three cargoes and a very expensive lighthouse "
                        "keeper,' Merrow says pleasantly. 'Let's settle the bill.'"},
}


def T(text):
    return {"do": "text", "text": text}


def SAY(who, text):
    return {"do": "say", "who": who, "text": text}


ROOMS = {
    # ================================================================ village
    "saltmere": {
        "name": "Saltmere", "town": True, "wandering": False,
        "desc": "A cluster of cottages under the cliff, the tarred pier, the Gull & Anchor "
                "tavern, Ned's Chandlery, and the little Chapel of the Tides. A switchback "
                "path climbs the cliff north to the dark lighthouse.",
        "features": [
            {"id": "bram", "label": "Talk to Bram, the harbormaster",
             "requires": {"not_flag": "quest"}, "once": True, "effects": [
                SAY("Bram", "You've weapons and you're not from here, which makes you the "
                            "best offer I've had all week. The Lantern's dark. Ships are "
                            "dying on the Teeth. Somebody needs to go up there, find out "
                            "what happened to Corwin, and light that lamp."),
                SAY("Bram", "Saltmere will pay a hundred and fifty gold, all of it. Here, "
                            "the chapel sent these up. Mother Wenna says you'll need them."),
                {"do": "items_each", "id": "potion of cure light wounds", "qty": 1},
                {"do": "flag", "name": "quest"},
                {"do": "journal", "text": "Quest: relight the Lantern and learn why it went "
                                          "dark (150 gp)."},
             ]},
            {"id": "bram2", "label": "Talk to Bram again",
             "requires": {"flag": "quest", "not_flag": "ledger"}, "effects": [
                SAY("Bram", "Still here? The path's just north. Mind the Teeth."),
             ]},
            {"id": "confront", "label": "Confront Bram with Captain Merrow's ledger",
             "requires": {"flag": "ledger", "not_flag": "bram_done"}, "once": True,
             "check": {"skill": "Intimidate", "dc": 12, "bonus": 4,
                       "prompt": "Who confronts him? (Intimidate DC 12, +4 for the evidence)"},
             "success": [
                T("Bram looks at the ledger, at his own name in Merrow's neat handwriting, and "
                  "goes grey. He confesses everything: he told Merrow which ships carried "
                  "silver, and she paid the kobolds to darken the light."),
                SAY("Bram", "I never meant for anyone to die. I swear it."),
                T("The village elders lock him in the net-house to await the magistrate. "
                  "They press Bram's own strongbox on you as the promised reward."),
                {"do": "flag", "name": "bram_done"},
                {"do": "gold", "gp": 250},
                {"do": "xp", "amount": 300, "why": "traitor unmasked"},
             ],
             "failure": [
                T("Bram blusters, then bolts out the back door and runs straight into a crowd "
                  "of very angry fishermen who saw the ledger over your shoulder. That settles "
                  "that."),
                {"do": "flag", "name": "bram_done"},
                {"do": "gold", "gp": 150},
                {"do": "xp", "amount": 150, "why": "traitor caught"},
             ]},
            {"id": "finish", "label": "Report to the village: the Lantern burns again",
             "requires": {"flags": ["lantern_lit", "enc:captain"]}, "once": True,
             "effects": [
                T("The whole village turns out on the pier as the great beam sweeps the "
                  "water."),
                {"do": "gold", "gp": 150},
                {"do": "xp", "amount": 400, "why": "the Lantern relit and the wreckers "
                                                   "broken"},
                {"do": "end_adventure"},
             ]},
            {"id": "rumors", "label": "Ask around the Gull & Anchor for rumors "
                                      "(Gather Information)",
             "effects": [{"do": "rumors"}]},
            {"id": "shop", "label": "Shop at Ned's Chandlery (gear, weapons, armor)",
             "effects": [{"do": "shop", "name": "Ned's Chandlery",
                          "sections": ["general", "weapons", "armor", "magic"]}]},
            {"id": "temple", "label": "Visit the Chapel of the Tides (healing, potions, cures)",
             "effects": [{"do": "temple"}]},
            {"id": "inn", "label": "Rent rooms at the Gull & Anchor and rest (5 sp each)",
             "effects": [{"do": "rest", "cost_sp": 5, "safe": True}]},
            {"id": "recruit", "label": "Recruit a new hero (replace the fallen or grow the party)",
             "effects": [{"do": "recruit"}]},
        ],
        "exits": {
            "north": {"to": "cliff_path", "label": "Climb the cliff path toward the Lantern",
                      "requires": {"flag": "quest"}},
        },
    },
    # ================================================================ the headland
    "cliff_path": {
        "name": "The Cliff Path", "travel_minutes": 30, "wandering": False,
        "first": "The path switchbacks up the cliff face, slick with spray. Far below, the "
                 "Teeth froth white.",
        "desc": "A narrow path halfway up the cliff. Gulls wheel overhead. Above, the "
                "lighthouse yard; below, Saltmere's roofs.",
        "features": [
            {"id": "watch", "label": "Watch the headland for movement (Spot DC 14)",
             "check": {"skill": "Spot", "dc": 14, "who": "each", "need": "any",
                       "retry": False},
             "success": [T("Among the rocks at the top: a glint of a hooded lantern, quickly "
                           "covered. Someone small is waiting in the yard."),
                         {"do": "flag", "name": "warned_yard"},
                         {"do": "xp", "amount": 25, "why": "sharp eyes"}],
             "failure": [T("Just gulls and spray.")]},
            {"id": "wreck_beach", "label": "Look down at the wreck on the Teeth",
             "once": True, "effects": [
                T("The broken hull of the Silver Gannet sits on the rocks. Strange: no "
                  "cargo, no crates, no barrels anywhere on the shore. Someone salvaged it, "
                  "fast and quietly."),
                {"do": "journal", "text": "The Silver Gannet's cargo was taken before it "
                                          "could wash ashore."}]},
        ],
        "exits": {
            "south": {"to": "saltmere", "label": "Back down to Saltmere"},
            "north": {"to": "lighthouse_yard", "label": "Up to the lighthouse yard"},
        },
    },
    "lighthouse_yard": {
        "name": "The Lighthouse Yard", "flee_to": "cliff_path",
        "first": "The Lantern towers over a walled yard of wind-bent grass. The tower door is "
                 "shut. At the cliff edge, worn steps lead down toward the sea.",
        "desc": "The lighthouse yard: the stone tower, a keeper's shed, and the old "
                "smugglers' stair down the cliff to the east.",
        "encounters_enter": ["yard"],
        "features": [
            {"id": "shed", "label": "Search the keeper's shed",
             "requires": {"enc_cleared": "yard"}, "once": True, "effects": [
                T("The shed is ransacked. Under an overturned bench you find a flask of lamp "
                  "oil, a coil of rope, and old Corwin's spare key on a nail."),
                {"do": "item", "id": "oil"},
                {"do": "item", "id": "rope"},
                {"do": "item", "id": "lighthouse key", "to_actor": True},
             ]},
            {"id": "kobold_loot", "label": "Search the kobolds",
             "requires": {"enc_cleared": "yard"}, "once": True, "effects": [
                T("Copper bits, a few silver coins with a stranger's mint mark, and a crude "
                  "drawing of a black-sailed ship."),
                {"do": "gold", "gp": 12},
             ]},
        ],
        "exits": {
            "south": {"to": "cliff_path", "label": "Back down the cliff path"},
            "in": {"to": "lighthouse_base", "label": "The lighthouse door",
                   "blocked_by": "yard",
                   "lock": {"key": "lighthouse key", "open_dc": 15, "break_dc": 18,
                            "text": "The heavy door is locked."}},
            "down": {"to": "cove", "label": "The smugglers' stair down the cliff",
                     "blocked_by": "yard", "trap": "loose_steps"},
        },
        "traps": {
            "loose_steps": {"name": "crumbling steps", "search_dc": 15, "disable_dc": 15,
                            "stone": True, "found_text": "Several of the old steps are cracked "
                            "through; one good stomp and they'll fall.",
                            "trigger_text": "A step crumbles under your boot!",
                            "bypass": {"skill": "Climb", "dc": 10},
                            "bypass_label": "Climb down beside the broken steps (Climb DC 10 "
                                            "each)",
                            "effects": [{"do": "damage", "dice": "2d6", "who": "actor",
                                         "save": ["ref", 15, "half"], "tags": ["trap"]}]},
        },
    },
    "lighthouse_base": {
        "name": "Inside the Lantern", "flee_to": "lighthouse_yard",
        "desc": "The ground floor of the tower: the keeper's cot, a cold stove, and a spiral "
                "stair winding up into the dark. Crates are stacked against one wall, "
                "stamped with the mark of the Silver Gannet.",
        "features": [
            {"id": "crates", "label": "Examine the crates (Appraise DC 12)",
             "check": {"skill": "Appraise", "dc": 12, "retry": False},
             "success": [T("Silver plate, wrapped in oilcloth: the Gannet's cargo, worth "
                           "thousands. Someone meant to collect it from here."),
                         {"do": "journal", "text": "The wrecked ships' cargo is hidden in the "
                                                   "lighthouse."},
                         {"do": "xp", "amount": 25, "why": "careful eye"}],
             "failure": [T("Lots of heavy crates. Probably valuable.")]},
            {"id": "corwin_log", "label": "Read the keeper's logbook on the table",
             "once": True, "effects": [
                T("Corwin's last entry is shaky: 'The harbormaster sent word a ship's captain "
                  "wants to pay me to let the light go dark one night. I said no. Told Bram "
                  "I'd tell the magistrate. Someone's coming up the path. Small. Lots of "
                  "them...'"),
                {"do": "journal", "text": "Corwin's log: a captain offered him money to darken "
                                          "the light, through Bram."}]},
        ],
        "secrets": [
            {"id": "trapdoor", "search_dc": 15, "effects": [
                T("Under the cot, a trapdoor! Damp air rises from below."),
                {"do": "reveal_exit", "exit": "down"}]},
        ],
        "exits": {
            "out": {"to": "lighthouse_yard", "label": "Out to the yard"},
            "up": {"to": "lamp_room", "label": "Climb the spiral stair"},
            "down": {"to": "cellar", "label": "Through the trapdoor",
                     "hidden": {"search_dc": 15, "found_text": "a trapdoor under the cot"}},
        },
    },
    "lamp_room": {
        "name": "The Lamp Room", "flee_to": "lighthouse_base",
        "desc": "The top of the tower: a great glass lens like a giant's eye, its oil "
                "reservoir and wick-mechanism beside it. The wind howls around the gallery.",
        "encounters_enter": ["lamp"],
        "features": [
            {"id": "relight", "label": "Relight the Lantern",
             "requires": {"enc_cleared": "lamp", "not_flag": "lantern_lit"},
             "check": {"skill": "Knowledge (architecture and engineering)", "dc": 10,
                       "bonus": 0, "take10_ok": True,
                       "prompt": "Who repairs the mechanism? (Knowledge (architecture and "
                                 "engineering) DC 10; or anyone with the Disable Device "
                                 "trick of reversing it)"},
             "success": [
                T("The wreckers jammed the wick-feed and fouled the oil. You clear it, fill "
                  "the reservoir, strike a light... and the Lantern blazes. Its beam sweeps "
                  "out over the Teeth for the first time in nine nights."),
                {"do": "flag", "name": "lantern_lit"},
                {"do": "xp", "amount": 200, "why": "the Lantern relit"},
                {"do": "journal", "text": "The Lantern is lit! Now find whoever paid the "
                                          "wreckers."}],
             "failure": [T("The mechanism is jammed in some way you can't see. Maybe someone "
                           "else can work it out, or fiddle with it (Disable Device)...")]},
            {"id": "relight2", "label": "Fiddle the jammed mechanism free (Disable Device DC 12)",
             "requires": {"enc_cleared": "lamp", "not_flag": "lantern_lit"},
             "check": {"skill": "Disable Device", "dc": 12, "take10_ok": True},
             "success": [
                T("A jammed pawl, a wedge of driftwood, a snapped spring: fixed. The "
                  "Lantern roars into life and its beam sweeps the sea."),
                {"do": "flag", "name": "lantern_lit"},
                {"do": "xp", "amount": 200, "why": "the Lantern relit"},
                {"do": "journal", "text": "The Lantern is lit! Now find whoever paid the "
                                          "wreckers."}],
             "failure": [T("Something's still stuck.")]},
            {"id": "relight3", "label": "Work the mechanism out by trial and error "
                                       "(Intelligence check DC 12; takes a while)",
             "requires": {"enc_cleared": "lamp", "not_flag": "lantern_lit"},
             "check": {"skill": "ability:int", "dc": 12, "take10_ok": True},
             "success": [
                T("Gear by gear, you puzzle it out. The wick-feed was jammed with driftwood. "
                  "With a whoosh, the Lantern blazes and its beam sweeps the Teeth."),
                {"do": "flag", "name": "lantern_lit"},
                {"do": "xp", "amount": 200, "why": "the Lantern relit"},
                {"do": "journal", "text": "The Lantern is lit! Now find whoever paid the "
                                          "wreckers."}],
             "failure": [T("An hour of fiddling and swearing later, still nothing. (You can "
                           "keep trying.)")]},
            {"id": "gallery", "label": "Look out from the gallery",
             "requires": {"enc_cleared": "lamp"}, "once": True, "effects": [
                T("Behind Gull Rock, a black-sailed ship rides at anchor. A longboat is "
                  "pulled up in the cove below the cliff, beside a dark cave mouth."),
                {"do": "journal", "text": "A black-sailed ship waits behind Gull Rock; its "
                                          "boat is in the cove below the lighthouse."}]},
            {"id": "smuggler_loot", "label": "Search the smuggler",
             "requires": {"enc_cleared": "lamp"}, "once": True, "effects": [
                T("A purse and a folded note: 'Bring the silver down through the caves "
                  "tonight. - M.'"),
                {"do": "gold", "gp": 20}]},
        ],
        "exits": {"down": {"to": "lighthouse_base", "label": "Down the spiral stair"}},
    },
    "cellar": {
        "dark": True, "name": "The Cellar", "flee_to": "lighthouse_base",
        "desc": "A damp stone cellar of oil casks and gnawed flour sacks. In the far wall, "
                "a crack wide enough to squeeze through breathes cold sea air.",
        "encounters_enter": ["cellar"],
        "features": [
            {"id": "casks", "label": "Search the oil casks", "requires": {"enc_cleared": "cellar"},
             "once": True, "effects": [
                T("Most are empty, but two flasks of alchemist's fire sit wrapped in straw "
                  "behind them: wreckers' tools."),
                {"do": "item", "id": "alchemist's fire", "qty": 2}]},
        ],
        "exits": {
            "up": {"to": "lighthouse_base", "label": "Back up the trapdoor"},
            "crack": {"to": "sea_caves", "label": "Squeeze through the crack toward the sea"},
        },
    },
    # ================================================================ below
    "cove": {
        "terrain": "open",
        "name": "Smugglers' Cove", "flee_to": "lighthouse_yard",
        "desc": "A shingle beach in a notch of the cliff, invisible from the village. A "
                "longboat is drawn up on the stones. A cave mouth gapes in the rock to the "
                "north.",
        "encounters_enter": ["cove"],
        "features": [
            {"id": "boat", "label": "Search the longboat", "requires": {"enc_cleared": "cove"},
             "once": True, "effects": [
                T("Under a tarp: a potion, a coil of good rope, and a pouch of coins."),
                {"do": "item", "id": "potion of cure light wounds"},
                {"do": "gold", "gp": 30}]},
        ],
        "exits": {
            "up": {"to": "lighthouse_yard", "label": "Climb the smugglers' stair"},
            "north": {"to": "sea_caves", "label": "Into the cave mouth"},
        },
    },
    "sea_caves": {
        "dark": True, "name": "The Sea Caves", "flee_to": "cove",
        "desc": "Twisting caves of black rock, thick with old web. The tide sighs somewhere "
                "ahead. Passages lead to a flooded grotto (west), up through a crack "
                "(the lighthouse cellar), and toward lamplight (north).",
        "encounters_enter": ["spiders"],
        "features": [
            {"id": "cocoon", "label": "Cut open the webbed cocoon",
             "requires": {"enc_cleared": "spiders"}, "once": True, "effects": [
                T("Inside, horribly, is old Corwin the lighthouse keeper, long dead. His "
                  "keeper's medallion and a scroll case are still on him."),
                {"do": "item", "id": "scroll of bless"},
                {"do": "item", "id": "antitoxin"},
                {"do": "journal", "text": "Found Corwin's body in the sea caves."}]},
        ],
        "exits": {
            "south": {"to": "cove", "label": "Out to the cove"},
            "crack": {"to": "cellar", "label": "Up the crack to the lighthouse cellar"},
            "west": {"to": "wreck_grotto", "label": "Toward the sound of water (swim the "
                                                    "flooded passage, Swim DC 10)",
                     "effects": [{"do": "swim", "dc": 10}]},
            "north": {"to": "captains_den", "label": "Toward the lamplight",
                      "blocked_by": "spiders"},
        },
    },
    "wreck_grotto": {
        "dark": True, "name": "The Wreck Grotto", "flee_to": "sea_caves",
        "desc": "A cathedral of a cave, half flooded by the tide. The broken stern of an "
                "older ship, the Merry Ann, juts from the water, its strongroom door hanging "
                "open below the waterline.",
        "encounters_enter": ["drowned"],
        "features": [
            {"id": "dive", "label": "Swim down to the sunken strongroom (Swim DC 12)",
             "requires": {"enc_cleared": "drowned"},
             "check": {"skill": "Swim", "dc": 12, "take10_ok": True},
             "success": [T("Your lungs burn, but your hands find a small iron chest. Back on "
                           "the rocks, it holds coins, a ring, and a sealed bottle."),
                         {"do": "gold", "gp": 90},
                         {"do": "item", "id": "ring of protection +1"},
                         {"do": "item", "id": "potion of cure light wounds"}],
             "failure": [T("The cold water drives you back up, gasping."),
                         {"do": "damage", "dice": "1d4", "who": "actor"}]},
        ],
        "exits": {"east": {"to": "sea_caves", "label": "Back to the caves"}},
    },
    "captains_den": {
        "name": "The Captain's Den", "flee_to": "sea_caves", "no_rest": True,
        "no_rest_text": "Not here. This is Merrow's lair.",
        "desc": "A dry cave fitted out like a ship's cabin: a chart table, a rum cask, "
                "lanterns, and a sea chest. Beyond, a tunnel slopes down to where the "
                "black ship's boat can reach at high tide.",
        "encounters_enter": [],
        "features": [
            {"id": "fight", "label": "Draw steel on Captain Merrow",
             "requires": {"enc_active": "captain"},
             "effects": [{"do": "fight", "enc": "captain"}]},
            {"id": "bluff", "label": "Bluff: 'We're the new crew Bram sent' "
                                     "(Bluff DC 18, wins a surprise round)",
             "requires": {"enc_active": "captain"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Bluff", "dc": 18},
             "success": [T("Merrow squints, half buys it, and turns her back to pour the rum. "
                           "That's your moment."),
                         {"do": "fight", "enc": "captain", "surprise": "monsters"}],
             "failure": [T("'Bram didn't send anyone,' Merrow says. 'Bram never sends anyone. "
                           "That's why I like him.'"),
                         {"do": "fight", "enc": "captain"}]},
            {"id": "chest", "label": "Open Merrow's sea chest",
             "requires": {"enc_cleared": "captain"}, "once": True, "effects": [
                T("Gold, a fine cutlass belt, and a leather ledger in Merrow's neat hand: "
                  "dates, ships, cargoes... and payments to 'B. the harbormaster'."),
                {"do": "gold", "gp": 160},
                {"do": "item", "id": "potion of cure moderate wounds"},
                {"do": "flag", "name": "ledger"},
                {"do": "journal", "text": "Merrow's ledger proves Bram the harbormaster "
                                          "sold out the ships. Confront him in Saltmere."}]},
        ],
        "exits": {"south": {"to": "sea_caves", "label": "Back to the caves"}},
    },
}
