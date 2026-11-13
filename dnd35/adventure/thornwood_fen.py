"""THE THORNWOOD FEN
An original adventure for 1-4 heroes of 6th-8th level. A sequel for heroes who
opened Greyfang Pass.

Children are vanishing from the fen village of Marrowmere. The lizardfolk who
used to trade fish for iron have started raiding instead, and something stalks
the old causeway. Behind it all is Grandmother Thorn, a green hag who has made
her nest in the drowned Abbey of Saint Wendel, with trolls for servants.
"""

ID = "thornwood_fen"
TITLE = "The Thornwood Fen"
LEVELS = "6-8"
START_LEVEL = 6
SUMMARY = ("A fen village losing its children, a troll under the causeway, charmed "
           "lizardfolk, a haunted barrow, and a green hag in a drowned abbey.")
START = "marrowmere"
REST_ENCOUNTER_CHANCE = 0.3
TEMPLE_NAME = "Chapel of the Dawnfather"
TEMPLE_GREETING = ("Mother Ilse, the old priestess of Pelor, looks up from a cot where a "
                   "feverish child sleeps. 'Light keep you. What can the chapel do?'")

INTRO = """
Marrowmere stands on stilts at the edge of the Thornwood Fen, a village of reed
roofs and plank walkways where the mist never quite lifts. You arrive on a grey
afternoon to the sound of a bell tolling: not for a death, the ferryman tells
you, but for a missing child. The fourth this month.

The lizardfolk who used to trade fish for iron have turned raider. Something
huge has been seen under the old causeway. And at night, the villagers say, an
old woman's voice sings from the direction of the drowned abbey, though no one
has lived there for a hundred years.

Warden Ysolde has sent to every town on the river for help. You are what came.
"""

ENDING = """
With Grandmother Thorn dead, the singing in the fen stops. The lizardfolk wake
from their long dream, horrified at what they've done, and send their elders to
Marrowmere with baskets of fish and a hundred apologies.

The freed children are carried home through the mist on their parents'
shoulders, and for the first time in a month the bell of Marrowmere rings for
joy. Warden Ysolde has a new walkway built across the fen and names it for you.

THE END (for now).
"""

RUMORS = [
    (5, "There's a troll under the old causeway. It asks a toll. Nobody who's refused "
        "has come back. And they say you can't kill a troll: it just gets up again."),
    (10, "Fire, that's what trolls fear. Fire or acid. Cut one down and burn it, or it "
         "heals right back. The apothecary sells alchemist's fire for a reason."),
    (10, "The lizardfolk aren't themselves. Their eyes are glassy, like sleepwalkers. Old "
         "Pell swears he saw a bone totem in their village, humming with witchery."),
    (15, "There are statues on the abbey walls. Grotesques. My grandfather swore they "
         "moved. Swords bounce off them, he said; you need a blessed or magic blade."),
    (15, "The Fen Knight is buried on an island out in the reeds, with his sword "
         "Dawnreed. His barrow is cursed: the dead there drink the life out of you."),
    (20, "A hag's touch saps the strength right out of your arms. And she can look like "
         "anyone: a kindly old granny, even. Don't trust a sweet face in the fen."),
]

WANDERING = [
    {"text": "Two glassy-eyed lizardfolk rise out of the reeds, clubs raised!",
     "monsters": ["lizardfolk", "lizardfolk"], "requires": {"not_flag": "lizards_free"}},
    {"text": "The reeds part and a dire boar charges, squealing!",
     "monsters": ["dire boar"]},
    {"text": "A branch overhead uncoils. It isn't a branch.",
     "monsters": ["giant constrictor snake"]},
    {"text": "Grey statues of herons and one very surprised lizardfolk stand among the "
             "reeds. Something with too many legs is watching you from the mud.",
     "monsters": ["basilisk"]},
    {"text": "A ragged pack of wolves, starving in the fen, closes in!",
     "monsters": ["wolf", "wolf", "wolf"]},
]

ENCOUNTERS = {
    "boar": {"room": "fen_road", "monsters": ["dire boar"], "per_extra_hero": ["wolf"],
             "ambush": True, "ambush_text": "Something big is breathing in the reeds beside "
                                             "the path...",
             "text": "A dire boar bursts out of the reeds, tusks lowered!",
             "title": "THE FEN ROAD"},
    "owlbear": {"room": "owl_hollow", "monsters": ["owlbear"], "per_extra_hero": ["wolf"],
                "title": "THE HOLLOW",
                "text": "With a hoot that turns into a roar, an owlbear lunges out of its "
                        "nest of bones!"},
    "bridge": {"room": "causeway", "monsters": ["troll"], "per_extra_hero": ["lizardfolk"],
               "names": {"troll": "Old Gutch"}, "title": "THE TROLL UNDER THE CAUSEWAY",
               "text": "Old Gutch heaves himself up onto the stones, dripping and grinning. "
                       "'No toll? Then Gutch takes the toll out of you.'"},
    "village": {"room": "lizard_village",
                "monsters": ["lizardfolk", "lizardfolk", "lizardfolk", "lizardfolk"],
                "per_extra_hero": ["lizardfolk", "lizardfolk"], "title": "THE SUNKEN VILLAGE",
                "text": "The lizardfolk turn as one, their eyes glazed, and come at you "
                        "without a sound."},
    "barrow": {"room": "barrow_isle", "monsters": ["wight", "wight"],
               "per_extra_hero": ["wight"], "title": "THE FEN KNIGHT'S BARROW",
               "text": "Two shapes rise from the burial niches, eyes like coals in grey "
                       "faces. Their hands reach for your warmth."},
    "gargoyles": {"room": "abbey_gate", "monsters": ["gargoyle", "gargoyle"],
                  "per_extra_hero": ["gargoyle"], "ambush": True,
                  "ambush_text": "The grotesques on the abbey wall are very still. Too still.",
                  "title": "THE ABBEY WALLS",
                  "text": "Stone cracks. Two of the grotesques spread their wings and drop on "
                          "you!"},
    "undercroft": {"room": "undercroft", "monsters": ["troll"],
                   "per_extra_hero": ["wight"], "names": {"troll": "Brine"},
                   "title": "THE UNDERCROFT",
                   "text": "A troll hunched over the cages straightens up, licking its "
                           "fingers. 'Grandmother said no one comes. Grandmother was wrong. "
                           "Brine is hungry.'"},
    "thorn": {"room": "nave", "monsters": ["green hag", "lizardfolk", "lizardfolk"],
              "per_extra_hero": ["wight"],
              "names": {"green hag": "Grandmother Thorn"},
              "overrides": {"green hag": {"bonus_hp": 10}}, "can_flee": True,
              "title": "GRANDMOTHER THORN",
              "text": "The kindly old woman's face slides off like wet paper. Beneath it: "
                      "green skin, black iron nails, and a mouth full of needles. 'Such "
                      "fresh, strong ones,' Grandmother Thorn croons. Two glassy-eyed "
                      "lizardfolk rise out of the black water. 'Hold them still for "
                      "Granny, my pets.'"},
}


def T(text):
    return {"do": "text", "text": text}


def SAY(who, text):
    return {"do": "say", "who": who, "text": text}


ROOMS = {
    # ================================================================ village
    "marrowmere": {
        "name": "Marrowmere", "town": True, "wandering": False,
        "desc": "Marrowmere's plank walkways over black water: the Heron's Rest inn, "
                "Pell's Apothecary & Outfitters, the little Chapel of the Dawnfather, and "
                "the Warden's longhouse. A raised path leads east into the fen.",
        "features": [
            {"id": "warden", "label": "Speak with Warden Ysolde in the longhouse",
             "requires": {"not_flag": "quest"}, "once": True, "effects": [
                SAY("Warden Ysolde", "Four children in a month. Taken from their beds, and "
                                     "the doors still barred from inside. The lizardfolk "
                                     "carry them off into the fen, but the lizardfolk were "
                                     "our friends a season ago. Something has its claws "
                                     "in them."),
                SAY("Warden Ysolde", "Find our children. Find whatever is behind this and "
                                     "end it. Marrowmere will pay twelve hundred gold, every "
                                     "coin we have. And take these; Mother Ilse brewed "
                                     "them."),
                {"do": "items_each", "id": "potion of cure serious wounds", "qty": 1},
                {"do": "flag", "name": "quest"},
                {"do": "journal", "text": "Quest: find Marrowmere's missing children and "
                                          "whatever is taking them (1,200 gp)."},
             ]},
            {"id": "warden2", "label": "Speak with Warden Ysolde again",
             "requires": {"flag": "quest", "not_flag": "thorn_dead"}, "effects": [
                SAY("Warden Ysolde", "The causeway is the only dry way across the fen. If "
                                     "the troll's still there... take fire. Lots of it."),
             ]},
            {"id": "victory", "label": "Return to Warden Ysolde",
             "requires": {"flag": "thorn_dead"}, "once": True,
             "effects": [{"do": "custom", "fn": "homecoming"}]},
            {"id": "rumors", "label": "Ask around the Heron's Rest for rumors "
                                      "(Gather Information)",
             "effects": [{"do": "rumors"}]},
            {"id": "shop", "label": "Pell's Apothecary & Outfitters (gear, alchemist's "
                                    "fire, arms, fine and magic items)",
             "effects": [{"do": "shop", "name": "Pell's Apothecary & Outfitters",
                          "sections": ["general", "weapons", "armor", "fine", "magic"]}]},
            {"id": "temple", "label": "Visit the Chapel of the Dawnfather (healing, "
                                      "restoration, raise dead)",
             "effects": [{"do": "temple"}]},
            {"id": "inn", "label": "Rent rooms at the Heron's Rest and rest (1 gp each)",
             "effects": [{"do": "rest", "cost_sp": 10, "safe": True}]},
            {"id": "recruit", "label": "Recruit a new hero (replace the fallen or grow the "
                                       "party)",
             "effects": [{"do": "recruit"}]},
        ],
        "exits": {
            "east": {"to": "fen_road", "label": "Take the raised path into the fen",
                     "requires": {"flag": "quest"}},
        },
    },
    # ================================================================ the fen
    "fen_road": {
        "name": "The Raised Path", "travel_minutes": 90, "flee_to": "marrowmere",
        "first": "The path is a hump of packed earth a few feet above the water, lined with "
                 "dead willows. Within minutes, Marrowmere is gone in the mist behind you.",
        "desc": "A raised path through reeds and black water. East, the old stone "
                "causeway; north, a thicket of thorn where something has been dragging "
                "carcasses.",
        "encounters_enter": ["boar"],
        "features": [
            {"id": "tracks", "label": "Study the drag marks and footprints (Survival DC 18)",
             "check": {"skill": "Survival", "dc": 18, "retry": False},
             "success": [T("Lizardfolk prints, many of them, walking in a strange dead "
                           "straight line, as if sleepwalking. They carried something "
                           "small. The trail runs east over the causeway toward their "
                           "sunken village, then on north toward the abbey."),
                         {"do": "journal", "text": "The lizardfolk carry the children east "
                                                   "to their village, then north toward "
                                                   "the drowned abbey."},
                         {"do": "xp", "amount": 150, "why": "reading the fen"}],
             "failure": [T("Mud, reeds, and more mud.")]},
        ],
        "exits": {
            "west": {"to": "marrowmere", "label": "Back to Marrowmere"},
            "north": {"to": "owl_hollow", "label": "Into the thorn thicket"},
            "east": {"to": "causeway", "label": "On to the old causeway"},
        },
    },
    "owl_hollow": {
        "name": "The Thorn Hollow", "flee_to": "fen_road",
        "desc": "A hollow in the thorns, roofed by a fallen oak. The ground is littered with "
                "bones, feathers, and the rusted gear of people who came here before you.",
        "encounters_enter": ["owlbear"],
        "features": [
            {"id": "bones", "label": "Search the bones and gear",
             "requires": {"enc_cleared": "owlbear"}, "once": True, "effects": [
                T("Under the bones: a ranger's kit, long rotted, and a fine bow still "
                  "strung, its wood dark with age and humming faintly. A pair of bracers, "
                  "too. Whoever owned them was very good, and not quite good enough."),
                {"do": "item", "id": "+1 longbow"},
                {"do": "item", "id": "bracers of armor +2"},
                {"do": "gold", "gp": 220}]},
        ],
        "exits": {"south": {"to": "fen_road", "label": "Back to the raised path"}},
    },
    "causeway": {
        "name": "The Old Causeway", "flee_to": "fen_road",
        "first": "An old stone causeway runs out across open water toward a line of "
                 "drowned trees. Halfway across, the stones sag over a culvert, and "
                 "something down there is breathing.",
        "desc": "The causeway: mossy stones over deep water. Bones are piled in the culvert "
                "below. East, the causeway reaches the lizardfolk's sunken village.",
        "features": [
            {"id": "fight", "label": "Cross the causeway, ready for a fight",
             "requires": {"enc_active": "bridge"},
             "effects": [{"do": "fight", "enc": "bridge"}]},
            {"id": "toll", "label": "Pay the troll's toll (200 gp)",
             "requires": {"enc_active": "bridge", "not_flag": "paid"},
             "effects": [{"do": "custom", "fn": "pay_toll"}]},
            {"id": "talk", "label": "Talk Old Gutch into letting you pass for free "
                                    "(Diplomacy: make him friendly)",
             "requires": {"enc_active": "bridge"}, "effects": [
                {"do": "diplomacy", "npc": "Old Gutch", "start": "unfriendly",
                 "goal": "friendly", "success": [
                    SAY("Old Gutch", "Gutch likes you. Gutch lets friends pass. Friends tell "
                                     "Gutch stories next time, yes?"),
                    {"do": "resolve_enc", "enc": "bridge", "factor": 0.75}],
                 "failure": [T("Gutch grunts and folds his long arms. 'Toll, or fight.'")]}]},
            {"id": "bluff", "label": "Convince Old Gutch the Warden sent you to pay later "
                                     "(Bluff DC 22)",
             "requires": {"enc_active": "bridge"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Bluff", "dc": 22},
             "success": [T("Gutch scratches his head with a claw. 'Warden pays later. Warden "
                           "always pays.' He sinks back under the stones, grumbling."),
                         {"do": "resolve_enc", "enc": "bridge", "factor": 0.5}],
             "failure": [T("'Gutch is not STUPID,' the troll roars, and comes up out of "
                           "the water."),
                         {"do": "fight", "enc": "bridge"}]},
            {"id": "culvert", "label": "Search the troll's culvert",
             "requires": {"enc_cleared": "bridge"}, "once": True, "effects": [
                T("Among the bones: purses, rings and buckles from a hundred unlucky "
                  "travellers, and a gleaming steel shield with a heron on it."),
                {"do": "gold", "gp": 380},
                {"do": "item", "id": "+2 heavy steel shield"},
                {"do": "item", "id": "ring of protection +1"}]},
        ],
        "exits": {
            "west": {"to": "fen_road", "label": "Back to the raised path"},
            "east": {"to": "lizard_village", "label": "Across the causeway to the sunken "
                                                      "village",
                     "blocked_by": "bridge",
                     "blocked_text": "The troll is in the way."},
        },
    },
    "lizard_village": {
        "name": "The Sunken Village", "flee_to": "causeway",
        "desc": "Domed reed huts on half-sunk pilings. At the center, a bone totem hung "
                "with fen-witch charms hums faintly. Boats are tied along the edge; a "
                "channel winds north toward the abbey, and a low island rises in the reeds "
                "to the south.",
        "features": [
            {"id": "fight", "label": "Fight the lizardfolk",
             "requires": {"enc_active": "village"},
             "effects": [{"do": "fight", "enc": "village"}]},
            {"id": "sneak", "label": "Slip in quietly to reach the totem (Move Silently vs "
                                     "their Listen)",
             "requires": {"enc_active": "village"},
             "effects": [{"do": "stealth_fight", "enc": "village"}]},
            {"id": "totem", "label": "Break the hag's spell on the totem (Spellcraft or "
                                     "Knowledge (arcana) DC 20)",
             "requires": {"not_flag": "lizards_free"},
             "check": {"skill": "best:Spellcraft|Knowledge (arcana)", "dc": 20},
             "success": [{"do": "custom", "fn": "free_lizards"}],
             "failure": [T("The charms twist under your fingers. The lizardfolk turn "
                           "toward you, hissing."),
                         {"do": "fight", "enc": "village"}]},
            {"id": "totem2", "label": "Smash the totem (Strength DC 18)",
             "requires": {"not_flag": "lizards_free", "enc_cleared": "village"},
             "check": {"skill": "ability:str", "dc": 18},
             "success": [{"do": "custom", "fn": "free_lizards"}],
             "failure": [T("The bones are bound with something stronger than sinew.")]},
            {"id": "elder", "label": "Speak with Elder Sss'kara",
             "requires": {"flag": "lizards_free"}, "effects": [
                SAY("Elder Sss'kara", "The old woman in the abbey sang to us, and we "
                                      "dreamed. In the dream we did terrible things. Take "
                                      "the boat channel north; my hunters will row you to "
                                      "the water-door under the abbey. The stone birds on "
                                      "the walls will never see you.")]},
        ],
        "exits": {
            "west": {"to": "causeway", "label": "Back over the causeway"},
            "south": {"to": "barrow_isle", "label": "Row out to the barrow island"},
            "north": {"to": "abbey_gate", "label": "Wade the channel north to the abbey "
                                                  "gate (Swim DC 10)",
                      "effects": [{"do": "swim", "dc": 10}]},
            "boat": {"to": "undercroft", "label": "Let the lizardfolk row you to the "
                                                 "abbey's water-door",
                     "requires": {"flag": "lizards_free"}},
        },
    },
    "barrow_isle": {
        "terrain": "dungeon",
        "dark": True, "name": "The Fen Knight's Barrow", "flee_to": "lizard_village",
        "desc": "A grassy mound on a reed island, its stone door cracked open. Inside, "
                "burial niches line a short passage to a knight's tomb.",
        "encounters_enter": ["barrow"],
        "secrets": [
            {"id": "niche", "search_dc": 22, "effects": [
                T("Behind a loose capstone in the knight's own niche: an amulet of green "
                  "stone, still warm, and a pair of blackened bracers laid across a "
                  "squire's bones."),
                {"do": "item", "id": "amulet of natural armor +2"},
                {"do": "item", "id": "bracers of defenselessness"}]},
        ],
        "features": [
            {"id": "tomb", "label": "Open the Fen Knight's tomb",
             "requires": {"enc_cleared": "barrow"}, "once": True, "effects": [
                T("Sir Wendel's bones lie in rusted mail, hands folded on a longsword "
                  "that shines as if forged yesterday: Dawnreed. On one finger, a silver "
                  "ring."),
                {"do": "item", "id": "dawnreed"},
                {"do": "item", "id": "ring of protection +2"},
                {"do": "xp", "amount": 300, "why": "the barrow laid to rest"}]},
        ],
        "exits": {"north": {"to": "lizard_village", "label": "Row back to the village"}},
    },
    # ================================================================ the abbey
    "abbey_gate": {
        "name": "The Drowned Abbey", "flee_to": "lizard_village",
        "first": "The Abbey of Saint Wendel rises from the water like a sinking ship, its "
                 "bell tower leaning, its walls crowned with stone grotesques.",
        "desc": "The abbey's flooded courtyard. Stone grotesques crouch on the walls. The "
                "chapter house door stands open; the great nave is sealed and dark.",
        "encounters_enter": ["gargoyles"],
        "features": [],
        "exits": {
            "south": {"to": "lizard_village", "label": "Back down the channel"},
            "in": {"to": "chapter_house", "label": "Into the chapter house",
                   "blocked_by": "gargoyles"},
        },
    },
    "chapter_house": {
        "name": "The Chapter House", "flee_to": "abbey_gate",
        "desc": "The monks' old meeting room, now a witch's parlor: a rocking chair by a "
                "cold hearth, jars of things floating in brine, and a small coat on a "
                "peg. Stairs lead down into darkness.",
        "secrets": [
            {"id": "jars", "search_dc": 18, "effects": [
                T("Behind the brine jars, a witch's stash: potions in clay bottles, and a "
                  "headband of braided silver."),
                {"do": "item", "id": "potion of cure serious wounds", "qty": 2},
                {"do": "item", "id": "headband of intellect +2"}]},
        ],
        "features": [
            {"id": "journal", "label": "Read the ledger on the table", "once": True,
             "effects": [
                T("A ledger in a spidery hand: names of Marrowmere children, and beside each "
                  "a note like 'plump' or 'for the solstice.' The last page: 'The trolls "
                  "grow greedy. Brine guards the larder. My scaly pets guard me.'"),
                {"do": "journal", "text": "The children are in the larder under the abbey, "
                                          "guarded by a troll called Brine. The hag keeps "
                                          "charmed lizardfolk as bodyguards."}]},
        ],
        "exits": {
            "out": {"to": "abbey_gate", "label": "Back to the courtyard"},
            "down": {"to": "undercroft", "label": "Down the stairs"},
        },
    },
    "undercroft": {
        "dark": True, "name": "The Undercroft", "flee_to": "chapter_house", "no_rest": True,
        "no_rest_text": "Not with children in cages and a hag overhead.",
        "desc": "A vaulted cellar, half flooded. Wicker cages hang from the ribs of the "
                "vault, and small frightened faces peer out. A water-door opens on the "
                "channel; a great door leads up into the nave.",
        "encounters_enter": ["undercroft"],
        "features": [
            {"id": "free", "label": "Free the children (Open Lock DC 20 or Use Rope DC 15 "
                                    "to lower the cages)",
             "requires": {"enc_cleared": "undercroft", "not_flag": "children_free"},
             "check": {"skill": "Use Rope", "dc": 15, "take10_ok": True},
             "success": [{"do": "custom", "fn": "free_children"}],
             "failure": [T("The cage ropes are knotted with witch-knots. Try again.")]},
            {"id": "free2", "label": "Hack the cages down (Strength DC 16)",
             "requires": {"enc_cleared": "undercroft", "not_flag": "children_free"},
             "check": {"skill": "ability:str", "dc": 16},
             "success": [{"do": "custom", "fn": "free_children"}],
             "failure": [T("The wicker is tougher than it looks.")]},
        ],
        "exits": {
            "up": {"to": "chapter_house", "label": "Up the stairs to the chapter house"},
            "water": {"to": "lizard_village", "label": "Out the water-door by boat",
                      "requires": {"flag": "lizards_free"}},
            "nave": {"to": "nave", "label": "Through the great door into the nave",
                     "blocked_by": "undercroft",
                     "blocked_text": "The troll is in the way."},
        },
    },
    "nave": {
        "name": "The Drowned Nave", "flee_to": "undercroft", "no_rest": True,
        "no_rest_text": "Not in the hag's own lair.",
        "desc": "The abbey's great nave, knee-deep in black water. Candles burn on the "
                "broken altar, and an old woman in a shawl sits there knitting, humming.",
        "features": [
            {"id": "fight", "label": "Attack the old woman", "requires": {"enc_active": "thorn"},
             "effects": [{"do": "fight", "enc": "thorn"}]},
            {"id": "see", "label": "Listen to her, and watch her closely (Sense Motive DC 20)",
             "requires": {"enc_active": "thorn"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Sense Motive", "dc": 20},
             "success": [SAY("The old woman", "Lost, my dears? Come sit by Granny..."),
                         T("Her shadow on the wall is all wrong: hunched, long-nailed. And "
                           "there are eyes in the water behind the altar. You strike "
                           "first!"),
                         {"do": "fight", "enc": "thorn", "surprise": "monsters"}],
             "failure": [SAY("The old woman", "Lost, my dears? Come sit by Granny..."),
                         T("You step closer. Too close."),
                         {"do": "fight", "enc": "thorn", "surprise": "party"}]},
            {"id": "hoard", "label": "Search the altar and the hag's nest",
             "requires": {"enc_cleared": "thorn"}, "once": True, "effects": [
                T("Under the altar: the abbey's lost silver, the hag's own hoard of "
                  "trinkets, and a cloak sewn from heron feathers."),
                {"do": "gold", "gp": 1500},
                {"do": "item", "id": "cloak of resistance +2"},
                {"do": "item", "id": "periapt of wisdom +2"},
                {"do": "item", "id": "+2 chain shirt"},
                {"do": "flag", "name": "thorn_dead"},
                {"do": "journal", "text": "Grandmother Thorn is dead. Return to "
                                          "Marrowmere."}]},
        ],
        "exits": {"down": {"to": "undercroft", "label": "Back down to the undercroft"}},
    },
}


# ---------------------------------------------------------------- scripted bits
def pay_toll(gm, actor, eff):
    payer = gm._payer(200)
    if not payer:
        return
    payer.cp -= 200 * 100
    gm.gs.flags.add("paid")
    gm.run([
        T("You toss the purse down into the culvert. A long green arm snatches it."),
        SAY("Old Gutch", "Good toll. Pass, pass. Gutch hears things, for a good toll: the "
                         "old woman in the abbey sings the scaly ones to sleep. Gutch does "
                         "not go near her. Even Gutch."),
        {"do": "resolve_enc", "enc": "bridge", "xp": False},
    ])


def free_lizards(gm, actor, eff):
    if "lizards_free" in gm.gs.flags:
        return
    gm.gs.flags.add("lizards_free")
    if not gm.enc_done("village"):
        gm.run([{"do": "resolve_enc", "enc": "village", "factor": 1.0}])
    # her charmed bodyguards wake up too
    gm.run([{"do": "remove_monster", "enc": "thorn", "count": 2, "room": "nave"}])
    gm.run([
        T("The totem cracks with a sound like a breaking fever. All around the village, "
          "lizardfolk blink, shudder, and sink to the mud, keening."),
        {"do": "xp", "amount": 300, "why": "the lizardfolk freed"},
        {"do": "journal", "text": "The lizardfolk are free of the hag's spell. They can row "
                                  "you to the abbey's water-door, and the hag has lost "
                                  "her lizardfolk bodyguards."},
    ])


def free_children(gm, actor, eff):
    if "children_free" in gm.gs.flags:
        return
    gm.gs.flags.add("children_free")
    gm.run([
        T("One by one, you lower the cages and lift the children out: four of them, cold, "
          "filthy, and alive. The oldest, a girl of nine, grips your hand and won't let "
          "go."),
        SAY("Little Bet", "She's upstairs. She said tomorrow was the feast. Please don't "
                          "leave us down here."),
        {"do": "xp", "amount": 400, "why": "the children found alive"},
        {"do": "journal", "text": "The four missing children are found alive in the "
                                  "undercroft."},
    ])


def homecoming(gm, actor, eff):
    gs = gm.gs
    gm.run([
        T("Warden Ysolde hears you out in silence, then walks out onto the walkway and "
          "rings the bell herself."),
        {"do": "gold", "gp": 1200},
        {"do": "xp", "amount": 800, "why": "the Thornwood Fen made safe"},
    ])
    if "children_free" in gs.flags:
        gm.run([SAY("Warden Ysolde", "And you brought them home. All four. I don't have "
                                     "the words."),
                {"do": "xp", "amount": 400, "why": "every child home"}])
    else:
        gm.run([T("No one says it aloud, but every eye goes to the empty walkway behind "
                  "you. The children are still out there in the abbey.")])
        if not gm.ui.confirm("End the adventure now, without the children?", False):
            if "victory" in gs.rs()["used"]:
                gs.rs()["used"].remove("victory")
            gm.ui.out("You turn back toward the fen.")
            return
    gm.run([{"do": "end_adventure"}])
