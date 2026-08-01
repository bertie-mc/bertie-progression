package com.berlord.bertie_progression.item;

import com.berlord.bertie_progression.ModItems;
import com.mojang.datafixers.util.Pair;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.MapItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.saveddata.maps.MapDecorationTypes;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;

import java.util.Optional;

/**
 * A "finder": a craftable chart that turns itself into a real exploration map of one structure.
 *
 * <p>Why this exists rather than a recipe that simply outputs a map: a map to a structure cannot be a
 * recipe RESULT. {@code Recipe.assemble(input, HolderLookup.Provider)} is handed registries and
 * nothing else - no level, no position - because the result is computed speculatively for the grid
 * preview, for EMI and the recipe book, and for autocrafters that have no player. Locating needs
 * {@code ChunkGenerator.findNearestMapStructure(ServerLevel, ..., BlockPos, ...)}, i.e. exactly the
 * two things assemble() lacks. Vanilla has the same constraint, which is why its treasure maps come
 * from the {@code minecraft:exploration_map} LOOT function (a LootContext carries level + origin).
 *
 * <p>So the craft outputs this item, and the resolve happens at a moment that does have a world:
 * <ul>
 *   <li><b>Player craft</b> - {@link #onCraftedBy} stamps {@code bertie_progression:player_crafted} on the
 *       stack; the next {@link #inventoryTick} in a server player's inventory resolves it.</li>
 *   <li><b>Any other craft</b> (mechanical crafter, no player) - no flag is ever set, so it stays a
 *       finder until someone right-clicks it.</li>
 *   <li><b>Locate fails</b> (wrong dimension, out of range, structure absent) - it stays a finder and
 *       says so. Nothing is consumed and no blank map is produced, so it can be retried elsewhere.</li>
 * </ul>
 *
 * <p>The flag is cleared before the search runs, so a failed resolve happens ONCE. A radius-500
 * search is blocking and must never end up on a tick loop.
 */
public class FinderItem extends Item {

    /** Chunks, not blocks. Each item carries its own radius so it can be tuned independently. */
    public static final int STANDARD_RADIUS = 500;

    private final ResourceLocation structureId;
    private final String mapNameKey;
    private final int searchRadius;

    public FinderItem(Properties properties, ResourceLocation structureId, String mapNameKey,
                      int searchRadius) {
        super(properties);
        this.structureId = structureId;
        this.mapNameKey = mapNameKey;
        this.searchRadius = searchRadius;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        ItemStack map = resolve(serverLevel, serverPlayer);
        if (map == null) {
            return InteractionResultHolder.fail(stack);   // still a finder, nothing lost
        }
        // MUST go through ItemUtils, NOT shrink()+inventory.add(). Shrinking a single-item stack frees
        // the held slot, Inventory.add then drops the map straight into that slot, and vanilla's
        // useItem finishes by calling setItemInHand(hand, <the stack we returned>) - which overwrites
        // the map with the emptied chart. That is exactly how the first build lost both maps while
        // still allocating map_5.dat / map_6.dat. createFilledResult does the swap in the right order.
        return InteractionResultHolder.sidedSuccess(
                ItemUtils.createFilledResult(stack, serverPlayer, map, false), false);
    }

    /**
     * Marks the stack as player-crafted. This flag is the ONLY thing separating a player craft from
     * an autocrafted one - {@code onCraftedBy} is not called without a player.
     */
    @Override
    public void onCraftedBy(ItemStack stack, Level level, Player player) {
        stack.set(ModItems.PLAYER_CRAFTED.get(), true);
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (level.isClientSide
                || !(level instanceof ServerLevel serverLevel)
                || !(entity instanceof ServerPlayer serverPlayer)
                || !Boolean.TRUE.equals(stack.get(ModItems.PLAYER_CRAFTED.get()))) {
            return;
        }
        // Clear FIRST: one attempt, whatever happens. Never retry a blocking search on a tick.
        stack.remove(ModItems.PLAYER_CRAFTED.get());
        ItemStack map = resolve(serverLevel, serverPlayer);
        if (map == null) {
            return;   // stays a finder; right-click retries it somewhere better
        }
        // Add BEFORE shrinking: shrinking first frees this slot and Inventory.add would reuse it,
        // which is the same slot-collision that broke the use() path.
        give(serverPlayer, map);
        stack.shrink(1);
    }

    /** @return the finished map, or null if the structure could not be located (caller keeps the finder). */
    private ItemStack resolve(ServerLevel level, ServerPlayer player) {
        ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, structureId);
        Optional<Holder.Reference<Structure>> holder =
                level.registryAccess().registryOrThrow(Registries.STRUCTURE).getHolder(key);
        if (holder.isEmpty()) {
            player.displayClientMessage(Component.translatable(
                    "message.bertie_progression.finder_missing", structureId.toString()), true);
            return null;
        }
        player.displayClientMessage(Component.translatable("message.bertie_progression.finder_searching"), true);
        Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator()
                .findNearestMapStructure(level, HolderSet.direct(holder.get()),
                        player.blockPosition(), searchRadius, false);
        if (found == null) {
            player.displayClientMessage(Component.translatable("message.bertie_progression.finder_none"), true);
            return null;
        }
        BlockPos pos = found.getFirst();
        // Same construction the vanilla exploration_map loot function uses: a scale-2 map centred on
        // the structure, biome-preview rendered, with a target decoration pinned on it.
        ItemStack map = MapItem.create(level, pos.getX(), pos.getZ(), (byte) 2, true, true);
        MapItem.renderBiomePreviewMap(level, map);
        MapItemSavedData.addTargetDecoration(map, pos, "+", MapDecorationTypes.RED_X);
        map.set(DataComponents.ITEM_NAME, Component.translatable(mapNameKey));
        player.displayClientMessage(Component.translatable(
                "message.bertie_progression.finder_found", pos.getX(), pos.getZ()), false);
        return map;
    }

    private static void give(ServerPlayer player, ItemStack map) {
        if (!player.getInventory().add(map)) {
            player.drop(map, false);
        }
    }
}
