package com.berlord.bertie_s1;

import com.berlord.bertie_s1.item.CraftingLicenseItem;
import com.berlord.bertie_s1.item.DescentAnchorItem;
import com.berlord.bertie_s1.item.FinderItem;
import com.berlord.bertie_s1.item.LocatorItem;
import com.berlord.bertie_s1.item.NetherlyMealItem;
import com.berlord.bertie_s1.item.WeepingEyeItem;
import com.mojang.serialization.Codec;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Rarity;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(BertieS1.MODID);
    public static final DeferredRegister<DataComponentType<?>> DATA_COMPONENTS =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, BertieS1.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, BertieS1.MODID);

    public static final Supplier<DataComponentType<GlobalPos>> RETURN_POS = DATA_COMPONENTS.register(
            "return_pos", () -> DataComponentType.<GlobalPos>builder()
                    .persistent(GlobalPos.CODEC).networkSynchronized(GlobalPos.STREAM_CODEC).build());

    /**
     * Set by {@link FinderItem#onCraftedBy} and consumed by its inventoryTick. It is the only signal
     * that separates a player craft from an autocrafted one - onCraftedBy never fires without a player.
     */
    public static final Supplier<DataComponentType<Boolean>> PLAYER_CRAFTED = DATA_COMPONENTS.register(
            "player_crafted", () -> DataComponentType.<Boolean>builder()
                    .persistent(Codec.BOOL).networkSynchronized(ByteBufCodecs.BOOL).build());

    private static final List<DeferredItem<? extends Item>> ALL = new ArrayList<>();

    private static DeferredItem<Item> simple(String id, int stack) {
        DeferredItem<Item> it = ITEMS.registerSimpleItem(id, new Item.Properties().stacksTo(stack));
        ALL.add(it);
        return it;
    }

    private static DeferredItem<Item> rare(String id, int stack, Rarity rarity) {
        DeferredItem<Item> it = ITEMS.registerSimpleItem(id, new Item.Properties().stacksTo(stack).rarity(rarity));
        ALL.add(it);
        return it;
    }

    // --- Opening / foundry (plan §2.1) ---
    public static final DeferredItem<Item> OPENING_MALLET = ITEMS.registerSimpleItem(
            "opening_mallet", new Item.Properties().stacksTo(1).durability(256));
    public static final DeferredItem<Item> STONE_CRUCIBLE_BLANK = simple("stone_crucible_blank", 16);
    public static final DeferredItem<Item> STONE_POUR_CHANNEL = simple("stone_pour_channel", 16);

    // --- Create bridge ---
    public static final DeferredItem<Item> KINETIC_VANE = simple("kinetic_vane", 64);
    // Transitional items for the Create sequenced-assembly recipes (batch 8): structural beam + water wheels.
    public static final DeferredItem<Item> INCOMPLETE_STRUCTURAL_BEAM = simple("incomplete_structural_beam", 64);
    public static final DeferredItem<Item> INCOMPLETE_SMALL_WATER_WHEEL = simple("incomplete_small_water_wheel", 64);
    public static final DeferredItem<Item> INCOMPLETE_LARGE_WATER_WHEEL = simple("incomplete_large_water_wheel", 64);
    // Shield Maiden (batch 8): naga-trophy ritual output; grants access to the Twilight Lich. Dupe-able.
    public static final DeferredItem<Item> SHIELD_MAIDEN = simple("shield_maiden", 16);
    // Acolyte of Deflection (batch 17): the same idea one boss on - a lich-trophy ritual output that
    // takes over from the raw trophy as the gate to what follows the Lich.
    public static final DeferredItem<Item> ACOLYTE_OF_DEFLECTION = simple("acolyte_of_deflection", 16);
    public static final DeferredItem<Item> KINETIC_PATTERN_PLATE = simple("kinetic_pattern_plate", 16);

    // --- Table license chain ---
    // (Crafting Language Slate/Seal and the Spirit Altar Witness were dropped, berlord batch 4.)
    /** Consumable: permanently unlocks the 3x3 grid for the player who uses it. */
    public static final DeferredItem<CraftingLicenseItem> CRAFTING_LICENSE = ITEMS.register(
            "crafting_license", () -> new CraftingLicenseItem(
                    new Item.Properties().stacksTo(1).rarity(Rarity.RARE)));

    // --- Portals / dimension keys ---
    // NETHER_LINTEL and NETHER_LINTEL_CORE removed 2026-07-31 (berlord): obsolete now the Nether is
    // entered by eating a Netherly Meal. Nothing else consumed either item.
    public static final DeferredItem<Item> TWILIGHT_CONCORD = simple("twilight_concord", 16);
    public static final DeferredItem<DescentAnchorItem> DESCENT_ANCHOR = ITEMS.register(
            "descent_anchor", () -> new DescentAnchorItem(new Item.Properties().stacksTo(1).rarity(Rarity.RARE)));

    // --- Altar witnesses / resonances ---
    public static final DeferredItem<Item> RUNEWOOD_RESONANCE = simple("runewood_resonance", 1);
    // ARCANA_RESONANCE removed 2026-07-31 (berlord): no recipe ever consumed it.

    // --- Deep dark / echo chain ---
    public static final DeferredItem<Item> WARDEN_ECHO_PATTERN = rare("warden_echo_pattern", 1, Rarity.UNCOMMON);
    public static final DeferredItem<Item> SPIRIT_FOCUSED_ECHO = simple("spirit_focused_echo", 16);
    public static final DeferredItem<LocatorItem> ECHOING_CITY_COMPASS = ITEMS.register(
            "echoing_city_compass", () -> new LocatorItem(new Item.Properties().stacksTo(1),
                    ResourceLocation.parse("minecraft:ancient_city"), FinderItem.STANDARD_RADIUS));
    public static final DeferredItem<LocatorItem> WEEPING_COMPASS = ITEMS.register(
            "weeping_compass", () -> new LocatorItem(new Item.Properties().stacksTo(1),
                    ResourceLocation.parse("malum:weeping_well"), FinderItem.STANDARD_RADIUS));
    public static final DeferredItem<WeepingEyeItem> WEEPING_EYE = ITEMS.register(
            "weeping_eye", () -> new WeepingEyeItem(new Item.Properties().stacksTo(16),
                    ResourceLocation.parse("malum:weeping_well"), FinderItem.STANDARD_RADIUS));
    public static final DeferredItem<Item> WELL_ATTUNEMENT = rare("well_attunement", 1, Rarity.RARE);

    /**
     * Netherly Meal: 8 nutrition, saturation 20. Vanilla stores saturation as a MODIFIER, and the
     * real value is nutrition * modifier * 2 - so 20 saturation off 8 nutrition needs 1.25f, not 20f.
     */
    public static final DeferredItem<NetherlyMealItem> NETHERLY_MEAL = ITEMS.register(
            "netherly_meal", () -> new NetherlyMealItem(new Item.Properties().stacksTo(16)
                    .food(new FoodProperties.Builder().nutrition(8).saturationModifier(1.25F).build())));

    // --- Finders (batch 17): craftable charts that resolve into a real exploration map. See FinderItem. ---
    public static final DeferredItem<FinderItem> SIROK_NEST_MAP = ITEMS.register(
            "sirok_nest_map", () -> new FinderItem(new Item.Properties().stacksTo(16),
                    ResourceLocation.parse("block_factorys_bosses:sandworm_nest"),
                    "item.bertie_s1.sirok_nest_map.filled", FinderItem.STANDARD_RADIUS));
    public static final DeferredItem<FinderItem> KRAKEN_SHIP_MAP = ITEMS.register(
            "kraken_ship_map", () -> new FinderItem(new Item.Properties().stacksTo(16),
                    ResourceLocation.parse("block_factorys_bosses:kraken_ship"),
                    "item.bertie_s1.kraken_ship_map.filled", FinderItem.STANDARD_RADIUS));
    public static final DeferredItem<FinderItem> YETI_HIDEOUT_MAP = ITEMS.register(
            "yeti_hideout_map", () -> new FinderItem(new Item.Properties().stacksTo(16),
                    ResourceLocation.parse("block_factorys_bosses:yeti_hideout"),
                    "item.bertie_s1.yeti_hideout_map.filled", FinderItem.STANDARD_RADIUS));

    // --- Elemental cores (batch 17c): the four 7x7 crafter walls that converge on the Nether. ---
    public static final DeferredItem<Item> ABYSSAL_CORE = simple("abyssal_core", 16);
    public static final DeferredItem<Item> DESERT_CORE = simple("desert_core", 16);
    public static final DeferredItem<Item> CURSED_CORE = simple("cursed_core", 16);
    public static final DeferredItem<Item> STORM_CORE = simple("storm_core", 16);

    // --- Final altars / capstone ---
    public static final DeferredItem<Item> COMPLEX_SPECTRUM_SEAL = rare("complex_spectrum_seal", 16, Rarity.RARE);
    public static final DeferredItem<Item> SOULBOUND_AUTHORITY = rare("soulbound_authority", 16, Rarity.RARE);
    public static final DeferredItem<Item> IGNITIUM_LATTICE = rare("ignitium_lattice", 4, Rarity.RARE);
    public static final DeferredItem<Item> IGNITIUM_STRUT = rare("ignitium_strut", 16, Rarity.UNCOMMON);
    public static final DeferredItem<Item> DRAGONBONE_FRAME = rare("dragonbone_frame", 4, Rarity.RARE);
    public static final DeferredItem<Item> DRAGONBONE_BRACE = rare("dragonbone_brace", 16, Rarity.UNCOMMON);
    public static final DeferredItem<Item> CONCORDANT_MOONSTEEL_INGOT = rare("concordant_moonsteel_ingot", 64, Rarity.RARE);
    public static final DeferredItem<Item> HEPHAESTIAN_SOVEREIGN_SEAL = rare("hephaestian_sovereign_seal", 16, Rarity.RARE);
    public static final DeferredItem<Item> CONVERGENCE_MATRIX = rare("convergence_matrix", 4, Rarity.EPIC);
    public static final DeferredItem<Item> MEKANISM_ACCESS_CORE = rare("mekanism_access_core", 1, Rarity.EPIC);
    public static final DeferredItem<Item> BOSS_REMATCH_SEAL = simple("boss_rematch_seal", 16);

    // --- Block items ---
    public static final DeferredItem<BlockItem> ECHO_LOCK_ITEM =
            ITEMS.registerSimpleBlockItem(ModBlocks.ECHO_LOCK);

    public static final Supplier<CreativeModeTab> MAIN_TAB = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.bertie_s1"))
            .icon(() -> new ItemStack(MEKANISM_ACCESS_CORE.get()))
            .displayItems((params, out) -> {
                out.accept(OPENING_MALLET.get());
                for (DeferredItem<? extends Item> it : ALL) out.accept(it.get());
                out.accept(DESCENT_ANCHOR.get());
                out.accept(ECHOING_CITY_COMPASS.get());
                out.accept(WEEPING_COMPASS.get());
                out.accept(WEEPING_EYE.get());
                out.accept(NETHERLY_MEAL.get());
                out.accept(SIROK_NEST_MAP.get());
                out.accept(KRAKEN_SHIP_MAP.get());
                out.accept(YETI_HIDEOUT_MAP.get());
                out.accept(CRAFTING_LICENSE.get());
                out.accept(ECHO_LOCK_ITEM.get());
            })
            .build());

    private ModItems() {}
}
