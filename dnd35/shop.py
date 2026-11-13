"""Buying, selling, and managing inventory."""
from __future__ import annotations

from typing import List, Sequence

from . import rules
from .character import Character
from .data.items import EQUIPPABLE_KINDS, GEAR, SHOP_STOCK, item_data, item_name, make_item
from .ui import c


def _price(iid: str) -> int:
    return item_data(make_item(iid))["cost"]


def _pick_char(ui, party: Sequence[Character], prompt: str = "Who?") -> Character:
    alive = [p for p in party if not p.dead]
    if len(alive) == 1:
        return alive[0]
    return alive[ui.choose(prompt, [f"{p.name} ({rules.money_str(p.cp)})" for p in alive])]


def shop_menu(ui, party: Sequence[Character], shop_name: str, sections: List[str],
              markup: float = 1.0) -> None:
    while True:
        ui.sub(shop_name)
        ui.out("  " + "   ".join(f"{p.name}: {rules.money_str(p.cp)}" for p in party
                                 if not p.dead))
        opts = [f"Browse {s}" for s in sections] + ["Sell items (half price)",
                                                    "Give money to another hero",
                                                    "Leave"]
        i = ui.choose("Shop", opts)
        if i < len(sections):
            browse(ui, party, sections[i], markup)
        elif i == len(sections):
            sell(ui, party)
        elif i == len(sections) + 1:
            give_money(ui, party)
        else:
            return


def browse(ui, party, section: str, markup: float) -> None:
    stock = SHOP_STOCK[section]
    while True:
        opts = []
        for iid in stock:
            d = item_data(make_item(iid))
            price = int(_price(iid) * markup)
            extra = ""
            if d["kind"] == "weapon":
                extra = (f"{d['damage']} {('19' if d['crit_range'] == 19 else str(d['crit_range']))}"
                         f"{'-20' if d['crit_range'] < 20 else ''}/x{d['crit_mult']} "
                         f"{d['category']} {d['hands']}")
            elif d["kind"] in ("armor", "shield"):
                extra = (f"AC +{d['ac']}, max Dex {d['max_dex'] if d['max_dex'] is not None else '-'}"
                         f", ACP {d['acp']}, ASF {d['asf']}%, {d['category']}")
            else:
                extra = d.get("desc", "")
            opts.append(f"{d['name']:<30} {rules.money_str(price):>10}  {extra}")
        i = ui.choose(f"Buy what? ({section})", opts, allow_cancel=True)
        if i is None:
            return
        iid = stock[i]
        who = _pick_char(ui, party, "Buy for whom?")
        price = int(_price(iid) * markup)
        qty = 1
        d = item_data(make_item(iid))
        if d.get("stack") or d["kind"] == "consumable" or iid in ("dagger", "javelin"):
            max_afford = who.cp // price if price else 20
            if max_afford <= 0:
                ui.bad(f"{who.name} can't afford that.")
                continue
            qty = ui.ask_int("How many?", 1, min(20, max_afford), 1)
        cost = price * qty
        if cost > who.cp:
            ui.bad(f"{who.name} can't afford that ({rules.money_str(cost)}).")
            continue
        who.cp -= cost
        count = GEAR.get(iid, {}).get("ammo_count")
        entry = who.add_item(iid, qty * (count or 1))
        ui.good(f"{who.name} buys {item_name(entry)} x{qty * (count or 1)} for "
                f"{rules.money_str(cost)}.")
        if d["kind"] in ("armor", "shield", "weapon") and ui.confirm("Equip it now?", True):
            ui.out(who.equip(entry))


def sell(ui, party) -> None:
    who = _pick_char(ui, party, "Who is selling?")
    # a good eye for value (Appraise DC 12) gets a better deal: 55% instead of half
    from . import dice
    best = max(party, key=lambda p: p.skill_total("Appraise"))
    with dice.rolling(best, "Appraise"):
        r = dice.d20()
    keen = r + best.skill_total("Appraise") >= 12
    ui.roll(f"{best.name} Appraise: d20={r} {best.skill_total('Appraise'):+d} = "
            f"{r + best.skill_total('Appraise')} vs DC 12 -> "
            f"{'knows what things are worth (+10% on sales)' if keen else 'no better deal'}")
    while True:
        items = [e for e in who.inventory if item_data(e)["cost"] > 0
                 and e["id"] not in ("ember sigil", "iron key")]
        if not items:
            ui.out("Nothing to sell.")
            return
        opts = []
        for e in items:
            d = item_data(e)
            unit = d["cost"] * (11 if keen else 10) // 20
            if d.get("ammo_count"):
                unit = d["cost"] * (11 if keen else 10) // 20 // d["ammo_count"]
            slot = " [equipped]" if e.get("slot") else ""
            opts.append(f"{item_name(e)} x{e['qty']}{slot}  -> {rules.money_str(unit)} each")
        i = ui.choose("Sell which item?", opts, allow_cancel=True)
        if i is None:
            return
        e = items[i]
        d = item_data(e)
        unit = d["cost"] * (11 if keen else 10) // 20
        if d.get("ammo_count"):
            unit = d["cost"] * (11 if keen else 10) // 20 // d["ammo_count"]
        qty = 1 if e["qty"] == 1 else ui.ask_int("How many?", 1, e["qty"], e["qty"])
        e.pop("slot", None) if qty >= e["qty"] else None
        who.remove_item(e, qty)
        who.cp += unit * qty
        ui.good(f"Sold for {rules.money_str(unit * qty)}.")


def give_money(ui, party) -> None:
    alive = [p for p in party if not p.dead]
    if len(alive) < 2:
        ui.out("No one to give money to.")
        return
    giver = _pick_char(ui, alive, "Who gives?")
    others = [p for p in alive if p is not giver]
    taker = others[0] if len(others) == 1 else others[ui.choose("To whom?",
                                                                [p.name for p in others])]
    gp = ui.ask_int("How many gold pieces?", 0, giver.cp // 100, 0)
    giver.cp -= gp * 100
    taker.cp += gp * 100
    ui.good(f"{giver.name} gives {gp} gp to {taker.name}.")


def inventory_menu(ui, party: Sequence[Character], in_combat: bool = False) -> None:
    who = _pick_char(ui, party, "Whose inventory?")
    with ui.acting(who.player):
        _inventory_loop(ui, party, who)


def _inventory_loop(ui, party, who) -> None:
    while True:
        ui.sub(f"{who.name}'s inventory ({who.total_weight()} lb., {who.load()} load, "
               f"{rules.money_str(who.cp)})")
        entries = list(who.inventory)
        if not entries:
            ui.out(f"{who.name} carries nothing.")
            return
        opts = []
        for e in entries:
            d = item_data(e)
            slot = c(f" [{e['slot']}]", "green") if e.get("slot") else ""
            qty = f" x{e['qty']}" if e.get("qty", 1) > 1 else ""
            desc = d.get("desc", "")
            opts.append(f"{item_name(e)}{qty}{slot}  {desc}")
        i = ui.choose("Select an item", opts, allow_cancel=True)
        if i is None:
            return
        e = entries[i]
        d = item_data(e)
        acts = []
        if d["kind"] in EQUIPPABLE_KINDS:
            if e.get("slot"):
                acts.append("Unequip")
            else:
                acts.append("Equip")
                if d["kind"] == "weapon" and d["hands"] in ("light", "one"):
                    acts.append("Equip in off hand")
        if d["kind"] == "consumable" and d.get("use") in ("spell", "antitoxin"):
            acts.append("Use / drink")
        if d["kind"] == "consumable" and d.get("use") == "scroll":
            acts.append("Read scroll")
        if d["kind"] in ("wand", "staff"):
            acts.append("Use / drink")
        acts += ["Give to another hero", "Drop"]
        j = ui.choose(f"{item_name(e)}", acts, allow_cancel=True)
        if j is None:
            continue
        act = acts[j]
        if act == "Equip":
            if d["kind"] == "armor" and not who.armor_proficient(d):
                ui.warn("Not proficient: its armor check penalty will apply to attacks.")
            if d["kind"] == "weapon" and not who.is_proficient({"wid": e["id"],
                                                                 "category": d["category"]}):
                ui.warn("Not proficient: -4 on attack rolls.")
            ui.out(who.equip(e))
        elif act == "Equip in off hand":
            ui.out(who.equip(e, "off"))
        elif act == "Unequip":
            who.unequip(e)
            ui.out(f"{who.name} unequips {item_name(e)}.")
        elif act in ("Use / drink", "Read scroll"):
            from .magic import use_consumable_out_of_combat
            use_consumable_out_of_combat(ui, who, e, party)
        elif act == "Give to another hero":
            others = [p for p in party if p is not who and not p.dead]
            if not others:
                ui.out("No one to give it to.")
                continue
            to = others[0] if len(others) == 1 else others[ui.choose("To whom?",
                                                                     [p.name for p in others])]
            qty = 1 if e["qty"] == 1 else ui.ask_int("How many?", 1, e["qty"], e["qty"])
            given = dict(e, qty=qty)
            given.pop("slot", None)
            if qty >= e["qty"]:
                who.inventory.remove(e)
            else:
                e["qty"] -= qty
            to.add_item(given)
            ui.out(f"{who.name} gives {item_name(given)} x{qty} to {to.name}.")
        elif act == "Drop":
            if ui.confirm(f"Really drop {item_name(e)}?", False):
                e.pop("slot", None)
                who.inventory.remove(e)
