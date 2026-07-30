package com.berlord.bertie_s1.item;

import com.mojang.datafixers.util.Pair;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.Optional;

/**
 * Single-target structure locator (R30A Echoing City Compass -> minecraft:ancient_city,
 * R37D Weeping Compass -> malum:weeping_well). Never lists arbitrary structures.
 */
public class LocatorItem extends Item {

    private final ResourceLocation structureId;
    /** Chunks. berlord 2026-07-29: 500 is the standard; kept per-item so one can be tuned alone. */
    private final int searchRadius;

    public LocatorItem(Properties properties, ResourceLocation structureId, int searchRadius) {
        super(properties);
        this.structureId = structureId;
        this.searchRadius = searchRadius;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, structureId);
        Optional<Holder.Reference<Structure>> holder =
                serverLevel.registryAccess().registryOrThrow(Registries.STRUCTURE).getHolder(key);
        if (holder.isEmpty()) {
            serverPlayer.displayClientMessage(
                    Component.translatable("message.bertie_s1.locator_missing", structureId.toString()), true);
            return InteractionResultHolder.fail(stack);
        }
        serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.locator_searching"), true);
        Pair<BlockPos, Holder<Structure>> found = serverLevel.getChunkSource().getGenerator()
                .findNearestMapStructure(serverLevel, HolderSet.direct(holder.get()),
                        serverPlayer.blockPosition(), searchRadius, false);
        if (found == null) {
            serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.locator_none"), true);
            return InteractionResultHolder.fail(stack);
        }
        BlockPos pos = found.getFirst();
        serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.locator_found",
                structureId.toString(), pos.getX(), pos.getZ()), false);
        return InteractionResultHolder.consume(stack);
    }
}
