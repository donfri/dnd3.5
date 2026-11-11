"""Adventures. Each module is plain data (rooms, encounters, text) plus a few scripts.

To add one: copy an existing module, give it a unique ID, and list it below.
"""
from . import drowned_lantern, ember_barrow, greyfang_pass, thornwood_fen

ORDER = [ember_barrow, drowned_lantern, greyfang_pass, thornwood_fen]
ADVENTURES = {m.ID: m for m in ORDER}


def get(adv_id: str):
    return ADVENTURES.get(adv_id, ember_barrow)
