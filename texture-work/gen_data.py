#!/usr/bin/env python3
"""
bertie_progression data/asset generator for the progression recipe ledger.

Writes into src/main/resources/:
  data/bertie_progression/recipe/**        authored recipes
  data/<other>/recipe/**          stock overrides (false-condition disables / replacements)
  data/forbidden_arcanus/forbidden_arcanus/hephaestus_forge/ritual/  augmented tier upgrades
  data/bertie_progression/forbidden_arcanus/hephaestus_forge/ritual/          authored rituals
  data/bertie_progression/tags/**          stripped_logs item+block tags
  assets/bertie_progression/**             lang, item models, blockstates, block models

Run:  python texture-work/gen_data.py
"""
import io
import json
import os
import shutil

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")

MODID = "bertie_progression"

# ---------------------------------------------------------------- helpers

written = []

def write(relpath, obj):
    path = os.path.join(RES, relpath.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    written.append(relpath)

def conds(*mods):
    """neoforge:conditions list — AND of mod_loaded for each external mod."""
    return [{"type": "neoforge:mod_loaded", "modid": m} for m in sorted(set(mods))]

DISABLED = {
    "neoforge:conditions": [{"type": "neoforge:false"}],
    "type": "minecraft:crafting_shapeless",
    "ingredients": [{"item": "minecraft:stone"}],
    "result": {"id": "minecraft:stone", "count": 1},
}

def external_mods(*ids):
    """Extract non-minecraft/bertie_progression namespaces from item/tag id strings."""
    out = set()
    for i in ids:
        if i is None:
            continue
        i = i.lstrip("#")  # tags carry the same namespace semantics
        ns = i.split(":")[0] if ":" in i else "minecraft"
        if ns not in ("minecraft", MODID, "c"):
            out.add(ns)
    return out

def shaped(pattern, key, result_id, count=1, category="misc", extra_conds=None):
    ids = list(key.values()) + [result_id]
    mods = external_mods(*[v if isinstance(v, str) else None for v in ids])
    obj = {}
    if mods or extra_conds:
        obj["neoforge:conditions"] = conds(*mods) + (extra_conds or [])
    obj.update({
        "type": "minecraft:crafting_shaped",
        "category": category,
        "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
        "pattern": pattern,
        "result": {"id": result_id, "count": count},
    })
    return obj

def shapeless(ingredients, result_id, count=1):
    mods = external_mods(*[i for i in ingredients], result_id)
    obj = {}
    if mods:
        obj["neoforge:conditions"] = conds(*mods)
    obj.update({
        "type": "minecraft:crafting_shapeless",
        "category": "misc",
        "ingredients": [({"tag": i[1:]} if i.startswith("#") else {"item": i}) for i in ingredients],
        "result": {"id": result_id, "count": count},
    })
    return obj

def mech(pattern, key, result_id, count=1):
    """create:mechanical_crafting"""
    mods = external_mods(*key.values(), result_id) | {"create"}
    return {
        "neoforge:conditions": conds(*mods),
        "type": "create:mechanical_crafting",
        "accept_mirrored": False,
        "category": "misc",
        "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
        "pattern": pattern,
        "result": {"id": result_id, "count": count},
        "show_notification": True,
    }

def infusion(input_item, input_count, extra, spirits, result_id, count=1):
    """malum:spirit_infusion. extra = [(id,count)...], spirits = [(type,count)...]

    A leading '#' on the input or any extra makes it a TAG ingredient (Malum's own
    recipes use {"tag": ...}, e.g. #minecraft:stone_tool_materials for the rocks).
    """
    def _ing(i, c):
        return ({"tag": i[1:], "count": c} if i.startswith("#") else {"item": i, "count": c})
    mods = external_mods(input_item, result_id, *[e[0] for e in extra]) | {"malum"}
    return {
        "neoforge:conditions": conds(*mods),
        "type": "malum:spirit_infusion",
        "input": _ing(input_item, input_count),
        "extraInputs": [_ing(i, c) for i, c in extra],
        "spirits": [{"type": t, "count": c} for t, c in spirits],
        "result": {"id": result_id, "count": count},
    }

def ritual(main, inputs, result_id, count=1, tier=None, essences=None, xp=0):
    """FA hephaestus ritual. inputs = [(id,count)...]

    NO neoforge:conditions here: rituals are a DATAPACK REGISTRY that only exists
    when forbidden_arcanus is present (absent-FA environments ignore the folder),
    and every referenced mod is a hard member of the current pack. Unconditional files
    make a parse problem a loud server-boot error instead of a silent skip.

    HARD CONSTRAINT (verified in-game): the Forge has 8 pedestals and each input
    item occupies one pedestal, so sum(amounts) must be <= 8 — every stock ritual
    obeys this and exceeding it makes the ritual uncraftable (and crashes the
    JEI/TMRV ritual display with AIOOBE index 8).
    """
    total = sum(c for _, c in inputs)
    assert total <= 8, f"ritual inputs exceed 8 pedestals ({total}): {result_id}"
    # FA stores XP cost as essences.experience (4th key; verified against stock rituals).
    ess = dict(essences) if essences else {"aureal": 0, "blood": 0, "souls": 0}
    if xp:
        ess["experience"] = xp
    obj = {
        "essences": ess,
        "inputs": [{"amount": c, "ingredient": ({"tag": i[1:]} if i.startswith("#") else {"item": i})}
                   for i, c in inputs],
        "magic_circle": "forbidden_arcanus:create_item",
        "main_ingredient": {"item": main},
        "result": {"type": "forbidden_arcanus:create_item",
                   "result_item": {"id": result_id, "count": count}},
    }
    if tier:
        obj["forge_tier"] = tier
    return obj

def ritual_component_input(obj, index, item_id, components, amount):
    """Swap input #index for a neoforge component-aware ingredient (slag plates)."""
    obj["inputs"][index] = {
        "amount": amount,
        "ingredient": {
            "type": "neoforge:components",
            "items": item_id,
            "components": components,
        },
    }
    return obj

def instiller(center, center_count, ing1, ing2, result_id, count=1, time=200, xp=2.0):
    mods = external_mods(center, ing1, ing2, result_id) | {"pastel"}
    return {
        "neoforge:conditions": conds(*mods),
        "type": "pastel:spirit_instiller",
        "time": time,
        "experience": xp,
        "ingredient1": ing1,
        "ingredient2": ing2,
        "center_ingredient": {"item": center, "count": center_count},
        "result": {"id": result_id, "count": count},
    }

def pedestal(pattern, key, colors, result_id, count=1, tier="complex", time=400, xp=4.0):
    mods = external_mods(*key.values(), result_id) | {"pastel"}
    return {
        "neoforge:conditions": conds(*mods),
        "type": "pastel:pedestal",
        "tier": tier,
        "time": time,
        "experience": xp,
        "colors": colors,
        "pattern": pattern,
        "key": key,
        "result": {"id": result_id, "count": count},
    }

def stonecutting(ingredient, result_id, count=1):
    mods = external_mods(ingredient, result_id)
    obj = {}
    if mods:
        obj["neoforge:conditions"] = conds(*mods)
    obj.update({
        "type": "minecraft:stonecutting",
        "ingredient": ({"tag": ingredient[1:]} if ingredient.startswith("#") else {"item": ingredient}),
        "result": {"id": result_id, "count": count},
    })
    return obj

def darkstone_pool(name, members):
    """All-pairs stonecutter exchange within a darkstone family (slab outputs = 2).
    Members are FA block paths (forbidden_arcanus:*). Members never cross pools."""
    for src in members:
        for dst in members:
            if src == dst:
                continue
            cnt = 2 if dst.endswith("_slab") else 1
            s = src.split(":")[-1]
            d = dst.split(":")[-1]
            write(f"{R}/stonecutting/darkstone_{name}/{s}__to__{d}.json",
                  stonecutting(src, dst, cnt))

def double_smelting(a, b, result_id, count=1, time=200, xp=0.5):
    mods = external_mods(a, b, result_id) | {"slag"}
    return {
        "neoforge:conditions": conds(*mods),
        "type": "slag:double_smelting",
        "ingredientA": ({"tag": a[1:]} if a.startswith("#") else {"item": a}),
        "ingredientB": ({"tag": b[1:]} if b.startswith("#") else {"item": b}),
        "result": {"id": result_id, "count": count},
        "experience": xp,
        "cookingTime": time,
    }

SP = lambda t, c: (f"malum:{t}", c)   # spirit tuple
EARLY4 = [SP("aerial", 4), SP("aqueous", 4), SP("earthen", 4), SP("infernal", 4)]
EARLY8 = [SP("aerial", 8), SP("aqueous", 8), SP("earthen", 8), SP("infernal", 8)]
ALL8x8 = EARLY8 + [SP("arcane", 8), SP("eldritch", 8), SP("sacred", 8), SP("wicked", 8)]

IRON_PLATE = {"slag:material_type": "slag:iron", "slag:part_type": "slag:plate"}
COPPER_PLATE = {"slag:material_type": "slag:copper", "slag:part_type": "slag:plate"}
GOLD_PLATE = {"slag:material_type": "slag:golden", "slag:part_type": "slag:plate"}

# ---------------------------------------------------------------- recipes

R = "data/bertie_progression/recipe"

# ---- inventory 2x2 (I2) ----
write(f"{R}/inventory_2x2/opening_mallet.json",            # R02B
      shapeless(["berlords_carving:wood_slate", "minecraft:stick"], "bertie_progression:opening_mallet"))
write(f"{R}/inventory_2x2/stone_crucible_blank.json",      # R02C
      shapeless(["berlords_carving:stone_slate", "minecraft:cobblestone"], "bertie_progression:stone_crucible_blank"))
write(f"{R}/inventory_2x2/stone_pour_channel.json",        # R02D
      shapeless(["berlords_carving:stone_slate", "minecraft:cobblestone", "minecraft:cobblestone"],
                "bertie_progression:stone_pour_channel"))
write(f"{R}/inventory_2x2/hand_crank.json",                # R14D  (PP/PA)
      shaped(["PP", "PA"], {"P": "#minecraft:planks", "A": "create:andesite_alloy"}, "create:hand_crank"))
# R18 (Licensed Crafting Plinth) removed — block dropped, berlord batch 4.
# Note 4 (2026-07-22): pre-table Mundabitur Dust — shapeless 4 -> 1 (the R28A table bulk 6->4 stays).
write(f"{R}/inventory_2x2/mundabitur_dust_pretable.json",
      shapeless(["forbidden_arcanus:arcane_crystal_dust", "minecraft:phantom_membrane",
                 "minecraft:redstone", "minecraft:gunpowder"],
                "forbidden_arcanus:mundabitur_dust", 1))
# Note 6: pre-table Deorum Nugget — shapeless dust + rose gold + charcoal + arcane SPECK -> 1 nugget.
# (berlord 2026-07-22 batch 2: arcane ingredient downgraded dust -> speck, 1/9 of a dust.)
write(f"{R}/inventory_2x2/deorum_nugget_pretable.json",
      shapeless(["forbidden_arcanus:mundabitur_dust", "slag:rose_gold_ingot",
                 "minecraft:charcoal", "forbidden_arcanus:arcane_crystal_dust_speck"],
                "forbidden_arcanus:deorum_nugget", 1))
# FA ships speck->dust (9 specks in a 3x3) but NO dust->speck split; add it so specks are
# obtainable pre-table (FA's own speck sources are gavel/loot, late and rare).
write(f"{R}/inventory_2x2/arcane_crystal_dust_split.json",
      shapeless(["forbidden_arcanus:arcane_crystal_dust"],
                "forbidden_arcanus:arcane_crystal_dust_speck", 9))
# Weeping Eye (C2, berlord 2026-07-22 batch 2): locates the Weeping Well. Recipe unspecified by
# Weeping Eye (berlord 2026-07-25): the 2x2 shapeless is replaced by a HEATED Create mixing —
# 1 Ender Pearl + 4 Prismarine Shards + 6 Refined Brilliance. (Basin recipes allow up to 64
# ingredient entries — BasinRecipe.getMaxInputCount, jar-verified — so 11 entries is fine.)
write(f"{R}/create/weeping_eye_mixing.json",
      {"neoforge:conditions": conds("create", "malum"), "type": "create:mixing",
       "heat_requirement": "heated",
       "ingredients": ([{"item": "minecraft:ender_pearl"}]
                       + [{"item": "minecraft:prismarine_shard"} for _ in range(4)]
                       + [{"item": "malum:refined_brilliance"} for _ in range(6)]),
       "results": [{"id": "bertie_progression:weeping_eye"}]})
# Note 7: Stonecutter (replaces stock, see override below) — shaped 2x2 fits the pre-table grid.
write(f"{R}/inventory_2x2/stonecutter.json",
      shaped(["ID", "SS"], {"I": "minecraft:iron_ingot", "D": "slag:deep_alloy",
                            "S": "minecraft:smooth_stone"}, "minecraft:stonecutter"))

# ---- licensed-table 3x3 (T3) ----
write(f"{R}/table/mundabitur_bulk.json",                   # R28A
      shapeless(["forbidden_arcanus:arcane_crystal_dust", "minecraft:redstone", "minecraft:blaze_powder",
                 "minecraft:bone_meal", "minecraft:phantom_membrane", "minecraft:gunpowder"],
                "forbidden_arcanus:mundabitur_dust", 4))
write(f"{R}/table/fusion_shrine_basalt.json",              # R22
      shaped(["TAC", "DSB"],
             {"T": "pastel:topaz_shard", "A": "minecraft:amethyst_shard", "C": "pastel:citrine_shard",
              "D": "forbidden_arcanus:chiseled_arcane_polished_darkstone", "S": "malum:arcane_spirit",
              "B": "create:brass_sheet"},
             "pastel:fusion_shrine_basalt"))
write(f"{R}/table/warden_echo_pattern.json",               # R31
      shaped(["ASA", "SCS", "AMA"],
             {"A": "minecraft:amethyst_shard", "S": "minecraft:sculk",
              "C": "deeperdarker:warden_carapace", "M": "minecraft:phantom_membrane"},
             "bertie_progression:warden_echo_pattern"))

# ---- Brick Forge double smelting (SLAG) ----
# Ore double-smelts are 2 raw -> 1 ingot (berlord batch 5: "make all ore smelting brick forge 2->1").
write(f"{R}/slag/first_copper_ingots.json",  double_smelting("minecraft:raw_copper", "minecraft:raw_copper", "minecraft:copper_ingot", 1))   # R05D1
write(f"{R}/slag/first_iron_ingots.json",    double_smelting("minecraft:raw_iron", "minecraft:raw_iron", "minecraft:iron_ingot", 1))         # R05D2
write(f"{R}/slag/first_gold_ingots.json",    double_smelting("minecraft:raw_gold", "minecraft:raw_gold", "minecraft:gold_ingot", 1))         # R05D3
write(f"{R}/slag/first_zinc_ingots.json",    double_smelting("create:raw_zinc", "create:raw_zinc", "create:zinc_ingot", 1))                  # R05D4
# Runes: two Runic Stones double-smelt into 2 Runes on the Brick Forge.
write(f"{R}/slag/runes.json",
      double_smelting("#forbidden_arcanus:runic_stones", "#forbidden_arcanus:runic_stones",
                      "forbidden_arcanus:rune", 2))
# R12 removed (berlord batch 3): Brass is no longer a Brick-Forge double-smelt — it is now a
# Hephaestus ritual (see brass_ingot.json below).
# R18A removed (berlord 2026-07-22 batch 2): Refined Soulstone now via Brick-Forge bed recipe
# (4 Raw Soulstone + 1 Diamond, see BedRecipes.refined_soulstone). Charcoal + vanilla-smelt routes gone.
# Note 10 (2026-07-22): Arcane Crystal Dust now smelted in the Brick Forge, 2 crystal -> 1 dust
# (replaces the removed Mallet+crystal->4dust bed recipe R06C). NOTE: slag:double_smelting has no
# secondary/chance output field, so the requested "+25% bonus dust" is NOT expressible here — shipped
# as a flat 2->1. Revisit if a bonus is wanted (needs a different recipe type / code).
write(f"{R}/slag/arcane_crystal_dust.json",
      double_smelting("forbidden_arcanus:arcane_crystal", "forbidden_arcanus:arcane_crystal",
                      "forbidden_arcanus:arcane_crystal_dust", 1, 200, 0.5))

# ---- Hephaestus rituals (HF1+, data-driven demo of the retained-recipe list) ----
RIT = "data/bertie_progression/forbidden_arcanus/hephaestus_forge/ritual"

# R13 Electron Tubes MOVED to the Spirit Altar (berlord batch 3: "spirit crafts are better suited").
# Same recipe feel: Natural Quartz core + Redstone + Slag-cast Gold/Iron Plates, paid in spirits.
r13 = infusion("malum:natural_quartz", 1, [("minecraft:redstone", 2)],
               [SP("arcane", 2), SP("aerial", 2)], "create:electron_tube", 3)
for _comps in (GOLD_PLATE, IRON_PLATE):
    r13["extraInputs"].append({"type": "neoforge:components", "items": "slag:dynamic_part",
                               "components": _comps, "count": 1})
write(f"{R}/malum/electron_tube.json", r13)

# Brass Ingot (berlord batch 3): Hephaestus ritual — Colossal Iron core + Deorum + 2 Zinc + 2 Rose
# Gold -> 2 Brass. Replaces the removed Brick-Forge double-smelt.
write(f"{RIT}/brass_ingot.json",
      ritual("armageddon_mod:colossal_iron_ingot",
             [("forbidden_arcanus:deorum_ingot", 1), ("create:zinc_ingot", 2),
              ("slag:rose_gold_ingot", 2)],
             "create:brass_ingot", 2, tier=1))

# Brass Casing (berlord batch 3): apply a Brass Ingot onto an Edelwood Log (Create item application).
write(f"{R}/create/brass_casing_edelwood.json", {
    "neoforge:conditions": conds("create", "forbidden_arcanus"),
    "type": "create:item_application",
    "ingredients": [{"tag": "forbidden_arcanus:edelwood_logs"}, {"item": "create:brass_ingot"}],
    "results": [{"id": "create:brass_casing"}],
})

# r14_water_wheel ritual REMOVED (berlord batch 8): Water Wheel is now the bound-soul sequenced assembly.
# (Stale ritual file is rm'd; rituals are a hard registry so it must be deleted, not condition-disabled.)
# r14a (Brass Casing ritual) removed — Brass Casing is now the Edelwood-Log item application above.
# r14a0 andesite_casing_blank ritual REMOVED (berlord 2026-07-24): custom casing chain scrapped;
# create:andesite_casing restored to its Create default item-application (see the DISABLED block below).
write(f"{RIT}/r14b_kinetic_pattern_plates.json",
      ritual("berlords_carving:stone_big_slate",
             [("create:brass_nugget", 4), ("forbidden_arcanus:arcane_crystal_dust", 1)],
             "bertie_progression:kinetic_pattern_plate", 4, tier=1))
# r14c gearbox-from-blank ritual REMOVED (berlord 2026-07-24): gearbox reverts to Create's default
# recipe (andesite casing + 4 shafts), which works again now that andesite casing is restored.
# R15 Mechanical Crafter MOVED to the Spirit Altar (berlord batch 4), now yields ONE:
# Brass Casing core + Dragon Bone + Electron Tube + Cogwheel, paid in Eldritch/Earthen/Arcane.
write(f"{R}/malum/mechanical_crafter.json",
      infusion("create:brass_casing", 1,
               [("block_factorys_bosses:dragon_bone", 1), ("create:electron_tube", 1),
                ("create:cogwheel", 1), ("minecraft:diamond", 1)],
               [SP("eldritch", 4), SP("earthen", 4), SP("arcane", 4)],
               "create:mechanical_crafter", 1))
# R16 (Crafting Language Seals) removed with the Seal/Witness/Slate (berlord batch 4).
# The 3x3 gate is now the consumable Crafting License — RECIPE STILL NEEDED (berlord to supply).

# Earplugs (berlord batch 4, overwrites Ice & Fire's): String core + 2 Planks + 6 Wool, 20 aureal.
write(f"{RIT}/earplugs.json",
      ritual("minecraft:string",
             [("#minecraft:planks", 2), ("#minecraft:wool", 6)],
             "iceandfire:earplugs", 1, tier=1,
             essences={"aureal": 20, "blood": 0, "souls": 0}))
write("data/iceandfire/recipe/earplugs.json", DISABLED)

# Builder Stone (berlord batch 4, overwrites Armageddon's): Siren Tear core + 2 Colossal Iron +
# 2 Gilded Plate + Gilded Ingot smithing template + 2 Amethyst + 1 Emerald (8 = full pedestal ring).
write(f"{RIT}/builder_stone.json",
      ritual("iceandfire:siren_tear",
             [("armageddon_mod:colossal_iron_ingot", 2), ("armageddon_mod:gilded_plate", 2),
              ("armageddon_mod:gilded_ingot_smithing_template", 1),
              ("minecraft:amethyst_shard", 2), ("minecraft:emerald", 1)],
             "armageddon_mod:builder_stone", 1, tier=1,
             essences={"aureal": 200, "blood": 10000, "souls": 10}))
write("data/armageddon_mod/recipe/builderstonerecipe.json", DISABLED)

# Spirit Altar (berlord 2026-07-22 batch 2): Runewood Planks core + 4 Refined Soulstone + 4 gold
# plate, 100 XP / 5000 blood / 10 souls / 500 aureal. NOTE "gilded plate" read as the Slag GOLDEN
# plate (dynamic_part{golden,plate}) — matches the old altar recipe and keeps C2 self-contained;
# swap to armageddon_mod:gilded_plate (a goblin-lord drop) if the boss loot was meant instead.
r19 = ritual("malum:runewood_planks",
             [("malum:refined_soulstone", 4), ("placeholder", 4)],
             "malum:spirit_altar", 1, tier=1,
             essences={"aureal": 500, "blood": 5000, "souls": 10}, xp=100)
ritual_component_input(r19, 1, "slag:dynamic_part", GOLD_PLATE, 4)
write(f"{RIT}/r19_spirit_altar.json", r19)

# R26A Nether Lintel Core RITUAL REMOVED (berlord 2026-07-31) together with the Nether Lintel and
# the Core themselves - both items are obsolete now the Nether is entered through the Netherly Meal.
# This also closes the long-open "what replaces the Crafting Language Seal as its third input"
# question: there is no ritual left to have a third input.

# R29B Ritual Burner Cage REMOVED (berlord 2026-07-26) along with the item itself.

write(f"{RIT}/r29_spirit_instiller.json",
      ritual("pastel:pedestal_onyx",
             [("malum:arcana_pylon", 1), ("forbidden_arcanus:deorum_ingot", 1), ("create:brass_sheet", 1),
              ("malum:arcane_spirit", 2), ("malum:eldritch_spirit", 1),
              ("malum:sacred_spirit", 1), ("malum:wicked_spirit", 1)],
             "pastel:spirit_instiller", 1, tier=2))
# R30 Twilight Concord RITUAL REMOVED (berlord 2026-07-26): it consumed the Serpent Scale Blank and
# the Ritual Burner Cage, both now deleted. The Concord's spirit-infusion route (C2) is the sole one.
write(f"{RIT}/r30a_echoing_city_compass.json",
      ritual("minecraft:compass",
             [("pastel:onyx_shard", 1), ("minecraft:sculk", 3), ("malum:aqueous_spirit", 4)],
             "bertie_progression:echoing_city_compass", 1, tier=2,
             essences={"aureal": 250, "blood": 0, "souls": 0}))
write(f"{RIT}/r31a_spirit_crucible.json",
      ritual("deeperdarker:reinforced_echo_shard",
             [("malum:refined_soulstone", 3), ("create:brass_sheet", 4), ("pastel:onyx_shard", 1)],
             "malum:spirit_crucible", 1, tier=2))
# Note 13 (2026-07-22): additive Carving Station route via HF1 (stock 2x2 recipe untouched).
# XP cost removed (berlord note, 2026-07-22 batch 2).
write(f"{RIT}/carving_station.json",
      ritual("minecraft:stonecutter",
             [("minecraft:amethyst_shard", 1), ("minecraft:heart_of_the_sea", 1),
              ("minecraft:chiseled_deepslate", 2)],
             "berlords_carving:carving_station", 1, tier=1,
             essences={"aureal": 100, "blood": 1000, "souls": 5}))
write(f"{RIT}/r32_descent_anchor.json",
      ritual("bertie_progression:spirit_focused_echo",
             [("deeperdarker:warden_carapace", 1), ("twilightforest:lich_trophy", 1), ("pastel:onyx_shard", 1)],
             "bertie_progression:descent_anchor", 1, tier=2))
write(f"{RIT}/r36a_soulbinding_brazier.json",
      ritual("betterend:aeternium_ingot",
             [("malum:soul_stained_steel_ingot", 4), ("malum:hallowed_gold_ingot", 2),
              ("minecraft:dragon_head", 1)],
             "malum:soulbinding_brazier", 1, tier=3))
write(f"{RIT}/r37c_sovereign_seals.json",
      ritual("forbidden_arcanus:arcane_crystal",
             [("forbidden_arcanus:deorum_ingot", 4), ("malum:arcane_spirit", 4)],
             "bertie_progression:hephaestian_sovereign_seal", 4, tier=3,
             essences={"aureal": 1000, "blood": 2000, "souls": 0}))
write(f"{RIT}/r37f_ignis_rematch_seal.json",
      ritual("minecraft:blaze_powder",
             [("minecraft:blaze_powder", 3), ("minecraft:nether_bricks", 3), ("malum:infernal_spirit", 2)],
             "bertie_progression:boss_rematch_seal", 1, tier=3))
write(f"{RIT}/r40_convergence_matrix.json",
      ritual("minecraft:dragon_head",
             [("bertie_progression:soulbound_authority", 1), ("bertie_progression:complex_spectrum_seal", 1),
              ("bertie_progression:well_attunement", 1), ("bertie_progression:ignitium_lattice", 1),
              ("bertie_progression:dragonbone_frame", 1)],
             "bertie_progression:convergence_matrix", 2, tier=3,
             essences={"aureal": 2500, "blood": 12000, "souls": 64}))

# ---- Malum spirit infusions ----
# R19A (Spirit Altar Witness) removed — item dropped, berlord batch 4.
write(f"{R}/malum/runewood_resonance.json",                # R20A
      infusion("malum:refined_soulstone", 1, [], [SP("aerial", 4)], "bertie_progression:runewood_resonance"))
# R21C Arcana Resonance REMOVED (berlord 2026-07-31): nothing ever consumed it. The Arcana Pylon
# takes the RUNEWOOD Resonance (R20A above), which stays.
write(f"{R}/malum/sculk_blocks.json",                      # R30S
      infusion("minecraft:deepslate", 1, [("malum:refined_soulstone", 1)], [SP("aqueous", 8)],
               "minecraft:sculk", 8))
write(f"{R}/malum/spirit_focused_echo.json",               # R31B (soul crystal consumed — demo deviation)
      infusion("deeperdarker:reinforced_echo_shard", 1, [("deeperdarker:soul_crystal", 1)],
               [SP("arcane", 8), SP("aqueous", 8)], "bertie_progression:spirit_focused_echo"))
write(f"{R}/malum/soulbound_authority.json",               # R37 (Brazier band demo: altar infusion)
      infusion("minecraft:dragon_head", 1,
               [("pastel:moonstone_shard", 1), ("malum:soul_stained_steel_ingot", 4)],
               ALL8x8, "bertie_progression:soulbound_authority", 4))
write(f"{R}/malum/weeping_compass.json",                   # R37D
      infusion("bertie_progression:soulbound_authority", 1,
               [("bertie_progression:spirit_focused_echo", 1), ("malum:refined_soulstone", 4), ("pastel:moonstone_shard", 4)],
               [], "bertie_progression:weeping_compass"))
write(f"{R}/malum/well_attunement.json",                   # R37E (natural-Well offering deferred)
      infusion("bertie_progression:weeping_compass", 1, [("bertie_progression:soulbound_authority", 1)],
               [SP("arcane", 8)], "bertie_progression:well_attunement"))
write(f"{R}/malum/ashlord_rematch_seal.json",              # R37G
      infusion("deeperdarker:sculk_bone", 4,
               [("minecraft:end_stone_bricks", 4), ("bertie_progression:spirit_focused_echo", 1)],
               [SP("infernal", 16)], "bertie_progression:boss_rematch_seal"))

# ---- Mechanical Crafter recipes ----
# R17 removed with the Seal. The vanilla Crafting Table currently has NO recipe (its stock one is
# disabled below) — RECIPE STILL NEEDED (berlord to supply), along with the Crafting License.
write(f"{R}/mechanical/exclusive/runic_workbench.json",         # R21A
      mech(["RGR", "SPS", "RGR"],
           {"R": "malum:runewood_planks", "G": "malum:hallowed_gold_ingot",
            "S": "malum:refined_soulstone", "P": "malum:arcana_pylon"},
           "malum:runic_workbench"))
# R24A Victory Ledger recipe removed (berlord 2026-07-25) along with the block itself.
# R27 Nether Lintel recipe removed (berlord 2026-07-31) along with the item and its Core.
write(f"{R}/mechanical/exclusive/echo_lock.json",               # R31C
      mech(["DSD", "SOS", "DSD"],
           {"D": "minecraft:deepslate_tiles", "S": "minecraft:sculk", "O": "pastel:onyx_shard"},
           "bertie_progression:echo_lock"))
write(f"{R}/mechanical/exclusive/ignitium_lattice_5x5.json",    # R38 (x2 output)
      mech(["KSSSK", "SIIIS", "SIIIS", "SIIIS", "KSSSK"],
           {"K": "bertie_progression:kinetic_pattern_plate", "S": "malum:infernal_spirit", "I": "cataclysm:ignitium_ingot"},
           "bertie_progression:ignitium_lattice", 2))
write(f"{R}/mechanical/exclusive/ignitium_struts_3x3.json",     # R38A (single run -> 8)
      mech(["KBK", "BLB", "KBK"],
           {"K": "bertie_progression:kinetic_pattern_plate", "B": "create:brass_sheet", "L": "bertie_progression:ignitium_lattice"},
           "bertie_progression:ignitium_strut", 8))
write(f"{R}/mechanical/exclusive/dragonbone_frame_5x5.json",    # R39 (x2 output)
      mech(["ABMBA", "BBBBB", "MBEBM", "BBBBB", "ABMBA"],
           {"A": "betterend:aeternium_ingot", "B": "block_factorys_bosses:dragon_bone",
            "M": "pastel:moonstone_chiseled_calcite", "E": "bertie_progression:spirit_focused_echo"},
           "bertie_progression:dragonbone_frame", 2))
write(f"{R}/mechanical/exclusive/dragonbone_braces_3x3.json",   # R39A (single run -> 8)
      mech(["MAM", "AFA", "MAM"],
           {"M": "pastel:moonstone_chiseled_calcite", "A": "betterend:aeternium_ingot",
            "F": "bertie_progression:dragonbone_frame"},
           "bertie_progression:dragonbone_brace", 8))
write(f"{R}/mechanical/exclusive/avaritia_nether_crafting_table.json",  # R41
      mech(["IPEPD", "PRIDP", "EIMDE", "PRDIP", "RPEPR"],
           {"I": "bertie_progression:ignitium_strut", "D": "bertie_progression:dragonbone_brace",
            "E": "minecraft:end_stone_bricks", "R": "deeperdarker:reinforced_echo_shard",
            "P": "pastel:moonstone_glass", "M": "bertie_progression:convergence_matrix"},
           "avaritia:nether_crafting_table"))

# ---- Pastel ----
write(f"{R}/pastel/complex_spectrum_seals.json",           # R37A
      pedestal(["DR"], {"D": "minecraft:dragon_breath", "R": "deeperdarker:reinforced_echo_shard"},
               {"pastel:cyan": 4, "pastel:magenta": 4, "pastel:yellow": 4, "pastel:black": 4, "pastel:white": 4},
               "bertie_progression:complex_spectrum_seal", 4))
write(f"{R}/pastel/moonstone_synthesis.json",              # R32A
      instiller("pastel:moonstone_shard", 1, "pastel:bismuth_flake", "pastel:onyx_powder",
                "pastel:moonstone_shard", 4, 400, 4.0))
write(f"{R}/pastel/warden_reinforced_echo_batch.json",     # R31R (one 32-batch — demo economy)
      instiller("bertie_progression:warden_echo_pattern", 1, "minecraft:amethyst_shard", "minecraft:sculk",
                "deeperdarker:reinforced_echo_shard", 32, 600, 8.0))
write(f"{R}/pastel/concordant_moonsteel.json",             # R37B
      instiller("betterend:terminite_ingot", 4, "pastel:moonstone_powder", "forbidden_arcanus:arcane_crystal_dust",
                "bertie_progression:concordant_moonsteel_ingot", 4, 400, 4.0))

# (R25 proof-replication family removed with the proof items — berlord 2026-07-22.)

# ---- Avaritia capstone ----
write(f"{R}/avaritia/mekanism_access_core.json", {         # R42 — exact §8.5
    "neoforge:conditions": conds("avaritia"),
    "type": "avaritia:shaped_table",
    "tier": 2,
    "key": {
        "I": {"item": "bertie_progression:ignitium_strut"},
        "D": {"item": "bertie_progression:dragonbone_brace"},
        "P": {"item": "bertie_progression:complex_spectrum_seal"},
        "B": {"item": "bertie_progression:soulbound_authority"},
        "O": {"item": "bertie_progression:concordant_moonsteel_ingot"},
        "S": {"item": "bertie_progression:hephaestian_sovereign_seal"},
        "C": {"item": "bertie_progression:convergence_matrix"},
    },
    "pattern": ["IDPDI", "BOSOB", "PSCSP", "BOSOB", "IDPDI"],
    "result": {"id": "bertie_progression:mekanism_access_core", "count": 1},
})

# ---------------------------------------------------------------- stock overrides

# The 3x3 gate itself
write("data/minecraft/recipe/crafting_table.json", DISABLED)

# Smithing Table loses its bottom plank row -> fits the 2x2 inventory grid
# (replaces the Field Smithing Core route; berlord 2026-07-22)
write("data/minecraft/recipe/smithing_table.json",
      shaped(["II", "PP"], {"I": "minecraft:iron_ingot", "P": "#minecraft:planks"},
             "minecraft:smithing_table"))

# Note 7: replace the vanilla Stonecutter recipe with the authored 2x2 (iron+deep_alloy over smooth stone).
write("data/minecraft/recipe/stonecutter.json", DISABLED)

# Note 6: Deorum ingot <-> nugget becomes 4:1 (stock FA is the 9-grid). Override both stock recipes.
write("data/forbidden_arcanus/recipe/deorum_nugget_from_deorum_ingot.json",
      shapeless(["forbidden_arcanus:deorum_ingot"], "forbidden_arcanus:deorum_nugget", 4))
# Note (2026-07-22 batch 2): nugget -> ingot is a SHAPED 2x2 (4 nuggets), not shapeless.
write("data/forbidden_arcanus/recipe/deorum_ingot_from_deorum_nugget.json",
      shaped(["NN", "NN"], {"N": "forbidden_arcanus:deorum_nugget"},
             "forbidden_arcanus:deorum_ingot", 1))

# Note 8: darkstone stonecutter exchange — two isolated pools (normal / arcane). Gilded Chiseled
# Polished Darkstone is the ARCANE entry point (obtainable early via the forge bed R07B).
FA = "forbidden_arcanus"
darkstone_pool("normal", [f"{FA}:{b}" for b in [
    "darkstone", "darkstone_slab", "darkstone_stairs", "darkstone_wall",
    "polished_darkstone", "polished_darkstone_slab", "polished_darkstone_stairs",
    "polished_darkstone_wall", "chiseled_polished_darkstone",
    "polished_darkstone_bricks", "cracked_polished_darkstone_bricks",
    "polished_darkstone_brick_slab", "polished_darkstone_brick_stairs",
    "polished_darkstone_brick_wall", "tiled_polished_darkstone_bricks"]])
darkstone_pool("arcane", [f"{FA}:{b}" for b in [
    "gilded_chiseled_polished_darkstone", "arcane_polished_darkstone",
    "arcane_polished_darkstone_slab", "arcane_polished_darkstone_stairs",
    "arcane_polished_darkstone_wall", "arcane_polished_darkstone_pillar",
    "chiseled_arcane_polished_darkstone"]])

# Create: pre-table kinetics get authored routes; no-grid bypasses closed (§3.3)
for p in ["crafting/kinetics/water_wheel", "crafting/kinetics/hand_crank",
          "crafting/materials/electron_tube", "crafting/kinetics/mechanical_crafter",
          "item_application/brass_casing_from_log", "item_application/brass_casing_from_wood"]:
    write(f"data/create/recipe/{p}.json", DISABLED)
# batch 8 (berlord 2026-07-24): empty_blaze_burner is NO LONGER disabled — it gets a real 3x3 + 5x5
# recipe (see batch 8 below). Lighting it by capturing a blaze is a Create interaction, unaffected.
# Note 16 (berlord 2026-07-24): andesite_casing_from_log/wood are NO LONGER disabled — Create's
# default item-application (Andesite Alloy on a stripped log/wood) is the restored andesite casing route.

# Note 18 (berlord 2026-07-24): Copper Casing accepts ONLY stripped twilight oak as its wood, gating
# it behind the Twilight Forest. Overrides Create's any-stripped-log/wood item-applications.
def _copper_casing(wood_id, suffix):
    write(f"data/create/recipe/item_application/copper_casing_from_{suffix}.json",
          {"neoforge:conditions": conds("create", "twilightforest"),
           "type": "create:item_application",
           "ingredients": [{"item": wood_id}, {"tag": "c:ingots/copper"}],
           "results": [{"id": "create:copper_casing"}]})
_copper_casing("twilightforest:stripped_twilight_oak_log", "log")
_copper_casing("twilightforest:stripped_twilight_oak_wood", "wood")

# Note 8 (berlord 2026-07-24): Furnace replaces vanilla — iron frame with a cobble/netherrack base.
# On the crafting table (overwrites the vanilla recipe id) and the Mechanical Crafter.
_FURNACE_PAT = ["III", "I I", "CNC"]
_FURNACE_KEY = {"I": "minecraft:iron_ingot", "C": "minecraft:cobblestone", "N": "minecraft:netherrack"}
write("data/minecraft/recipe/furnace.json", shaped(_FURNACE_PAT, _FURNACE_KEY, "minecraft:furnace"))
write(f"{R}/mechanical/pre_table/furnace.json", mech(_FURNACE_PAT, _FURNACE_KEY, "minecraft:furnace"))

# ==================================================== berlord batch 6 (2026-07-24, "build all")
# Every id below was verified in the pack instance jars (elemental_metals, iceandfire, malum,
# forbidden_arcanus, irons_spellbooks, slag, create, twilightforest).

# --- Note 9: Blast Furnace (table + mecha), Clibano Core, Refined Brilliance smelts ---
_BLAST_PAT = ["FFF", "FUF", "SMS"]
_BLAST_KEY = {"F": "elemental_metals:fire_infused_iron_ingot", "U": "minecraft:furnace",
              "S": "minecraft:smooth_stone", "M": "minecraft:magma_block"}
write("data/minecraft/recipe/blast_furnace.json", shaped(_BLAST_PAT, _BLAST_KEY, "minecraft:blast_furnace"))
write(f"{R}/mechanical/pre_table/blast_furnace.json", mech(_BLAST_PAT, _BLAST_KEY, "minecraft:blast_furnace"))
# Clibano Core: Spirit Altar (Malum) infusion of a Brick Forge.
write(f"{R}/malum/clibano_core.json",
      infusion("slag:brick_forge", 1,
               [("minecraft:blast_furnace", 4), ("forbidden_arcanus:chiseled_polished_darkstone", 8),
                ("forbidden_arcanus:rune", 12), ("iceandfire:fire_lily", 6)],
               [("malum:infernal", 48), ("malum:wicked", 32), ("malum:sacred", 32),
                ("malum:earthen", 16), ("malum:aerial", 16)],
               "forbidden_arcanus:clibano_core", 1))
# Refined Brilliance: Brick Forge 2->1; Furnace + Blast 1->1. (Clibano 1->1.5 NOT done — FA's clibano
# recipe only supports a typed `residue`, not a 50%-chance copy of the result; needs a mixin.)
write(f"{R}/slag/refined_brilliance_forge.json",
      double_smelting("malum:raw_brilliance", "malum:raw_brilliance", "malum:refined_brilliance", 1))
def _cook(kind, tid, src, dst, time):
    write(f"{R}/cooking/{tid}.json",
          {"neoforge:conditions": conds("malum"), "type": kind, "category": "misc",
           "ingredient": {"item": src}, "result": {"id": dst}, "experience": 0.3, "cookingtime": time})
_cook("minecraft:smelting", "refined_brilliance_smelt", "malum:raw_brilliance", "malum:refined_brilliance", 200)
_cook("minecraft:blasting", "refined_brilliance_blast", "malum:raw_brilliance", "malum:refined_brilliance", 100)

# --- Note 11: elemental infused-iron ingots (Spirit Altar; input iron ingot, +4 uncommon ink last) ---
_INK = ("irons_spellbooks:uncommon_ink", 4)
def _elem(out, scale, mid, mcount, extra_id, sp1, sp2):
    write(f"{R}/malum/elem_{out}.json",
          infusion("minecraft:iron_ingot", 1,
                   [(f"iceandfire:sea_serpent_scales_{scale}", 1), (mid, mcount), (extra_id, 1), _INK],
                   [(f"malum:{sp1}", 8), (f"malum:{sp2}", 4)],
                   f"elemental_metals:{out}_infused_iron_ingot", 1))
_elem("arcane", "purple", "minecraft:ender_pearl", 3, "irons_spellbooks:arcane_ingot", "arcane", "eldritch")
_elem("fire", "red", "minecraft:blaze_powder", 3, "minecraft:lava_bucket", "infernal", "wicked")
_elem("frost", "blue", "minecraft:snowball", 3, "minecraft:packed_ice", "aqueous", "wicked")
_elem("lightning", "bronze", "minecraft:glowstone_dust", 3, "irons_spellbooks:lightning_bottle", "aerial", "infernal")
_elem("soul", "teal", "minecraft:soul_sand", 3, "forbidden_arcanus:corrupt_soul", "sacred", "aerial")
# Healing (berlord): the component-matched regen potion never matched (Malum read it component-blind, so
# EMI showed the base "Uncraftable Potion"). Use a plain potion — clean infusion() like the others.
write(f"{R}/malum/elem_healing.json",
      infusion("minecraft:iron_ingot", 1,
               [("iceandfire:sea_serpent_scales_green", 1), ("minecraft:seagrass", 3),
                ("minecraft:potion", 1), ("irons_spellbooks:uncommon_ink", 4)],
               [SP("earthen", 8), SP("sacred", 4)],
               "elemental_metals:healing_infused_iron_ingot", 1))

# --- Note 12/13: Twilight Concord, Arcane Ingot, Soulstained Steel (all Spirit Altar) ---
write(f"{R}/malum/twilight_concord.json",
      infusion("iceandfire:cyclops_eye", 1,
               [("malum:mnemonic_fragment", 27), ("malum:null_slate", 9), ("irons_spellbooks:arcane_ingot", 3),
                ("minecraft:ender_pearl", 3), ("iceandfire:stymphalian_bird_feather", 3),
                ("create:andesite_alloy", 27), ("malum:soul_stained_steel_ingot", 3)],
               [(f"malum:{s}", 27) for s in ("aerial", "aqueous", "arcane", "earthen",
                                             "eldritch", "infernal", "sacred", "wicked")],
               "bertie_progression:twilight_concord", 1))
write(f"{R}/malum/arcane_ingot.json",
      infusion("forbidden_arcanus:deorum_ingot", 1, [("irons_spellbooks:arcane_essence", 8)],
               [("malum:arcane", 4)], "irons_spellbooks:arcane_ingot", 1))
write(f"{R}/malum/soulstained_steel.json",
      infusion("forbidden_arcanus:obsidiansteel_ingot", 1, [("malum:refined_soulstone", 4)],
               [("malum:earthen", 3), ("malum:arcane", 6), ("malum:wicked", 9)],
               "malum:soul_stained_steel_ingot", 1))

# --- Note 12: Twilight Forest portal reconfig (tag overrides; replace=true drops the vanilla entries) ---
write("data/twilightforest/tags/item/portal/activator.json",
      {"replace": True, "values": ["bertie_progression:twilight_concord"]})
write("data/twilightforest/tags/block/portal/fluid.json",
      {"replace": True, "values": ["slag:molten_prismarine"]})
write("data/twilightforest/tags/block/portal/decoration.json",
      {"replace": True, "values": ["iceandfire:fire_lily", "iceandfire:frost_lily", "iceandfire:lightning_lily"]})

# --- Note 19: Slag foundry — mecha versions, block-of-deep-alloy, crucible->1, drain/interface, melter ritual ---
_DA = "#c:ingots/deep_alloy"
# Block of Deep Alloy: Create compacting (press + basin), 9 deep alloy.
write(f"{R}/create/deep_alloy_block_compacting.json",
      {"neoforge:conditions": conds("create", "slag"), "type": "create:compacting",
       "ingredients": [{"item": "slag:deep_alloy"} for _ in range(9)],
       "results": [{"id": "slag:deep_alloy_block"}]})
# Casting table + basin: mecha versions mirroring Slag's crafting recipes.
write(f"{R}/mechanical/pre_table/casting_table.json", mech(["AAA", "A A"], {"A": _DA}, "slag:table"))
write(f"{R}/mechanical/pre_table/casting_basin.json", mech(["A A", "A A", "AAA"], {"A": _DA}, "slag:basin"))
# Crucible: table recipe forced to output 1 (Slag ships 4) + mecha version, also 1.
_CRU_PAT, _CRU_KEY = ["D D", "D D", "DBD"], {"D": _DA, "B": "#c:storage_blocks/deep_alloy"}
write("data/slag/recipe/crafting/crucible.json", shaped(_CRU_PAT, _CRU_KEY, "slag:crucible", 1))
write(f"{R}/mechanical/pre_table/crucible.json", mech(_CRU_PAT, _CRU_KEY, "slag:crucible", 1))
# Drain: new shape (3 deep alloy) replaces Slag's 1-ingot shapeless, on table + mecha.
_DRAIN_PAT = ["DD ", "  D"]
write("data/slag/recipe/crafting/drain.json", shaped(_DRAIN_PAT, {"D": _DA}, "slag:drain", 1))
write(f"{R}/mechanical/pre_table/drain.json", mech(_DRAIN_PAT, {"D": _DA}, "slag:drain", 1))
# Fluid Interface (crucible_interface): deep-alloy frame + brass, on table + mecha.
_FI_PAT, _FI_KEY = ["DDD", "B B", "DDD"], {"D": _DA, "B": "#c:ingots/brass"}
write("data/slag/recipe/crafting/crucible_interface.json", shaped(_FI_PAT, _FI_KEY, "slag:crucible_interface", 1))
write(f"{R}/mechanical/pre_table/fluid_interface.json", mech(_FI_PAT, _FI_KEY, "slag:crucible_interface", 1))
# Melter: now a Hephaestus ritual (clibano core core + 8 pedestals); Slag's native craft AND the old
# bertie bed route (R05A, removed in BedRecipes.java) are gone so the ritual is the sole source.
write("data/slag/recipe/crafting/melter.json", DISABLED)
write(f"{RIT}/melter.json",
      ritual("forbidden_arcanus:clibano_core",
             [("slag:crucible", 4), ("slag:rose_gold_block", 1), ("create:fluid_tank", 1),
              ("forbidden_arcanus:smelter_prism", 1), ("slag:drain", 1)],
             "slag:melter", 1, tier=1, essences={"aureal": 500, "blood": 0, "souls": 10}))

# ==================================================== Note 17: quest line 3 — Create kinetics
# Table recipes OVERWRITE Create's own (same resource path); Mechanical Crafter versions are added.
# Symbols: A andesite_alloy, B andesite_casing, S shaft, C cogwheel, W large_cogwheel, H whisk,
# F propeller, R iron_bars, V wool, E iron_sheet, I iron_block (press) / iron_ingot (chute). N=empty.
_CK = "data/create/recipe/crafting/kinetics"
_AA, _AC, _SH, _CG, _LC = "create:andesite_alloy", "create:andesite_casing", "create:shaft", "create:cogwheel", "create:large_cogwheel"
_ISH, _BS, _CS = "create:iron_sheet", "create:brass_sheet", "create:copper_sheet"
_ET, _PR = "create:electron_tube", "create:propeller"
def _p(rows):  # note used 'N' for empty; Minecraft patterns use spaces
    return [r.replace("N", " ") for r in rows]

# Depot
_dk = {"A": _AA, "B": _AC}
# Note batch 7: depot — 3 casings on the bottom row. batch 8 (berlord 2026-07-24): remove the TOP ROW.
write(f"{_CK}/depot.json", shaped(_p(["AAA", "BBB"]), _dk, "create:depot"))
write(f"{R}/mechanical/kinetics/depot.json", mech(_p(["ANNNA", "AAAAA", "NBBBN"]), _dk, "create:depot"))
# Mechanical Press (I = iron BLOCK)
_pk = {"S": _SH, "C": _CG, "B": _AC, "I": "minecraft:iron_block"}
# Note batch 7: press table — top-middle stays a shaft, cogwheels -> casings.
write(f"{_CK}/mechanical_press.json", shaped(_p(["NSN", "BBB", "NIN"]), {"S": _SH, "B": _AC, "I": "minecraft:iron_block"}, "create:mechanical_press"))
# batch 8 (berlord 2026-07-24): 5x5 press — top-middle casing->shaft, small cogwheels->casings (my
# read of the terse note; flagged for berlord). Large cogwheel (W) centre kept; no small cogwheels left.
write(f"{R}/mechanical/kinetics/mechanical_press.json",
      mech(_p(["NBSBN", "SBWBS", "NBSBN", "NNSNN", "NIIIN"]),
           {"S": _SH, "B": _AC, "I": "minecraft:iron_block", "W": _LC}, "create:mechanical_press"))
# Mechanical Mixer
_mk = {"S": _SH, "C": _CG, "B": _AC, "H": "create:whisk"}
write(f"{_CK}/mechanical_mixer.json", shaped(_p(["NSN", "CBC", "NHN"]), _mk, "create:mechanical_mixer"))
write(f"{R}/mechanical/kinetics/mechanical_mixer.json",
      mech(_p(["NNSNN", "NBSBN", "NCWCN", "NBSBN", "NNHNN"]), {**_mk, "W": _LC}, "create:mechanical_mixer"))
# Basin
write(f"{_CK}/basin.json", shaped(_p(["ANA", "ANA", "AAA"]), {"A": _AA}, "create:basin"))
write(f"{R}/mechanical/kinetics/basin.json", mech(_p(["ANNNA", "ANNNA", "ANNNA", "AAAAA"]), {"A": _AA}, "create:basin"))
# Whisk — table recipe kept (Create default); Mechanical Crafter version added
write(f"{R}/mechanical/kinetics/whisk.json",
      mech(_p(["NNANN", "NEAEN", "EAEAE", "EAEAE", "NENEN"]), {"A": _AA, "E": _ISH}, "create:whisk"))
# Encased Fan — 3x3 table + 5x5 mecha
_fk = {"E": _ISH, "S": _SH, "B": _AC, "F": _PR}
write(f"{_CK}/encased_fan.json", shaped(_p(["EEE", "SBF", "EEE"]), _fk, "create:encased_fan"))
write(f"{R}/mechanical/kinetics/encased_fan.json",
      mech(_p(["BBBBB", "BCCCR", "SSNCF", "BCCCR", "BBBBB"]), {"B": _AC, "C": _CG, "R": "minecraft:iron_bars", "S": _SH, "F": _PR}, "create:encased_fan"))

# --- Note 17 recipe changes (not quests) — overwrite Create's crafting recipes ---
# Brass ingot via mixing: Zinc + Rose Gold.
write("data/create/recipe/mixing/brass_ingot.json",
      {"neoforge:conditions": conds("create", "slag"), "type": "create:mixing",
       "ingredients": [{"item": "create:zinc_ingot"}, {"item": "slag:rose_gold_ingot"}],
       "results": [{"id": "create:brass_ingot"}]})
write(f"{_CK}/chute.json", shaped(_p(["INI", "INI", "ENE"]), {"I": "minecraft:iron_ingot", "E": _ISH}, "create:chute"))
write(f"{_CK}/smart_chute.json", shaped(_p(["PNP", "PKP", "PTP"]), {"P": _BS, "K": "create:chute", "T": _ET}, "create:smart_chute"))
write(f"{_CK}/fluid_pipe.json", shaped(_p(["SNS", "INI", "SNS"]), {"S": _CS, "I": "minecraft:copper_ingot"}, "create:fluid_pipe"))
# batch 8 (berlord 2026-07-24): remove the horizontal fluid-pipe recipe.
write(f"{R}/create/fluid_pipe_horizontal.json", DISABLED)
# Note batch 7: remove the OLD 4-output fluid pipe recipe. Create ships TWO — fluid_pipe.json is
# overridden with the copper recipe above; fluid_pipe_vertical.json is the leftover, so disable it.
write("data/create/recipe/crafting/kinetics/fluid_pipe_vertical.json", DISABLED)
# Note batch 7: smart fluid pipe — electron tube in the middle, a fluid pipe top and bottom.
write(f"{_CK}/smart_fluid_pipe.json", shaped(_p(["PFP", "PTP", "PFP"]), {"P": _BS, "F": "create:fluid_pipe", "T": _ET}, "create:smart_fluid_pipe"))
write(f"{_CK}/fluid_valve.json", shaped(_p(["IFI", "ISI", "IFI"]), {"I": _ISH, "F": "create:fluid_pipe", "S": "create:speedometer"}, "create:fluid_valve"))
write(f"{_CK}/mechanical_pump.json", shaped(_p(["IFI", "ICI", "IFI"]), {"I": _ISH, "F": "create:fluid_pipe", "C": _CG}, "create:mechanical_pump"))
write(f"{_CK}/weighted_ejector.json", shaped(_p(["GGG", "SDS", "NCN"]), {"G": "create:golden_sheet", "S": _SH, "D": "create:depot", "C": _CG}, "create:weighted_ejector"))
write(f"{_CK}/copper_valve_handle.json", shaped(_p(["ZNZ", "ZAZ", "NZN"]), {"Z": _CS, "A": _AA}, "create:copper_valve_handle"))
write(f"{_CK}/nozzle.json", shaped(_p(["AAA", "VNV", "AAA"]), {"A": _AA, "V": "#minecraft:wool"}, "create:nozzle"))
# Note batch 7: Propeller (5x5 mecha) + Wrench (5x5 mecha, ADDITIVE — Create's normal recipe kept).
write(f"{R}/mechanical/kinetics/propeller.json",
      mech(_p(["NEENN", "NNENE", "EEAEE", "ENENN", "NNEEN"]), {"E": _ISH, "A": _AA}, "create:propeller"))
write(f"{R}/mechanical/kinetics/wrench.json",
      mech(_p(["NGGGC", "NNGSC", "NGSCN", "NSNNN", "SNNNN"]),
           {"G": "create:golden_sheet", "S": "minecraft:stick", "C": _CG}, "create:wrench"))

# ==================================================== "slow Clibano" (was the ignitium demo)
# berlord batch 8 (2026-07-24): repurposed. Slow soul-fire Clibano alloy — Hallowed Gold + Soulstained
# Steel -> Bound Soul Ingot (mythsandlegends), cooking_time 9000, with an Arcane Crystal Dust residue.
# Filename/residue_type id kept as "ignitium" to avoid stale files; ids are internal. Bound Soul Ingot
# keeps its own original recipe too (this is an extra route). NEEDS A RESTART (residue_type = dynamic
# registry). Gates: Artisan Relic + soul fire.
write(f"{R}/ignitium_ingot_from_clibano_combustion.json", {
    "type": "forbidden_arcanus:clibano_combustion",
    "category": "misc",
    "cooking_time": 9000,
    "enhancer": "forbidden_arcanus:artisan_relic",
    "experience": 1.0,
    "fire_type": "soul_fire",
    "ingredients": {"first": {"item": "malum:hallowed_gold_ingot"},
                    "second": {"item": "malum:soul_stained_steel_ingot"}},
    "residue": {"type": "bertie_progression:ignitium", "chance": 0.1},
    "result": {"count": 1, "id": "mythsandlegends:bound_soul_ingot"},
})
# Slow-clibano residue is Arcane Crystal Dust (berlord's explicit exception to "secondary = primary").
write("data/bertie_progression/forbidden_arcanus/residue_type/ignitium.json", {
    "combine_info": {"required_amount": 1, "result": {"count": 1, "id": "forbidden_arcanus:arcane_crystal_dust"}},
    "name": {"text": "Arcane Crystal Residue"},
})

# Deeper and Darker: Reinforced Echo goes through the Warden Echo Pattern (R31/R31R)
write("data/deeperdarker/recipe/reinforced_echo_shard.json", DISABLED)

# Pastel: Fusion Shrine moves to the licensed table (R22)
write("data/pastel/recipe/pedestal/tier2/fusion_shrine_basalt.json", DISABLED)
write("data/pastel/recipe/pedestal/tier2/fusion_shrine_calcite.json", DISABLED)

# Avaritia: R41 is the sole Nether Crafting Table source
write("data/avaritia/recipe/nether_crafting_table.json", DISABLED)

# Forbidden Arcanus: pedestal via Brick-Forge bed (R09A); stock 3x3 disabled
write("data/forbidden_arcanus/recipe/darkstone_pedestal.json", DISABLED)

# Slag armor swap (berlord 2026-07-22 batch 2): wooden/bone Slag ARMOR is replaced by Immersive
# Armors' sets (carving armor-overrides config). Slag's own 2x2 part recipes for those 8 armor
# parts are disabled; TOOL parts (pickaxe heads etc.) are untouched.
for _part in ["helmet", "chestplate", "leggings", "boots"]:
    for _mat in ["wooden", "bone"]:
        write(f"data/slag/recipe/crafting/parts/{_part}_{_mat}.json", DISABLED)

# Immersive Armors originals removed for the same 8 pieces: CARVING is the route (the carving
# armor-overrides config points wood/bone big-slate carves at these items).
for _piece in ["helmet", "chestplate", "leggings", "boots"]:
    for _set in ["wooden", "bone"]:
        write(f"data/immersive_armors/recipe/{_set}_{_piece}.json", DISABLED)

# Malum: pylon gains the resonance witness (R21); catalyzer becomes the authored R31A2
write("data/malum/recipe/spirit_infusion/arcana_pylon.json",
      infusion("malum:runewood_obelisk", 1,
               [("malum:refined_soulstone", 8), ("malum:hex_ash", 4), ("malum:soulwood_planks", 2),
                ("bertie_progression:runewood_resonance", 1)],
               EARLY8, "malum:arcana_pylon"))
write("data/malum/recipe/spirit_infusion/spirit_catalyzer.json",
      infusion("pastel:onyx_shard", 1,
               [("malum:hallowed_gold_ingot", 4), ("create:brass_sheet", 4)],
               ALL8x8, "malum:spirit_catalyzer"))

# God of War chapter (berlord 2026-07-22 batch 2): both spellbook entry recipes REPLACE the
# stock 3x3 recipes with 2x2 pre-table shapes.
# Flimsy Journal (copper spell book): Copper Ingot + Leather over String + Paper.
write("data/irons_spellbooks/recipe/copper_spell_book.json",
      shaped(["CL", "SP"], {"C": "#c:ingots/copper", "L": "minecraft:leather",
                            "S": "minecraft:string", "P": "minecraft:paper"},
             "irons_spellbooks:copper_spell_book"))
# Inscription Table: Book and Quill top-right, two Planks below.
write("data/irons_spellbooks/recipe/inscription_table.json",
      shaped([" B", "PP"], {"B": "minecraft:writable_book", "P": "#minecraft:planks"},
             "irons_spellbooks:inscription_table"))

# FA: augmented tier upgrades (stock essences/main/magic_circle preserved; inputs appended)
# HF2 upgrade (berlord 2026-07-29): the four elemental cores converge here. 8 pedestals exactly.
# "all essence maxed" = the TIER I ceiling (1000/10/10000/900, jar-verified from HephaestusForgeLevel):
# the T1->T2 ritual is performed ON a tier-I forge, which physically cannot hold more than that.
write("data/forbidden_arcanus/forbidden_arcanus/hephaestus_forge/ritual/upgrade_tier_2.json", {
    "essences": {"aureal": 1000, "blood": 10000, "souls": 10, "experience": 900},
    "inputs": [
        {"amount": 2, "ingredient": {"item": "bertie_progression:abyssal_core"}},
        {"amount": 2, "ingredient": {"item": "bertie_progression:desert_core"}},
        {"amount": 2, "ingredient": {"item": "bertie_progression:cursed_core"}},
        {"amount": 2, "ingredient": {"item": "bertie_progression:storm_core"}},
        # berlord 2026-07-31: "double all cores required". 2x4 = 8 pedestals, the hard cap - so the
        # 4 Arcane Crystal that used to fill the last four slots had to come out. There is no
        # arrangement of doubled cores that keeps them: 2+2+2+2+4 = 12 > 8.
    ],
    "magic_circle": "forbidden_arcanus:upgrade_tier",
    "main_ingredient": {"item": "forbidden_arcanus:carved_edelwood_log"},
    "match_tier_exact": True,
    "result": {"type": "forbidden_arcanus:upgrade_tier", "result_tier": 2},
})
write("data/forbidden_arcanus/forbidden_arcanus/hephaestus_forge/ritual/upgrade_tier_3.json", {
    "essences": {"aureal": 1000, "blood": 9000, "souls": 50},
    "inputs": [
        {"amount": 3, "ingredient": {"item": "forbidden_arcanus:arcane_crystal"}},
        {"amount": 3, "ingredient": {"item": "forbidden_arcanus:deorum_ingot"}},
        {"amount": 2, "ingredient": {"item": "pastel:moonstone_shard"}},
    ],
    "magic_circle": "forbidden_arcanus:upgrade_tier",
    "main_ingredient": {"item": "forbidden_arcanus:chiseled_polished_darkstone"},
    "match_tier_exact": True,
    "result": {"type": "forbidden_arcanus:upgrade_tier", "result_tier": 3},
})

# ================= Chapter 2 recipe overhaul (berlord 2026-07-22 batch 2) =================

# Spirit Altar stock craft removed -> only the Hephaestus ritual (r19 above) makes it.
write("data/malum/recipe/spirit_altar.json", DISABLED)

# Refined Soulstone: only the Brick-Forge bed (4 Raw Soulstone + 1 Diamond, see BedRecipes).
# Disable the plain furnace/blast routes from raw. (Charcoal double-smelt R18A already removed.)
write("data/malum/recipe/soulstone_from_raw_smelting.json", DISABLED)
write("data/malum/recipe/soulstone_from_raw_blasting.json", DISABLED)

# Andesite Alloy: only via the Brick Forge (Zinc Ingot + Andesite double-smelt). Disable Create's
# crafting-table routes (iron-nugget AND zinc-nugget) and both mixing routes.
write(f"{R}/slag/andesite_alloy.json",
      double_smelting("create:zinc_ingot", "minecraft:andesite", "create:andesite_alloy", 1, 200, 0.2))
# NOTE: the ZINC mixing route stays ENABLED (berlord batch 4) — only the iron-nugget mixing recipe
# and both crafting-table routes are removed.
for _p in ["crafting/materials/andesite_alloy", "crafting/materials/andesite_alloy_from_zinc",
           "mixing/andesite_alloy"]:
    write(f"data/create/recipe/{_p}.json", DISABLED)

# Zinc nugget<->ingot becomes 4:1 (shaped 2x2 up; shapeless 1->4 down). Stock 1:9 both ways disabled.
write(f"{R}/inventory_2x2/zinc_ingot_from_nuggets.json",
      shaped(["NN", "NN"], {"N": "create:zinc_nugget"}, "create:zinc_ingot", 1))
write(f"{R}/inventory_2x2/zinc_nuggets_from_ingot.json",
      shapeless(["create:zinc_ingot"], "create:zinc_nugget", 4))
write("data/create/recipe/crafting/materials/zinc_ingot_from_compacting.json", DISABLED)
write("data/create/recipe/crafting/materials/zinc_nugget_from_decompacting.json", DISABLED)

# Windmill Sail (create:white_sail): 1 Edelwood Stick + 1 Shaft + 1 Wool + 1 Andesite Alloy -> 2.
write("data/create/recipe/crafting/kinetics/white_sail.json",
      shaped(["ES", "WA"], {"E": "forbidden_arcanus:edelwood_stick", "S": "create:shaft",
                            "W": "#minecraft:wool", "A": "create:andesite_alloy"},
             "create:white_sail", 2))

# Windmill Bearing: Hephaestus ritual (Polished Deepslate core + 4 Shaft + 2 Deorum Nuggets,
# 120 aureal / 5 souls). Stock crafting-table recipe disabled.
write(f"{RIT}/windmill_bearing.json",
      ritual("minecraft:polished_deepslate",
             [("create:shaft", 4), ("forbidden_arcanus:deorum_nugget", 2),
              ("minecraft:slime_ball", 2)],
             "create:windmill_bearing", 1, tier=1,
             essences={"aureal": 120, "blood": 0, "souls": 5}))
write("data/create/recipe/crafting/kinetics/windmill_bearing.json", DISABLED)

# ================= Chapter 2 row 5 + crafter wall (berlord batch 5) =================

# Mundabitur: FA's stock 6-ingredient shapeless is identical in inputs to our R28A bulk (which yields
# 4), so EMI showed two identical recipes. Disable the stock one.
write("data/forbidden_arcanus/recipe/mundabitur_dust.json", DISABLED)

# Wayward Compass: Hephaestus — Compass core + 2 Arcane Essence + 4 Runes + 2 Ender Pearls (=8).
write(f"{RIT}/wayward_compass.json",
      ritual("minecraft:compass",
             [("irons_spellbooks:arcane_essence", 2), ("forbidden_arcanus:rune", 4),
              ("minecraft:ender_pearl", 2)],
             "irons_spellbooks:wayward_compass", 1, tier=1,
             essences={"aureal": 0, "blood": 0, "souls": 4}, xp=10))

# Crude Scythe: Hephaestus — Decrepit Scythe core + Colossal Iron + 3 Iron + 2 Ice&Fire Dragon Bone
# + Gilded Ingot smithing template + Lantern (=8).
write(f"{RIT}/crude_scythe.json",
      ritual("irons_spellbooks:decrepit_scythe",
             [("armageddon_mod:colossal_iron_ingot", 1), ("minecraft:iron_ingot", 3),
              ("iceandfire:dragonbone", 2), ("armageddon_mod:gilded_ingot_smithing_template", 1),
              ("minecraft:lantern", 1)],
             "malum:crude_scythe", 1, tier=1,
             essences={"aureal": 1000, "blood": 1000, "souls": 10}))

# The Dead King drops the Decrepit Scythe 100% of the time, unaffected by Looting. This is the mod's
# own loot table with one guaranteed, condition-free pool prepended (its original pools preserved).
write("data/irons_spellbooks/loot_table/entities/dead_king.json", {
    "type": "minecraft:entity",
    "pools": [
        {"rolls": 1, "bonus_rolls": 0.0,
         "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:decrepit_scythe"}]},
        {"rolls": 1, "bonus_rolls": 0.0,
         "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:arcane_essence",
                      "functions": [
                          {"function": "minecraft:set_count", "add": False,
                           "count": {"type": "minecraft:uniform", "min": 28.0, "max": 45.0}},
                          {"function": "minecraft:enchanted_count_increase",
                           "enchantment": "minecraft:looting",
                           "count": {"type": "minecraft:uniform", "min": 2.0, "max": 6.0}}]}]},
        {"rolls": 1,
         "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:blood_staff"},
                     {"type": "minecraft:item", "name": "irons_spellbooks:necronomicon_spell_book"}],
         "conditions": [
             {"condition": "minecraft:killed_by_player"},
             {"condition": "minecraft:random_chance_with_enchanted_bonus",
              "enchantment": "minecraft:looting", "unenchanted_chance": 0.5,
              "enchanted_chance": {"type": "minecraft:linear", "base": 0.55,
                                   "per_level_above_first": 0.05}}]},
    ],
})

# Mechanical Crafters crafting Mechanical Crafters — additive, crafter-wall only, yields 1.
write(f"{R}/mechanical/exclusive/mechanical_crafter_wall.json",
      mech(["AEA", "SBS", "ACA"],
           {"A": "create:andesite_alloy", "E": "create:electron_tube", "S": "create:shaft",
            "B": "create:brass_casing", "C": "create:cogwheel"},
           "create:mechanical_crafter", 1))

# THE CRAFTING TABLE: a 5x5 crafter wall — Edelwood Planks ring, Null Slate corners, Cogwheel sides,
# Creaking Heart centre (berlord's original spec). 2026-07-24: vanillabackport 1.1.7.10 added to the
# pack; contrary to the earlier session's check it DOES register the Creaking Heart — as
# minecraft:creaking_heart (blockstate, item model and loot table all minecraft-namespace, verified
# in the jar), so that id is used here.
CENTRE_ITEM = "minecraft:creaking_heart"
write(f"{R}/mechanical/pre_table/vanilla_crafting_table.json",
      mech(["PPPPP", "PNCNP", "PCHCP", "PNCNP", "PPPPP"],
           {"P": "forbidden_arcanus:edelwood_planks", "N": "malum:null_slate",
            "C": "create:cogwheel", "H": CENTRE_ITEM},
           "minecraft:crafting_table", 1))

# ==================================================== berlord batch 8 (2026-07-24, "build" session)
# Create machines + magic. Ids jar-verified this session; grids transcribed from berlord's notes/imgs.
# belt ITEM = create:belt_connector (create:belt is the placed block, not craftable).
_BELT = "create:belt_connector"
_p = lambda rows: [r.replace("N", " ") for r in rows]  # restore _p (a loop at ~L927 rebinds it to a str)

# --- Tunnels: 3x3 = CRAFTING TABLE (berlord: not mech crafters); 4x4 = mechanical crafting.
#     Brass = swap andesite_alloy->brass_ingot, top-middle->electron_tube. (paths kept to avoid stale files) ---
write(f"{R}/mechanical/kinetics/andesite_tunnel_3x3.json",
      shaped(["AAA", "ABA", "ABA"], {"A": _AA, "B": _BELT}, "create:andesite_tunnel"))
write(f"{R}/mechanical/kinetics/andesite_tunnel_4x4.json",
      mech(["AAAA", "ABBA", "ABBA", "ABBA"], {"A": _AA, "B": _BELT}, "create:andesite_tunnel"))
write(f"{R}/mechanical/kinetics/brass_tunnel_3x3.json",
      shaped(["ATA", "ABA", "ABA"], {"A": "create:brass_ingot", "B": _BELT, "T": _ET}, "create:brass_tunnel"))
write(f"{R}/mechanical/kinetics/brass_tunnel_4x4.json",
      mech(["ATTA", "ABBA", "ABBA", "ABBA"], {"A": "create:brass_ingot", "B": _BELT, "T": _ET}, "create:brass_tunnel"))

# --- Funnels: 3x3 crafting table (bottom row ANA per berlord's correction); 4x4 mech ---
write(f"{R}/mechanical/kinetics/andesite_funnel_3x3.json",
      shaped(_p(["NAN", "ABA", "ANA"]), {"A": _AA, "B": _BELT}, "create:andesite_funnel"))
write(f"{R}/mechanical/kinetics/andesite_funnel_4x4.json",
      mech(_p(["NAAN", "ABBA", "ANNA", "ANNA"]), {"A": _AA, "B": _BELT}, "create:andesite_funnel"))
write(f"{R}/mechanical/kinetics/brass_funnel_3x3.json",
      shaped(_p(["NTN", "ABA", "ANA"]), {"A": "create:brass_ingot", "B": _BELT, "T": _ET}, "create:brass_funnel"))
write(f"{R}/mechanical/kinetics/brass_funnel_4x4.json",
      mech(_p(["NTTN", "ABBA", "ANNA", "ANNA"]), {"A": "create:brass_ingot", "B": _BELT, "T": _ET}, "create:brass_funnel"))
# berlord batch 8: remove Create's stock tunnel/funnel crafting recipes so only the recipes above make them.
for _tf in ["andesite_tunnel", "brass_tunnel", "andesite_funnel", "brass_funnel"]:
    write(f"data/create/recipe/crafting/logistics/{_tf}.json", DISABLED)

# --- Brass Hand (5x5 mech) ---
write(f"{R}/mechanical/kinetics/brass_hand.json",
      mech(_p(["NAAN", "NAAN", "BBBB", "NBNN"]), {"A": _AA, "B": _BS}, "create:brass_hand"))

# --- Crushing Wheel: OVERRIDE Create's own 5x5 mech recipe (stock: 16 andesite_alloy + 4 planks +
#     1 stone centre -> 2). berlord: planks->obsidiansteel ingot, centre->canopy wood, output 1;
#     andesite-alloy filler kept (berlord's screenshot IS the stock recipe). ---
write("data/create/recipe/mechanical_crafting/crushing_wheel.json",
      mech(_p(["NAAAN", "AAOAA", "AOCOA", "AAOAA", "NAAAN"]),
           {"A": _AA, "O": "forbidden_arcanus:obsidiansteel_ingot", "C": "twilightforest:canopy_wood"},
           "create:crushing_wheel", 1))

# --- Hallowed Gold Ingot: Spirit Infusion (brass core + magic metals + 4 quartz + mnemonic) ---
write(f"{R}/malum/hallowed_gold_ingot.json",
      infusion("create:brass_ingot", 1,
               [("malum:cthonic_gold", 1), ("forbidden_arcanus:deorum_ingot", 1),
                ("irons_spellbooks:arcane_ingot", 1), ("armageddon_mod:gilded_nugget", 1),
                ("minecraft:quartz", 4), ("malum:mnemonic_fragment", 1)],
               [SP("sacred", 9), SP("eldritch", 6), SP("infernal", 3)],
               "malum:hallowed_gold_ingot", 1))

# --- Empty Blaze Burner: 3x3 table + 5x5 mech (replaces Create's craft; blaze-capture lighting stays) ---
_EBB = {"S": _ISH, "R": "minecraft:netherrack", "I": "slag:deep_alloy"}
write("data/create/recipe/crafting/kinetics/empty_blaze_burner.json",
      shaped(_p(["SNS", "SRS", "III"]), _EBB, "create:empty_blaze_burner"))
write(f"{R}/mechanical/kinetics/empty_blaze_burner.json",
      mech(_p(["SNNNS", "SNNNS", "SSSSS", "IRRRI", "IIIII"]), _EBB, "create:empty_blaze_burner"))

# --- Lit Blaze Burner: Spirit Infusion (additive; blaze-capture route unaffected) ---
write(f"{R}/malum/blaze_burner.json",
      infusion("create:empty_blaze_burner", 1,
               [("minecraft:nether_brick", 12), ("elemental_metals:fire_infused_iron_ingot", 2),
                ("born_in_chaos_v1:dark_metal_ingot", 1), ("minecraft:campfire", 1)],
               [SP("wicked", 16), SP("earthen", 16), SP("infernal", 32)],
               "create:blaze_burner", 1))

# --- Rose Quartz: additive Mixing route (berlord batch 8: 8 redstone + 1 quartz). ---
write(f"{R}/create/rose_quartz_mixing.json",
      {"neoforge:conditions": conds("create"), "type": "create:mixing",
       "ingredients": ([{"item": "minecraft:redstone"} for _ in range(8)] + [{"item": "minecraft:quartz"}]),
       "results": [{"id": "create:rose_quartz"}]})

# --- Mechanical Saw: 3x3 OVERRIDES Create's (stock " A "/"AIA"/" C " = iron plate/iron ingot/casing),
#     iron ingot -> propeller; plus a 5x4 mech version (berlord's grid). ---
write("data/create/recipe/crafting/kinetics/mechanical_saw.json",
      shaped(_p(["NAN", "APA", "NCN"]), {"A": "#c:plates/iron", "P": _PR, "C": _AC}, "create:mechanical_saw"))
write(f"{R}/mechanical/kinetics/mechanical_saw.json",
      mech(_p(["NSSSN", "SSISS", "SIPIS", "BBBBB"]),
           {"S": _ISH, "I": "minecraft:iron_ingot", "P": _PR, "B": _AC}, "create:mechanical_saw"))

# --- Deployer: 3x3 OVERRIDES Create's (stock column electron_tube/casing/brass_hand) + shafts in the
#     empty spots; plus a 5x5 mech version (berlord's grid). ---
write("data/create/recipe/crafting/kinetics/deployer.json",
      shaped(["SBS", "SCS", "SIS"], {"S": _SH, "B": _ET, "C": _AC, "I": "create:brass_hand"}, "create:deployer"))
write(f"{R}/mechanical/kinetics/deployer.json",
      mech(_p(["NNBNN", "NACAN", "SACAS", "NATAN", "NNSNN"]),
           {"B": "create:brass_hand", "A": _AC, "S": _SH, "T": _ET, "C": _CG}, "create:deployer"))

# --- Fluid machines (berlord batch 8): table versions OVERRIDE Create; mech versions additive.
#     "casing" here = copper_casing; "copper pipe" = create:fluid_pipe (no create:copper_pipe exists). ---
_COC = "create:copper_casing"
# Spout: 3x3 table + 5x5 mech
write("data/create/recipe/crafting/kinetics/spout.json",
      shaped(["SKS", "BPB", "SVS"],
             {"S": _CS, "K": _COC, "B": _BELT, "P": "create:fluid_pipe", "V": "create:copper_valve_handle"},
             "create:spout"))
write(f"{R}/mechanical/kinetics/spout.json",
      mech(_p(["CCPCC", "CBTBC", "CBTBC", "NCPCN", "NNVNN"]),
           {"C": _CS, "P": "create:fluid_pipe", "B": _COC, "T": "create:fluid_tank", "V": "create:copper_valve_handle"},
           "create:spout"))
# Copper Valve Handle: additive mech variant
write(f"{R}/mechanical/kinetics/copper_valve_handle_mecha.json",
      mech(_p(["CANAC", "CANAC", "NCACN", "NNCNN"]), {"C": _CS, "A": _AA}, "create:copper_valve_handle"))
# Fluid Tank: 3x3 table + 5x5 mech
write("data/create/recipe/crafting/kinetics/fluid_tank.json",
      shaped(["CCC", "CGC", "CCC"], {"C": _CS, "G": "minecraft:glass"}, "create:fluid_tank"))
write(f"{R}/mechanical/kinetics/fluid_tank.json",
      mech(["CCCCC", "CGGGC", "CGGGC", "CGGGC", "CCCCC"], {"C": _CS, "G": "minecraft:glass"}, "create:fluid_tank"))
# Copper (fluid) Pipe: additive 4x4 mech variant
write(f"{R}/mechanical/kinetics/fluid_pipe_mecha.json",
      mech(_p(["CNNC", "INNI", "INNI", "CNNC"]), {"C": _CS, "I": "minecraft:copper_ingot"}, "create:fluid_pipe"))
# Item Drain: 3x2 table + 5x3 mech
write("data/create/recipe/crafting/kinetics/item_drain.json",
      shaped(["CBC", "CDC"], {"C": _CS, "B": "minecraft:iron_bars", "D": _COC}, "create:item_drain"))
write(f"{R}/mechanical/kinetics/item_drain.json",
      mech(_p(["CBBBC", "CNNNC", "DDDDD"]), {"C": _CS, "B": "minecraft:iron_bars", "D": _COC}, "create:item_drain"))

# --- Precision Mechanism: OVERRIDE Create's sequenced assembly. berlord: input BRASS sheet; 3rd deploy
#     -> Lightning-Infused Iron Nugget; cog deploys + output/chances kept as-is. ---
_INC = "create:incomplete_precision_mechanism"
def _deploy(item):
    return {"type": "create:deploying", "ingredients": [{"item": _INC}, {"item": item}], "results": [{"id": _INC}]}
write("data/create/recipe/sequenced_assembly/precision_mechanism.json", {
    "neoforge:conditions": conds("create", "elemental_metals"),
    "type": "create:sequenced_assembly",
    "ingredient": {"item": "create:brass_sheet"},
    "loops": 5,
    "results": [
        {"chance": 120.0, "id": "create:precision_mechanism"},
        {"chance": 8.0, "id": "create:golden_sheet"},
        {"chance": 8.0, "id": "create:andesite_alloy"},
        {"chance": 5.0, "id": "create:cogwheel"},
        {"chance": 3.0, "id": "minecraft:gold_nugget"},
        {"chance": 2.0, "id": "create:shaft"},
        {"chance": 2.0, "id": "create:crushed_raw_gold"},
        {"id": "minecraft:iron_ingot"},
        {"id": "minecraft:clock"},
    ],
    "sequence": [_deploy("create:cogwheel"), _deploy("create:large_cogwheel"),
                 _deploy("elemental_metals:lightning_infused_iron_nugget")],
    "transitional_item": {"id": _INC},
})

# --- Mechanical Arm: 3x3 OVERRIDES Create (LLA/L__/IC_; A: andesite_alloy -> brass_hand per berlord);
#     5x5 mech additive. 's' = brass sheet (berlord). ---
write("data/create/recipe/crafting/kinetics/mechanical_arm.json",
      shaped(["LLA", "L  ", "IC "],
             {"L": "#c:plates/brass", "A": "create:brass_hand",
              "I": "create:precision_mechanism", "C": "create:brass_casing"}, "create:mechanical_arm"))
write(f"{R}/mechanical/kinetics/mechanical_arm.json",
      mech(_p(["NNSSS", "NNSNH", "NSSNN", "NSPSN", "BBBBB"]),
           {"S": _BS, "H": "create:brass_hand", "P": "create:precision_mechanism", "B": "create:brass_casing"},
           "create:mechanical_arm"))

# --- Structural Beam + Water Wheel Create sequenced assemblies (berlord batch 8). Each needs its own
#     registered transitional item (ModItems incomplete_*). loops=1 (single pass; berlord gave no loop). ---
def _seq_assembly(path, transitional, ingredient, steps, results, mods=(), loops=1):
    def _step(s):
        kind = s[0]
        if kind == "deploy":
            return {"type": "create:deploying", "ingredients": [{"item": transitional}, {"item": s[1]}], "results": [{"id": transitional}]}
        if kind == "press":
            return {"type": "create:pressing", "ingredients": [{"item": transitional}], "results": [{"id": transitional}]}
        if kind == "saw":
            return {"type": "create:cutting", "ingredients": [{"item": transitional}], "results": [{"id": transitional}]}
        if kind == "fill":
            return {"type": "create:filling", "ingredients": [{"item": transitional}, {"type": "neoforge:single", "amount": s[2], "fluid": s[1]}], "results": [{"id": transitional}]}
        raise ValueError(kind)
    write(path, {"neoforge:conditions": conds("create", *mods), "type": "create:sequenced_assembly",
                 "ingredient": {"item": ingredient}, "loops": loops, "results": results,
                 "sequence": [_step(s) for s in steps], "transitional_item": {"id": transitional}})

# Structural Beam: shaft -> 16-step sequence -> 70% x1 / 30% x2.
_seq_assembly(f"{R}/create/structural_beam_assembly.json", "bertie_progression:incomplete_structural_beam", "create:shaft",
              [("deploy", "create:brass_nugget"), ("deploy", "create:brass_nugget"), ("press",),
               ("deploy", "minecraft:vine"), ("deploy", "malum:earthen_spirit"),
               ("deploy", "minecraft:armadillo_scute"), ("deploy", "minecraft:armadillo_scute"),
               ("deploy", "minecraft:armadillo_scute"), ("deploy", "minecraft:armadillo_scute"), ("press",),
               ("fill", "slag:molten_quartz", 144),
               ("deploy", "create:copper_sheet"), ("deploy", "create:copper_sheet"), ("deploy", "create:copper_sheet"),
               ("deploy", "born_in_chaos_v1:diamond_termite_shard"), ("saw",)],
              [{"chance": 0.7, "id": "bertie_progression:kinetic_vane", "count": 1},
               {"chance": 0.3, "id": "bertie_progression:kinetic_vane", "count": 2}],
              mods=("malum", "slag", "born_in_chaos_v1"))
# Small Water Wheel: bound soul ingot + 8x deploy structural beam.
_seq_assembly(f"{R}/create/small_water_wheel_assembly.json", "bertie_progression:incomplete_small_water_wheel",
              "mythsandlegends:bound_soul_ingot", [("deploy", "bertie_progression:kinetic_vane")] * 8,
              [{"id": "create:water_wheel", "count": 1}], mods=("mythsandlegends",))
# Large Water Wheel: small water wheel + 8x deploy structural beam.
_seq_assembly(f"{R}/create/large_water_wheel_assembly.json", "bertie_progression:incomplete_large_water_wheel",
              "create:water_wheel", [("deploy", "bertie_progression:kinetic_vane")] * 8,
              [{"id": "create:large_water_wheel", "count": 1}])

# --- Shield Maiden (berlord batch 8): Hephaestus ritual on a Naga Trophy (grants Lich access). 8 pedestals. ---
write(f"{RIT}/shield_maiden.json",
      ritual("twilightforest:naga_trophy",
             [("twilightforest:firefly_jar", 2), ("create:precision_mechanism", 1),
              ("mythsandlegends:bound_soul_ingot", 1), ("iceandfire:hippocampus_fin", 1),
              ("born_in_chaos_v1:fangofthe_hound_leader", 1), ("born_in_chaos_v1:nightmare_claw", 1),
              ("born_in_chaos_v1:permafrost_shard", 1)],
             "bertie_progression:shield_maiden", 1, tier=1,   # berlord 2026-07-29: was tier=2
             essences={"aureal": 100, "blood": 3000, "souls": 10}, xp=100))

# --- Naga Trophy dupe (berlord batch 8): Spirit Infusion -> 2 trophies ("dupe it if you have friends"). ---
#     (berlord 2026-07-25: dropped the shattered skull + dark atrium, added cactus and green scales.)
#     Extra order = berlord's display order (EMI lays extras out in list order).
write(f"{R}/malum/naga_trophy_dupe.json",
      infusion("twilightforest:naga_trophy", 1,
               [("born_in_chaos_v1:ethereal_spirit", 2), ("minecraft:cactus", 12),
                ("iceandfire:sea_serpent_scales_green", 3), ("malum:cthonic_gold", 1),
                ("l2complements:totemic_gold_nugget", 3)],
               [SP("wicked", 6), SP("eldritch", 6), SP("aerial", 6), SP("earthen", 6)],
               "twilightforest:naga_trophy", 2))

# --- Mason Jar: mechanical-crafting recipe (berlord: identical to TF's default log-ring, yields 4). ---
write(f"{R}/mechanical/kinetics/mason_jar.json",
      mech(_p(["GWG", "GNG", "GGG"]), {"G": "minecraft:glass", "W": "twilightforest:twilight_oak_log"},
           "twilightforest:mason_jar", 4))

# --- Water Wheels: berlord — the sequenced assemblies are the sole route; disable Create's defaults.
#     (The r14 Hephaestus ritual is also removed above.) ---
write("data/create/recipe/crafting/kinetics/water_wheel.json", DISABLED)
write("data/create/recipe/crafting/kinetics/large_water_wheel.json", DISABLED)

# --- Colossal Iron Ingot: Create compacting (press over basin), 16 iron ingots + 250 mb Common Ink.
#     Fluid ingredient format verified from Create's diorite_from_flint compacting recipe. ---
write(f"{R}/create/colossal_iron_compacting.json",
      {"neoforge:conditions": conds("create", "armageddon_mod", "irons_spellbooks"),
       "type": "create:compacting",
       "heat_requirement": "heated",
       "ingredients": ([{"item": "minecraft:iron_ingot"} for _ in range(16)]
                       + [{"type": "neoforge:single", "amount": 250, "fluid": "irons_spellbooks:common_ink"}]),
       "results": [{"id": "armageddon_mod:colossal_iron_ingot"}]})

# --- Clibano: stock FA "secondary output" = its residue, a residue_type whose combine_info.result was a
#     BLOCK. berlord: make it the PRIMARY item. Override each shared residue_type -> result = the ingot/
#     item, required_amount 1 (recipe chances untouched). Each residue_type maps 1:1 to its primary, so
#     copper->copper_ingot, iron->iron_ingot, etc. CAVEAT (jar-decompiled): FA only pays residue on
#     SOUL/ENCHANTED fire; on PLAIN fire there is NO secondary at all — that gate needs a mixin. ---
def _residue(name, result_id, label):
    write(f"data/forbidden_arcanus/forbidden_arcanus/residue_type/{name}.json",
          {"combine_info": {"required_amount": 1, "result": {"count": 1, "id": result_id}},
           "name": {"text": label}})
_residue("copper", "minecraft:copper_ingot", "Copper Residue")
_residue("iron", "minecraft:iron_ingot", "Iron Residue")
_residue("gold", "minecraft:gold_ingot", "Gold Residue")
_residue("coal", "minecraft:coal", "Coal Residue")
_residue("diamond", "minecraft:diamond", "Diamond Residue")
_residue("emerald", "minecraft:emerald", "Emerald Residue")
_residue("lapis_lazuli", "minecraft:lapis_lazuli", "Lapis Residue")
_residue("netherite", "minecraft:netherite_scrap", "Netherite Residue")
_residue("rune", "forbidden_arcanus:rune", "Rune Residue")
_residue("arcane_crystal", "forbidden_arcanus:arcane_crystal", "Arcane Crystal Residue")

# Obsidiansteel clibano: raw iron -> Colossal Iron Ingot; drop the secondary entirely (no residue field).
write("data/forbidden_arcanus/recipe/clibano_combustion/obsidiansteel_ingot_from_clibano_combustion.json",
      {"neoforge:conditions": conds("forbidden_arcanus", "armageddon_mod"),
       "type": "forbidden_arcanus:clibano_combustion", "category": "misc",
       "cooking_time": 100, "enhancer": "forbidden_arcanus:artisan_relic", "experience": 0.5,
       "fire_type": "fire",
       "ingredients": {"first": {"item": "armageddon_mod:colossal_iron_ingot"},
                       "second": {"item": "minecraft:obsidian"}},
       "result": {"count": 1, "id": "forbidden_arcanus:obsidiansteel_ingot"}})

# Remove the iron -> "soulsteel" route (berlord: "soulsteel" = malum:soul_stained_steel_ingot; the
# Spirit-Infusion of 1 iron ingot + 4 refined soulstone + spirits). Disable Malum's recipe.
write("data/malum/recipe/spirit_infusion/soul_stained_steel_ingot.json", DISABLED)

# Hallowed Gold: replace Malum's default production (gold ingot + 4 quartz + spirits) with our brass
# Spirit-Infusion above. (Block/nugget round-trip recipes left intact.)
write("data/malum/recipe/spirit_infusion/hallowed_gold_ingot.json", DISABLED)

# Remove the crafting recipe for Arcane Ingot (berlord): Iron's Spellbooks' 3x3 (8 Arcane Essence
# around an arcane-ingot-base). Disabled; the deorum-core Spirit Infusion (arcane_ingot.json) remains.
write("data/irons_spellbooks/recipe/arcane_ingot.json", DISABLED)

# Deorum Ingot 3x3 (berlord: gold -> brass ingot). Override FA's #*#/MXM/#*# with brass at the centre.
write("data/forbidden_arcanus/recipe/deorum_ingot.json",
      shaped(["#*#", "MXM", "#*#"],
             {"#": "minecraft:charcoal", "*": "forbidden_arcanus:arcane_crystal_dust",
              "M": "forbidden_arcanus:mundabitur_dust", "X": "create:brass_ingot"},
             "forbidden_arcanus:deorum_ingot"))

# ================================================================ batch 9 (berlord 2026-07-25)

# --- Glass Bottle: 2 Glass double-smelted on the Brick Forge. ---
write(f"{R}/slag/glass_bottle.json",
      double_smelting("minecraft:glass", "minecraft:glass", "minecraft:glass_bottle", 1))

# --- THE CRAFTING LICENSE (OWED #1, closed by berlord 2026-07-25). Hephaestus ritual, Tier I:
#     forge_tier omitted = any tier, matching FA's own early rituals (ferrognetic_mixture etc.).
#     Chapter 2's finale, so it must be reachable on the T1 forge the player raised in Chapter 1.
#     900 "experience" is berlord's ink-for-XP swap mod paying the XP cost in common ink.
#     Exactly 8 inputs = exactly 8 pedestals (the ritual() assert is at its ceiling). ---
write(f"{RIT}/crafting_license.json",
      ritual("minecraft:crafting_table",
             [("twilightforest:exanimate_essence", 1), ("create:precision_mechanism", 1),
              ("mythsandlegends:bound_soul_ingot", 1), ("l2complements:totemic_gold_ingot", 1),
              ("create:electron_tube", 1), ("bertie_progression:kinetic_vane", 1),
              ("irons_spellbooks:blank_rune", 1), ("minecraft:writable_book", 1)],
             "bertie_progression:crafting_license", 1,
             essences={"aureal": 1000, "blood": 10000, "souls": 10}, xp=900))

# --- Lich Trophy dupe (berlord): Spirit Infusion, 1 trophy -> 2, same shape as the Naga dupe. ---
#     Extra order = berlord's display order (EMI lays extras out in list order).
write(f"{R}/malum/lich_trophy_dupe.json",
      infusion("twilightforest:lich_trophy", 1,
               [("iceandfire:stymphalian_bird_feather", 2), ("born_in_chaos_v1:shattered_skull", 1),
                ("l2complements:totemic_gold_ingot", 1), ("mythsandlegends:bound_soul_ingot", 1),
                ("malum:mnemonic_fragment", 4)],
               [SP("wicked", 6), SP("eldritch", 6), SP("arcane", 6), SP("aerial", 6)],
               "twilightforest:lich_trophy", 2))

# ================================================================ batch 10 (berlord 2026-07-25)

# --- Armageddon summons, ported to the Brick Forge so they are reachable PRE-TABLE. Both stock
#     recipes are 3x3 (table-gated) with these exact ingredients, so these are additive early routes,
#     compressed to the 2 ingredients slag:double_smelting allows. small_flowers = the stock tag. ---
write(f"{R}/slag/iron_remote.json",
      double_smelting("minecraft:iron_ingot", "minecraft:sunflower",
                      "armageddon_mod:iron_remote", 1))
write(f"{R}/slag/strange_coin.json",
      double_smelting("armageddon_mod:colossal_iron_ingot", "minecraft:gold_ingot",
                      "armageddon_mod:strange_coin", 1))

# berlord 2026-07-31: both stock 3x3 routes are OUT, so the two Brick Forge recipes above are now
# the only way to either item. The Iron Remote also narrows from #minecraft:small_flowers to the
# Sunflower specifically - which is a TALL flower and was never in that tag, so this is a real
# tightening, not a restatement. armageddon_mod:infinite_iron_remote_recipe is a DIFFERENT item and
# is left alone. Needs the armageddon_mod ordering="AFTER" edge in neoforge.mods.toml.
write("data/armageddon_mod/recipe/iron_remote_recipe.json", DISABLED)
write("data/armageddon_mod/recipe/strange_coin_recipe.json", DISABLED)

# --- Refined Soulstone: was a Mallet bed recipe (4 raw + diamond); berlord moved it to a plain
#     Brick-Forge alloy, 1 Diamond + 1 Raw Soulstone. ---
write(f"{R}/slag/refined_soulstone.json",
      double_smelting("minecraft:diamond", "malum:raw_soulstone", "malum:refined_soulstone", 1))

# --- Compass: the Mallet bed recipe is gone and Iron's Spellbooks' 3x3 Wayward Compass is disabled;
#     a Hephaestus ritual is the route now (Redstone core + 4 Iron on pedestals). ---
write("data/irons_spellbooks/recipe/wayward_compass.json", DISABLED)
write(f"{RIT}/compass.json",
      ritual("minecraft:redstone", [("minecraft:iron_ingot", 4)], "minecraft:compass", 1))

# --- Aureal Bottle: a Hephaestus ritual so Aureal can be bootstrapped WITHOUT already having Aureal —
#     hence no essence cost. Main ingredient is a real WATER BOTTLE, pinned with a neoforge:components
#     ingredient (Ritual.mainIngredient is a plain vanilla Ingredient, so custom types work; the same
#     shape already drives the slag-plate ritual inputs). 4+2+2 = 8 pedestals, at the ceiling. ---
write(f"{RIT}/aureal_bottle.json",
      {**ritual("minecraft:potion",
                [("forbidden_arcanus:arcane_crystal_dust", 4), ("minecraft:rotten_flesh", 2),
                 ("#bertie_progression:meat", 2)],
                "forbidden_arcanus:aureal_bottle", 1),
       "main_ingredient": {"type": "neoforge:components", "items": "minecraft:potion",
                           "components": {"minecraft:potion_contents": {"potion": "minecraft:water"}}}})

# --- Crude Scythe: Malum's own recipe removed; the Hephaestus reforge of the Dead King's Decrepit
#     Scythe (r_harvest ritual) is the sole route. ---
write("data/malum/recipe/crude_scythe.json", DISABLED)

# ================================================================ batch 13 (berlord 2026-07-27)
# Malum totemic branch + crucible line.

# --- Totemic Staff: berlord's 2x2 replaces Malum's 3x3 diagonal. Grid is
#     N B / A N  (N = empty), B = runewood planks tag, A = FA edelwood stick. ---
write("data/malum/recipe/totemic_staff.json",
      shaped([" B", "A "], {"B": "#malum:runewood_planks", "A": "forbidden_arcanus:edelwood_stick"},
             "malum:totemic_staff"))

# --- Runewood Totem Base: Spirit Altar, runewood LOG core, one of every spirit, and
#     4 Hex Ash + 4 FA Runes on the pedestals (replaces Malum's 4-log/6-plank/2-ash version). ---
write("data/malum/recipe/spirit_infusion/runewood_totem_base.json",
      infusion("malum:runewood_log", 1,
               [("malum:hex_ash", 4), ("forbidden_arcanus:rune", 4)],
               [SP(s, 1) for s in ("aerial", "aqueous", "arcane", "earthen",
                                   "eldritch", "infernal", "sacred", "wicked")],
               "malum:runewood_totem_base", 1))

# --- Hex Ash: keep Malum's gunpowder + 1 arcane spirit; one charcoal fragment and one soulstone. ---
write("data/malum/recipe/spirit_infusion/hex_ash.json",
      infusion("minecraft:gunpowder", 1,
               [("forbidden_arcanus:arcane_crystal_dust_speck", 1),
                ("malum:arcane_charcoal_fragment", 1),
                ("malum:refined_soulstone", 1)],
               [SP("arcane", 1)], "malum:hex_ash", 1))

# --- Arcane Charcoal: was 4 coal -> 4 on arcane + 2 infernal. berlord: 1 -> 1, one infernal only. ---
write("data/malum/recipe/spirit_infusion/arcane_charcoal.json",
      infusion("#minecraft:coals", 1, [], [SP("infernal", 1)], "malum:arcane_charcoal", 1))

# --- Tainted / Twisted Rock: both were 16 stone -> 16. berlord: 1 -> 1, and each now takes its own
#     stone - Tainted from DIORITE, Twisted from GRANITE. Spirits unchanged. ---
for _rock, _sp, _stone in (("tainted", "sacred", "minecraft:diorite"),
                           ("twisted", "wicked", "minecraft:granite")):
    write(f"data/malum/recipe/spirit_infusion/{_rock}_rock.json",
          infusion(_stone, 1, [], [SP(_sp, 1), SP("arcane", 1)], f"malum:{_rock}_rock", 1))

# --- Spirit Jar: Malum's 1x2 is Hallowed Gold over glass; berlord swaps in a Create brass sheet. ---
write("data/malum/recipe/spirit_jar.json",
      shaped(["X", "Y"], {"X": "create:brass_sheet", "Y": "#c:glass_blocks"}, "malum:spirit_jar"))

# --- Alchemical Calx: stock is 4 clay -> 4 on arcane/earthen/aqueous x2. berlord: 6 clay -> 1 with
#     three new pedestal inputs; spirits untouched. ---
write("data/malum/recipe/spirit_infusion/alchemical_calx.json",
      infusion("minecraft:clay_ball", 6,
               [("malum:grim_talc", 1), ("minecraft:bone", 5), ("#c:mushrooms", 3)],
               [SP("arcane", 2), SP("earthen", 2), SP("aqueous", 2)],
               "malum:alchemical_calx", 1))

# --- Alchemical Impetus: 4 Calx core, 4 Earthen + 4 Aerial, four 4x pedestal inputs, and the result
#     is handed over PRE-DAMAGED to 8 durability. Impetuses are 800 max (ImpetusItem ctor) and
#     spirit_infusion deserializes `result` with ItemStack.CODEC, so `components` works here -
#     see docs/malum-impetus-recipes.md. 800 - 8 = damage 792. ---
_impetus = infusion("malum:alchemical_calx", 4,
                    [("malum:hex_ash", 4), ("malum:raw_soulstone", 4),
                     ("malum:raw_brilliance", 4), ("malum:natural_quartz", 4)],
                    [SP("earthen", 4), SP("aerial", 4)], "malum:alchemical_impetus", 1)
_impetus["result"]["components"] = {"minecraft:damage": 792}
write("data/malum/recipe/spirit_infusion/alchemical_impetus.json", _impetus)

# --- Spirit Crucible focusing (malum:spirit_focusing). Stock ships a whole alchemical-impetus family
#     under data/MINECRAFT/recipe/spirit_crucible/ (amethyst, glowstone, gunpowder, prismarine,
#     quartz, redstone - all cost 1 / 300t); only the glowstone one is replaced here. ---
def focusing(input_item, result_id, count, spirits, time=600, cost=2):
    return {"neoforge:conditions": conds("malum"), "type": "malum:spirit_focusing",
            "input": {"item": input_item},
            "result": {"id": result_id, "count": count},
            "spirits": [{"type": t, "count": c} for t, c in spirits],
            "time": time, "durabilityCost": cost}

write("data/minecraft/recipe/spirit_crucible/glowstone_dust.json", DISABLED)   # stock: 1 infernal -> 8
write(f"{R}/malum/focusing_glowstone_dust.json",
      focusing("malum:alchemical_impetus", "minecraft:glowstone_dust", 4,
               [SP("infernal", 2), SP("earthen", 1)]))
write(f"{R}/malum/focusing_blaze_powder.json",
      focusing("malum:alchemical_impetus", "minecraft:blaze_powder", 2,
               [SP("infernal", 4), SP("aerial", 2)]))

# ================================================================ batch 11 (berlord 2026-07-26)

# --- Refined Brilliance: Malum's raw-brilliance smelt AND blast both yield 2, duplicating our own
#     1-output cooking recipes in EMI. berlord: kill the x2 pair. (The brilliant_stone and crushed/
#     deepslate variants are untouched - they take different inputs.) ---
write("data/malum/recipe/brilliance_from_raw_blasting.json", DISABLED)
write("data/malum/recipe/brilliance_from_raw_smelting.json", DISABLED)

# --- Platings: Malum's 3x3 crafting recipes (which yield 2) are out; a Create press turns
#     1 ingot into 1 plating instead. ---
for _metal in ("soul_stained_steel", "malignant_pewter"):
    write(f"data/malum/recipe/{_metal}_plating.json", DISABLED)
    write(f"{R}/create/{_metal}_plating_pressing.json",
          {"neoforge:conditions": conds("create", "malum"), "type": "create:pressing",
           "ingredients": [{"item": f"malum:{_metal}_ingot"}],
           "results": [{"id": f"malum:{_metal}_plating"}]})

# ================================================================ batch 17 (berlord 2026-07-29)

# --- Acolyte of Deflection: the Lich-Trophy counterpart of the Shield Maiden. Same shape as
#     shield_maiden.json above - a boss trophy is forged into the key that opens the next path,
#     so the trophy is spent rather than hoarded (and the Lich dupe below it pays for a second).
#     8 pedestals exactly (2 + 2 + 1 + 1 + 1 + 1). Forge T1, like the Shield Maiden now is.
#     "400 ink" = the xp field, paid in Iron's ink by forgeink (see crafting_license above).
#     Dragon Bone here is ICE AND FIRE's (iceandfire:dragonbone), NOT
#     block_factorys_bosses:dragon_bone - both display as "Dragon Bone". ---
write(f"{RIT}/acolyte_of_deflection.json",
      ritual("twilightforest:lich_trophy",
             [("iceandfire:dragonbone", 2), ("malum:hallowed_gold_ingot", 2),
              ("born_in_chaos_v1:shattered_skull", 1), ("create:precision_mechanism", 1),
              ("mythsandlegends:bound_soul_ingot", 1), ("twilightforest:magic_map_focus", 1)],
             "bertie_progression:acolyte_of_deflection", 1, tier=1,
             essences={"aureal": 100, "blood": 6000, "souls": 10}, xp=400))

# --- Deep Waters Key: was a plain 3x3 (clay/sand/cobbled deepslate, deepwaters:hovaport). berlord
#     moves it onto the Hephaestus Forge. 8 pedestals exactly (4 + 2 + 2). "200 ink" = the xp field.
#     forge_tier omitted = any tier: it is the ROOT of the C3 water path, so it must be reachable on
#     the T1 forge, same reasoning as crafting_license. ---
write(f"{RIT}/deepwaters_key.json",
      ritual("minecraft:nautilus_shell",
             [("iceandfire:sea_serpent_fang", 4), ("malum:warp_flux", 2), ("slag:deep_alloy", 2)],
             "deepwaters:endlesscaves", 1,
             essences={"aureal": 60, "blood": 0, "souls": 4}, xp=200))
write("data/deepwaters/recipe/hovaport.json", DISABLED)

# --- Crowned Jelly (deepwaters:howa_crow_j): stock is Pearl/Gold/Medusabucket in a plus. berlord
#     swaps the gold for Hallowed Gold and fills the four corners with Flaming Opal. ---
write("data/deepwaters/recipe/howa_crow_j.json",
      shaped(["dad", "bcb", "dad"],
             {"a": "deepwaters:pearl", "b": "malum:hallowed_gold_ingot",
              "c": "deepwaters:medusabucket", "d": "deepwaters:fopal"},
             "deepwaters:crownedjelly"))

# --- Block of Flaming Opal (deepwaters:howafopalblock): the mod already trades 4 gems for the block,
#     but SHAPELESS. berlord wants the 2x2 shape. Same 4-in/1-out ratio, so the mod's own unblock
#     recipe (1 block -> 4 gems) stays balanced and is left alone. ---
write("data/deepwaters/recipe/howafopalblock.json",
      shaped(["ff", "ff"], {"f": "deepwaters:fopal"}, "deepwaters:fopal_block"))

# --- Snow Queen Trophy dupe: 1 trophy -> 2, same shape as the Naga and Lich dupes above.
#     Extra order = berlord's display order (EMI lays extras out in list order). ---
write(f"{R}/malum/snow_queen_trophy_dupe.json",
      infusion("twilightforest:snow_queen_trophy", 1,
               [("minecraft:bone", 12), ("minecraft:blue_ice", 1),
                ("minecraft:snow_block", 6), ("malum:wind_nucleus", 2),
                ("born_in_chaos_v1:phantom_powder", 3)],
               [SP("wicked", 6), SP("eldritch", 6), SP("aqueous", 6), SP("aerial", 6)],
               "twilightforest:snow_queen_trophy", 2))

# --- Sirok's Nest map (berlord 2026-07-29, note 1 of the finder series). A FINDER item, not a map:
#     a recipe result cannot be a structure map (Recipe.assemble gets no level/position), so the craft
#     yields bertie_progression:sirok_nest_map and FinderItem resolves it. See FinderItem's class comment.
#     The Gorgon Head is a CATALYST - matched, required, returned to the grid - which is why this uses
#     our own bertie_progression:catalyst_shaped serializer instead of minecraft:crafting_shaped. ---
# "any type of chitin works": Ice and Fire ships three and NO chitin tag exists in any pack jar
# (checked all 109), so we ship our own rather than trust a tag we do not control.
write("data/bertie_progression/tags/item/deathworm_chitin.json",
      {"values": ["iceandfire:deathworm_chitin_red", "iceandfire:deathworm_chitin_yellow",
                  "iceandfire:deathworm_chitin_white"]})

write(f"{R}/sirok_nest_map.json",
      {"neoforge:conditions": conds("iceandfire", "irons_spellbooks", "block_factorys_bosses"),
       "type": "bertie_progression:catalyst_shaped",
       "category": "misc",
       "key": {"c": {"tag": "bertie_progression:deathworm_chitin"},
               "g": {"item": "iceandfire:gorgon_head"},
               "i": {"item": "minecraft:glow_ink_sac"},
               "m": {"item": "minecraft:map"},
               "r": {"item": "irons_spellbooks:rare_ink"}},
       "pattern": ["cgc", "imi", "crc"],
       "result": {"id": "bertie_progression:sirok_nest_map", "count": 1},
       "catalyst": {"item": "iceandfire:gorgon_head"}})

# --- The four Cataclysm eyes: Hephaestus rituals REPLACING Cataclysm's own 3x3 crafts (berlord
#     2026-07-29). Each is core + 8 pedestals (2+2+2+2), and each core is the trophy or gauntlet the
#     boss at the end of that C3 row drops - so every row now spends its own kill.
#     NOTE: berlord gave no essence cost and no forge tier for any of the four. They ship free and
#     any-tier, as specified; flagged to him. ---
# "any coral - not block, not dead, not fan": #minecraft:coral_plants is exactly that set, but vanilla
# ships it only as a BLOCK tag (verified against the 1.21.1 client jar), so we ship the item tag.
write("data/bertie_progression/tags/item/corals.json",
      {"values": ["minecraft:tube_coral", "minecraft:brain_coral", "minecraft:bubble_coral",
                  "minecraft:fire_coral", "minecraft:horn_coral"]})

for _stock in ("desert_eye", "cursed_eye", "storm_eye", "abyss_eye"):
    write(f"data/cataclysm/recipe/{_stock}.json", DISABLED)

write(f"{RIT}/desert_eye.json",
      ritual("block_factorys_bosses:sandworm_gauntlet",
             [("malum:grim_talc", 2), ("minecraft:dead_bush", 2),
              ("malum:cthonic_gold", 2), ("minecraft:chiseled_sandstone", 2)],
             "cataclysm:desert_eye", 1))
write(f"{RIT}/cursed_eye.json",
      ritual("block_factorys_bosses:ice_gauntlet",
             [("twilightforest:alpha_yeti_fur", 2), ("minecraft:snowball", 2),
              ("iceandfire:ectoplasm", 2), ("minecraft:packed_ice", 2)],
             "cataclysm:cursed_eye", 1))
write(f"{RIT}/storm_eye.json",
      ritual("twilightforest:ur_ghast_trophy",
             [("twilightforest:knightmetal_ingot", 2), ("minecraft:phantom_membrane", 2),
              ("iceandfire:amphithere_feather", 2), ("minecraft:sea_lantern", 2)],
             "cataclysm:storm_eye", 1))
write(f"{RIT}/abyss_eye.json",
      ritual("deepwaters:blackpearl",
             [("block_factorys_bosses:kraken_tooth", 2), ("#bertie_progression:corals", 2),
              ("iceandfire:sea_serpent_fang", 2), ("minecraft:crying_obsidian", 2)],
             "cataclysm:abyss_eye", 1))

# --- batch 17c (berlord 2026-07-29): the two remaining finders and the four elemental CORES. ---
# Kraken map: Black Pearl is the catalyst. "any sea serpent goes" -> Ice and Fire's OWN tag, which
# already lists all seven scale colours; no bertie tag needed here.
write(f"{R}/kraken_ship_map.json",
      {"neoforge:conditions": conds("iceandfire", "irons_spellbooks", "deepwaters", "block_factorys_bosses"),
       "type": "bertie_progression:catalyst_shaped", "category": "misc",
       "key": {"s": {"tag": "iceandfire:scales/sea_serpent"},
               "p": {"item": "deepwaters:blackpearl"},
               "i": {"item": "minecraft:glow_ink_sac"},
               "m": {"item": "minecraft:map"},
               "r": {"item": "irons_spellbooks:rare_ink"}},
       "pattern": ["sps", "imi", "srs"],
       "result": {"id": "bertie_progression:kraken_ship_map", "count": 1},
       "catalyst": {"item": "deepwaters:blackpearl"}})

# Skor hideout map: Snow Queen Trophy is the catalyst (so the trophy is HELD, not spent).
write(f"{R}/yeti_hideout_map.json",
      {"neoforge:conditions": conds("twilightforest", "irons_spellbooks", "block_factorys_bosses"),
       "type": "bertie_progression:catalyst_shaped", "category": "misc",
       "key": {"f": {"item": "twilightforest:alpha_yeti_fur"},
               "q": {"item": "twilightforest:snow_queen_trophy"},
               "i": {"item": "minecraft:glow_ink_sac"},
               "m": {"item": "minecraft:map"},
               "r": {"item": "irons_spellbooks:rare_ink"}},
       "pattern": ["fqf", "imi", "frf"],
       "result": {"id": "bertie_progression:yeti_hideout_map", "count": 1},
       "catalyst": {"item": "twilightforest:snow_queen_trophy"}})

# --- The four elemental cores. 7x7 mechanical-crafter walls, transcribed from berlord's screenshots
#     (all four are 4-fold symmetric, which is the check that the transcription is right).
#     Each wall yields TWO (berlord 2026-07-31), which is exactly what the doubled HF2 ritual eats,
#     so one wall per core still upgrades the forge once. ---
write(f"{R}/mechanical/abyssal_core.json",
      mech(["WWPPPWW", "WPOAOPW", "PODCDOP", "PACBCAP", "PODCDOP", "WPOAOPW", "WWPPPWW"],
           {"W": "malum:astral_weave", "P": "malum:soul_stained_steel_plating",
            "O": "deepwaters:fopal", "A": "deepwaters:aquamarine_block",
            "D": "minecraft:diamond_block", "C": "cataclysm:coral_chunk",
            "B": "deepwaters:blackpearl"},
           "bertie_progression:abyssal_core", 2))
write(f"{R}/mechanical/desert_core.json",
      mech(["SSSGSSS", "SCRKRCS", "SRCKCRS", "GKKMKKG", "SRCKCRS", "SCRKRCS", "SSSGSSS"],
           {"S": "create:brass_sheet", "G": "armageddon_mod:gilded_plate",
            "C": "malum:cthonic_gold", "R": "slag:rose_gold_block",
            "K": "iceandfire:dragonbone", "M": "cataclysm:ancient_metal_block"},
           "bertie_progression:desert_core", 2))
write(f"{R}/mechanical/cursed_core.json",
      mech(["DDFDFDD", "DFSSSFD", "FSBBBSF", "DSBCBSD", "FSBBBSF", "DFSSSFD", "DDFDFDD"],
           {"D": "slag:deep_alloy_block", "F": "malum:imitation_flesh",
            "S": "malum:cursed_sapball", "B": "cataclysm:black_steel_ingot",
            "C": "cataclysm:cursium_ingot"},
           "bertie_progression:cursed_core", 2))
write(f"{R}/mechanical/storm_core.json",
      mech(["BLBLBLB", "LPNINPL", "BNEPENB", "LIPHPIL", "BNEPENB", "LPNINPL", "BLBLBLB"],
           {"B": "irons_spellbooks:lightning_bottle", "L": "cataclysm:lacrima",
            "P": "minecraft:lapis_block", "N": "malum:wind_nucleus",
            "I": "elemental_metals:lightning_infused_iron_ingot",
            "E": "cataclysm:essence_of_the_storm", "H": "minecraft:heart_of_the_sea"},
           "bertie_progression:storm_core", 2))

# ================================================================ batch 18 (berlord 2026-07-29)
# Dark Arts textile/pouch/scythe branch and Imitation Heart rewrite.

# Any Ice and Fire dragon heart is the core. The mod's own dragon_hearts tag contains fire, ice and
# lightning hearts (jar-verified); all four requested pedestal stacks are unbounded Malum extras.
write("data/malum/recipe/spirit_infusion/imitation_heart.json",
      infusion("#iceandfire:dragon_hearts", 1,
               [("malum:imitation_flesh", 4), ("malum:warp_flux", 2),
                ("create:brass_sheet", 6), ("malum:iridescent_ether", 6)],
               [SP("sacred", 16), SP("wicked", 16), SP("arcane", 16), SP("eldritch", 16)],
               "malum:imitation_heart", 1))

# Soulwoven Silk: replaces Malum's 2 Wool + 2 String -> 4 stock infusion.
write("data/malum/recipe/spirit_infusion/soulwoven_silk.json",
      infusion("#minecraft:wool", 4,
               [("malum:hex_ash", 1), ("born_in_chaos_v1:spiritual_dust", 1),
                ("minecraft:string", 5), ("minecraft:leather", 3)],
               [SP("sacred", 4), SP("aerial", 3), SP("earthen", 3)],
               "malum:soulwoven_silk", 1))

# Arcane Cloth: replace Iron's Spellbooks' wool centre with Soulwoven Silk; the eight-essence ring
# and one-cloth output stay the same.
write("data/irons_spellbooks/recipe/magic_cloth.json",
      shaped(["AAA", "ASA", "AAA"],
             {"A": "irons_spellbooks:arcane_essence", "S": "malum:soulwoven_silk"},
             "irons_spellbooks:magic_cloth"))

# Astral Weave gains a Spirit Altar route; Malum's phantom/ghast reaping data remains available.
write(f"{R}/malum/astral_weave.json",
      infusion("irons_spellbooks:magic_cloth", 1,
               [("malum:soulwoven_silk", 2), ("minecraft:phantom_membrane", 3),
                ("minecraft:string", 8)],
               [SP("sacred", 8), SP("aerial", 12), SP("arcane", 16)],
               "malum:astral_weave", 1))

# Soulwoven Pouch: stock 1x2 craft disabled; Bundle core + exactly eight Forge pedestals.
write("data/malum/recipe/soulwoven_pouch.json", DISABLED)
write(f"{RIT}/soulwoven_pouch.json",
      ritual("minecraft:bundle",
             [("malum:soulwoven_silk", 4), ("minecraft:string", 4)],
             "malum:soulwoven_pouch", 1,
             essences={"aureal": 30, "blood": 1000, "souls": 0}))

# Ravenous Pouch: stock Spirit Infusion disabled; its Tier-I Forge replacement also fills all eight
# pedestals (3 + 2 + 1 + 2).
write("data/malum/recipe/spirit_infusion/ravenous_pouch.json", DISABLED)
write(f"{RIT}/ravenous_pouch.json",
      ritual("malum:soulwoven_pouch",
             [("twilightforest:raven_feather", 3), ("malum:soulwoven_silk", 2),
              ("malum:grim_talc", 1), ("minecraft:string", 2)],
             "malum:ravenous_pouch", 1, tier=1))

# Soulstained Steel Scythe: replace Malum's stock infusion and retain the Crude Scythe components.
_soulstained_scythe = infusion(
    "malum:crude_scythe", 1,
    [("iceandfire:dragonbone", 2), ("malum:soul_stained_steel_plating", 6),
     ("malum:malignant_lead", 12), ("malum:mnemonic_fragment", 20)],
    ALL8x8, "malum:soul_stained_steel_scythe", 1)
_soulstained_scythe["carryOverComponentData"] = True
write("data/malum/recipe/spirit_infusion/soul_stained_steel_scythe.json",
      _soulstained_scythe)

# --- Living Flesh (berlord 2026-07-30): Malum's own spirit_infusion for it is overridden. The
#     block round-trip (living_flesh_from_block) is LEFT ALONE - killing it would strand any
#     Block of Living Flesh a player already owns. ---
# "dragon flesh (any of 3)": the three share no stem and no mod ships a tag, so we ship one.
write("data/bertie_progression/tags/item/dragon_flesh.json",
      {"values": ["iceandfire:fire_dragon_flesh", "iceandfire:ice_dragon_flesh",
                  "iceandfire:lightning_dragon_flesh"]})
write("data/malum/recipe/spirit_infusion/living_flesh.json",
      infusion("#bertie_progression:dragon_flesh", 1,
               [("minecraft:rotten_flesh", 64), ("irons_spellbooks:blood_vial", 8),
                ("born_in_chaos_v1:monster_flesh", 4)],
               [SP("sacred", 6), SP("wicked", 6), SP("aqueous", 6)],
               "malum:living_flesh", 1))

# --- Sturdy Sheet + Powdered Obsidian (berlord 2026-07-30) -------------------------------------
# Sheet: the assembly now starts from an Obsidiansteel Ingot instead of obsidian dust, with two
# deploy steps applying Powdered Obsidian in front of Create's original fill/press/press. Written out
# by hand rather than through _seq_assembly so the absence of `loops` matches stock exactly - the
# stock recipe omits it, and writing an explicit value would be a silent behaviour change.
_UOS = "create:unprocessed_obsidian_sheet"
_deploy = lambda item: {"type": "create:deploying",
                        "ingredients": [{"item": _UOS}, {"item": item}],
                        "results": [{"id": _UOS}]}
write("data/create/recipe/sequenced_assembly/sturdy_sheet.json", {
    "neoforge:conditions": conds("create", "forbidden_arcanus"),
    "type": "create:sequenced_assembly",
    "ingredient": {"item": "forbidden_arcanus:obsidiansteel_ingot"},
    "results": [{"id": "create:sturdy_sheet"}],
    "sequence": [
        _deploy("create:powdered_obsidian"),
        _deploy("create:powdered_obsidian"),
        {"type": "create:filling",
         "ingredients": [{"item": _UOS},
                         {"type": "neoforge:single", "amount": 500, "fluid": "minecraft:lava"}],
         "results": [{"id": _UOS}]},
        {"type": "create:pressing", "ingredients": [{"item": _UOS}], "results": [{"id": _UOS}]},
        {"type": "create:pressing", "ingredients": [{"item": _UOS}], "results": [{"id": _UOS}]},
    ],
    "transitional_item": {"id": _UOS},
})

# Crushing obsidian: was 1 dust + 75% obsidian back. Now a second dust at 25% and the obsidian
# return cut to 10%, so crushing is a real conversion rather than a near-free duplicator.
write("data/create/recipe/crushing/obsidian.json", {
    "neoforge:conditions": conds("create"),
    "type": "create:crushing",
    "ingredients": [{"item": "minecraft:obsidian"}],
    "processing_time": 500,
    "results": [{"id": "create:powdered_obsidian"},
                {"chance": 0.25, "id": "create:powdered_obsidian"},
                {"chance": 0.1, "id": "minecraft:obsidian"}],
})

# --- Netherly Meal (berlord 2026-07-31): Hephaestus T2, Bowl core, 7 pedestals.
#     "max souls, max blood" = the TIER II ceiling (50 / 15000), jar-verified from HephaestusForgeLevel
#     - the ritual runs ON a T2 forge, so those are the most it can hold. Aureal and ink unspecified,
#     so both are zero. ---
write(f"{RIT}/netherly_meal.json",
      ritual("minecraft:bowl",
             [("iceandfire:fire_dragon_heart", 1), ("cataclysm:koboleton_bone", 1),
              ("malum:living_flesh", 1), ("iceandfire:fire_dragon_blood", 1),
              ("#iceandfire:scales/dragon/fire", 2), ("minecraft:lava_bucket", 1)],
             "bertie_progression:netherly_meal", 1, tier=2,
             essences={"aureal": 0, "blood": 15000, "souls": 50}))

# ================================================================ REMOVED ITEMS (berlord 2026-07-30)
# Source of truth: docs/removed/<modid>.md, hand-edited. See docs/removed/README.md.
# This section does three things:
#   1. finds EVERY recipe in the pack whose result is a removed id and overrides it with
#      neoforge:false - searched by RESULT, so no recipe file is ever named by hand;
#   2. writes removed_items.json at the jar root for RemovedItems.java, which drops the ids from
#      every creative tab (and therefore from EMI, whose index-source is `creative`);
#   3. rewrites the LEAKS block in each doc with the loot tables that still reference a removed id.
# Needs a synced bertie pack instance to scan. Without it: warn and skip, never silently emit nothing.

REMOVED_DOCS = os.path.normpath(os.path.join(ROOT, "..", "..", "docs", "removed"))
INSTANCE_MODS = os.path.join(os.environ.get("APPDATA", ""), "PrismLauncher", "instances",
                             "bertie demo", ".minecraft", "mods")

def _parse_removed(path, modid):
    """Strict pipe-table parser. A malformed row is a build error, never a silent skip."""
    rows, in_table = [], False
    for n, line in enumerate(io.open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if line.startswith("<!-- LEAKS:"):
            break
        if not line.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            raise SystemExit(f"{path}:{n}: expected 4 columns, got {len(cells)}: {line}")
        if cells[1].lower() == "id":          # header
            in_table = True
            continue
        if set("".join(cells)) <= set("-: "):  # separator
            continue
        if not in_table:
            continue
        name, iid, reason, date = cells
        iid = iid.strip("`")
        if ":" not in iid:
            raise SystemExit(f"{path}:{n}: id has no namespace: {iid!r}")
        if iid.split(":")[0] != modid:
            raise SystemExit(f"{path}:{n}: id {iid!r} does not belong in {modid}.md")
        if not reason:
            raise SystemExit(f"{path}:{n}: {iid} has no reason")
        rows.append({"name": name, "id": iid, "reason": reason, "removed": date})
    return rows

def _result_ids(obj, out):
    """Pull every result item id out of a recipe of ANY type/shape."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("result", "results"):
                for e in (v if isinstance(v, list) else [v]):
                    if isinstance(e, str):
                        out.add(e)
                    elif isinstance(e, dict):
                        for kk in ("id", "item"):
                            if isinstance(e.get(kk), str):
                                out.add(e[kk])
            elif isinstance(v, (dict, list)):
                _result_ids(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _result_ids(v, out)
    return out

_removed = []
if os.path.isdir(REMOVED_DOCS):
    for _fn in sorted(os.listdir(REMOVED_DOCS)):
        if _fn.endswith(".md") and _fn != "README.md":
            _removed += _parse_removed(os.path.join(REMOVED_DOCS, _fn), _fn[:-3])

# Walk the pack ONCE: registered item ids (for glob expansion), recipes by result, loot references.
# Skipped entirely when nothing is removed, so an empty list costs nothing.
_items, _hits, _leaks = set(), [], {}
_scan_ok = False
if _removed:
    import fnmatch
    import zipfile
    _scan = [os.path.join(INSTANCE_MODS, f) for f in sorted(os.listdir(INSTANCE_MODS))
             if f.endswith(".jar")] if os.path.isdir(INSTANCE_MODS) else []
    _vanilla = os.path.join(os.environ.get("APPDATA", ""), "PrismLauncher", "libraries", "com",
                            "mojang", "minecraft", "1.21.1", "minecraft-1.21.1-client.jar")
    if os.path.isfile(_vanilla):
        _scan.append(_vanilla)
    if not _scan:
        print("  !! REMOVED ITEMS: no jars found - recipe disables NOT emitted, LEAKS not refreshed.")
    else:
        _scan_ok = True
        _raw = [r["id"] for r in _removed]
        for _jp in _scan:
            _jn = os.path.basename(_jp)
            try:
                _zf = zipfile.ZipFile(_jp)
            except zipfile.BadZipFile:
                continue
            with _zf:
                for _n in _zf.namelist():
                    _parts = _n.split("/")
                    # registered items, same rule jarindex uses: an item MODEL is the proof
                    if (len(_parts) >= 5 and _parts[0] == "assets" and _parts[2] == "models"
                            and _parts[3] == "item" and _n.endswith(".json")):
                        _items.add(f"{_parts[1]}:{'/'.join(_parts[4:])[:-5]}")
        # Brace expansion first: `foo_{a,b}` -> `foo_a`, `foo_b`. Lets one row say "this material,
        # these slots", which a bare `*` cannot - and a bare material glob over-matches every tool
        # and ingot in the mod (berlord 2026-07-30: l2complements:eternium_* is 12 items, not 4).
        def _braces(pat):
            i = pat.find("{")
            if i < 0:
                return [pat]
            j = pat.find("}", i)
            if j < 0:
                raise SystemExit(f"docs/removed: unclosed brace in {pat!r}")
            out = []
            for _opt in pat[i + 1:j].split(","):
                out += _braces(pat[:i] + _opt.strip() + pat[j + 1:])
            return out

        _removed = [dict(_r, id=_e) for _r in _removed for _e in _braces(_r["id"])]

        # expand globs now that we know what exists
        _expanded, _pattern_of = [], {}
        for _r in _removed:
            if "*" in _r["id"] or "?" in _r["id"]:
                _m = sorted(i for i in _items if fnmatch.fnmatchcase(i, _r["id"]))
                if not _m:
                    raise SystemExit(f"docs/removed: pattern {_r['id']!r} matched NOTHING. "
                                     f"A pattern that matches nothing is always a mistake.")
                print(f"  removed items: {_r['id']}  ->  {len(_m)} items")
                _expanded += _m
                for _i in _m:
                    _pattern_of[_i] = _r["id"]
            else:
                if _r["id"] not in _items:
                    raise SystemExit(f"docs/removed: {_r['id']!r} is not a registered item in this pack.")
                _expanded.append(_r["id"])
        _want = set(_expanded)
        # second pass: recipes and loot, now that we know the concrete ids
        for _jp in _scan:
            _jn = os.path.basename(_jp)
            try:
                _zf = zipfile.ZipFile(_jp)
            except zipfile.BadZipFile:
                continue
            with _zf:
                for _n in _zf.namelist():
                    if not _n.endswith(".json") or not _n.startswith("data/"):
                        continue
                    _is_recipe, _is_loot = "/recipe" in _n, "/loot_table" in _n
                    if not (_is_recipe or _is_loot):
                        continue
                    try:
                        _d = json.loads(_zf.read(_n).decode("utf-8-sig"))
                    except Exception:
                        continue
                    if _is_recipe:
                        for _r2 in _result_ids(_d, set()):
                            if _r2 in _want:
                                _hits.append((_n, _r2))
                    else:
                        _txt = json.dumps(_d)
                        for _r2 in _want:
                            if f'"{_r2}"' in _txt:
                                _leaks.setdefault(_r2, []).append(f"{_jn}: {_n}")

_removed_ids = sorted({i for i in (_expanded if _removed and _scan_ok else [])})
write("removed_items.json", _removed_ids)

# MANIFEST. gen_data only ever writes, so without this, deleting a row would leave its
# neoforge:false override behind and the item would stay uncraftable forever - which defeats the
# whole point of the list being reversible. This MUST run even when the list is empty: the first
# version gated it and deleting the last row left the override in place (caught end-to-end).
_manifest_path = os.path.join(ROOT, "texture-work", ".removed_recipes.json")
_old_manifest = []
if os.path.isfile(_manifest_path):
    with open(_manifest_path, encoding="utf-8") as _f:
        _old_manifest = json.load(_f)
_new_manifest = sorted({_p for _p, _ in _hits})
if _removed and not _scan_ok:
    _new_manifest = _old_manifest          # could not scan: change nothing rather than wipe
else:
    for _stale in sorted(set(_old_manifest) - set(_new_manifest)):
        _abs = os.path.join(RES, _stale.replace("/", os.sep))
        if os.path.isfile(_abs):
            os.remove(_abs)
            print(f"  removed items: re-enabled {_stale}")
    for _path in _new_manifest:
        write(_path, DISABLED)
    with open(_manifest_path, "w", encoding="utf-8", newline="\n") as _f:
        json.dump(_new_manifest, _f, indent=2)
print(f"  removed items: {len(_removed_ids)} ids, {len(_new_manifest)} recipes disabled, "
      f"{len(_leaks)} with loot leaks")

# Refresh the LEAKS block in every doc, replacing ONLY between the markers.
_OPEN = "<!-- LEAKS: generated every build, do not edit by hand -->"
_CLOSE = "<!-- /LEAKS -->"
if os.path.isdir(REMOVED_DOCS) and (not _removed or _scan_ok):
    for _fn in sorted(os.listdir(REMOVED_DOCS)):
        if not _fn.endswith(".md") or _fn == "README.md":
            continue
        _p = os.path.join(REMOVED_DOCS, _fn)
        _src = io.open(_p, encoding="utf-8").read()
        if _OPEN not in _src or _CLOSE not in _src:
            continue
        _body = []
        for _i in sorted(i for i in _removed_ids if i.split(":")[0] == _fn[:-3]):
            _l = _leaks.get(_i)
            if _l:
                _body.append(f"- **{_i}** — still referenced by {len(_l)} loot table(s):")
                _body += [f"  - `{x}`" for x in _l[:8]]
                if len(_l) > 8:
                    _body.append(f"  - ...and {len(_l) - 8} more")
        _block = ("\n\n## Leaks\n\nLoot tables that still reference a removed id, i.e. ways it can "
                  "still be obtained despite having no recipe.\n\n"
                  + ("\n".join(_body) if _body else "_None._") + "\n\n")
        _head, _rest = _src.split(_OPEN, 1)
        _tail = _rest.split(_CLOSE, 1)[1]
        io.open(_p, "w", encoding="utf-8", newline="\n").write(
            _head + _OPEN + _block + _CLOSE + _tail)

# ================================================================ Deep Waters Shrine ponder schematic
# The scene structure is generated from the SAME grid the matcher uses, and this script ASSERTS the
# two agree (it parses LAYERS straight out of DeepWatersShrineHandler.java). A ponder that teaches a
# shrine the handler would then reject is worse than no ponder at all, so the check is load-bearing.
SHRINE_LAYERS = [
    ["MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM"],  # L1 floor
    ["..SBS..", ".M...M.", "S.MMM.S", "B.MPM.B", "S.MMM.S", ".M...M.", "..SBS.."],  # L2
    [".......", ".M...M.", "..M.M..", "...C...", "..M.M..", ".M...M.", "......."],  # L3 conduit
    [".......", ".M...M.", "..MMM..", "..MPM..", "..MMM..", ".M...M.", "......."],  # L4
    ["MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM", "MMMMMMM"],  # L5 roof
    ["..SLS..", ".....B.", "S.S.S.S", "L...S.L", "SS...SS", ".......", "..SLS.."],  # L6 crystals
]
SHRINE_BLOCKS = {
    "M": "minecraft:mossy_stone_bricks",
    "P": "deepwaters:fopal_pillar",
    "C": "minecraft:conduit",
    "L": "deepwaters:cryslaaquamarine",
    "B": "deepwaters:crysmeaquamarine",
    "S": "deepwaters:cryssmaquamarine",
}

def _assert_shrine_matches_java():
    """Parse LAYERS out of the handler and fail loudly if it has drifted from SHRINE_LAYERS."""
    java = os.path.join(ROOT, "src", "main", "java", "com", "berlord", "bertie_progression",
                        "shrine", "DeepWatersShrineHandler.java")
    if not os.path.isfile(java):
        return
    import re as _re
    src = open(java, encoding="utf-8").read()
    body = src.split("String[][] LAYERS = {", 1)[1].split("\n    };", 1)[0]
    rows = _re.findall(r'"([.MPCLBS]{7})"', body)
    flat = [r for layer in SHRINE_LAYERS for r in layer]
    assert rows == flat, (
        "Deep Waters shrine schematic DRIFT: gen_data.SHRINE_LAYERS != "
        "DeepWatersShrineHandler.LAYERS\n"
        f"  java  ({len(rows)} rows): {rows}\n"
        f"  python({len(flat)} rows): {flat}")

_assert_shrine_matches_java()

def _write_shrine_nbt():
    """Vanilla structure NBT (gzipped) for the ponder scene: 7 wide x 6 tall x 7 deep."""
    import gzip, struct

    def _str(s):
        b = s.encode("utf-8")
        return struct.pack(">H", len(b)) + b

    def _named(tag_id, name, payload):
        return bytes([tag_id]) + _str(name) + payload

    palette, index = [], {}
    for ch, bid in SHRINE_BLOCKS.items():
        index[ch] = len(palette)
        palette.append(bid)

    blocks = []
    for y, layer in enumerate(SHRINE_LAYERS):
        for z, row in enumerate(layer):          # row 0 = north = z 0
            for x, ch in enumerate(row):
                if ch == ".":
                    continue
                blocks.append((x, y, z, index[ch]))

    # palette: TAG_List of TAG_Compound {Name:String}
    pal = b""
    for bid in palette:
        pal += _named(8, "Name", _str(bid)) + b"\x00"
    palette_tag = _named(9, "palette", bytes([10]) + struct.pack(">i", len(palette)) + pal)

    # CRITICAL: `size` and each block's `pos` are TAG_LIST OF TAG_INT (list type 9, element type 3),
    # NOT TAG_Int_Array (11). StructureTemplate.load reads them with getList(..., Tag.TAG_INT), which
    # returns an EMPTY list for an int-array — so an int-array version loads a 0x0x0 structure and
    # logs NOTHING. That produced a silently blank ponder scene. Verified against Create's own
    # assets/create/ponder/gauges.nbt, which uses list-of-int for both.
    def _int_list(*vals):
        return bytes([3]) + struct.pack(">i", len(vals)) + b"".join(struct.pack(">i", v) for v in vals)

    # blocks: TAG_List of TAG_Compound {pos:[list of 3 int], state:Int}
    blk = b""
    for x, y, z, st in blocks:
        pos = _named(9, "pos", _int_list(x, y, z))
        blk += pos + _named(3, "state", struct.pack(">i", st)) + b"\x00"
    blocks_tag = _named(9, "blocks", bytes([10]) + struct.pack(">i", len(blocks)) + blk)

    size_tag = _named(9, "size", _int_list(7, len(SHRINE_LAYERS), 7))
    entities_tag = _named(9, "entities", bytes([10]) + struct.pack(">i", 0))
    data_version = _named(3, "DataVersion", struct.pack(">i", 3955))   # 1.21.1

    root = _named(10, "", size_tag + entities_tag + palette_tag + blocks_tag
                  + data_version + b"\x00")

    path = os.path.join(RES, "assets", MODID, "ponder", "deepwaters_shrine.nbt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wb") as f:
        f.write(root)
    written.append("assets/bertie_progression/ponder/deepwaters_shrine.nbt")

_write_shrine_nbt()

# ---------------------------------------------------------------- tags

STRIPPED = [f"minecraft:stripped_{w}_log" for w in
            ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry"]] + \
           ["minecraft:stripped_crimson_stem", "minecraft:stripped_warped_stem", "minecraft:stripped_bamboo_block"]
write("data/bertie_progression/tags/item/stripped_logs.json", {"replace": False, "values": STRIPPED})
write("data/bertie_progression/tags/block/stripped_logs.json", {"replace": False, "values": STRIPPED})

# Natural in-world logs only (no stripped/wood variants) — quest-1 detection tag
NATURAL_LOGS = [f"minecraft:{w}_log" for w in
                ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry"]] + \
               ["minecraft:crimson_stem", "minecraft:warped_stem"]
write("data/bertie_progression/tags/item/natural_logs.json", {"replace": False, "values": NATURAL_LOGS})

# "Any meat" for the Aureal ritual. NOT #minecraft:meat — jar-checked, that tag holds ONLY modded
# meats in this pack (jerkies, dragon flesh, meef, crab) and not one vanilla cut, so a player holding
# beef could never finish the ritual. List the vanilla meats explicitly and pull the convention tags
# in optionally (required:false, so a missing tag is not a load error) to pick up modded ones too.
MEATS = [f"minecraft:{m}" for m in
         ["beef", "cooked_beef", "porkchop", "cooked_porkchop", "chicken", "cooked_chicken",
          "mutton", "cooked_mutton", "rabbit", "cooked_rabbit"]]
write("data/bertie_progression/tags/item/meat.json",
      {"replace": False,
       "values": MEATS + [{"id": t, "required": False} for t in
                          ("#minecraft:meat", "#c:foods/raw_meat", "#c:foods/cooked_meat")]})

# Hidden advancement fired by holding 8+ natural logs — the FTB "Get wood" quest task
write("data/bertie_progression/advancement/got_wood.json", {
    "criteria": {
        "got_wood": {
            "trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": "#bertie_progression:natural_logs", "count": {"min": 8}}]},
        }
    }
})

# Note 5 (2026-07-22): "copper tier" of minability. NOTE/DEVIATION: vanilla has no native tier
# between stone and iron, and Slag makes copper/bone = stone tier and flint <= stone (jar-verified
# tiers copper/bone/stone=3, flint=2, iron=4), so a true STONE-EXCLUDING copper tier isn't possible
# without custom Tier code + Slag tool overrides. Shipped as a STONE-tier gate: these ores drop out
# of needs_iron_tool into needs_stone_tool -> mineable before iron by stone/copper/bone tools (bone
# reliably; flint depends on Slag's internal mapping). `needs_copper_tool` is a forward marker for
# "add stuff later". Plain stone picks also work (can't be excluded here).
COPPER_TIER_ORES = ["forbidden_arcanus:arcane_crystal_ore", "forbidden_arcanus:deepslate_arcane_crystal_ore",
                    "minecraft:redstone_ore", "minecraft:deepslate_redstone_ore"]
# NeoForge tag remove requires a values key present alongside remove (vanilla TagLoader reads values first).
write("data/minecraft/tags/block/needs_iron_tool.json",
      {"replace": False, "values": [], "remove": COPPER_TIER_ORES})
write("data/minecraft/tags/block/needs_stone_tool.json", {"replace": False, "values": COPPER_TIER_ORES})
write("data/bertie_progression/tags/block/needs_copper_tool.json", {"replace": False, "values": COPPER_TIER_ORES})

# Ch1 gear quests detect the wooden PARTS (decision 2026-07-22: assembled modular gear has
# no stable predicate surface — no Slag triggers/advancements exist, and assembled component
# values are per-instance). Part component values are jar-verified from Slag-n-Embers 1.1a
# data/slag/recipe/crafting/parts/*_wooden.json; detection is source-agnostic (carved or crafted).
def _wooden_part(part):
    return {
        "trigger": "minecraft:inventory_changed",
        "conditions": {"items": [{
            "items": "slag:dynamic_part",
            "components": {"slag:material_type": "slag:wooden", "slag:part_type": f"slag:{part}"},
        }]},
    }

write("data/bertie_progression/advancement/wooden_armor_set.json", {
    "criteria": {part: _wooden_part(part) for part in ["helmet", "chestplate", "leggings", "boots"]},
    "requirements": [[part] for part in ["helmet", "chestplate", "leggings", "boots"]],
})

write("data/bertie_progression/advancement/wooden_pickaxe_head.json", {
    "criteria": {"head": _wooden_part("pickaxe_head")},
})

# Note 11: copper-tier pickaxe = flint OR bone pickaxe (either satisfies). Detect the head part.
def _mat_part(material, part):
    return {
        "trigger": "minecraft:inventory_changed",
        "conditions": {"items": [{
            "items": "slag:dynamic_part",
            "components": {"slag:material_type": f"slag:{material}", "slag:part_type": f"slag:{part}"},
        }]},
    }
write("data/bertie_progression/advancement/copper_pickaxe_head.json", {
    "criteria": {"flint": _mat_part("flint", "pickaxe_head"), "bone": _mat_part("bone", "pickaxe_head")},
    "requirements": [["flint", "bone"]],
})

# §5.5/R30: the Twilight portal accepts ONLY the Twilight Concord (stock tag = diamonds).
write("data/twilightforest/tags/item/portal/activator.json",
      {"replace": True, "values": [{"id": "bertie_progression:twilight_concord", "required": False}]})

# ================================================================ batch 19 (berlord 2026-07-31)

# --- Ur-Ghast Trophy duplication, on the Spirit Altar. One trophy in, two out: the trophy is the
#     infusion INPUT (Malum consumes it) so the recipe pays for itself once and profits thereafter.
#     Five extraInputs, which spirit_infusion allows - its cap is pedestals reachable in the 4x3x4
#     capture box, NOT the Hephaestus 8-pedestal rule. Blood Vial is irons_spellbooks:blood_vial
#     (jar-verified by lang value + item model), Dragon Bone is iceandfire:dragonbone. ---
write("data/malum/recipe/spirit_infusion/ur_ghast_trophy_dupe.json",
      infusion("twilightforest:ur_ghast_trophy", 1,
               [("minecraft:bone_block", 16), ("irons_spellbooks:blood_vial", 6),
                ("iceandfire:dragonbone", 6), ("minecraft:ghast_tear", 4),
                ("minecraft:fire_charge", 8)],
               [SP("wicked", 6), SP("eldritch", 6), SP("aerial", 6), SP("infernal", 6)],
               "twilightforest:ur_ghast_trophy", 2))

# ---------------------------------------------------------------- assets

ITEMS = {
    "opening_mallet": "Opening Mallet",
    "stone_crucible_blank": "Stone Crucible Blank",
    "stone_pour_channel": "Stone Pour Channel",
    "weeping_eye": "Weeping Eye",
    "kinetic_vane": "Structural Beam",
    "incomplete_structural_beam": "Incomplete Structural Beam",
    "incomplete_small_water_wheel": "Incomplete Water Wheel",
    "incomplete_large_water_wheel": "Incomplete Large Water Wheel",
    "shield_maiden": "Shield Maiden",
    "acolyte_of_deflection": "Acolyte of Deflection",
    "netherly_meal": "Netherly Meal",
    "sirok_nest_map": "Sirok's Nest Map",
    "kraken_ship_map": "Kraken Ship Map",
    "yeti_hideout_map": "Skor's Hideout Map",
    "abyssal_core": "Abyssal Core",
    "desert_core": "Desert Core",
    "cursed_core": "Cursed Core",
    "storm_core": "Storm Core",
    "kinetic_pattern_plate": "Kinetic Pattern Plate",
    "crafting_license": "Crafting License",
    "twilight_concord": "Twilight Concord",
    "spirit_focused_echo": "Spirit-Focused Echo",
    "runewood_resonance": "Runewood Resonance",
    "warden_echo_pattern": "Warden Echo Pattern",
    "echoing_city_compass": "Echoing City Compass",
    "weeping_compass": "Weeping Compass",
    "well_attunement": "Well Attunement",
    "descent_anchor": "Descent Anchor",
    "complex_spectrum_seal": "Complex Spectrum Seal",
    "soulbound_authority": "Soulbound Authority",
    "ignitium_lattice": "Ignitium Lattice",
    "ignitium_strut": "Ignitium Strut",
    "dragonbone_frame": "Dragonbone Frame",
    "dragonbone_brace": "Dragonbone Brace",
    "concordant_moonsteel_ingot": "Concordant Moonsteel Ingot",
    "hephaestian_sovereign_seal": "Hephaestian Sovereign Seal",
    "convergence_matrix": "Convergence Matrix",
    "mekanism_access_core": "Mekanism Access Core",
    "boss_rematch_seal": "Boss Rematch Seal",
}

BLOCKS = {
    "echo_lock": "Echo Lock",
}

# item models
for item_id in ITEMS:
    write(f"assets/bertie_progression/models/item/{item_id}.json",
          {"parent": "minecraft:item/generated", "textures": {"layer0": f"bertie_progression:item/{item_id}"}})
# Weeping Eye reuses vanilla's Eye of Ender model/texture (no bespoke texture needed).
write("assets/bertie_progression/models/item/weeping_eye.json", {"parent": "minecraft:item/ender_eye"})
# Crafting License borrows vanilla's paper model (no bespoke texture yet).
write("assets/bertie_progression/models/item/crafting_license.json", {"parent": "minecraft:item/paper"})
# Sirok's Nest Map borrows vanilla's empty-map model (no bespoke texture yet - berlord has not sent one).
for _m in ("sirok_nest_map", "kraken_ship_map", "yeti_hideout_map"):
    write(f"assets/bertie_progression/models/item/{_m}.json", {"parent": "minecraft:item/map"})
# These cores have no bespoke texture yet - each borrows a vanilla item that reads close to
# its element, so they are at least distinguishable on sight. storm_core is NOT in this list:
# it has real art (texture-work/make_storm_core.py) and takes the generated model written by
# the ITEMS loop above. Re-adding it here would hide that texture behind an amethyst shard.
for _c, _par in (("abyssal_core", "minecraft:item/heart_of_the_sea"),
                 ("desert_core", "minecraft:item/brick"),
                 ("cursed_core", "minecraft:item/echo_shard")):
    write(f"assets/bertie_progression/models/item/{_c}.json", {"parent": _par})
# Transitional sequenced-assembly items: beam reuses a vanilla stick; water-wheel incompletes reuse the
# real wheel item models (berlord: "incomplete [large/small] water wheel uses [large/small] water wheel").
write("assets/bertie_progression/models/item/incomplete_structural_beam.json",
      {"parent": "minecraft:item/generated", "textures": {"layer0": "minecraft:item/stick"}})
write("assets/bertie_progression/models/item/incomplete_small_water_wheel.json", {"parent": "create:item/water_wheel"})
write("assets/bertie_progression/models/item/incomplete_large_water_wheel.json", {"parent": "create:item/large_water_wheel"})

# block models + blockstates + block items
for block_id in BLOCKS:
    write(f"assets/bertie_progression/models/block/{block_id}.json",
          {"parent": "minecraft:block/cube_all", "textures": {"all": f"bertie_progression:block/{block_id}"}})
    write(f"assets/bertie_progression/blockstates/{block_id}.json",
          {"variants": {"": {"model": f"bertie_progression:block/{block_id}"}}})
    write(f"assets/bertie_progression/models/item/{block_id}.json",
          {"parent": f"bertie_progression:block/{block_id}"})

# lang
lang = {"itemGroup.bertie_progression": "Bertie Progression"}
for item_id, name in ITEMS.items():
    lang[f"item.bertie_progression.{item_id}"] = name
for block_id, name in BLOCKS.items():
    lang[f"block.bertie_progression.{block_id}"] = name
lang.update({
    "message.bertie_progression.table_unlicensed": "You do not know how to use a crafting grid yet - consume a Crafting License first.",
    "message.bertie_progression.crafting_licensed": "The crafting language settles into your hands. The 3x3 grid is yours.",
    "message.bertie_progression.already_licensed": "You already hold the crafting language.",
    "message.bertie_progression.forge_formed": "The Brick Forge roars to life!",
    "message.bertie_progression.pedestal_formed": "The darkstone column settles into a pedestal.",
    # Ponder scene text. Ponder does NOT fall back to the literal passed to .text(...) — it looks up
    # "<modid>.ponder.<sceneId>.header" / ".text_N", numbered in the order the showText calls run.
    # Without these the scene shows raw lang keys. Keep in step with ShrinePonderPlugin.
    "bertie_progression.ponder.deepwaters_shrine.header": "Raising the Deep Waters Shrine",
    "bertie_progression.ponder.deepwaters_shrine.text_1": "Seven by seven of Mossy Stone Bricks. Build it underwater, in the Deep Waters - nowhere else works.",
    "bertie_progression.ponder.deepwaters_shrine.text_2": "A Flaming Opal Pillar at the centre, wrapped in a solid three by three, with four posts on the diagonals.",
    "bertie_progression.ponder.deepwaters_shrine.text_3": "Aquamarine crystals ring the edge - Small at the corners of each face, a Bundle in the middle.",
    "bertie_progression.ponder.deepwaters_shrine.text_4": "The Conduit sits at the very centre, held in a diagonal lattice. This is the heart of the shrine.",
    "bertie_progression.ponder.deepwaters_shrine.text_5": "Above the Conduit, the pillar and the posts repeat - but no crystals this time.",
    "bertie_progression.ponder.deepwaters_shrine.text_6": "Cap it with a second seven by seven roof.",
    "bertie_progression.ponder.deepwaters_shrine.text_7": "Crown it with crystals. This layer is NOT symmetrical - copy it exactly. The centre stays empty.",
    "bertie_progression.ponder.deepwaters_shrine.text_8": "Any rotation works. Leave water around the shrine and a clear column above it, or nothing will happen.",
    "bertie_progression.ponder.deepwaters_shrine.text_9": "Use a Crowned Jelly on the Conduit.",
    "bertie_progression.ponder.deepwaters_shrine.text_10": "The shrine floods, and a Stormcall Altar rises on a pyramid of Polished Azure Seastone where the Conduit stood.",
    "message.bertie_progression.shrine_no_space": "not enough space",
    "message.bertie_progression.shrine_formed": "The shrine floods, and the Stormcall Altar rises.",
    "message.bertie_progression.paper_need_cane": "You need at least 3 Sugar Cane to press paper.",
    "message.bertie_progression.paper_need_slates": "You need two Wood Slates in your inventory to press paper.",
    "message.bertie_progression.no_imbrifer": "Imbrifer (pastel:deeper_down) is not present in this world.",
    "message.bertie_progression.descended": "The anchor drags you down into Imbrifer.",
    "message.bertie_progression.locator_searching": "The needle spins, searching...",
    "message.bertie_progression.locator_missing": "Target structure %s is not present in this world.",
    "message.bertie_progression.locator_none": "No target found within range.",
    "message.bertie_progression.locator_found": "%s located near X=%s, Z=%s.",
    # FinderItem (batch 17). Separate keys from the locator's: a finder consumes itself into a map.
    "message.bertie_progression.finder_searching": "The chart darkens, reading the land...",
    "message.bertie_progression.finder_missing": "Nothing like %s exists in this world.",
    "message.bertie_progression.finder_none": "Nothing within range. Carry the chart further and try again.",
    "message.bertie_progression.finder_found": "The chart is now a map. X=%s, Z=%s.",
    "message.bertie_progression.nether_locked": "The heat refuses you. Eat a Netherly Meal first.",
    "item.bertie_progression.sirok_nest_map.filled": "Map to Sirok's Nest",
    "item.bertie_progression.kraken_ship_map.filled": "Map to the Kraken's Ship",
    "item.bertie_progression.yeti_hideout_map.filled": "Map to Skor's Hideout",
})
write("assets/bertie_progression/lang/en_us.json", lang)

print(f"Wrote {len(written)} files under {RES}")
