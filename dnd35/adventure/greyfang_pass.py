"""GREYFANG PASS
An original adventure for 1-4 heroes of 3rd-5th level. A natural sequel for heroes
who finished The Ember King's Barrow or The Drowned Lantern.

An ogre warlord named Skarn has taken the old border keep that guards Greyfang
Pass. His gnolls and worgs raid every caravan, and the mountain town of Highcairn
is slowly starving.
"""

ID = "greyfang_pass"
TITLE = "Greyfang Pass"
LEVELS = "3-5"
START_LEVEL = 3
SUMMARY = ("A mountain pass held by an ogre warlord, his gnoll raiders and worg packs. "
           "A broken bridge, a captured keep, and prisoners to free.")
START = "highcairn"
REST_ENCOUNTER_CHANCE = 0.3
TEMPLE_NAME = "Shrine of the Mountain Father"
TEMPLE_GREETING = ("Brother Hallan of the Mountain Father lowers his hammer-shaped holy "
                   "symbol. 'Stone endures. So shall you. What do you need?'")

INTRO = """
Highcairn huddles in a notch of the Greyfang Mountains, a town of slate roofs and
smoking chimneys built around a market square that, three months ago, was full of
dwarven merchants and lowland wool traders.

Now the square is empty. An ogre the gnolls call Skarn the Breaker has taken the old
border keep at the top of the pass. Nothing gets through. The last caravan, a dwarf
trading house carrying a winter's worth of grain, never arrived.

The town reeve has posted a notice on the shrine door: REWARD. ANY WHO CAN OPEN
THE PASS. Your names are about to be added to it.
"""

ENDING = """
With Skarn fallen, the gnolls scatter into the high crags and the worgs go with them.
The dwarves of House Durnhal limp down into Highcairn behind you, and by the next
morning their grain wagons are rolling through the square, and the town smells of
fresh bread for the first time in months.

The reeve orders your names carved on the keep's gatehouse. Old Thane Durnhal grips
your hands and swears that any door in the dwarf-holds will open for you, should you
ever need one.

THE END (for now).
"""

RUMORS = [
    (5, "Skarn's no ordinary ogre. Wears a dwarf king's chainmail as a belt, they say, "
        "and swings a club made from a whole oak."),
    (10, "The gnolls keep worgs, great clever wolves. They hunt the pass road at dusk."),
    (10, "The rope bridge over Widow's Gorge is cut. There's a beam left; a steady foot "
         "could walk it, or a strong arm could rig a line."),
    (15, "The old keep has a postern gate on the north side, hidden in the rocks. The "
         "builders used it to bring in supplies in winter."),
    (15, "Gnolls are cowards at heart. Kill their leader and the rest might run."),
    (20, "The dwarves of House Durnhal are being held alive. Skarn wants a ransom from "
         "the dwarf-holds, which means there's still time."),
]

WANDERING = [
    {"text": "A sunning rock-snake as thick as your thigh takes exception to your boots.",
     "monsters": ["constrictor snake"]},
    {"text": "A pair of gnoll scouts comes loping down the trail!",
     "monsters": ["gnoll", "gnoll"], "requires": {"not_flag": "enc:hall"}},
    {"text": "A worg howls nearby, and then it's on you!",
     "monsters": ["worg"], "requires": {"not_flag": "enc:hall"}},
    {"text": "Wolves, drawn by the smell of your camp!",
     "monsters": ["wolf", "wolf"]},
]

ENCOUNTERS = {
    "road": {"room": "pass_road", "monsters": ["worg"], "per_extra_hero": ["wolf"],
             "ambush": True, "ambush_text": "The wind drops. Something is watching from "
                                             "the rocks above the road...",
             "text": "A worg leaps down from the rocks, jaws wide!", "title": "THE ROAD"},
    "camp": {"room": "gnoll_camp", "monsters": ["gnoll", "gnoll"],
             "per_extra_hero": ["gnoll"], "title": "THE RAIDERS' CAMP",
             "text": "Gnolls leap up from around the fire, cackling, axes in hand!"},
    "tower": {"room": "watchtower", "monsters": ["orc", "orc", "gnoll"],
              "per_extra_hero": ["orc"], "title": "THE WATCHTOWER",
              "text": "Orc mercenaries and a gnoll come boiling down the tower stairs!"},
    "den": {"room": "worg_den", "monsters": ["worg", "wolf"], "per_extra_hero": ["worg"],
            "title": "THE WORG DEN",
            "text": "A worg and its wolf packmate rise from a nest of bones, the worg growling "
                    "words in a guttural tongue."},
    "yard": {"room": "keep_yard", "monsters": ["gnoll", "orc"],
             "per_extra_hero": ["gnoll"], "title": "THE KEEP YARD",
             "text": "The yard guards spot you and howl the alarm!"},
    "hall": {"room": "great_hall", "monsters": ["ogre", "gnoll"],
             "per_extra_hero": ["gnoll"], "names": {"ogre": "Skarn the Breaker"},
             "overrides": {"ogre": {"bonus_hp": 4}}, "can_flee": True,
             "title": "SKARN THE BREAKER",
             "text": "Skarn heaves himself out of a throne of stacked shields, dragging an "
                     "oak-trunk club. 'Little warriors,' he rumbles. 'Skarn will make you "
                     "into little stew.'"},
}


def T(text):
    return {"do": "text", "text": text}


def SAY(who, text):
    return {"do": "say", "who": who, "text": text}


ROOMS = {
    # ================================================================ town
    "highcairn": {
        "name": "Highcairn", "town": True, "wandering": False,
        "desc": "Highcairn's empty market square: the Broken Wheel inn, Kessa's Arms & "
                "Armor, the stone Shrine of the Mountain Father, and the reeve's hall. The "
                "pass road climbs east into the Greyfangs.",
        "features": [
            {"id": "reeve", "label": "Speak with Reeve Odda in the hall",
             "requires": {"not_flag": "quest"}, "once": True, "effects": [
                SAY("Reeve Odda", "Adventurers. Good. I've no soldiers left to send; Skarn "
                                  "killed them at the keep in the spring. The pass must open "
                                  "before the snows, or we starve."),
                SAY("Reeve Odda", "Break Skarn's hold on the keep. If the Durnhal dwarves "
                                  "are still alive up there, bring them home. The town will "
                                  "pay five hundred gold, and the dwarves will pay more. Take "
                                  "these from our stores."),
                {"do": "items_each", "id": "potion of cure moderate wounds", "qty": 1},
                {"do": "flag", "name": "quest"},
                {"do": "journal", "text": "Quest: break Skarn the ogre's hold on Greyfang "
                                          "Keep and rescue the Durnhal dwarves (500 gp)."},
             ]},
            {"id": "reeve2", "label": "Speak with Reeve Odda again",
             "requires": {"flag": "quest", "not_flag": "skarn_dead"}, "effects": [
                SAY("Reeve Odda", "The road's east. Watch for worgs at dusk, and gods "
                                  "speed you."),
             ]},
            {"id": "victory", "label": "Return to Reeve Odda with news of Skarn's fall",
             "requires": {"flag": "skarn_dead"}, "once": True, "effects": [
                T("The reeve rings the hall bell herself. People pour into the square."),
                {"do": "gold", "gp": 500},
                {"do": "xp", "amount": 500, "why": "Greyfang Pass reopened"},
                {"do": "end_adventure"},
             ]},
            {"id": "rumors", "label": "Ask around the Broken Wheel for rumors "
                                      "(Gather Information)",
             "effects": [{"do": "rumors"}]},
            {"id": "shop", "label": "Kessa's Arms & Armor (gear, weapons, armor, fine and "
                                    "magic arms)",
             "effects": [{"do": "shop", "name": "Kessa's Arms & Armor",
                          "sections": ["general", "weapons", "armor", "fine", "magic"]}]},
            {"id": "temple", "label": "Visit the Shrine of the Mountain Father "
                                      "(healing, potions, cures)",
             "effects": [{"do": "temple"}]},
            {"id": "inn", "label": "Rent rooms at the Broken Wheel and rest (5 sp each)",
             "effects": [{"do": "rest", "cost_sp": 5, "safe": True}]},
            {"id": "recruit", "label": "Recruit a new hero (replace the fallen or grow the "
                                       "party)",
             "effects": [{"do": "recruit"}]},
        ],
        "exits": {
            "east": {"to": "pass_road", "label": "Take the pass road into the mountains",
                     "requires": {"flag": "quest"}},
        },
    },
    # ================================================================ the pass
    "pass_road": {
        "terrain": "open",
        "name": "The Pass Road", "travel_minutes": 120, "flee_to": "highcairn",
        "first": "The road climbs through pine and then bare rock. A burned wagon lies on "
                 "its side, its oxen long gone. Claw marks score the wood.",
        "desc": "A rocky road switchbacking up the mountain. Smoke rises from a camp to the "
                "north. East, the road reaches the edge of Widow's Gorge.",
        "encounters_enter": ["road"],
        "features": [
            {"id": "wagon", "label": "Search the burned wagon", "once": True, "effects": [
                T("Under the charred planks: a dwarf trader's lockbox, unopened, and a "
                  "bloody scrap of a Durnhal house banner."),
                {"do": "gold", "gp": 60},
                {"do": "journal", "text": "The Durnhal caravan was taken here; tracks lead "
                                          "toward the keep."}]},
            {"id": "tracks", "label": "Read the tracks (Survival DC 15)",
             "check": {"skill": "Survival", "dc": 15, "retry": False},
             "success": [T("Gnolls, a dozen at least, and the long padding prints of worgs. "
                           "The prisoners' boot prints go east, toward the gorge, then "
                           "north around it: a hidden trail to the keep's back side."),
                         {"do": "flag", "name": "know_postern"},
                         {"do": "xp", "amount": 50, "why": "expert tracking"}],
             "failure": [T("Lots of feet, lots of paws. They went east.")]},
        ],
        "exits": {
            "west": {"to": "highcairn", "label": "Back down to Highcairn"},
            "north": {"to": "gnoll_camp", "label": "Toward the camp smoke"},
            "east": {"to": "gorge", "label": "On to Widow's Gorge"},
        },
    },
    "gnoll_camp": {
        "name": "The Raiders' Camp", "flee_to": "pass_road",
        "desc": "A ring of hide tents around a bone-strewn fire pit, built in the lee of a "
                "boulder. Stolen caravan goods are piled everywhere.",
        "features": [
            {"id": "attack", "label": "Attack the camp", "requires": {"enc_active": "camp"},
             "effects": [{"do": "fight", "enc": "camp"}]},
            {"id": "sneak", "label": "Sneak up on the camp (Move Silently vs their Listen)",
             "requires": {"enc_active": "camp"},
             "effects": [{"do": "stealth_fight", "enc": "camp"}]},
            {"id": "parley", "label": "Parley with the gnolls (Diplomacy: from hostile to "
                                      "indifferent, DC 25)",
             "requires": {"enc_active": "camp"}, "effects": [
                {"do": "diplomacy", "npc": "the gnoll raiders", "start": "hostile",
                 "goal": "indifferent", "success": [
                    {"do": "text", "text": "The gnolls' leader barks a laugh, takes a bribe of "
                                           "your bread and salt, and leads her pack off into "
                                           "the crags. 'Skarn pays badly anyway.'"},
                    {"do": "resolve_enc", "enc": "camp", "factor": 0.75}],
                 "failure": [{"do": "text", "text": "The gnolls start circling, grinning."},
                             {"do": "fight", "enc": "camp"}]}]},
            {"id": "scare", "label": "Make the gnolls think an army is coming "
                                     "(Bluff DC 18)",
             "requires": {"enc_active": "camp"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Bluff", "dc": 18},
             "success": [T("Shouted orders to imaginary soldiers, a few well-placed rocks, a "
                           "horn blast... the gnolls panic and flee into the crags, leaving "
                           "everything behind."),
                         {"do": "resolve_enc", "enc": "camp"}],
             "failure": [T("The gnolls laugh their awful hyena laugh and charge."),
                         {"do": "fight", "enc": "camp"}]},
            {"id": "loot", "label": "Search the camp", "requires": {"enc_cleared": "camp"},
             "once": True, "effects": [
                T("Among the stolen goods: dwarven ale, a sack of coins, two potions, and a "
                  "masterwork dwarven warhammer."),
                {"do": "gold", "gp": 140},
                {"do": "item", "id": "potion of cure moderate wounds"},
                {"do": "item", "id": "potion of bull's strength"},
                {"do": "item", "id": "masterwork warhammer"}]},
        ],
        "exits": {"south": {"to": "pass_road", "label": "Back to the road"}},
    },
    "gorge": {
        "name": "Widow's Gorge", "flee_to": "pass_road",
        "first": "The road ends at a sheer drop. A rope bridge once crossed the gorge; its "
                 "ropes have been cut and dangle into the mist far below. A single stout "
                 "beam still spans the gap.",
        "desc": "The edge of Widow's Gorge. The cut bridge, the single beam across, and on "
                "the far side a crumbling watchtower. A goat trail leads north along the "
                "near edge.",
        "traps": {
            "beam": {"name": "narrow beam over the gorge", "search_dc": 0, "disable_dc": 99,
                     "no_disable": True,
                     "found_text": "", "trigger_text": "The beam shifts under your feet!",
                     "bypass": {"skill": "Balance", "dc": 12},
                     "bypass_label": "Walk the beam (Balance DC 12 each; a fall is deadly)",
                     "effects": [{"do": "damage", "dice": "3d6", "who": "actor",
                                  "save": ["ref", 15, "half"], "tags": ["trap"]}]},
        },
        "on_first_enter": [{"do": "custom", "fn": "reveal_beam"}],
        "features": [
            {"id": "rig", "label": "Rig a rope line across first (Use Rope DC 15; needs rope)",
             "requires": {"has_item": "rope", "not_flag": "line_rigged"},
             "check": {"skill": "Use Rope", "dc": 15, "take10_ok": True},
             "success": [T("You lash a rope to the posts on both ends. Now everyone can cross "
                           "with a handhold."),
                         {"do": "flag", "name": "line_rigged"},
                         {"do": "custom", "fn": "safe_beam"}],
             "failure": [T("The knot slips; the line won't hold yet. Try again.")]},
        ],
        "exits": {
            "west": {"to": "pass_road", "label": "Back along the road"},
            "east": {"to": "watchtower", "label": "Cross the gorge on the beam",
                     "trap": "beam"},
            "north": {"to": "goat_trail", "label": "Follow the goat trail north",
                      "requires": {"flag": "know_postern"}},
        },
    },
    "goat_trail": {
        "name": "The Goat Trail", "flee_to": "gorge",
        "on_first_enter": [{"do": "text", "text": "The wind off the peaks cuts like a knife."},
                           {"do": "exposure", "type": "cold", "dc": 12}],
        "desc": "A dizzying ledge along the gorge wall, wide enough for one. It ends in a "
                "cave that reeks of wet dog, and beyond it, the north wall of the keep.",
        "features": [],
        "exits": {
            "south": {"to": "gorge", "label": "Back to the gorge"},
            "in": {"to": "worg_den", "label": "Into the reeking cave"},
        },
    },
    "worg_den": {
        "dark": True, "name": "The Worg Den", "flee_to": "goat_trail",
        "desc": "A cave floored with bones and fur. A tunnel at the back climbs toward the "
                "keep: the old postern passage.",
        "encounters_enter": ["den"],
        "features": [
            {"id": "bones", "label": "Search the bones", "requires": {"enc_cleared": "den"},
             "once": True, "effects": [
                T("Among the bones, the gear of soldiers who held the keep in spring: a ring, "
                  "a cloak that sheds the dust, and a key on a chain marked 'postern'."),
                {"do": "item", "id": "cloak of resistance +1"},
                {"do": "item", "id": "postern key"},
                {"do": "gold", "gp": 45}]},
        ],
        "exits": {
            "out": {"to": "goat_trail", "label": "Back out to the trail"},
            "up": {"to": "keep_yard", "label": "Up the postern passage into the keep",
                   "blocked_by": "den",
                   "lock": {"key": "postern key", "open_dc": 22, "break_dc": 25,
                            "text": "The postern door at the top of the passage is "
                                    "iron-bound and locked."},
                   "effects": [{"do": "flag", "name": "postern"}]},
        },
    },
    "watchtower": {
        "name": "The Watchtower", "flee_to": "gorge",
        "desc": "A half-ruined tower on the far side of the gorge, used by Skarn's "
                "mercenaries as a lookout. The keep looms beyond, its main gate shut.",
        "encounters_enter": ["tower"],
        "features": [
            {"id": "loot", "label": "Search the lookout post", "requires": {"enc_cleared": "tower"},
             "once": True, "effects": [
                T("The orcs' pay chest and a horn. The horn's signal pattern is scratched "
                  "into its side: three short, one long. The gate guards' all-clear."),
                {"do": "gold", "gp": 110},
                {"do": "flag", "name": "horn"},
                {"do": "journal", "text": "The watchtower horn: three short, one long blasts "
                                          "opens Greyfang Keep's gate."}]},
        ],
        "exits": {
            "west": {"to": "gorge", "label": "Back across the gorge"},
            "east": {"to": "keep_gate", "label": "Approach the keep's main gate"},
        },
    },
    "keep_gate": {
        "name": "The Gate of Greyfang Keep", "flee_to": "watchtower",
        "desc": "A squat stone keep with a barred gate under a gatehouse. Arrow slits stare "
                "down at you.",
        "features": [
            {"id": "horn", "label": "Blow the horn: three short, one long",
             "requires": {"flag": "horn", "not_flag": "gate_open"}, "once": True, "effects": [
                T("A pause... then the bar grinds back and the gate creaks open. A bored "
                  "gnoll waves you in before it notices who you are."),
                {"do": "flag", "name": "gate_open"},
                {"do": "flag", "name": "surprise_yard"}]},
            {"id": "climb", "label": "Climb the wall beside the gatehouse (Climb DC 15 each)",
             "requires": {"not_flag": "gate_open"},
             "check": {"skill": "Climb", "dc": 15, "who": "each", "need": "all"},
             "success": [T("Fingertips and boot-toes, up the old stones and over. You drop "
                           "into the gatehouse and lift the bar."),
                         {"do": "flag", "name": "gate_open"}],
             "failure": [T("Someone slips and falls, hard."),
                         {"do": "damage", "dice": "2d6", "who": "actor"}]},
            {"id": "forge", "label": "Forge marching orders in Skarn's hand and wave them at "
                                     "the gatehouse (Forgery DC 16)",
             "requires": {"not_flag": "gate_open"},
             "check": {"skill": "Forgery", "dc": 16, "retry": False},
             "success": [T("A scrap of hide, a smear of soot, a fair copy of the paw-print "
                           "seal you saw on the raiders' gear. The gnoll squints at it for a "
                           "long moment, shrugs, and hauls the bar back."),
                         {"do": "flag", "name": "gate_open"},
                         {"do": "flag", "name": "surprise_yard"},
                         {"do": "xp", "amount": 100, "why": "talked through the gate"}],
             "failure": [T("The gnoll sniffs the 'orders', then tears them in half and "
                           "laughs. They won't fall for that twice.")]},
            {"id": "force", "label": "Force the gate (Strength DC 25; noisy)",
             "requires": {"not_flag": "gate_open"},
             "check": {"skill": "ability:str", "dc": 25},
             "success": [T("With a groan of tortured iron, the bar snaps!"),
                         {"do": "flag", "name": "gate_open"}],
             "failure": [T("The gate shudders but holds. Laughter drifts down from the arrow "
                           "slits.")]},
        ],
        "exits": {
            "west": {"to": "watchtower", "label": "Back to the watchtower"},
            "in": {"to": "keep_yard", "label": "Through the gate into the keep",
                   "requires": {"flag": "gate_open"}},
        },
    },
    # ================================================================ the keep
    "keep_yard": {
        "name": "The Keep Yard", "flee_to": "keep_gate",
        "desc": "A muddy courtyard of overturned carts and gnawed bones. The great hall "
                "stands across the yard; steps lead down to the cells.",
        "features": [
            {"id": "fight", "label": "Fight the yard guards", "requires": {"enc_active": "yard"},
             "effects": [{"do": "custom", "fn": "yard_fight"}]},
        ],
        "exits": {
            "out": {"to": "keep_gate", "label": "Out through the gate",
                    "requires": {"flag": "gate_open"}},
            "postern": {"to": "worg_den", "label": "Down the postern passage",
                        "requires": {"flag": "postern"}},
            "down": {"to": "cells", "label": "Down to the cells", "blocked_by": "yard",
                     "blocked_text": "The guards are between you and the steps."},
            "north": {"to": "great_hall", "label": "Into the great hall", "blocked_by": "yard",
                      "blocked_text": "The guards are between you and the hall."},
        },
    },
    "cells": {
        "dark": True, "name": "The Cells", "flee_to": "keep_yard",
        "desc": "A row of iron-barred cells. Inside, a dozen grimy, furious dwarves glare "
                "out at you, then realize you're not gnolls.",
        "features": [
            {"id": "free", "label": "Free the dwarves (Open Lock DC 18, or Strength DC 20)",
             "requires": {"not_flag": "dwarves_free"},
             "check": {"skill": "Open Lock", "dc": 18, "take10_ok": True},
             "success": [{"do": "custom", "fn": "free_dwarves"}],
             "failure": [T("The old lock is rusted solid. Try again, or try brute force.")]},
            {"id": "free2", "label": "Wrench the cell doors open (Strength DC 20)",
             "requires": {"not_flag": "dwarves_free"},
             "check": {"skill": "ability:str", "dc": 20},
             "success": [{"do": "custom", "fn": "free_dwarves"}],
             "failure": [T("The bars bend, but not enough.")]},
        ],
        "exits": {"up": {"to": "keep_yard", "label": "Back up to the yard"}},
    },
    "great_hall": {
        "name": "The Great Hall", "flee_to": "keep_yard", "no_rest": True,
        "no_rest_text": "Not in Skarn's own hall.",
        "desc": "A long hall with a fire pit the size of a cart, banners torn down, and a "
                "throne of stacked dwarven shields at the far end.",
        "features": [
            {"id": "fight", "label": "Challenge Skarn", "requires": {"enc_active": "hall"},
             "effects": [{"do": "fight", "enc": "hall"}]},
            {"id": "intimidate", "label": "Order the gnolls to flee before their master falls "
                                          "(Intimidate DC 20)",
             "requires": {"enc_active": "hall"}, "once": True, "once_on_fail": True,
             "check": {"skill": "Intimidate", "dc": 20},
             "success": [T("Your voice rings off the rafters. The gnolls look at each other, "
                           "at you, at Skarn... and bolt for the doors. Skarn roars after "
                           "them, then turns to face you alone."),
                         {"do": "remove_monster", "enc": "hall", "count": 3,
                          "room": "great_hall"},
                         {"do": "fight", "enc": "hall"}],
             "failure": [T("Skarn laughs so hard the rafters shake. 'Get them.'"),
                         {"do": "fight", "enc": "hall"}]},
            {"id": "throne", "label": "Search Skarn's throne", "requires": {"enc_cleared": "hall"},
             "once": True, "effects": [
                T("Skarn's hoard: the Durnhal strongbox, a fine dwarven axe still sharp after "
                  "a hundred years, and the dwarf king's chainmail, cut down into something "
                  "a person could actually wear."),
                {"do": "gold", "gp": 400},
                {"do": "item", "id": "+1 battleaxe"},
                {"do": "item", "id": "+1 chain shirt"},
                {"do": "item", "id": "potion of cure moderate wounds", "qty": 2},
                {"do": "flag", "name": "skarn_dead"},
                {"do": "journal", "text": "Skarn is dead. Return to Highcairn."}]},
        ],
        "exits": {"south": {"to": "keep_yard", "label": "Back to the yard"}},
    },
}


# ---------------------------------------------------------------- scripted bits
def reveal_beam(gm, actor, eff):
    """The beam is an obvious hazard, not a hidden trap."""
    st = gm.gs.rs()
    if "beam" not in st["found_traps"]:
        st["found_traps"].append("beam")


def safe_beam(gm, actor, eff):
    st = gm.gs.rs()
    if "beam" not in st["disabled_traps"]:
        st["disabled_traps"].append("beam")


def yard_fight(gm, actor, eff):
    surprise = "monsters" if "surprise_yard" in gm.gs.flags or "postern" in gm.gs.flags \
        else None
    if surprise:
        gm.ui.gm("They never expected anyone to come in that way. You catch them flat-footed!")
    gm.start_encounter("yard", surprise=surprise)


def free_dwarves(gm, actor, eff):
    if "dwarves_free" in gm.gs.flags:
        return
    gm.gs.flags.add("dwarves_free")
    gm.run([
        T("The cell doors swing open. The dwarves pour out, grabbing chair legs and "
          "broken spears."),
        SAY("Thane Durnhal", "Our thanks, friends. Skarn's in the hall. We'll hold the yard "
                             "and the gate; you go and crack his skull. Here: we hid this "
                             "from the brutes."),
        {"do": "item", "id": "potion of cure moderate wounds"},
        {"do": "xp", "amount": 200, "why": "the dwarves freed"},
        {"do": "journal", "text": "The Durnhal dwarves are free and holding the yard."},
    ])
