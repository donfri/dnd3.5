"""Detailed text character sheets."""
from __future__ import annotations

from typing import List

from . import rules
from .character import Character
from .data.classes import CLASSES
from .data.feats import FEATS
from .data.items import item_data, item_name
from .data.skills import SKILL_ORDER, SKILLS
from .data.spells import SPELLS
from .rules import fmt_mod

W = 78


def _box(title: str) -> str:
    return f"+-- {title} " + "-" * (W - len(title) - 6) + "+"


def _sum(comps) -> int:
    return sum(v for _, v, _ in comps)


def _explain(comps, skip_zero=True) -> str:
    parts = []
    for _, v, src in comps:
        if v == 0 and skip_zero:
            continue
        parts.append(f"{v:+d} {src}")
    return ", ".join(parts) or "+0"


def attack_lines(ch: Character) -> List[str]:
    lines = []
    bab = ch.bab()
    iters = rules.iterative_attacks(bab)
    for w in ch.weapon_infos():
        comps = ch.attack_components(w, power=0)
        total = _sum(comps)
        full = "/".join(f"{total - bab + b:+d}" for b in iters)
        dice, dcomps = ch.damage_profile(w)
        db = _sum(dcomps)
        dmg = dice + (f"{db:+d}" if db else "")
        crit = (f"{w['crit_range']}-20" if w["crit_range"] < 20 else "20") + f"/x{w['crit_mult']}"
        rng = f", {w['range']} ft." if w.get("ranged") and w.get("range") else ""
        state = {"main": "", "off": " [off hand]", None: " [stowed]"}[w.get("wielded")]
        ammo = ""
        if w.get("ammo"):
            ammo = f", {ch.ammo_count(w['ammo'])} {w['ammo']}"
        elif w.get("thrown") and w.get("entry"):
            ammo = f", qty {w['entry'].get('qty', 1)}"
        prof = "" if ch.is_proficient(w) else " (NOT PROFICIENT)"
        lines.append(f"  {w['name']}{state}: {full}  dmg {dmg}  crit {crit}  "
                     f"{w['dtype']}{rng}{ammo}{prof}")
        lines.append(f"      ({_explain(comps)})")
    return lines


def render(ch: Character, full: bool = True) -> str:
    L: List[str] = []
    r = ch.race_data
    L.append("=" * W)
    L.append(f" {ch.name.upper()}".ljust(40) + f"Player: {ch.player or '-'}")
    L.append(f" {r['name']} {ch.class_summary()}  (character level {ch.level})")
    L.append(f" Alignment: {ch.alignment}   Deity: {ch.deity or '-'}   Size: "
             f"{ch.size.title()}   Speed: {ch.speed()} ft.")
    L.append(f" Gender: {ch.gender or '-'}   Age: {ch.age or '-'}   Height: {ch.height or '-'}"
             f"   Weight: {ch.weight or '-'}")
    nxt = ch.xp_next() if ch.level < rules.MAX_LEVEL else None
    L.append(f" XP: {ch.xp}" + (f" / {nxt} for level {ch.level + 1}" if nxt else " (max level)")
             + ("   ** LEVEL UP AVAILABLE **" if ch.can_level_up() else ""))
    L.append(f" Languages: {', '.join(ch.languages)}   Vision: {r['vision']}")
    L.append("=" * W)

    # abilities
    L.append(_box("ABILITIES"))
    for ab in rules.ABILITIES:
        base = ch.base_abilities[ab]
        racial = r["ability_adj"].get(ab, 0)
        inc = ch.ability_increases.count(ab)
        cur = ch.ability(ab)
        temp = (cur or 0) - (base + racial + inc)
        extra = []
        if racial:
            extra.append(f"racial {racial:+d}")
        if inc:
            extra.append(f"level {inc:+d}")
        if temp:
            extra.append(f"temp {temp:+d}")
        if ch.ability_damage.get(ab):
            extra.append(f"damage -{ch.ability_damage[ab]}")
        L.append(f"| {rules.ABILITY_NAMES[ab]:<13} {str(cur):>3}  ({fmt_mod(rules.ability_mod(cur))})"
                 f"   base {base:<3}{'  ' + ', '.join(extra) if extra else ''}")

    # combat
    L.append(_box("COMBAT"))
    hp = ch.hp
    L.append(f"| HP: {hp} / {ch.max_hp()}" + (f"  (+{ch.temp_hp} temp)" if ch.temp_hp else "")
             + f"   Status: {ch.status_word()}   Hit dice: "
             + ", ".join(f"{n}d{CLASSES[c]['hd']}" for c, n in ch.classes().items()))
    ac = ch.ac_components()
    L.append(f"| AC: {_sum(ac)}   Touch: {ch.ac('touch')}   Flat-footed: {ch.ac('flat')}")
    L.append(f"|     ({_explain(ac[1:])})")
    L.append(f"| Initiative: {fmt_mod(ch.initiative())}   Base attack: {fmt_mod(ch.bab())}"
             f"   Grapple: {fmt_mod(ch.grapple())}")
    for kind in ("fort", "ref", "will"):
        comps = ch.save_components(kind)
        L.append(f"| {('Fortitude', 'Reflex', 'Will')[('fort', 'ref', 'will').index(kind)]:<10}"
                 f"{fmt_mod(_sum(comps)):>4}   ({_explain(comps)})")
    acp = ch.armor_check_penalty()
    asf = ch.arcane_spell_failure()
    md = ch.max_dex_bonus()
    L.append(f"| Armor check penalty: {acp}   Max Dex: {md if md is not None else '-'}"
             f"   Arcane spell failure: {asf}%")
    if ch.dr():
        L.append(f"| Damage reduction: {ch.dr()}")
    L.append(_box("ATTACKS"))
    L.extend(attack_lines(ch))

    # skills
    if full:
        L.append(_box("SKILLS   (* = class skill, ACP = armor check penalty applies)"))
        rows = []
        for sk in SKILL_ORDER:
            info = SKILLS[sk]
            ranks = ch.skill_ranks.get(sk, 0)
            if info.get("trained") and ranks == 0:
                continue
            comps = ch.skill_components(sk)
            total = _sum(comps)
            star = "*" if ch.is_class_skill(sk) else " "
            misc = total - int(ranks) - ch.mod(info["ability"])
            rk = f"{ranks:g}"
            rows.append(f"{star}{sk[:24]:<24}{total:+3d} = {rk:>3}r {ch.mod(info['ability']):+d}"
                        f"{info['ability'][:3]} {misc:+d}")
        half = (len(rows) + 1) // 2
        for i in range(half):
            left = rows[i]
            right = rows[i + half] if i + half < len(rows) else ""
            L.append(f"| {left:<37}{right}")
        untrained = [sk for sk in SKILL_ORDER if SKILLS[sk].get("trained")
                     and ch.skill_ranks.get(sk, 0) == 0]
        L.append(f"| Untrained (can't use): {len(untrained)} trained-only skills hidden")

    # feats & abilities
    L.append(_box("FEATS"))
    for f in ch.feat_list():
        base = f.split(" (")[0]
        desc = FEATS.get(base, {}).get("desc", FEATS.get(f, {}).get("desc", ""))
        L.append(f"| {f}: {desc}")
    if full:
        L.append(_box("SPECIAL ABILITIES"))
        for s in ch.special_abilities():
            L.append(f"| {s}")
        daily = []
        if ch.rage_per_day():
            daily.append(f"Rage {ch.uses_left('rage')}/{ch.rage_per_day()}")
        if ch.turn_per_day():
            daily.append(f"Turn undead {ch.uses_left('turn')}/{ch.turn_per_day()}")
        if "Strength" in ch.domains:
            daily.append(f"Feat of strength {ch.uses_left('feat_of_strength')}/1")
        if daily:
            L.append("| Daily uses left: " + ", ".join(daily))

    # spells
    for cls in ch.caster_classes():
        L.extend(spell_block(ch, cls))

    # effects
    active = [e for e in ch.effects if not e.hidden]
    if active or ch.afflictions:
        L.append(_box("ACTIVE EFFECTS & CONDITIONS"))
        for e in active:
            L.append(f"| {e.describe()}")
        for a in ch.afflictions:
            L.append(f"| Disease: {a['name']} (Fort DC {a['dc']} each day)")

    # gear
    if full:
        L.append(_box("EQUIPMENT"))
        for e in ch.inventory:
            d = item_data(e)
            slot = f" [{e['slot']}]" if e.get("slot") else ""
            qty = f" x{e['qty']}" if e.get("qty", 1) > 1 else ""
            L.append(f"| {item_name(e)}{qty}{slot}   ({d.get('weight', 0)} lb.)")
        L.append(f"| Money: {rules.money_str(ch.cp)}   Carried: {ch.total_weight()} lb. "
                 f"({ch.load()} load; heavy load limit "
                 f"{rules.heavy_load(ch.ability('str') or 0, ch.base_size):g} lb.)")
    if ch.notes:
        L.append(_box("NOTES"))
        for n in ch.notes[-8:]:
            L.append(f"| {n}")
    L.append("=" * W)
    return "\n".join(L)


def spell_block(ch: Character, cls: str) -> List[str]:
    L = [_box(f"SPELLS ({CLASSES[cls]['name']}, caster level {ch.caster_level(cls)})")]
    per = ch.spells_per_day(cls)
    ab = ch.cast_ability(cls)
    dcs = ", ".join(f"L{sl} DC {10 + sl + ch.mod(ab)}" for sl in sorted(per))
    L.append(f"| Casting ability: {rules.ABILITY_NAMES[ab]}   Save DCs: {dcs}")
    if CLASSES[cls].get("prepared"):
        dom = ch.domain_slots() if cls == "cleric" else {}
        for sl in sorted(per):
            slots = ch.prepared.get(cls, {}).get(sl, [])
            names = []
            for s in slots:
                nm = s["spell"] + (" (D)" if s.get("domain") else "")
                names.append(f"[{'x' if s['used'] else ' '}] {nm}")
            extra = f" + {dom[sl]} domain" if sl in dom else ""
            L.append(f"| Level {sl}: {per[sl]}/day{extra}")
            for i in range(0, len(names), 3):
                L.append("|    " + "   ".join(names[i:i + 3]))
        if cls == "wizard":
            L.append("| Spellbook: " + ", ".join(sorted(ch.spellbook)))
        if cls == "cleric":
            L.append("| Domains: " + ", ".join(ch.domains) +
                     ("   (can spontaneously convert prepared spells into cure spells)"
                      if not ch.evil else ""))
    else:
        for sl in sorted(per):
            used = ch.spont_used.get(sl, 0)
            known = ", ".join(ch.spells_known.get(sl, []))
            L.append(f"| Level {sl}: {per[sl] - used}/{per[sl]} left   Known: {known}")
    return L


def short_status(ch) -> str:
    parts = [f"{ch.name}", f"HP {ch.hp}/{ch.max_hp()}" + (f"+{ch.temp_hp}" if ch.temp_hp else ""),
             f"AC {ch.ac()}"]
    w = ch.status_word()
    if w != "ok":
        parts.append(w.upper())
    tags = [e.name for e in ch.effects if not e.hidden]
    if tags:
        parts.append("[" + ", ".join(tags[:4]) + "]")
    return "  ".join(parts)


def spell_description(name: str) -> str:
    s = SPELLS[name]
    lv = ", ".join(f"{k.replace('_domain', ' domain').title()} {v}" for k, v in s["levels"].items())
    save = f"; save {s['save'][0].title()} {s['save'][1]}" if s.get("save") else ""
    return f"{name} ({s['school']}; {lv}{save}): {s['desc']}"
