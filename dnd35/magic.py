"""Spell resolution, saving throws, potions and scrolls."""
from __future__ import annotations

from typing import List, Optional, Sequence

from . import dice, rules
from .creature import Creature
from .data.classes import CLASSES
from .data.items import item_data
from .data.monsters import MONSTERS
from .data.spells import SPELLS
from .effects import Effect, ROUNDS_PER_HOUR, ROUNDS_PER_MINUTE


# ---------------------------------------------------------------- helpers
def saving_throw(ui, target: Creature, kind: str, dc: int, tags: Sequence[str] = (),
                 label: str = "") -> bool:
    roll = dice.d20()
    comps = target.save_components(kind, tags)
    bonus = sum(v for _, v, _ in comps)
    consume_one_shot(target, "save")
    total = roll + bonus
    ok = (roll == 20) or (roll != 1 and total >= dc)
    names = {"fort": "Fortitude", "ref": "Reflex", "will": "Will"}
    ui.roll(f"{target.name} {names[kind]} save{(' vs ' + label) if label else ''}: "
            f"d20={roll} {bonus:+d} = {total} vs DC {dc} -> {'SAVED' if ok else 'failed'}")
    return ok


def consume_one_shot(c: Creature, what: str) -> None:
    for e in list(c.effects):
        if "consume_any" in e.tags or (what == "attack" and "consume_attack" in e.tags):
            c.effects.remove(e)


def touch_attack(ui, caster: Creature, target: Creature, ranged: bool, combat=None) -> bool:
    roll = dice.d20()
    bonus = caster.bab() + (caster.mod("dex") if ranged else caster.mod("str"))
    bonus += rules.SIZE_ATTACK_AC[caster.size]
    bonus += caster.bonus("attack") + caster.bonus("ranged_attack" if ranged else "melee_attack")
    note = ""
    if ranged and combat is not None and combat.shooting_into_melee(caster, target):
        if not caster.has_feat("Precise Shot"):
            bonus -= 4
            note = " (-4 firing into melee)"
    consume_one_shot(caster, "attack")
    ac = target.ac("touch", attacker=caster, ranged=ranged)
    if combat is not None and combat.is_flat_footed(target):
        ac = min(ac, target.ac("touch", attacker=caster, ranged=ranged) -
                 max(0, target.mod("dex")))
    total = roll + bonus
    hit = roll == 20 or (roll != 1 and total >= ac)
    ui.roll(f"{'Ranged' if ranged else 'Melee'} touch attack: d20={roll} {bonus:+d} = {total} "
            f"vs touch AC {ac}{note} -> {'HIT' if hit else 'miss'}")
    return hit


def deal_damage(ui, target: Creature, amount: int, dtype: str, combat=None,
                source: str = "", magic: bool = True) -> int:
    dealt, note = target.take_damage(amount, dtype, magic=magic)
    extra = f" ({note})" if note else ""
    shown = dtype.replace("*", "")
    ui.out(f"  {target.name} takes {dealt} {shown} damage{extra}." if dealt else
           f"  {target.name} takes no damage{extra}.")
    if combat is not None:
        combat.after_damage(target)
    else:
        report_down(ui, target)
    return dealt


def report_down(ui, target: Creature) -> None:
    if target.dead:
        ui.bad(f"  {target.name} is {'slain' if not target.is_pc else 'DEAD'}!")
    elif target.is_pc and target.hp < 0:
        ui.bad(f"  {target.name} falls unconscious and is dying!")
    elif target.is_pc and target.hp == 0:
        ui.warn(f"  {target.name} is disabled (0 hp).")


def heal(ui, target: Creature, amount: int) -> int:
    was_down = target.hp < 0
    healed = target.heal(amount)
    ui.good(f"  {target.name} recovers {healed} hp ({target.hp}/{target.max_hp()}).")
    if was_down and target.hp >= 0:
        ui.good(f"  {target.name} regains consciousness!")
    return healed


def duration(spell: str, cl: int) -> int:
    per_level = {
        "Resistance": ROUNDS_PER_MINUTE, "Mage Armor": ROUNDS_PER_HOUR * cl,
        "Shield": ROUNDS_PER_MINUTE * cl, "Ray of Enfeeblement": ROUNDS_PER_MINUTE * cl,
        "True Strike": 2, "Enlarge Person": ROUNDS_PER_MINUTE * cl,
        "Bull's Strength": ROUNDS_PER_MINUTE * cl, "Cat's Grace": ROUNDS_PER_MINUTE * cl,
        "Bear's Endurance": ROUNDS_PER_MINUTE * cl, "Blur": ROUNDS_PER_MINUTE * cl,
        "Haste": cl, "Guidance": ROUNDS_PER_MINUTE, "Virtue": ROUNDS_PER_MINUTE,
        "Bless": ROUNDS_PER_MINUTE * cl, "Shield of Faith": ROUNDS_PER_MINUTE * cl,
        "Divine Favor": ROUNDS_PER_MINUTE, "Protection from Evil": ROUNDS_PER_MINUTE * cl,
        "Magic Weapon": ROUNDS_PER_MINUTE * cl, "Doom": ROUNDS_PER_MINUTE * cl,
        "Longstrider": ROUNDS_PER_HOUR * cl, "Resist Energy": 10 * ROUNDS_PER_MINUTE * cl,
        "Aid": ROUNDS_PER_MINUTE * cl, "Spiritual Weapon": cl, "Hold Person": cl,
        "Prayer": cl, "Magic Vestment": ROUNDS_PER_HOUR * cl,
        "Magic Circle against Evil": 10 * ROUNDS_PER_MINUTE * cl,
        "Flare": ROUNDS_PER_MINUTE, "Hideous Laughter": cl, "Remove Fear": 10 * ROUNDS_PER_MINUTE,
        "Entangle": ROUNDS_PER_MINUTE * cl, "Shillelagh": ROUNDS_PER_MINUTE * cl,
        "Magic Fang": ROUNDS_PER_MINUTE * cl, "Eagle's Splendor": ROUNDS_PER_MINUTE * cl,
        "Owl's Wisdom": ROUNDS_PER_MINUTE * cl, "Fox's Cunning": ROUNDS_PER_MINUTE * cl,
        "Heroism": 10 * ROUNDS_PER_MINUTE * cl, "Barkskin": 10 * ROUNDS_PER_MINUTE * cl,
        "Flaming Sphere": cl, "Hold Animal": cl, "Hold Monster": cl, "Slow": cl,
        "Good Hope": ROUNDS_PER_MINUTE * cl, "Displacement": cl, "Fear": cl,
        "Call Lightning": ROUNDS_PER_MINUTE * cl, "Call Lightning Storm": ROUNDS_PER_MINUTE * cl,
        "Greater Magic Fang": ROUNDS_PER_HOUR * cl,
        "Freedom of Movement": 10 * ROUNDS_PER_MINUTE * cl, "Death Ward": ROUNDS_PER_MINUTE * cl,
        "Divine Power": cl, "Spell Immunity": 10 * ROUNDS_PER_MINUTE * cl,
        "Greater Invisibility": cl, "Stoneskin": 10 * ROUNDS_PER_MINUTE * cl,
        "Righteous Might": cl, "Dispel Evil": cl,
    }
    return per_level.get(spell, ROUNDS_PER_MINUTE)


def _is_humanoid(t: Creature) -> bool:
    return t.ctype == "humanoid"


def _mind_immune(t: Creature, spell_tags) -> bool:
    imm = t.immunities()
    if "mind-affecting" in spell_tags and ("mind-affecting" in imm or
                                           getattr(t, "block", {}).get("mindless")):
        return True
    if "sleep" in spell_tags and ("sleep" in imm or "sleep" in
                                  getattr(t, "race_data", {}).get("immune", [])):
        return True
    return False


def _freed(t: Creature, what: str) -> bool:
    return what in t.immunities()


def _hold(ui, t, dc, stags, name, buff, ok: bool, why: str) -> None:
    if not ok:
        ui.out(f"  {t.name} is unaffected ({why}).")
    elif _freed(t, "paralysis"):
        ui.out(f"  {t.name} moves freely; the spell finds no grip.")
    elif not saving_throw(ui, t, "will", dc, stags):
        buff(t, name, tags=["paralyzed"], data={"save_each_round": ("will", dc, stags)})


def drain_level(ui, target, dc: int) -> None:
    """Energy drain: one more negative level (-1 attacks/saves/checks, -5 hp)."""
    if "negative" in target.immunities() or not target.is_living():
        ui.out(f"  {target.name} resists the draining touch.")
        return
    old = target.get_effect("Negative levels")
    n = (old.data.get("n", 0) if old else 0) + 1
    target.add_effect(Effect("Negative levels", None,
                             [("attack", "untyped", -n), ("saves", "untyped", -n),
                              ("skills", "untyped", -n), ("max_hp", "untyped", -5 * n)],
                             data={"n": n, "dc": dc}))
    ui.bad(f"  {target.name}'s life is drained! ({n} negative level{'s' if n > 1 else ''})")
    if target.is_pc and n >= target.level:
        target.dead = True
        ui.bad(f"  {target.name} is drained of all life and DIES!")
    target.check_death()


def raise_dead(ui, target) -> None:
    """Bring a dead hero back (Raise Dead / temple service), with the 3.5 cost in
    simplified form: XP drops to half a level below the hero's current level (or 2
    Constitution at 1st level)."""
    target.dead = False
    target.stable = True
    target.effects = []
    target.damage = max(0, target.max_hp() - max(1, target.level))
    if target.level <= 1:
        target.base_abilities["con"] = max(3, target.base_abilities["con"] - 2)
        ui.warn(f"  {target.name} returns weakened: -2 Constitution.")
    else:
        lo = rules.xp_for_level(target.level - 1)
        hi = rules.xp_for_level(target.level)
        target.xp = min(target.xp, hi - (hi - lo) // 2)
        ui.warn(f"  {target.name} returns, but much of their recent experience is lost "
                f"(XP now {target.xp}).")
    for by_level in getattr(target, "prepared", {}).values():
        for slots in by_level.values():
            for sl in slots:
                sl["used"] = True
    ui.good(f"  {target.name} gasps and opens their eyes. ALIVE! ({target.hp}/"
            f"{target.max_hp()} hp)")


def _save_tags(spell: dict, caster: Creature) -> List[str]:
    tags = ["spell", spell["school"]]
    tags += list(spell["tags"])
    if caster.evil:
        tags.append("evil_source")
    return tags


# ---------------------------------------------------------------- metamagic
_META: set = set()

METAMAGIC = {"Empower Spell": 2, "Extend Spell": 1, "Maximize Spell": 3, "Quicken Spell": 4,
             "Still Spell": 1, "Silent Spell": 1}


def _sroll(expr: str):
    """A spell's dice roll, with Empower / Maximize applied."""
    r = dice.roll(expr)
    if not _META & {"Empower Spell", "Maximize Spell"}:
        return r
    rolled = r.total - r.flat
    if "Maximize Spell" in _META:
        best = dice.maximum(expr) - r.flat
        extra = rolled // 2 if "Empower Spell" in _META else 0
        return dice.RollResult(f"{expr} maximized", r.flat + best + extra, r.rolls, r.flat)
    return dice.RollResult(f"{expr} empowered", r.flat + rolled * 3 // 2, r.rolls, r.flat)


def metamagic_choices(caster, cast: dict) -> List[tuple]:
    """(label, feat, extra spell levels, rod entry) a caster could add to this cast."""
    out = []
    if cast.get("item") or not hasattr(caster, "feat_list"):
        return out
    lvl = cast["level"]
    feats = [f for f in caster.feat_list() if f in METAMAGIC]
    cls = cast["class"]
    for f in feats:
        adj = METAMAGIC[f]
        if _slot_at(caster, cls, lvl + adj, cast) is not None:
            out.append((f"{f} (uses a level {lvl + adj} slot)", f, adj, None))
    for e in getattr(caster, "inventory", []):
        d = item_data(e)
        if d["kind"] == "rod" and lvl <= d["max_level"] and \
                caster.daily.get(f"rod:{e['id']}", 0) < 3:
            out.append((f"{d['metamagic']} via {d['name']} "
                        f"({3 - caster.daily.get('rod:' + e['id'], 0)}/day left)",
                        d["metamagic"], 0, e))
    return out


def _slot_at(caster, cls: str, level: int, cast: dict):
    """A free slot of the given level to pay for metamagic, or None."""
    if CLASSES[cls].get("prepared"):
        for s in caster.prepared.get(cls, {}).get(level, []):
            if not s["used"] and s is not cast.get("slot") and not s.get("domain"):
                return s
        return None
    per = caster.spells_per_day(cls)
    if level in per and caster.spont_used.get(level, 0) < per[level]:
        return ("spont", level)
    return None


def pick_metamagic(ui, caster, cast: dict, in_combat: bool = False) -> Optional[dict]:
    """Ask whether to add metamagic. Returns {"feats": set, "pay": ...} or {} for none,
    or None if cancelled."""
    choices = metamagic_choices(caster, cast)
    if in_combat:
        pass
    if not choices:
        return {}
    opts = ["Cast it normally"] + [c[0] for c in choices]
    i = ui.choose("Add metamagic?", opts, allow_cancel=True, default=0)
    if i is None:
        return None
    if i == 0:
        return {}
    label, feat, adj, rod = choices[i - 1]
    return {"feats": {feat}, "adj": adj, "rod": rod}


def pay_metamagic(caster, cast: dict, meta: dict) -> None:
    """Spend the slot (or rod use) for a metamagic cast instead of the normal one."""
    if meta.get("rod") is not None:
        key = f"rod:{meta['rod']['id']}"
        caster.daily[key] = caster.daily.get(key, 0) + 1
        caster.expend(cast)
        return
    slot = _slot_at(caster, cast["class"], cast["level"] + meta["adj"], cast)
    if isinstance(slot, tuple):
        caster.spont_used[slot[1]] = caster.spont_used.get(slot[1], 0) + 1
    elif slot is not None:
        slot["used"] = True


# ---------------------------------------------------------------- spell resistance
def resists(ui, caster, target, cl: int) -> bool:
    sr = target.spell_resistance() if hasattr(target, "spell_resistance") else 0
    if not sr:
        return False
    r = dice.d20()
    bonus = cl + (2 if caster.has_feat("Spell Penetration") else 0)
    ok = r + bonus >= sr
    ui.roll(f"Caster level check vs {target.name}'s spell resistance {sr}: d20={r}"
            f"{bonus:+d} = {r + bonus} -> {'penetrates' if ok else 'RESISTED'}")
    return not ok


# ---------------------------------------------------------------- dispel
def dispel(ui, caster, target, cl: int, allies) -> None:
    ally_names = {a.name for a in allies}
    hostile = target not in allies
    pool = [e for e in target.effects if e.data.get("cl") and
            ((e.source not in ally_names) if not hostile else True)]
    if not pool:
        ui.out(f"  {target.name} has no magic to dispel.")
        return
    any_gone = False
    for e in list(pool):
        r = dice.d20()
        tot = r + min(10, cl)
        dc = 11 + e.data["cl"]
        ui.roll(f"Dispel check vs {e.name}: d20={r}+{min(10, cl)} = {tot} vs DC {dc}")
        if tot >= dc:
            target.effects.remove(e)
            ui.good(f"  {e.name} on {target.name} is dispelled!")
            any_gone = True
            if e.data.get("summoned"):
                target.dead = True
        if hostile and any_gone:
            break   # a targeted dispel strips the strongest effect it can reach
    if not any_gone:
        ui.out("  The magic holds.")


# ---------------------------------------------------------------- summoning
SUMMON_LISTS = {
    "Summon Monster": {1: ["dire rat", "eagle"], 2: ["wolf", "riding dog"],
                       3: ["black bear", "leopard"], 4: ["dire wolf", "owlbear"],
                       5: ["brown bear", "dire boar"]},
    "Summon Nature's Ally": {1: ["eagle", "dire rat"], 2: ["wolf", "riding dog"],
                             3: ["black bear", "leopard"], 4: ["dire boar", "dire wolf"],
                             5: ["brown bear", "owlbear"]},
}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def summon_info(spell: str):
    base, num = spell.rsplit(" ", 1)
    lvl = {v: k for k, v in ROMAN.items()}[num]
    return base, lvl


# ---------------------------------------------------------------- main cast
def cast_spell(ui, caster: Creature, spell_name: str, targets: List[Creature], cl: int,
               dc: int, combat=None, allies: Optional[List[Creature]] = None,
               enemies: Optional[List[Creature]] = None, meta=()) -> bool:
    """Resolve a spell. Returns True if the spell was used up (always, once cast)."""
    global _META
    _META = set(meta or ())
    try:
        return _cast_spell(ui, caster, spell_name, targets, cl, dc, combat, allies, enemies)
    finally:
        _META = set()


def _cast_spell(ui, caster, spell_name, targets, cl, dc, combat, allies, enemies) -> bool:
    sp = SPELLS[spell_name]
    allies = allies if allies is not None else ([caster] + [t for t in targets if t is not caster])
    enemies = enemies or []
    stags = _save_tags(sp, caster)
    meta_txt = " (" + ", ".join(sorted(m.split()[0].lower() for m in _META)) + ")" \
        if _META else ""
    ui.out(f"{caster.name} casts {spell_name}{meta_txt}!", ("bmagenta",))
    if sp["sr"] and sp["target"] in ("enemy", "enemies"):
        kept = [t for t in targets if t is caster or t in (allies or [])
                or not resists(ui, caster, t, cl)]
        if not kept:
            return True
        targets = kept
    t0 = targets[0] if targets else caster
    n = spell_name

    def buff(target, eff_name, mods=(), tags=(), dur=None, data=None):
        d = dur if dur is not None else duration(n, cl)
        if d and "Extend Spell" in _META:
            d *= 2
        data = dict(data or {})
        data.setdefault("cl", cl)
        e = Effect(eff_name, d, mods, tags, source=caster.name, data=data)
        target.add_effect(e)
        ui.good(f"  {target.name}: {e.describe()}")
        return e

    # ------------------------------------------------------------ cantrips
    if n in ("Acid Splash", "Ray of Frost"):
        if touch_attack(ui, caster, t0, True, combat):
            deal_damage(ui, t0, _sroll("1d3").total, "acid" if n == "Acid Splash" else "cold",
                        combat)
    elif n == "Disrupt Undead":
        if t0.ctype != "undead":
            ui.out("  The ray has no effect on the living.")
        elif touch_attack(ui, caster, t0, True, combat):
            deal_damage(ui, t0, _sroll("1d6").total, "positive", combat)
    elif n == "Daze":
        if not _is_humanoid(t0) or t0.hit_dice() > 4 or _mind_immune(t0, sp["tags"]):
            ui.out(f"  {t0.name} is unaffected.")
        elif not saving_throw(ui, t0, "will", dc, stags):
            buff(t0, "Dazed", tags=["dazed"], dur=1)
    elif n == "Resistance":
        buff(t0, "Resistance", [("saves", "resistance", 1)])
    elif n in ("Detect Magic", "Light", "Mage Hand", "Prestidigitation", "Know Direction"):
        ui.out(f"  {sp['desc']}")
    # ------------------------------------------------------------ arcane 1
    elif n == "Magic Missile":
        missiles = min(5, 1 + (cl - 1) // 2)
        for i in range(missiles):
            tgt = targets[i % len(targets)] if targets else t0
            if tgt.get_effect("Shield"):
                ui.out(f"  The missile splashes harmlessly against {tgt.name}'s shield!")
                continue
            if tgt.dead:
                continue
            r = _sroll("1d4+1")
            ui.roll(f"Missile {i + 1}: {r.detail()}")
            deal_damage(ui, tgt, r.total, "force", combat)
    elif n == "Sleep":
        pool = 4
        cands = sorted([t for t in targets if not t.dead], key=lambda t: t.hit_dice())
        for t in cands:
            if t.hit_dice() > pool:
                continue
            if not t.is_living() or _mind_immune(t, sp["tags"]) or t.hit_dice() >= 5:
                ui.out(f"  {t.name} is unaffected.")
                continue
            pool -= t.hit_dice()
            if not saving_throw(ui, t, "will", dc, stags):
                buff(t, "Asleep", tags=["asleep"], dur=ROUNDS_PER_MINUTE * cl)
        if pool == 4:
            ui.out("  No one falls asleep.")
    elif n == "Color Spray":
        for t in targets:
            if _mind_immune(t, sp["tags"]) or not t.is_living():
                ui.out(f"  {t.name} is unaffected.")
                continue
            if saving_throw(ui, t, "will", dc, stags):
                continue
            hd = t.hit_dice()
            if hd <= 2:
                buff(t, "Color Spray (unconscious)", tags=["unconscious"],
                     dur=_sroll("2d4").total)
            elif hd <= 4:
                buff(t, "Color Spray (blinded)", tags=["blinded"], dur=_sroll("1d4").total)
                buff(t, "Color Spray (stunned)", tags=["stunned"], dur=1)
            else:
                buff(t, "Color Spray (stunned)", tags=["stunned"], dur=1)
    elif n == "Burning Hands":
        r = _sroll(f"{min(5, cl)}d4")
        ui.roll(f"Flames: {r.detail()}")
        for t in targets:
            _area_damage(ui, t, r.total, "fire", dc, stags, combat)
    elif n == "Mage Armor":
        buff(t0, "Mage Armor", [("ac", "armor", 4)])
    elif n == "Shield":
        buff(caster, "Shield", [("ac", "shield", 4)])
    elif n == "Ray of Enfeeblement":
        if touch_attack(ui, caster, t0, True, combat):
            pen = _sroll("1d6").total + min(5, cl // 2)
            cur = t0.ability("str") or 0
            pen = min(pen, max(0, cur - 1))
            buff(t0, "Enfeebled", [("str", "untyped", -pen)])
    elif n == "True Strike":
        buff(caster, "True Strike", [("attack", "insight", 20)], tags=["consume_attack"])
    elif n == "Enlarge Person":
        if not _is_humanoid(t0):
            ui.out("  Only humanoids can be enlarged.")
        else:
            buff(t0, "Enlarge Person", [("str", "size", 2), ("dex", "size", -2)],
                 tags=["enlarged"])
    # ------------------------------------------------------------ arcane 2
    elif n == "Scorching Ray":
        rays = 1 if cl < 7 else (2 if cl < 11 else 3)
        for _ in range(rays):
            if touch_attack(ui, caster, t0, True, combat):
                r = _sroll("4d6")
                ui.roll(r.detail())
                deal_damage(ui, t0, r.total, "fire", combat)
    elif n == "Melf's Acid Arrow":
        if touch_attack(ui, caster, t0, True, combat):
            r = _sroll("2d4")
            ui.roll(r.detail())
            deal_damage(ui, t0, r.total, "acid", combat)
            extra = cl // 3
            if extra and not t0.dead:
                buff(t0, "Acid Arrow", tags=["_dot"], dur=extra,
                     data={"dot": "2d4", "dtype": "acid"})
    elif n == "Bull's Strength":
        buff(t0, "Bull's Strength", [("str", "enhancement", 4)])
    elif n == "Cat's Grace":
        buff(t0, "Cat's Grace", [("dex", "enhancement", 4)])
    elif n == "Bear's Endurance":
        buff(t0, "Bear's Endurance", [("con", "enhancement", 4)])
    elif n == "Blur":
        buff(t0, "Blur", [("concealment", "concealment", 20)])
    # ------------------------------------------------------------ arcane 3
    elif n in ("Fireball", "Lightning Bolt"):
        r = _sroll(f"{min(10, cl)}d6")
        ui.roll(r.detail())
        dtype = "fire" if n == "Fireball" else "electricity"
        for t in targets:
            _area_damage(ui, t, r.total, dtype, dc, stags, combat)
    elif n == "Haste":
        for a in allies:
            if a.dead:
                continue
            buff(a, "Haste", [("attack", "haste", 1), ("ac", "dodge", 1),
                              ("save_ref", "dodge", 1), ("speed", "enhancement", 30)],
                 tags=["hasted"])
    # ------------------------------------------------------------ divine 0
    elif n == "Guidance":
        buff(t0, "Guidance", [("attack", "competence", 1), ("saves", "competence", 1),
                              ("skills", "competence", 1)], tags=["consume_any"])
    elif n == "Virtue":
        t0.temp_hp += 1
        buff(t0, "Virtue", tags=[], data={"on_end": "temp_hp", "amount": 1})
    elif n in ("Cure Minor Wounds", "Cure Light Wounds", "Cure Moderate Wounds",
               "Cure Serious Wounds", "Cure Critical Wounds"):
        _cure(ui, caster, t0, n, cl, dc, stags, combat)
    elif n in ("Inflict Light Wounds", "Inflict Moderate Wounds"):
        nd, cap = (1, 5) if "Light" in n else (2, 10)
        if touch_attack(ui, caster, t0, False, combat):
            amt = _sroll(f"{nd}d8").total + min(cap, cl)
            if t0.ctype == "undead":
                heal(ui, t0, amt)
            else:
                if saving_throw(ui, t0, "will", dc, stags):
                    amt //= 2
                deal_damage(ui, t0, amt, "negative", combat)
    elif n == "Bless":
        for a in allies:
            if not a.dead:
                buff(a, "Bless", [("attack", "morale", 1), ("saves_vs_fear", "morale", 1)])
    elif n == "Shield of Faith":
        buff(t0, "Shield of Faith", [("ac", "deflection", 2 + cl // 6)])
    elif n == "Divine Favor":
        b = max(1, min(3, cl // 3))
        buff(caster, "Divine Favor", [("attack", "luck", b), ("damage", "luck", b)])
    elif n == "Protection from Evil":
        buff(t0, "Protection from Evil", [("ac_vs_evil", "deflection", 2),
                                          ("saves_vs_evil", "resistance", 2)])
    elif n == "Magic Weapon":
        buff(t0, "Magic Weapon", [("weapon_enh", "enhancement", 1)])
    elif n == "Doom":
        if _mind_immune(t0, sp["tags"]) or "fear" in t0.immunities():
            ui.out(f"  {t0.name} is unaffected.")
        elif not saving_throw(ui, t0, "will", dc, stags):
            buff(t0, "Doom", tags=["shaken"])
    elif n == "Longstrider":
        buff(caster, "Longstrider", [("speed", "enhancement", 10)])
    elif n == "Resist Energy":
        buff(t0, "Resist Energy (fire)", [("resist_fire", "resistance", 10 if cl < 7 else 20)])
    # ------------------------------------------------------------ divine 2
    elif n == "Aid":
        hp = _sroll("1d8").total + min(10, cl)
        t0.temp_hp += hp
        buff(t0, "Aid", [("attack", "morale", 1), ("saves_vs_fear", "morale", 1)],
             data={"on_end": "temp_hp", "amount": hp})
        ui.good(f"  {t0.name} gains {hp} temporary hit points.")
    elif n == "Spiritual Weapon":
        wis = caster.mod("wis")
        buff(caster, "Spiritual Weapon", tags=["_spiritual_weapon"],
             data={"target": t0.uid, "bonus": caster.bab() + wis,
                   "damage": f"1d8+{min(5, cl // 3)}" if cl >= 3 else "1d8"})
        ui.out(f"  A shimmering weapon of force appears and flies at {t0.name}.")
        if combat is not None:
            combat.spiritual_weapon_attack(caster)
    elif n == "Hold Person":
        _hold(ui, t0, dc, stags, n, buff, _is_humanoid(t0) and not _mind_immune(t0, sp["tags"]),
              "humanoids only")
    elif n == "Hold Animal":
        _hold(ui, t0, dc, stags, n, buff, t0.ctype == "animal", "animals only")
    elif n == "Hold Monster":
        _hold(ui, t0, dc, stags, n, buff, t0.is_living() and not _mind_immune(t0, sp["tags"]),
              "mindless or not alive")
    # ------------------------------------------------------------ divine 3
    elif n == "Prayer":
        for a in allies:
            if not a.dead:
                buff(a, "Prayer", [("attack", "luck", 1), ("damage", "luck", 1),
                                   ("saves", "luck", 1), ("skills", "luck", 1)])
        for e in enemies:
            if not e.dead:
                buff(e, "Prayer (cursed)", [("attack", "luck", -1), ("damage", "luck", -1),
                                            ("saves", "luck", -1), ("skills", "luck", -1)])
    elif n == "Searing Light":
        if touch_attack(ui, caster, t0, True, combat):
            if t0.ctype == "undead":
                r = _sroll(f"{min(10, cl)}d6")
            else:
                r = _sroll(f"{min(5, max(1, cl // 2))}d8")
            ui.roll(r.detail())
            deal_damage(ui, t0, r.total, "holy", combat)
    elif n == "Magic Vestment":
        buff(t0, "Magic Vestment", [("armor_enh", "enhancement", max(1, min(5, cl // 4)))])
    elif n == "Magic Circle against Evil":
        for a in allies:
            if not a.dead:
                buff(a, "Magic Circle against Evil", [("ac_vs_evil", "deflection", 2),
                                                      ("saves_vs_evil", "resistance", 2)])
    # ------------------------------------------------------------ v2 spells
    elif n == "Flare":
        if not saving_throw(ui, t0, "fort", dc, stags):
            buff(t0, "Dazzled", [("attack", "untyped", -1)])
    elif n == "Grease":
        for t in targets:
            if not t.dead and not saving_throw(ui, t, "ref", dc, stags):
                t.add_effect(Effect("Prone", None, tags=["prone"]))
                ui.warn(f"  {t.name} slips and falls prone!")
    elif n == "Hideous Laughter":
        if _mind_immune(t0, sp["tags"]) or (t0.ability("int") or 0) < 3:
            ui.out(f"  {t0.name} doesn't get the joke (unaffected).")
        elif not saving_throw(ui, t0, "will", dc, stags):
            buff(t0, "Hideous Laughter", tags=["prone", "dazed"])
    elif n == "Remove Fear":
        for e in list(t0.effects):
            if e.tags & {"shaken", "frightened"} and e.name != "Fatigued":
                t0.effects.remove(e)
                ui.good(f"  {t0.name} is no longer {e.name.lower()}.")
        buff(t0, "Remove Fear", [("saves_vs_fear", "morale", 4)])
    elif n in ("Lesser Restoration", "Restoration"):
        if n == "Restoration":
            if t0.ability_damage:
                ui.good(f"  {t0.name}'s ability damage is fully restored.")
            t0.ability_damage = {}
            if t0.remove_effect("Negative levels"):
                ui.good(f"  {t0.name}'s drained life force returns.")
        elif t0.ability_damage:
            ab = max(t0.ability_damage, key=lambda a: t0.ability_damage[a])
            amt = _sroll("1d4").total
            t0.ability_damage[ab] = max(0, t0.ability_damage[ab] - amt)
            if not t0.ability_damage[ab]:
                del t0.ability_damage[ab]
            ui.good(f"  {t0.name} recovers {amt} points of {ab.upper()}.")
        for e in list(t0.effects):
            if "fatigued" in e.tags or (n == "Restoration" and "exhausted" in e.tags):
                t0.effects.remove(e)
                ui.good(f"  {t0.name} is no longer {e.name.lower()}.")
    elif n == "Entangle":
        for t in targets:
            if t.dead:
                continue
            if _freed(t, "entangle"):
                ui.out(f"  {t.name} slips through the grasping plants.")
            elif not saving_throw(ui, t, "ref", dc, stags):
                buff(t, "Entangled", [("attack", "untyped", -2), ("dex", "untyped", -4)],
                     tags=["entangled"], data={"save_each_round": ("ref", dc, stags)})
    elif n == "Produce Flame":
        if touch_attack(ui, caster, t0, True, combat):
            r = _sroll(f"1d6+{min(5, cl)}")
            ui.roll(r.detail())
            deal_damage(ui, t0, r.total, "fire", combat)
    elif n == "Shillelagh":
        buff(caster, "Shillelagh", tags=["shillelagh"])
    elif n == "Magic Fang":
        buff(t0, "Magic Fang", [("natural_weapon_enh", "enhancement", 1)])
    elif n == "Greater Magic Fang":
        buff(t0, "Greater Magic Fang",
             [("natural_weapon_enh", "enhancement", max(1, min(5, cl // 4)))])
    elif n in ("Eagle's Splendor", "Owl's Wisdom", "Fox's Cunning"):
        ab = {"Eagle's Splendor": "cha", "Owl's Wisdom": "wis", "Fox's Cunning": "int"}[n]
        buff(t0, n, [(ab, "enhancement", 4)])
    elif n == "Heroism":
        buff(t0, "Heroism", [("attack", "morale", 2), ("saves", "morale", 2),
                             ("skills", "morale", 2)])
    elif n == "Barkskin":
        buff(t0, "Barkskin", [("ac", "natural_enh", min(5, 2 + max(0, (cl - 3) // 3)))])
    elif n == "Flaming Sphere":
        buff(caster, "Flaming Sphere", tags=["_sphere"],
             data={"target": t0.uid, "dc": dc, "stags": stags})
        ui.out(f"  A rolling sphere of flame bursts into being and careens at {t0.name}.")
        if combat is not None:
            combat.flaming_sphere_attack(caster)
    elif n == "Sound Burst":
        r = _sroll("1d8")
        ui.roll(r.detail())
        for t in targets:
            if t.dead:
                continue
            deal_damage(ui, t, r.total, "sonic", combat)
            if not t.dead and "stun" not in t.immunities() and \
                    not saving_throw(ui, t, "fort", dc, stags):
                buff(t, "Stunned (sound burst)", tags=["stunned"], dur=1)
    elif n == "Remove Paralysis":
        freed = False
        for e in list(t0.effects):
            if "paralyzed" in e.tags:
                t0.effects.remove(e)
                freed = True
        ui.good(f"  {t0.name} can move again!" if freed else f"  {t0.name} wasn't paralyzed.")
    elif n == "Slow":
        for t in targets:
            if t.dead:
                continue
            if _freed(t, "slow"):
                ui.out(f"  {t.name} is unaffected.")
            elif not saving_throw(ui, t, "will", dc, stags):
                buff(t, "Slow", [("attack", "untyped", -1), ("ac", "untyped", -1),
                                 ("save_ref", "untyped", -1)], tags=["slowed"])
    elif n == "Good Hope":
        for a in allies:
            if not a.dead:
                buff(a, "Good Hope", [("attack", "morale", 2), ("damage", "morale", 2),
                                      ("saves", "morale", 2), ("skills", "morale", 2)])
    elif n == "Displacement":
        buff(t0, "Displacement", [("concealment", "concealment", 50)])
    elif n == "Bestow Curse":
        if touch_attack(ui, caster, t0, False, combat):
            if not saving_throw(ui, t0, "will", dc, stags):
                buff(t0, "Cursed", [("attack", "untyped", -4), ("saves", "untyped", -4),
                                    ("skills", "untyped", -4)], dur=None)
    elif n == "Fear":
        for t in targets:
            if t.dead:
                continue
            if _mind_immune(t, sp["tags"]) or "fear" in t.immunities():
                ui.out(f"  {t.name} knows no fear.")
            elif saving_throw(ui, t, "will", dc, stags):
                buff(t, "Shaken (fear)", tags=["shaken"], dur=1)
            else:
                buff(t, "Frightened", tags=["frightened", "shaken"])
    elif n in ("Call Lightning", "Call Lightning Storm"):
        storm = n == "Call Lightning Storm"
        bolts = min(15 if storm else 10, cl)
        e = buff(caster, n, tags=["_lightning"],
                 data={"bolts": bolts, "dice": "5d6" if storm else "3d6", "dc": dc,
                       "stags": stags})
        call_bolt(ui, caster, e, t0, combat)
    elif n == "Poison":
        if touch_attack(ui, caster, t0, False, combat):
            if "poison" in t0.immunities() or not t0.is_living() or t0.ability("con") is None:
                ui.out(f"  {t0.name} is immune to poison.")
            elif not saving_throw(ui, t0, "fort", dc, stags):
                amt = _sroll("1d10").total
                t0.ability_damage["con"] = t0.ability_damage.get("con", 0) + amt
                ui.bad(f"  {t0.name} takes {amt} Constitution damage!")
                if (t0.ability("con") or 0) <= 0:
                    t0.dead = True
                    if combat is not None:
                        combat.after_damage(t0)
                    else:
                        report_down(ui, t0)
                elif combat is not None:
                    combat.after_damage(t0)
    elif n == "Remove Disease":
        if t0.afflictions:
            ui.good(f"  {t0.name} is cured of " + ", ".join(a["name"] for a in t0.afflictions)
                    + ".")
            t0.afflictions = []
        else:
            ui.out(f"  {t0.name} has no disease to cure.")
    elif n == "Mass Cure Light Wounds":
        for a in allies:
            if not a.dead:
                _cure(ui, caster, a, n, cl, dc, stags, combat)
    elif n == "Freedom of Movement":
        for e in list(t0.effects):
            if e.tags & {"paralyzed", "entangled", "slowed"}:
                t0.effects.remove(e)
                ui.good(f"  {t0.name} breaks free of {e.name}.")
        buff(t0, "Freedom of Movement")
    elif n == "Death Ward":
        buff(t0, "Death Ward")
    elif n == "Divine Power":
        lvl = getattr(caster, "level", caster.hit_dice())
        caster.temp_hp += cl
        buff(caster, "Divine Power", [("str", "enhancement", 6),
                                      ("attack", "divine_power", max(0, lvl - caster.bab()))],
             data={"on_end": "temp_hp", "amount": cl})
    elif n == "Spell Immunity":
        buff(t0, "Spell Immunity", [("saves_vs_spell", "untyped", 4)])
    elif n == "Holy Smite":
        r = _sroll(f"{max(1, min(5, cl // 2))}d8")
        ui.roll(r.detail())
        for t in targets:
            if t.dead:
                continue
            if getattr(t, "is_pc", False) and "Evil" not in getattr(t, "alignment", "Evil"):
                ui.out(f"  {t.name} is untouched by the holy light.")
                continue
            amt = r.total if t.evil else r.total // 2
            if saving_throw(ui, t, "will", dc, stags):
                amt //= 2
            elif t.evil:
                buff(t, "Blinded (holy smite)", tags=["blinded"], dur=1)
            deal_damage(ui, t, amt, "holy", combat)
    elif n == "Shout":
        r = _sroll("5d6")
        ui.roll(r.detail())
        for t in targets:
            if t.dead:
                continue
            amt = r.total // 2 if saving_throw(ui, t, "fort", dc, stags) else r.total
            deal_damage(ui, t, amt, "sonic", combat)
    elif n == "Greater Invisibility":
        buff(t0, "Greater Invisibility", [("concealment", "concealment", 50),
                                          ("attack", "untyped", 2)], tags=["invisible"])
    elif n == "Ice Storm":
        b = _sroll("3d6")
        cdmg = _sroll("2d6")
        ui.roll(f"Hail {b.detail()}, cold {cdmg.detail()}")
        for t in targets:
            if t.dead:
                continue
            deal_damage(ui, t, b.total, "B", combat, magic=True)
            if not t.dead:
                deal_damage(ui, t, cdmg.total, "cold", combat)
    elif n == "Stoneskin":
        buff(t0, "Stoneskin", data={"left": min(150, 10 * cl)})
    elif n == "Flame Strike":
        r = _sroll(f"{min(15, cl)}d6")
        ui.roll(r.detail())
        for t in targets:
            if t.dead:
                continue
            amt = r.total
            if saving_throw(ui, t, "ref", dc, stags):
                if getattr(t, "has_evasion", lambda: False)():
                    ui.good(f"  {t.name} evades the column of fire!")
                    continue
                amt //= 2
            elif getattr(t, "has_improved_evasion", lambda: False)():
                amt //= 2
            deal_damage(ui, t, amt // 2, "fire", combat)
            if not t.dead:
                deal_damage(ui, t, amt - amt // 2, "holy", combat)
    elif n == "Dispel Magic":
        dispel(ui, caster, t0, cl, allies or [caster])
    elif n.startswith(("Summon Monster", "Summon Nature's Ally")):
        base, lvl = summon_info(n)
        if combat is None:
            ui.out("  Nothing answers: there's nothing to fight here.")
        else:
            pool = SUMMON_LISTS[base][lvl]
            key = pool[0] if len(pool) == 1 else pool[ui.choose(
                "Summon which creature?", [MONSTERS[k]["name"] for k in pool], default=0)]
            rounds = cl * (2 if "Extend Spell" in _META else 1)
            combat.add_summon(caster, key, rounds)
    elif n == "Raise Dead":
        if not t0.dead:
            ui.out(f"  {t0.name} isn't dead.")
        else:
            raise_dead(ui, t0)
    elif n == "Righteous Might":
        buff(caster, "Righteous Might", [("str", "size", 4), ("con", "size", 4),
                                         ("dex", "size", -2), ("ac", "natural_enh", 2)],
             tags=["enlarged"])
    elif n == "Slay Living":
        if touch_attack(ui, caster, t0, False, combat):
            if not t0.is_living() or "death" in t0.immunities():
                ui.out(f"  {t0.name} is unaffected by the death magic.")
            elif saving_throw(ui, t0, "fort", dc, stags):
                r = _sroll(f"3d6+{cl}")
                ui.roll(r.detail())
                deal_damage(ui, t0, r.total, "negative", combat)
            else:
                ui.bad(f"  {t0.name}'s life is snuffed out!")
                t0.damage = t0.max_hp() + 10
                t0.dead = True
                if combat is not None:
                    combat.after_damage(t0)
                else:
                    report_down(ui, t0)
    elif n == "Dispel Evil":
        buff(caster, "Dispel Evil", [("ac_vs_evil", "deflection", 4),
                                     ("saves_vs_evil", "resistance", 4)])
    elif n == "Cone of Cold":
        r = _sroll(f"{min(15, cl)}d6")
        ui.roll(r.detail())
        for t in targets:
            _area_damage(ui, t, r.total, "cold", dc, stags, combat)
    elif n == "Waves of Fatigue":
        for t in targets:
            if t.dead:
                continue
            if not t.is_living():
                ui.out(f"  {t.name} feels nothing.")
            elif t.has_tag("fatigued"):
                buff(t, "Exhausted", tags=["exhausted"], dur=None)
            else:
                buff(t, "Fatigued", tags=["fatigued"], dur=None)
    else:
        ui.out(f"  ({n} has no mechanical effect in this version.)")
    return True


def call_bolt(ui, caster, e, target, combat=None) -> None:
    """One bolt from an active call lightning effect."""
    if e.data.get("bolts", 0) <= 0 or target is None or target.dead:
        return
    e.data["bolts"] -= 1
    r = _sroll(e.data["dice"])
    ui.out(f"  A bolt of lightning lances down at {target.name}! ({e.data['bolts']} left)",
           ("byellow",))
    ui.roll(r.detail())
    _area_damage(ui, target, r.total, "electricity", e.data["dc"], e.data["stags"], combat)
    if e.data["bolts"] <= 0:
        caster.remove_effect(e.name)


def _area_damage(ui, t: Creature, total: int, dtype: str, dc: int, stags, combat) -> None:
    if t.dead:
        return
    saved = saving_throw(ui, t, "ref", dc, stags)
    evasion = getattr(t, "has_evasion", lambda: False)()
    if saved:
        amt = 0 if evasion else total // 2
        if evasion:
            ui.good(f"  {t.name} evades the blast completely!")
            return
    elif getattr(t, "has_improved_evasion", lambda: False)():
        amt = total // 2
        ui.good(f"  {t.name} twists away from the worst of it (improved evasion).")
    else:
        amt = total
    deal_damage(ui, t, amt, dtype, combat)


def _cure(ui, caster, t, n, cl, dc, stags, combat) -> None:
    table = {"Cure Minor Wounds": (0, 0), "Cure Light Wounds": (1, 5),
             "Cure Moderate Wounds": (2, 10), "Cure Serious Wounds": (3, 15),
             "Cure Critical Wounds": (4, 20), "Mass Cure Light Wounds": (1, 25)}
    nd, cap = table[n]
    if getattr(caster, "domains", None) and "Healing" in caster.domains:
        cl += 1
    amt = (_sroll(f"{nd}d8").total if nd else 0) + (min(cap, cl) if nd else 1)
    if t.ctype == "undead":
        if touch_attack(ui, caster, t, False, combat):
            if saving_throw(ui, t, "will", dc, stags):
                amt //= 2
            deal_damage(ui, t, amt, "positive", combat)
        return
    heal(ui, t, amt)
    if t.hp >= 0 and getattr(t, "stable", False):
        t.stable = False


# ---------------------------------------------------------------- targeting info
def spell_targets_kind(spell: str) -> str:
    return SPELLS[spell]["target"]


def caster_dc(caster, cast: dict) -> int:
    if cast.get("item"):
        return 10 + cast["level"] + (cast["level"] // 2 + 0)
    return caster.spell_dc(cast["class"], cast["spell"])


def caster_cl(caster, cast: dict) -> int:
    if cast.get("item"):
        return cast.get("cl", 1)
    cl = caster.caster_level(cast["class"])
    if "good" in SPELLS[cast["spell"]]["tags"] and "Good" in getattr(caster, "domains", []):
        cl += 1
    return cl


# ---------------------------------------------------------------- items
def scroll_usable(ch, d: dict):
    """Return (can_use, needs_umd) for a scroll."""
    spell = SPELLS[d["spell"]]
    kind = d.get("list")
    for cls in ch.classes():
        info = CLASSES[cls]
        if (kind is None or info.get("caster") == kind) and cls in spell["levels"]:
            return True, False
    if ch.skill_ranks.get("Use Magic Device", 0) > 0:
        return True, True
    return False, False


# ---------------------------------------------------------------- wands & staffs
def device_spells(d: dict) -> List[tuple]:
    return [tuple(x) for x in d["spells"]] if d.get("spells") else [(d["spell"], 1)]


def spend_charge(ui, ch, entry: dict, n: int = 1) -> None:
    from .data.items import charges_left
    entry["charges"] = charges_left(entry) - n
    if entry["charges"] <= 0:
        entry.pop("slot", None)
        if entry in ch.inventory:
            ch.inventory.remove(entry)
        ui.warn(f"The last charge is spent; the {item_data(entry)['name'].lower()} crumbles "
                f"to dust.")


def use_device_check(ui, ch, d: dict, spell: str) -> bool:
    """Spell trigger: the spell must be on one of your class lists, or Use Magic Device
    DC 20."""
    ok, umd = scroll_usable(ch, {"spell": spell})
    if not ok:
        ui.bad(f"{ch.name} can't work that (the spell isn't on their list, and they have no "
               f"Use Magic Device).")
        return False
    if umd:
        r = dice.d20()
        tot = r + ch.skill_total("Use Magic Device")
        ui.roll(f"Use Magic Device: d20={r} + {tot - r} = {tot} vs DC 20")
        if tot < 20:
            ui.bad("The device sputters. Nothing happens (no charge used).")
            return False
    return True


def device_cast(ui, ch, entry, spell, targets, combat=None, allies=None, enemies=None):
    d = item_data(entry)
    cost = dict(device_spells(d))[spell]
    cl = d.get("cl", 1)
    if d["kind"] == "staff":   # staffs use the wielder's caster level if higher
        for cls in ch.caster_classes():
            if cls in SPELLS[spell]["levels"]:
                cl = max(cl, ch.caster_level(cls))
    lvl = min(SPELLS[spell]["levels"].values())
    spend_charge(ui, ch, entry, cost)
    cast_spell(ui, ch, spell, targets, cl, 10 + lvl + lvl // 2, combat, allies=allies,
               enemies=enemies)


def use_device_out_of_combat(ui, user, entry, party) -> None:
    d = item_data(entry)
    spells = [s for s, _ in device_spells(d) if SPELLS[s]["target"] not in
              ("enemy", "enemies", "summon", "creature")]
    if not spells:
        ui.out("There's nothing to use that on right now.")
        return
    spell = spells[0] if len(spells) == 1 else spells[ui.choose(
        "Cast which spell?", spells, allow_cancel=True) or 0]
    if not use_device_check(ui, user, d, spell):
        return
    living = [p for p in party if not p.dead]
    target = user
    if SPELLS[spell]["target"] == "ally" and len(living) > 1:
        target = living[ui.choose("On whom?", [f"{p.name} ({p.hp}/{p.max_hp()} hp)"
                                              for p in living])]
    device_cast(ui, user, entry, spell, [target], allies=living)


def use_scroll_check(ui, ch, d: dict) -> bool:
    ok, umd = scroll_usable(ch, d)
    if not ok:
        ui.bad(f"{ch.name} can't use that scroll (the spell isn't on their list).")
        return False
    if umd:
        dc = 20 + d.get("cl", 1)
        r = dice.d20()
        tot = r + ch.skill_total("Use Magic Device")
        ui.roll(f"Use Magic Device: d20={r} + {tot - r} = {tot} vs DC {dc}")
        if tot < dc:
            ui.bad("The scroll's magic fizzles in confusion (try again later).")
            return False
    return True


def use_consumable_out_of_combat(ui, user, entry: dict, party) -> None:
    d = item_data(entry)
    if d["kind"] in ("wand", "staff"):
        use_device_out_of_combat(ui, user, entry, party)
        return
    if d.get("use") == "antitoxin":
        user.add_effect(Effect("Antitoxin", ROUNDS_PER_HOUR, [("save_fort_poison", "alchemical",
                                                               5)]))
        user.remove_item(entry, 1)
        ui.good(f"{user.name} drinks the antitoxin.")
        return
    spell = d["spell"]
    sp = SPELLS[spell]
    if sp["target"] in ("enemy", "enemies"):
        ui.out("There's nothing to use that on right now.")
        return
    if d["use"] == "scroll" and not use_scroll_check(ui, user, d):
        return
    target = user
    living = [p for p in party if not p.dead]
    if sp["target"] == "ally" and len(living) > 1:
        target = living[ui.choose("On whom?", [f"{p.name} ({p.hp}/{p.max_hp()} hp)"
                                              for p in living])]
    if d["use"] == "spell" and target is not user:
        ui.out(f"{user.name} gives {target.name} the potion.")
    cl = d.get("cl", 1)
    lvl = min(sp["levels"].values())
    cast_spell(ui, user if d["use"] == "scroll" else target, spell, [target], cl,
               10 + lvl + lvl // 2, allies=list(living))
    user.remove_item(entry, 1)


def cast_out_of_combat(ui, party) -> None:
    casters = [p for p in party if p.conscious and p.available_casts()]
    if not casters:
        ui.out("No one has spells available.")
        return
    who = casters[0] if len(casters) == 1 else casters[ui.choose(
        "Who casts?", [p.name for p in casters])]
    with ui.acting(who.player):
        _cast_for(ui, who, party)


def _cast_for(ui, who, party) -> None:
    if who.has_tag("raging"):
        ui.bad("Can't cast while raging.")
        return
    if not who.can_cast_now():
        ui.bad(f"{who.name} can't cast spells in animal form.")
        return
    casts = [c for c in who.available_casts()
             if SPELLS[c["spell"]]["target"] in ("ally", "self", "allies", "none")
             and (c["spell"] != "Raise Dead" or any(p.dead for p in party))]
    if not casts:
        ui.out(f"{who.name} has no spells useful outside combat right now.")
        return
    opts = [f"L{c['level']} {c['spell']}{' (spontaneous)' if c.get('spontaneous') else ''}"
            f"{' (domain)' if c.get('domain') else ''}: {SPELLS[c['spell']]['desc']}"
            for c in casts]
    i = ui.choose("Cast which spell?", opts, allow_cancel=True)
    if i is None:
        return
    cast = casts[i]
    sp = SPELLS[cast["spell"]]
    living = [p for p in party if not p.dead]
    for p in list(living):
        comp = p.companion_creature() if hasattr(p, "companion_creature") else None
        if comp is not None and not comp.dead:
            living.append(comp)
    target = who
    if cast["spell"] == "Raise Dead":
        dead = [p for p in party if p.dead]
        if not dead:
            ui.out("No one here needs raising (thankfully).")
            return
        target = dead[0] if len(dead) == 1 else dead[ui.choose("Raise whom?",
                                                               [p.name for p in dead])]
        cost = 5000 * 100
        if who.cp < cost:
            ui.bad(f"Raise Dead needs a diamond worth 5,000 gp, and {who.name} has only "
                   f"{rules.money_str(who.cp)}. (Pool the party's gold first.)")
            return
        who.cp -= cost
        ui.out(f"{who.name} crushes a 5,000 gp diamond over {target.name}'s body...")
    elif sp["target"] == "ally" and len(living) > 1:
        target = living[ui.choose("Target", [f"{p.name} ({p.hp}/{p.max_hp()} hp)"
                                             for p in living])]
    asf = who.arcane_spell_failure(cast["class"])
    who.expend(cast)
    if asf and dice.percent() <= asf:
        ui.bad(f"Arcane spell failure ({asf}%)! The spell fizzles.")
        return
    cast_spell(ui, who, cast["spell"], [target], caster_cl(who, cast), caster_dc(who, cast),
               allies=living)
