package com.berlord.bertie_s1.forge;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * Darkstone Pedestal world-formation (berlord 2026-07-22, replaces the R09A bed recipe).
 * Build a 3-high column — Arcane Polished Darkstone Pillar (bottom) + Wall + Slab (top) — and
 * apply Mundabitur Dust to the pillar (the same dust the Hephaestus Forge formation uses). The
 * column collapses into a Darkstone Pedestal at the pillar's position.
 */
public final class PedestalFormationHandler {

    private static final ResourceLocation MUNDABITUR =
            ResourceLocation.parse("forbidden_arcanus:mundabitur_dust");
    private static final ResourceLocation PILLAR =
            ResourceLocation.parse("forbidden_arcanus:arcane_polished_darkstone_pillar");
    private static final ResourceLocation WALL =
            ResourceLocation.parse("forbidden_arcanus:arcane_polished_darkstone_wall");
    private static final ResourceLocation SLAB =
            ResourceLocation.parse("forbidden_arcanus:arcane_polished_darkstone_slab");
    private static final ResourceLocation PEDESTAL =
            ResourceLocation.parse("forbidden_arcanus:darkstone_pedestal");

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() != InteractionHand.MAIN_HAND) return;
        Player player = event.getEntity();
        ItemStack held = event.getItemStack();
        if (!BuiltInRegistries.ITEM.getKey(held.getItem()).equals(MUNDABITUR)) return;

        Level level = event.getLevel();
        BlockPos pillarPos = event.getPos();
        if (!isBlock(level, pillarPos, PILLAR)) return;
        if (!isBlock(level, pillarPos.above(), WALL)) return;
        if (!isBlock(level, pillarPos.above(2), SLAB)) return;

        Block pedestal = BuiltInRegistries.BLOCK.get(PEDESTAL);
        if (pedestal == Blocks.AIR) return; // FA absent — leave the interaction alone

        event.setCanceled(true);
        if (level.isClientSide) return;

        level.removeBlock(pillarPos.above(2), false);
        level.removeBlock(pillarPos.above(), false);
        level.setBlockAndUpdate(pillarPos, pedestal.defaultBlockState());
        level.playSound(null, pillarPos, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.BLOCKS, 1f, 1.2f);
        if (!held.isEmpty() && !player.getAbilities().instabuild) held.shrink(1);
        player.displayClientMessage(Component.translatable("message.bertie_s1.pedestal_formed"), true);
    }

    private static boolean isBlock(Level level, BlockPos pos, ResourceLocation id) {
        BlockState state = level.getBlockState(pos);
        return BuiltInRegistries.BLOCK.getKey(state.getBlock()).equals(id);
    }

    private PedestalFormationHandler() {}
}
